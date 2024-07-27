import uuid
from typing import Any
from urllib.parse import urlparse

import httpx
from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import RedirectResponse

from .identity_owner import IdentityOwner
from .models.authorization_request_object import AuthorizationRequestObject
from .models.authorization_response_object import AuthorizationResponseObject
from .models.credentials import Credential, DeferredCredential
from .models.field_selection_object import FieldSelectionObject
from .models.presentation_submission_object import (
    DescriptorMapObject,
    PresentationSubmissionObject,
)
from .models.request_body import CredentialSelection


class WebIdentityOwner(IdentityOwner):
    """
    IdentityOwner that implements a HTTP API interface.
    """

    def __init__(
        self,
        redirect_uris: list[str],
        cred_offer_endpoint: str,
        *,
        oauth_client_options: dict[str, Any] = {},
        dev_mode: bool = False,
    ):
        """
        Create a new Identity Owner

        ### Parameters
        - redirect_uris(`list[str]`): A list of redirect URIs to register with issuers.
        It is the caller's responsibility to ensure these match with the API.
        - cred_offer_endpoint(`str`): The credential offer URI, e.g.
        "https://example.com/offer". The routes for receiving credential offers, and
        redirecting the user to authorise based on a credential offer, are dynamically
        determined by parsing this URI with `urllib.parse.urlparse` and retrieving the
        path.
        - oauth_client_options(`dict = {}`): A dictionary containing optional overrides
        for the wallet's OAuth client info, used in registration of new clients. See
        `WalletClientMetadata` for accepted fields.
        Note that even if keys `"redirect_uris"` or `"credential_offer_endpoint"` are
        provided, they will be overwritten by their respective positional arguments.
        """

        # Referenced in `get_server`
        offer_path = urlparse(cred_offer_endpoint).path
        self._credential_offer_endpoint = offer_path

        oauth_client_info = oauth_client_options
        oauth_client_info["redirect_uris"] = redirect_uris
        oauth_client_info["credential_offer_endpoint"] = cred_offer_endpoint
        super().__init__(oauth_client_info, dev_mode=dev_mode)
        self.current_transaction: AuthorizationRequestObject | None = None

    def get_server(self) -> FastAPI:
        router = FastAPI()

        router.get("/credentials/{cred_id}")(self.get_credential)
        router.get("/credentials")(self.get_credentials)
        router.delete("/credentials/{cred_id}")(self.delete_credential)
        router.get("/refresh/{cred_id}")(self.refresh_credential)
        router.get("/refresh")(self.refresh_all_deferred_credentials)
        router.get("/presentation/init")(self.get_auth_request)
        router.post("/presentation/")(self.present_selection)

        # Issuance (offer) endpoints
        router.get(self._credential_offer_endpoint)(self.get_credential_offer)
        router.post(self._credential_offer_endpoint)(self.request_authorization)
        # Might change this later from /add to something else
        router.get("/add")(self.get_access_token_and_credentials_from_callback)

        return router

    async def get_credential(
        self, cred_id: str, refresh: int = 1
    ) -> Credential | DeferredCredential:
        """
        Gets a credential by ID, if one exists

        ### Parameters
        - cred_id(`str`): The ID of the credential, as kept by the owner
        - refresh(`int = 1`): Whether or not to refresh the credential, if currently
        deferred. Expressed as an int for the purposes of making it easier to pass
        in the request URL as a query parameter. 0 is `False`, any other number is
        interpreted as `True` (default).

        ### Returns
        - `Credential | DeferredCredential`: The requested credential, if it exists.
        """
        r = refresh != 0
        try:
            return await super()._get_credential(cred_id, refresh=r)
        except Exception:
            raise HTTPException(
                status_code=400, detail=f"Credential with ID {cred_id} not found."
            )

    async def get_credentials(self) -> list[Credential | DeferredCredential]:
        """
        Gets all credentials
        TODO: Adjust when storage implemented

        ### Returns
        - `list[Credential | DeferredCredential]`: A list of credentials
        """
        return self.credentials.values()

    async def delete_credential(self, cred_id: str) -> str:
        """
        Delete a credential by ID, if one exists

        ### Parameters
        - cred_id(`str`): The ID of the credential to be deleted

        ### Returns
        - `Credential | DeferredCredential`: The requested credential, if it exists.
        """
        try:
            return await super()._delete_credential(cred_id)
        except Exception:
            raise HTTPException(
                status_code=404, detail=f"Credential with ID {cred_id} not found."
            )

    async def request_authorization(
        self, credential_selection: CredentialSelection
    ):  # -> RedirectResponse:
        """
        Redirects the user to authorize.
        """
        redirect_url: str
        if credential_selection.credential_offer:
            if credential_selection.issuer_uri:
                raise HTTPException(
                    status_code=400,
                    detail="Can't provide both issuer_uri and credential_offer.",
                )
            redirect_url = await self.get_auth_redirect_from_offer(
                credential_selection.credential_configuration_id,
                credential_selection.credential_offer,
            )
        elif credential_selection.issuer_uri:
            redirect_url = await self.get_auth_redirect(
                credential_selection.credential_configuration_id,
                credential_selection.issuer_uri,
            )

        else:
            raise HTTPException(
                status_code=400,
                detail="Please provide either issuer_uri or credential_offer.",
            )
        # return RedirectResponse(redirect_url, status_code=302)

        # TODO: Remove this, very temporary fix
        return RedirectResponse(
            redirect_url.replace("issuer-lib", "localhost"), status_code=302
        )

    async def get_auth_request(
        self,
        request_uri,
        client_id,  # TODO
        client_id_scheme,
        request_uri_method,  # TODO
    ) -> AuthorizationRequestObject:
        if client_id_scheme != "did":
            raise HTTPException(
                status_code=400,
                detail=f"client_id_scheme {client_id_scheme} not supported",
            )

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{request_uri}")

        # just send the auth request to the frontend for now
        # what the backend sends to the fronend should be up to implementation
        # although it shouldn't include sensitive info unless the user has
        # opted to share that information
        self.current_transaction = AuthorizationRequestObject.model_validate_json(
            response.text
        )
        return self.current_transaction

    async def present_selection(
        self, field_selections: FieldSelectionObject = Body(...)
    ):
        # find which attributes in which credentials fit the presentation definition
        # mark which credential and attribute for disclosure

        # list[Field]
        approved_fields = [
            x.field for x in field_selections.field_requests if x.approved
        ]
        pd = self.current_transaction.presentation_definition
        ids = pd.input_descriptors

        # list[tuple[input_descriptor_id, vp_token]]
        id_vp_tokens: list[tuple[str, str]] = []

        for id_object in ids:
            input_descriptor_id = id_object.id
            # dict[credential, [list[encoded disclosures]]]
            valid_credentials = {}
            ordered_approved_fields = [
                x for x in id_object.constraints.fields if x in approved_fields
            ]
            for field in ordered_approved_fields:
                paths = field.path
                # find all credentials with said field
                new_valid_creds = self._get_credentials_with_field(paths)

                if valid_credentials == {}:
                    valid_credentials = new_valid_creds
                    continue
                # make sure we keep creds with previously found fields
                for cred in valid_credentials:
                    if cred not in new_valid_creds:
                        valid_credentials.pop(cred)
                for cred in new_valid_creds:
                    if cred not in valid_credentials:
                        new_valid_creds.pop(cred)

                # valid credentials should equal new_valid_creds now

                # add the new disclosures to the old disclosures
                for cred in valid_credentials:
                    valid_credentials[cred] += new_valid_creds[cred]

                # no valid credentials found
                if valid_credentials == {}:
                    break

            # if no valid credentials found, go next
            if valid_credentials == {}:
                continue

            # create the vp_token
            credential, disclosures = valid_credentials.popitem()
            vp_token = f"{self._get_credential_payload(credential)}~"
            for disclosure in disclosures:
                vp_token += f"{disclosure}~"

            id_vp_tokens.append((input_descriptor_id, vp_token))

        final_vp_token = None
        descriptor_maps = []
        definition_id = self.current_transaction.presentation_definition.id
        transaction_id = self.current_transaction.state

        if len(id_vp_tokens) == 1:
            input_descriptor_id, vp_token = id_vp_tokens[0]
            final_vp_token = vp_token

            descriptor_map = {
                "id": input_descriptor_id,
                "format": "vc+sd-jwt",
                "path": "$.vp_token",
            }
            descriptor_maps.append(DescriptorMapObject(**descriptor_map))
        elif len(id_vp_tokens) > 1:
            final_vp_token = []
            for input_descriptor_id, vp_token in id_vp_tokens:
                idx = len(final_vp_token)
                final_vp_token.append(vp_token)

                descriptor_map = {
                    "id": input_descriptor_id,
                    "format": "vc+sd-jwt",
                    "path": f"$.vp_token[{idx}]",
                }
                descriptor_maps.append(DescriptorMapObject(**descriptor_map))

        presentation_submission = PresentationSubmissionObject(
            id=str(uuid.uuid4()),
            definition_id=definition_id,
            descriptor_map=descriptor_maps,
        )

        authorization_response = AuthorizationResponseObject(
            vp_token=final_vp_token,
            presentation_submission=presentation_submission,
            state=transaction_id,
        )

        response_uri = self.current_transaction.response_uri
        # make sure response_mode is direct_post
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{response_uri}", data=authorization_response.model_dump_json()
            )

        self.current_transaction = None
        return response.json()
