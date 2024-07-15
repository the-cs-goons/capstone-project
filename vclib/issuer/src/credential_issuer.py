import json
from base64 import urlsafe_b64decode
from datetime import UTC, datetime
from time import mktime
from typing import Annotated, Any
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException, Response, status
from fastapi.responses import RedirectResponse
from jwcrypto.jwk import JWK
from pydantic import ValidationError
from requests import Session

from vclib.common import SDJWTVCIssuer
from vclib.issuer.src.models.oauth import (
    AuthorizationDetails,
    OAuthTokenResponse,
    RegisteredClientMetadata,
    WalletClientMetadata,
)

from .models.requests import CredentialRequestBody, DeferredCredentialRequestBody
from .models.responses import (
    DIDConfigResponse,
    DIDJSONResponse,
    FormResponse,
    MetadataResponse,
    OAuthMetadataResponse,
    OptionsResponse,
    StatusResponse,
)


class CredentialIssuer:
    """Base class used for the credential issuer agent.

    ### Attributes
    - credentials(`dict`): A dictionary of available credentials that can be issued,
      with required fields and types
    - ticket(`int`): Internal tracking of current ticket number
    - mapping(`dict[str, int]`): Mapping of links to tickets
    - private_key: Private key used to sign credentials


    TODO
    uri
    paths

    """

    def __init__(
        self,
        credentials: dict[str, dict[str, dict[str, Any]]],
        uri: str,
        jwt_path: str,
        diddoc_path: str,
        did_config_path: str,
        metadata_path: str,
        oauth_metadata_path: str,
    ):
        self.credentials = credentials
        self.uri = uri

        try:
            with open(jwt_path, "rb") as key_file:
                self.jwt = JWK.from_pem(key_file.read())
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Could not find private jwt: {e}")
        except ValueError as e:
            raise ValueError(f"Invalid private jwt: {e}")

        try:
            with open(diddoc_path, "rb") as diddoc_file:
                self.diddoc = json.load(diddoc_file)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Could not find DIDDoc: {e}")
        except ValueError as e:
            raise ValueError(f"Invalid DIDDoc provided: {e}")

        try:
            with open(did_config_path, "rb") as did_config_file:
                self.did_config = json.load(did_config_file)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Could not find DID configuration json: {e}")
        except ValueError as e:
            raise ValueError(f"Invalid DID configuration json provided: {e}")

        try:
            with open(metadata_path, "rb") as metadata_file:
                self.metadata = json.load(metadata_file)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Could not find metadata json: {e}")
        except ValueError as e:
            raise ValueError(f"Invalid metadata json provided: {e}")

        try:
            with open(oauth_metadata_path, "rb") as oauth_metadata_file:
                self.oauth_metadata = json.load(oauth_metadata_file)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Could not find OAuth metadata json: {e}")
        except ValueError as e:
            raise ValueError(f"Invalid OAuth metadata json provided: {e}")

        self.client_ids = {}

        self.auth_codes = {}

        self.ticket = 0
        self.active_access_tokens = []
        self.auths_to_ids = {}
        self.access_to_ids = {}
        self.id_to_ticket = {}
        self.transaction_id_to_ticket = {}

    async def get_credential_options(self) -> OptionsResponse:
        """Retrieves available credentials that can be issued,
        along with required fields and types.
        """
        return OptionsResponse(options=self.credentials)

    async def get_did_json(self) -> DIDJSONResponse:
        return self.diddoc

    async def get_did_config(self) -> DIDConfigResponse:
        return self.did_config

    async def get_issuer_metadata(self) -> MetadataResponse:
        return self.metadata

    async def get_oauth_metadata(self) -> OAuthMetadataResponse:
        return self.oauth_metadata

    async def register(
        self, response: Response, request: WalletClientMetadata
    ) -> RegisteredClientMetadata:
        # TODO: Error handling

        client_id = str(uuid4())
        client_secret = str(uuid4())
        self.client_ids[client_id] = client_secret

        response.status_code = status.HTTP_201_CREATED

        return RegisteredClientMetadata(
            redirect_uris=request.redirect_uris,
            credential_offer_endpoint=request.credential_offer_endpoint,
            token_endpoint_auth_method=request.token_endpoint_auth_method,
            grant_types=request.grant_types,
            response_types=request.response_types,
            authorization_details_types=request.authorization_details_types,
            client_name=request.client_name,
            client_uri=request.client_uri,
            logo_uri=request.logo_uri,
            client_id=client_id,
            client_secret=client_secret,
            issuer_uri=self.uri,
        )

    async def authorize(
        self,
        response_type: str,
        client_id: str,
        redirect_uri: str,
        state: str,
        authorization_details: str,
    ):
        # TODO: Error checking

        cred_id = json.loads(authorization_details)[0]["credential_configuration_id"]
        form = self.credentials[cred_id]

        return FormResponse(form=form)

    async def receive_credential_request(
        self,
        response_type: str,
        client_id: str,
        redirect_uri: str,
        state: str,
        authorization_details: str,
        information: dict | None = None,
    ) -> RedirectResponse:
        """Receives a request for credentials.

        ### Parameters
        - cred_type(`str`): Type of credential being requested.
          This parameter is taken from the endpoint that was visited.
        - information(`dict`): Request body, containing information for the
          credential being requested.

        ### `POST`-ing requests
        Requests must:
        - Come from an endpoint corresponding to a valid credential type;
          e.g. `/request/drivers_license`
        - Contain fields in the request body matching those of the credential
          being applied for
        - Contain the correct data types in said fields.

        A `HTTPException` will be thrown if any of these are not met.

        Valid credential formats and required fields can be accessed through
        `get_credential_options()`.
        """
        cred_type = json.loads(authorization_details)[0]["credential_configuration_id"]

        if cred_type not in self.credentials:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Credential type {cred_type} is not supported",
            )

        try:
            self._check_input_typing(cred_type, information)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Fields for credential type {cred_type} were formatted incorrectly: {e}",  # noqa: E501
            )

        self.ticket += 1
        auth_code = str(uuid4())
        self.auth_codes[auth_code] = client_id

        cred_id = f"{cred_type}_{uuid4()!s}"
        self.auths_to_ids[auth_code] = [(cred_type, cred_id, redirect_uri)]
        self.id_to_ticket[cred_id] = self.ticket

        self.get_request(self.ticket, cred_type, information)

        return RedirectResponse(
            url=f"{redirect_uri}?code={auth_code}&state={state}",
            status_code=status.HTTP_302_FOUND,
        )

    async def token(
        self,
        grant_type: str,
        code: str,
        redirect_uri: str,
        authorization: Annotated[str | None, Header()] = None,
    ):
        # TODO: Error checking, proper authentication

        client_id, client_secret = (
            urlsafe_b64decode(authorization.split(" ")[1].encode("utf-8") + b"==")
            .decode("utf-8")
            .split(":")
        )
        if (
            self.auth_codes[code] == client_id
            and self.client_ids[client_id] == client_secret
        ):
            cred_type, cred_id, re_uri = self.auths_to_ids[code][0]
            if re_uri == redirect_uri:
                access_token = str(uuid4())
                self.active_access_tokens.append(access_token)
                self.access_to_ids[access_token] = (cred_id, None)

                auth_details = AuthorizationDetails(
                    type="openid_credential",
                    credential_configuration_id=cred_type,
                    credential_identifiers=[cred_id],
                )

                return OAuthTokenResponse(
                    access_token=access_token,
                    token_type="bearer",
                    expires_in=7200,
                    c_nonce=None,
                    c_nonce_expires_in=None,
                    authorization_details=[auth_details],
                )

            return {re_uri: redirect_uri}

        return {client_id: client_secret}

    async def get_credential(
        self,
        response: Response,
        request: dict[Any, Any],
        authorization: Annotated[str | None, Header()] = None,
    ):
        access_token = self._check_access_token(authorization)

        try:
            CredentialRequestBody.model_validate(request)
        except ValidationError:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"error": "invalid_credential_request"}

        if request["credential_identifier"] not in self.credentials:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"error": "unsupported_credential_type"}

        if self.access_to_ids[access_token][1] is not None:
            return {"transaction_id": self.access_to_ids[access_token][1]}

        ticket = self.id_to_ticket[self.access_to_ids[access_token][0]]

        cred_status = self.get_credential_status(ticket)

        if cred_status.status == "ACCEPTED":
            self.access_to_ids.pop(access_token)
            self.active_access_tokens.pop(access_token)
            credential = self.create_credential(
                request["credential_identifier"], cred_status.information
            )
            return {"credential": credential}

        if cred_status.status == "DENIED":
            # Unsure if we remove access token if denied
            # self.auths_to_ids.pop(access_token)
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"error": "credential_request_denied"}

        transaction_id = str(uuid4())
        self.transaction_id_to_ticket[transaction_id] = ticket
        self.access_to_ids[access_token] = (ticket, transaction_id)
        response.status_code = status.HTTP_202_ACCEPTED
        return {"transaction_id": transaction_id}

    async def get_deferred_credential(
        self,
        response: Response,
        request: dict[Any, Any],
        authorization: Annotated[str | None, Header()] = None,
    ):
        access_token = self._check_access_token(authorization)

        try:
            DeferredCredentialRequestBody.model_validate(request)
        except ValidationError:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"error": "invalid_credential_request"}

        if request["transaction_id"] not in self.transaction_id_to_ticket:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"error": "invalid_transaction_id"}

        ticket = self.transaction_id_to_ticket[request["transaction_id"]]

        cred_status = self.get_credential_status(ticket)
        if cred_status.information is not None:
            self.transaction_id_to_ticket.pop(request["transaction_id"])
            self.access_to_ids.pop(access_token)
            self.active_access_tokens.remove(access_token)
            credential = self.create_credential(
                cred_status.cred_type, cred_status.information
            )
            return {"credential": credential}

        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "issuance_pending"}

    def get_server(self) -> FastAPI:
        """Gets the server for the issuer."""
        router = FastAPI()

        # TODO: Allow customising endpoints using passed in metadata
        # router.get("/credentials/")(self.get_credential_options)
        # router.post("/request/{cred_type}")(self.receive_credential_request)

        router.get("/.well-known/did.json")(self.get_did_json)
        router.get("/.well-known/did-configuration")(self.get_did_config)
        router.get("/.well-known/openid-credential-issuer")(self.get_issuer_metadata)
        router.get("/.well-known/oauth-authorization-server")(self.get_oauth_metadata)

        """OAuth2 endpoints"""
        router.post("/oauth2/register")(self.register)
        router.get("/oauth2/authorize")(self.authorize)
        router.post("/oauth2/authorize")(self.receive_credential_request)
        router.post("/oauth2/token")(self.token)

        router.post("/credentials")(self.get_credential)
        router.post("/deferred")(self.get_deferred_credential)

        return router

    def _check_input_typing(self, cred_type: str, information: dict):
        """Checks fields in the given information are of the correct type.
        Raises `TypeError` if types do not match.
        """
        for field_name, field_info in self.credentials[cred_type].items():
            if field_name in information:
                value = information[field_name]
                if value is None:
                    if field_info.get("mandatory"):
                        raise TypeError(f"{field_name} is mandatory and was null")
                else:
                    match field_info["value_type"]:
                        case "string":
                            if not isinstance(value, str):
                                raise TypeError(f"{field_name} expected to be string")
                        case "number":
                            # bools can count as ints, and need to be explicitly checked
                            if not (
                                isinstance(value, int) and not isinstance(value, bool)
                            ) and not isinstance(value, float):
                                raise TypeError(f"{field_name} expected to be number")
                        case "boolean":
                            if not isinstance(value, bool):
                                raise TypeError(f"{field_name} expected to be boolean")
                        # Unimplemented, will be in future sprint
                        case ["array[", _typ, "]"]:
                            raise NotImplementedError
                        case "object":
                            raise NotImplementedError
            elif field_info.get("mandatory"):
                raise TypeError(f"{field_name} is mandatory and was not provided")
        for field_name in information:
            if field_name not in self.credentials[cred_type]:
                raise TypeError(f"{field_name} not required by {cred_type}")

    def _check_access_token(self, access_token: str) -> str:
        # TODO: Errors for incorrect/missing auth code
        if access_token is not None and access_token.startswith("Bearer "):
            ac = access_token.split(" ")[1]
            if ac in self.active_access_tokens:
                return ac

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or missing authorization code",
            headers={"WWW-Authenticate": "Bearer"},
        )

    ###
    ### User-defined functions, designed to be overwritten
    ###
    def get_request(self, _ticket: int, _cred_type: str, _information: dict):
        """## !!! This function must be `@override`n !!!

        Function to accept and process requests.

        ### Parameters
        - ticket(`int`): Ticket number of the request. This is generated by the class.
        - cred_type(`str`):  Type of credential being requested.
          This parameter is taken from the endpoint that was visited.
        - information(`dict`): Request body, containing information for the
        credential being requested.
        """
        return

    def get_credential_status(self, _ticket: int) -> StatusResponse:
        """## !!! This function must be `@override`n !!!

        Function to process requests for credential application status updates, as
        well as returning credentials for successful applications.

        ### Parameters
        - ticket(`int`): Ticket number of the request. This is generated by the class.

        ### Returns
        A `StatusResponse` object is returned, with the following fields:
        - `status`: A string representing the status of the application.
        - `cred_type`: The type of credential that was requested.
        - `information`: Fields to be used in the new credential, once approved. Set as
          `None` otherwise.

        IMPORTANT: The `status` return value can be read by anyone with the link to
        specified ticket, and must not have any sensitive information contained.
        """
        return StatusResponse(status="PENDING", cred_type=None, information=None)

    def create_credential(self, cred_type: str, disclosable_claims: dict) -> str:
        """Function to generate credentials after being accepted.

        Overriding this function is *optional* - the default implementation is
        SD-JWT-VC.

        ### Parameters
        - cred_type(`str`):  Type of credential being requested.
          This parameter is taken from the endpoint that was visited.
        - disclosable_claims(`dict`): Contains disclosable claims for the credential
          being constructed.

        ### Returns
        - `str`: A string containing the new issued credential.
        """

        other = {"iat": mktime(datetime.now(UTC).timetuple())}
        new_credential = SDJWTVCIssuer(disclosable_claims, other, self.jwt, None)

        return new_credential.sd_jwt_issuance

    async def offer_credential(self, uri: str, credential_offer: str):
        with Session() as s:
            s.get(f"{uri}?credential_offer={credential_offer}")
        return {uri: credential_offer}
