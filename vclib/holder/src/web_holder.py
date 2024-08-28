from datetime import UTC, datetime, timedelta
from secrets import token_bytes
from typing import Annotated, Any
from urllib.parse import urlparse
from uuid import uuid4

import httpx
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import RedirectResponse
from jwt import DecodeError, ExpiredSignatureError, decode, encode
from pydantic import ValidationError

from vclib.common import vp_auth_request, vp_auth_response
from vclib.holder.src.models.login_register import (
    LoginRequest,
    RegisterRequest,
    UserAuthenticationResponse,
)
from vclib.holder.src.storage.abstract_storage_provider import AbstractStorageProvider

from .holder import Holder
from .models.credential_offer import CredentialOffer, CredentialSelection
from .models.credentials import Credential, DeferredCredential
from .models.field_selection_object import FieldSelectionObject


class WebHolder(Holder):
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
        super().__init__(oauth_client_info, storage_provider)
        self.current_transaction: vp_auth_request.AuthorizationRequestObject | None = (
            None
        )

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
        router.get("/refresh/{cred_id}")(self.refresh)
        router.get("/refresh")(self.refresh_all)

        # Presentation
        router.get("/presentation/init")(self.get_auth_request)
        router.post("/presentation/")(self.present_selection)

        # Issuance (offer) endpoints
        router.get(self._credential_offer_endpoint)(self.credential_offer)
        router.post(self._credential_offer_endpoint)(self.request_authorization)

        router.get("/add")(self.get_access_token_and_credentials_from_callback)

        return router

    ###
    ### Web-based Authentication / Authorization
    ###

    def _generate_jwt(
        self, payload: dict[str, Any], headers: dict[str, Any] | None = None
    ):
        # Default token generation scheme
        payload["exp"] = datetime.now(tz=UTC) + timedelta(seconds=self.TOKEN_EXP_SECS)
        return encode(payload, self.SECRET, algorithm="HS256", headers=headers)

    def generate_token(self, verified_auth: LoginRequest | RegisterRequest):
        return UserAuthenticationResponse(
            username=verified_auth.username,
            access_token=self._generate_jwt({"user": verified_auth.username}),
        )

    def check_token(self, authorization: Annotated[str | None, Header()] = None):
        """
        Check session token.

        ### Parameters
        - authorization(`str | None`): The bearer token giving authorization
        """
        if not authorization:
            raise HTTPException(status_code=403, detail="Unauthorized. Please log in.")
        (token_type, token) = authorization.split(" ")
        if token_type.lower() != "bearer":
            raise HTTPException(
                status_code=400, detail=f"Invalid token type {token_type}"
            )

        prompt = ". Please log in again."
        try:
            return decode(token, self.SECRET, self.SESSION_TOKEN_ALG)
        except DecodeError:
            raise HTTPException(
                status_code=400, detail="Invalid session token" + prompt
            )
        except ExpiredSignatureError:
            self.logout()
            raise HTTPException(status_code=400, detail="Session expired" + prompt)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid token" + prompt)

    def user_login(self, login: LoginRequest) -> UserAuthenticationResponse:
        """
        Log in a user.
        """
        try:
            self.login(login.username, login.password)
        except Exception:
            raise HTTPException(status_code=400, detail="Bad login attempt.")

        return self.generate_token(login)

    def user_register(self, reg: RegisterRequest) -> UserAuthenticationResponse:
        """
        Register a user.
        """
        if reg.password != reg.confirm:
            raise HTTPException(status_code=400, detail="Passwords don't match.")
        # Rudimentary password rule
        if len(reg.password) < self.MIN_PASSWORD_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Password must be at least {self.MIN_PASSWORD_LENGTH} characters long",  # noqa: E501
            )
        try:
            self.register(reg.username, reg.password)
        except Exception:
            raise HTTPException(
                status_code=400, detail=f"Could not register as {reg.username}."
            )

        return self.generate_token(reg)

    def user_logout(self):
        """
        Log out a user.
        """
        self.logout()

    ###
    ### Interaction with Wallet
    ###

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
        self.check_token(authorization)
        r = refresh != 0
        try:
            return await super().get_credential(cred_id, refresh=r)
        except Exception:
            raise HTTPException(
                status_code=400, detail=f"Credential with ID {cred_id} not found."
            )

    async def get_credentials(
        self,
        authorization: Annotated[str | None, Header()] = None,
    ) -> list[Credential | DeferredCredential]:
        """
        Get credentials.

        ### Parameters
        - authorization(`str | None`): The bearer token giving authorization

        ### Returns
        - `list[Credential | DeferredCredential]`: A list of credentials
        """
        self.check_token(authorization)
        return self.store.all_credentials()

    async def delete_credential(
        self,
        cred_id: str,
        authorization: Annotated[str | None, Header()] = None,
    ):
        """
        Delete a credential by ID, if one exists

        ### Parameters
        - cred_id(`str`): The ID of the credential to be deleted

        ### Returns
        - `Credential | DeferredCredential`: The requested credential, if it exists.
        """
        self.check_token(authorization)
        try:
            self.store.delete_credential(cred_id)
        except Exception:
            raise HTTPException(
                status_code=404, detail=f"Credential with ID {cred_id} not found."
            )

    async def refresh(
        self,
        cred_id: str,
        authorization: Annotated[str | None, Header()] = None,
    ) -> Credential | DeferredCredential:
        """
        Refresh credential.
        """
        self.check_token(authorization)
        return await self.refresh_credential(cred_id)

    async def refresh_all(
        self,
        authorization: Annotated[str | None, Header()] = None,
    ) -> list[str]:
        """
        Refresh all credentials.
        """
        self.check_token(authorization)
        return await self.refresh_all_deferred_credentials()

    async def credential_offer(
        self,
        credential_offer_uri: str | None = None,
        credential_offer: str | None = None,
        authorization: Annotated[str | None, Header()] = None,
    ) -> CredentialOffer:
        """
        Parses a credential offer.

        ### Parameters
        - credential_offer_uri(`str | None`): A URL linking to a credential offer
        object. If provided, `credential_offer` MUST be none.
        - credential_offer(`str`): A URL-encoded credential offer object. If given,
        `credential_offer_uri` MUST be none.

        ### Returns
        `CredentialOffer`: The credential offer.
        """
        self.check_token(authorization)
        return await self.get_credential_offer(credential_offer_uri, credential_offer)

    async def request_authorization(
        self,
        credential_selection: CredentialSelection,
        authorization: Annotated[str | None, Header()] = None,
    ):  # -> RedirectResponse:
        """
        Redirects the user to authorize.
        """
        self.check_token(authorization)
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

        return RedirectResponse(
            redirect_url.replace("issuer-lib", "localhost"), status_code=302
        )

    async def get_auth_request(
        self,
        request_uri,
        authorization: Annotated[str | None, Header()] = None,
    ) -> vp_auth_request.AuthorizationRequestObject:
        """Get authorization request from a verifier."""
        self.check_token(authorization)

        async with httpx.AsyncClient() as client:
            response = await client.post(f"{request_uri}")

        # just send the auth request to the frontend for now
        # what the backend sends to the fronend should be up to implementation
        # although it shouldn't include sensitive info unless the user has
        # opted to share that information
        try:
            self.current_transaction = vp_auth_request.AuthorizationRequestObject(
                **response.json()
            )
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"invalid_request: {e}")

        return self.current_transaction

    async def present_selection(
        self,
        field_selections: FieldSelectionObject,
        authorization: Annotated[str | None, Header()] = None,
    ):
        """Send verifiable presentation to the verifier."""
        # find which attributes in which credentials fit the presentation definition
        # mark which credential and attribute for disclosure
        if self.current_transaction is None:
            raise HTTPException(status_code=400, detail="No ongoing presentation found")

        self.check_token(authorization)
        approved_fields = [
            x.field for x in field_selections.field_requests if x.approved
        ]
        if len(approved_fields) == 0:
            raise HTTPException(
                status_code=403, detail="access_denied: credential request rejected"
            )
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
                filter = field.filter
                # find all credentials with said field
                new_valid_creds = self._get_credentials_with_field(paths, filter)

                if valid_credentials == {}:
                    valid_credentials = new_valid_creds
                    continue
                # if we the field is not optional,
                # we need to get rid of all the old credentials that don't
                # have the field.
                if not field.optional:
                    creds = set(valid_credentials.keys()).intersection(
                        set(new_valid_creds.keys())
                    )

                    # Cull keys
                    valid_credentials = {c: valid_credentials[c] for c in creds}
                    new_valid_creds = {c: new_valid_creds[c] for c in creds}

                # add the new disclosures to the old disclosures
                for cred in valid_credentials:
                    valid_credentials[cred] += new_valid_creds[cred]

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
                    "path": f"$[{idx}]",
                }
                descriptor_maps.append(
                    vp_auth_response.DescriptorMapObject(**descriptor_map)
                )

        elif len(id_vp_tokens) == 0:
            # return{"status_code": 403, "detail": "Presentation_failed"}
            raise HTTPException(
                status_code=403,
                detail="Access Denied: No appropriate credentials found",
            )

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

        response_uri = self.current_transaction.response_uri
        # make sure response_mode is direct_post
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{response_uri}", data=authorization_response.model_dump_json()
            )

        self.current_transaction = None
        if response.status_code == 200:
            return "success"
        return response.json()
