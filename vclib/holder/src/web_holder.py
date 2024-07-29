from datetime import UTC, datetime, timedelta
from functools import wraps
from secrets import token_bytes
from typing import Annotated, Any
from urllib.parse import urlparse
from uuid import uuid4

import httpx
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import RedirectResponse
from jwt import decode, encode

from vclib.common import vp_auth_request, vp_auth_response
from vclib.holder.src.models.login_register import (
    LoginRequest,
    RegisterRequest,
    UserAuthenticationResponse,
)
from vclib.holder.src.storage.abstract_storage_provider import AbstractStorageProvider

from .holder import Holder
from .models.credential_offer import CredentialSelection
from .models.credentials import Credential, DeferredCredential
from .models.field_selection_object import FieldSelectionObject


class WebIdentityOwner(Holder):
    """
    IdentityOwner that implements a HTTPS API interface.
    """

    # Can be increased, but a minimum of 10 will be used
    MIN_PASSWORD_LENGTH = 10
    TOKEN_EXP_SECS = 3600

    def __init__(
            self,
            redirect_uris: list[str],
            cred_offer_endpoint: str,
            storage_provider: AbstractStorageProvider,
            *,
            oauth_client_options: dict[str, Any] = {},
            dev_mode: bool = False,
            ):
        """
        Create a new Identity Owner

        ### Parameters
        - redirect_uris(`list[str]`): A list of redirect URIs to register
        with issuers. It is the caller's responsibility to ensure these
        match with the API.

        - cred_offer_endpoint(`str`): The credential offer URI, e.g.
        "https://example.com/offer". The routes for receiving credential
        offers, and redirecting the user to authorise based on a
        credential offer, are dynamically determined by parsing this URI
        with `urllib.parse.urlparse` and retrieving the path.

        - oauth_client_options(`dict = {}`): A dictionary containing
        optional overrides for the wallet's OAuth client info, used in
        registration of new clients. See `WalletClientMetadata` for
        accepted fields.
            - Note that even if keys `"redirect_uris"` or
            `"credential_offer_endpoint"` are provided, they will be
            overwritten by their respective positional arguments.

        - storage_provider(`AbstractStorageProvider`): An implementation of the
        `AbstractStorageProvider` abstract class.
        """

        # Referenced in `get_server`
        offer_path = urlparse(cred_offer_endpoint).path
        self._credential_offer_endpoint = offer_path
        self.wallet_uri = "localhost"

        oauth_client_info = oauth_client_options
        oauth_client_info["redirect_uris"] = redirect_uris
        oauth_client_info["credential_offer_endpoint"] = cred_offer_endpoint
        super().__init__(oauth_client_info, storage_provider, dev_mode=dev_mode)
        self.current_transaction: \
            vp_auth_request.AuthorizationRequestObject | None = None

        self.SECRET = token_bytes(32)
        self.SESSION_TOKEN_ALG = "HS256"


    def get_server(self) -> FastAPI:
        router = FastAPI()

        # Authentication
        router.post("/login")(self.user_login)
        router.post("/register")(self.user_register)
        router.get("/logout")(self.user_logout)
        router.get("/session")(self.check_token)

        router.get("/credentials/{cred_id}")(self.get_credential)
        router.get("/credentials")(self.get_credentials)
        router.delete("/credentials/{cred_id}")(self.delete_credential)
        router.get("/refresh/{cred_id}")(self.refresh_credential)
        router.get("/refresh")(self.refresh_all_deferred_credentials)

        # Presentation
        router.get("/presentation/init")(self.get_auth_request)
        router.post("/presentation/")(self.present_selection)

        # Issuance (offer) endpoints
        router.get(self._credential_offer_endpoint)(self.get_credential_offer)
        router.post(self._credential_offer_endpoint)(self.request_authorization)

        router.get("/add")(self.get_access_token_and_credentials_from_callback)

        return router

    ###
    ### Web-based Authentication / Authorization
    ###

    @staticmethod
    def authorize(func):
        @wraps(func)
        def _authorize_func(self: 'WebIdentityOwner', *args, **kwargs):
            auth = kwargs.get("authorization")
            self.check_token(auth)
            return func(self, *args, **kwargs)
        return _authorize_func

    def _generate_jwt(
            self,
            payload: dict[str, Any],
            headers: dict[str, Any] | None = None
            ):
        # Default token generation scheme
        payload["exp"] = datetime.now(tz=UTC) + timedelta(seconds=self.TOKEN_EXP_SECS)
        return encode(payload, self.SECRET, algorithm="HS256", headers=headers)

    def generate_token(self, verified_auth: LoginRequest | RegisterRequest):
        """
        TODO: Document overwriting
        """
        return UserAuthenticationResponse(
            username=verified_auth.username,
            access_token=self._generate_jwt({"user": verified_auth.username})
        )

    def check_token(self, authorization: Annotated[str | None, Header()] = None):
        """
        TODO: Document overwriting
        """
        if not authorization:
            raise HTTPException(status_code=403, detail="Unauthorized")
        (token_type, token) = authorization.split(' ')
        if token_type.lower() != "bearer":
            raise HTTPException(status_code=400, detail="Malformed token")
        return decode(token, self.SECRET, self.SESSION_TOKEN_ALG)

    def user_login(self, login: LoginRequest) -> UserAuthenticationResponse:
        try:
            self.login(login.username, login.password)
        except Exception:
            raise HTTPException(status_code=400, detail="Bad login attempt.")

        return self.generate_token(login)

    def user_register(self, reg: RegisterRequest) -> UserAuthenticationResponse:
        if reg.password != reg.confirm:
            raise HTTPException(status_code=400, detail="Passwords don't match.")
        # Rudimentary password rule
        if len(reg.password) < self.MIN_PASSWORD_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Password must be at least {self.MIN_PASSWORD_LENGTH} characters long" # noqa: E501
                )
        try:
            self.register(reg.username, reg.password)
        except Exception:
            raise HTTPException(
                status_code=400,
                detail=f"Could not register as {reg.username}."
                )

        return self.generate_token(self, RegisterRequest)

    def user_logout(self):
        self.logout()

    ###
    ### Interaction with Wallet
    ###

    @authorize
    async def get_credential(
        self,
        cred_id: str,
        authorization: Annotated[str | None, Header()] = None,
        refresh: int = 1,
    ) -> Credential | DeferredCredential:
        """
        Gets a credential by ID, if one exists

        ### Parameters
        - cred_id(`str`): The ID of the credential, as kept by the owner
        - refresh(`int = 1`): Whether or not to refresh the credential,
        if currently deferred. Expressed as an int for the purposes of
        making it easier to pass in the request URL as a query
        parameter. 0 is `False`, any other number is interpreted as
        `True` (default).

        ### Returns
        - `Credential | DeferredCredential`: The requested credential,
        if it exists.
        """
        r = refresh != 0
        try:
            return await super().get_credential(cred_id, refresh=r)
        except Exception:
            raise HTTPException(
                status_code=400,
                detail=f"Credential with ID {cred_id} not found."
            )

    @authorize
    async def get_credentials(
        self,
        authorization: Annotated[str | None, Header()] = None,
        ) -> list[Credential | DeferredCredential]:
        """
        TODO
        """
        return self.all_credentials()

    @authorize
    async def delete_credential(
            self,
            cred_id: str,
            authorization: Annotated[str | None, Header] = None,
            ) -> str:
        """
        Delete a credential by ID, if one exists

        ### Parameters
        - cred_id(`str`): The ID of the credential to be deleted

        ### Returns
        - `Credential | DeferredCredential`: The requested credential, if it exists.
        """
        try:
            super().delete_credential(cred_id)
        except Exception:
            raise HTTPException(
                status_code=404, detail=f"Credential with ID {cred_id} not found."
            )

    @authorize
    async def refresh_credential(
        self,
        cred_id: str,
        authorization: Annotated[str | None, Header] = None,
    ) -> Credential | DeferredCredential:
        return super().refresh_credential(cred_id)

    @authorize
    async def refresh_all_deferred_credentials(
        self,
        authorization: Annotated[str | None, Header] = None,
    ) -> list[str]:
        return super().refresh_all_deferred_credentials()

    @authorize
    async def request_authorization(
        self,
        credential_selection: CredentialSelection,
        authorization: Annotated[str | None, Header] = None,
    ):  # -> RedirectResponse:
        """
        Redirects the user to authorize.
        """
        redirect_url: str
        if credential_selection.credential_offer:
            if credential_selection.issuer_uri:
                raise HTTPException(
                    status_code=400,
                    detail="Can't provide both issuer_uri and credential_offer."
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

    @authorize
    async def get_auth_request(
        self,
        request_uri,
        client_id,  # TODO
        client_id_scheme,
        request_uri_method,  # TODO
        authorization: Annotated[str | None, Header] = None,
    ) -> vp_auth_request.AuthorizationRequestObject:
        if client_id_scheme != "did":
            raise HTTPException(
                status_code=400,
                detail=f"client_id_scheme {client_id_scheme} not supported",
            )

        async with httpx.AsyncClient() as client:
            response = await client.post(f"{request_uri}")

        # just send the auth request to the frontend for now
        # what the backend sends to the fronend should be up to implementation
        # although it shouldn't include sensitive info unless the user has
        # opted to share that information
        self.current_transaction = \
            vp_auth_request.AuthorizationRequestObject.model_validate_json(
            response.text
        )
        return self.current_transaction

    @authorize
    async def present_selection(
        self,
        field_selections: FieldSelectionObject,
        authorization: Annotated[str | None, Header] = None,
    ):
        # find which attributes in which credentials fit the presentation definition
        # mark which credential and attribute for disclosure
        # print(self.current_transaction)
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
                # ignore if field is optional
                if not field.optional:
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
                "path": "$",
            }
            descriptor_maps.append(
                vp_auth_response.DescriptorMapObject(**descriptor_map)
                )
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
                descriptor_maps.append(vp_auth_response.DescriptorMapObject(**descriptor_map))

        presentation_submission = vp_auth_response.PresentationSubmissionObject(
            id=str(uuid4()),
            definition_id=definition_id,
            descriptor_map=descriptor_maps,
        )

        authorization_response = vp_auth_response.AuthorizationResponseObject(
            vp_token=final_vp_token,
            presentation_submission=presentation_submission,
            state=transaction_id,
        )

        print(authorization_response)
        response_uri = self.current_transaction.response_uri
        # make sure response_mode is direct_post
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{response_uri}", data=authorization_response.model_dump_json()
            )

        self.current_transaction = None
        return response.json()
