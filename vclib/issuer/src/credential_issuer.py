import json
from base64 import urlsafe_b64decode
from datetime import UTC, datetime
from time import mktime
from typing import Annotated, Any
from uuid import uuid4

from fastapi import FastAPI, Form, Header, HTTPException, Response, status
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

from .models.metadata import (
    DIDConfigResponse,
    DIDJSONResponse,
    MetadataResponse,
    OAuthMetadataResponse,
)
from .models.requests import CredentialRequestBody, DeferredCredentialRequestBody
from .models.responses import (
    FormResponse,
    StatusResponse,
)


class CredentialIssuer:
    def __init__(
        self,
        jwt_path: str,
        diddoc_path: str,
        did_config_path: str,
        metadata_path: str,
        oauth_metadata_path: str,
    ):
        """Base class used for the credential issuer agent.

        ### Parameters
        - credentials(`dict`): A dictionary of available credentials that can be issued,
        with required fields and types
        - uri(`str`): Issuer's URI, used by the wallet agent to access endpoints
        - jwt_path(`str`): Path to PEM-encoded private JWT.
        - diddoc_path(`str`): Path to DIDDoc JSON object.
        - did_config_path(`str`): Path to DID configuraton JSON object.
        - metadata_path(`str`): Path to OpenID credential issuer metadata JSON object.
        - oauth_metadata_path(`str`): Path to OAuth metadata JSON object.
        """

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

        self.uri = self.metadata["credential_issuer"]

        self.credentials = {}
        for key, value in self.metadata["credential_configurations_supported"].items():
            self.credentials[key.replace(self.uri + "/", "")] = value["claims"]

        self.client_ids = {}

        self.auth_codes = {}

        self.ticket = 0
        self.active_access_tokens = []
        self.auths_to_ids = {}
        self.access_to_ids = {}
        self.id_to_ticket = {}
        self.transaction_id_to_ticket = {}

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
        """Receives a request to register a new client.

        ### Parameters
        - request(`WalletClientMetadata`): Expected metadata provided by the wallet, to
          be used in registering a new client.

        Returns a `RegisteredClientMetadata` object, containing all provided wallet
        metadata as well as the new client id, secret and the issuer's URI.
        """
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
        """Receives requests to authorize the wallet.

        This is the first half of the authorization flow and is called when the wallet
        posts a `GET` request to the authorization endpoint.

        ### Parameters
        - response_type(`str`): Expected to be `"code"`.
        - client_id(`str`): Client ID as assigned by the issuer by registration.
        - redirect-uri(`str`): URI to redirect the wallet to after successful
          authorization.
        - state(`str`): A string used to verify the state of the request. It MUST remain
          the same throughout the authorization process and be returned to the wallet at
          the end of the process.
        - authorization_details(`str`): A string representing a list of JSON objects.
          Each object MUST have the two fields in order as follows:
           - `"type"`: Expected to be `"openid_credential"`.
           - `"credential_configuration_id"`: Contains the ID of a credential type taken
             from the issuer's metadata endpoint.

        Returns the schema of the `credential_configuration_id` given.
        """
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
        """Receives requests to authorize the wallet.

        This is the second half of the authorization flow and is called when the wallet
        posts a `POST` request to the authorization endpoint, with the information
        needed to issue a credential in the body.

        ### Parameters
        - response_type(`str`): Expected to be `"code"`.
        - client_id(`str`): Client ID as assigned by the issuer by registration.
        - redirect-uri(`str`): URI to redirect the wallet to after successful
          authorization.
        - state(`str`): A string used to verify the state of the request. It MUST remain
          the same throughout the authorization process and be returned to the wallet at
          the end of the process.
        - authorization_details(`str`): A string representing a list of JSON objects.
          Each object MUST have the two fields in order as follows:
          - `"type"`: Expected to be `"openid_credential"`.
          - `"credential_configuration_id"`: Contains the ID of a credential type taken
             from the issuer's metadata endpoint.
        - information(`dict`): Request body, containing information for the
          credential being requested.

        ### Return Values
        Returns a `RedirectResponse`, with the following query parameters:
        - code: The authorization code to be used at the access token endpoint.
        - state: The state value given to the endpoint.
        """
        # TODO: Error checking
        cred_type = json.loads(authorization_details)[0]["credential_configuration_id"]

        if cred_type not in self.credentials:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Credential type {cred_type} is not supported",
            )

        self._check_input_typing(self.credentials[cred_type], cred_type, information)

        # try:
        #     self._check_input_typing(
        #         self.credentials[cred_type].items(), cred_type, information
        #     )
        # except Exception as e:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail=f"Fields for credential type {cred_type} were formatted incorrectly: {e}",  # noqa: E501
        #     )

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
        grant_type: Annotated[str, Form()],
        code: Annotated[str, Form()],
        redirect_uri: Annotated[str, Form()],
        authorization: Annotated[str | None, Header()] = None,
    ) -> OAuthTokenResponse:
        """Receives requests for access tokens.

        ### Parameters
        - grant_type(`str`): Expected to be `"authorization_code"`.
        - code(`str`): Authorization code given by the authorization endpoint.
        - redirect_uri(`str`): MUST be the same `redirect_uri` given to the
          authorization endpoint.
        - authorization(`str`): A Base64 encoded string containing
          `Basic client_id:client_secret`.

        Returns an `OAuthTokenResponse`.
        """

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

            # TODO: Incorrect redirect uri error

        # TODO: Incorrect client id/secret error
        return None

    async def get_credential(
        self,
        response: Response,
        request: dict[Any, Any],
        authorization: Annotated[str | None, Header()] = None,
    ):
        """Receives requests to retrieve a credential.

        ### Parameters
        - request(`dict[Any, Any]`): Request body. Expected to conform to
          `CredentialRequestBody`.
        - authorization(`str`): A string containing `"Bearer access_code"`.

        ### Return Values
        - If the credential is ACCEPTED:
          - Return the credential in the form `{"credential": credential}`.
        - If the credential is PENDING:
          - Return a transaction ID to be used at the deferred endpoint, in
            the form `{"transaction_id": transaction_id}`.
        - If the credential is DENIED:
          - Return a 400, with `{"error": "credential_request_denied"}`.
        """
        access_token = self._check_access_token(authorization)

        try:
            CredentialRequestBody.model_validate(request)
        except ValidationError:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"error": "invalid_credential_request"}

        if self.access_to_ids[access_token][0] != request["credential_identifier"]:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"error": "unsupported_credential_type"}

        if self.access_to_ids[access_token][1] is not None:
            return {"transaction_id": self.access_to_ids[access_token][1]}

        ticket = self.id_to_ticket[self.access_to_ids[access_token][0]]

        cred_status = self.get_credential_status(ticket)

        if cred_status.status == "ACCEPTED":
            self.access_to_ids.pop(access_token)
            self.active_access_tokens.remove(access_token)
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
        """Receives requests to retrieve a deferred credential.

        ### Parameters
        - request(`dict[Any, Any]`): Request body. Expected to conform to
          `DeferredCredentialRequestBody`.
        - authorization(`str`): A string containing `"Bearer access_code"`.

        ### Return Values
        - If the credential is ACCEPTED:
          - Return the credential in the form `{"credential": credential}`.
        - If the credential is PENDING:
          - Return a 400, with `{"error": "issuance_pending"}`.
        - If the credential is DENIED:
          - Return a 400, with `{"error": "credential_request_denied"}`.
        """
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
        if cred_status.status == "ACCEPTED":
            self.transaction_id_to_ticket.pop(request["transaction_id"])
            self.access_to_ids.pop(access_token)
            self.active_access_tokens.remove(access_token)
            credential = self.create_credential(
                cred_status.cred_type, cred_status.information
            )
            return {"credential": credential}

        response.status_code = status.HTTP_400_BAD_REQUEST

        if cred_status.status == "DENIED":
            # Unsure if we remove access token if denied
            # self.auths_to_ids.pop(access_token)
            return {"error": "credential_request_denied"}

        return {"error": "issuance_pending"}

    def get_server(self) -> FastAPI:
        """Gets the server for the issuer."""
        router = FastAPI()

        # TODO: Allow customising endpoints using passed in metadata

        auth_endpoint = self.oauth_metadata["authorization_endpoint"].replace(
            self.uri, ""
        )
        token_endpoint = self.oauth_metadata["token_endpoint"].replace(self.uri, "")
        register_endpoint = self.oauth_metadata["registration_endpoint"].replace(
            self.uri, ""
        )

        credential_endpoint = self.metadata["credential_endpoint"].replace(self.uri, "")
        deferred_endpoint = self.metadata["deferred_credential_endpoint"].replace(
            self.uri, ""
        )

        """Metadata must be hosted at these endpoints"""
        router.get("/.well-known/did.json")(self.get_did_json)
        router.get("/.well-known/did-configuration")(self.get_did_config)
        router.get("/.well-known/openid-credential-issuer")(self.get_issuer_metadata)
        router.get("/.well-known/oauth-authorization-server")(self.get_oauth_metadata)

        """OAuth2 endpoints"""
        router.get(auth_endpoint)(self.authorize)
        router.post(auth_endpoint)(self.receive_credential_request)
        router.post(token_endpoint)(self.token)
        router.post(register_endpoint)(self.register)

        router.post(credential_endpoint)(self.get_credential)
        router.post(deferred_endpoint)(self.get_deferred_credential)

        return router

    def _check_input_typing(self, template: dict, cred_type: str, information: dict):
        """Checks fields in the given information are of the correct type.
        Raises `TypeError` if types do not match.
        """
        for field_name, field_info in template.items():
            if field_name in information:
                values = information[field_name]
                if values is None:
                    if (
                        isinstance(field_info, list) and field_info[0].get("mandatory")
                    ) or field_info.get("mandatory"):
                        raise TypeError(f"{field_name} is mandatory and was null")
                else:
                    if isinstance(field_info, list):
                        field_info = field_info[0]
                    else:
                        values = [values]

                    for value in values:
                        if "value_type" in field_info:
                            match field_info["value_type"]:
                                case "any":
                                    # Type checking not needed
                                    pass
                                case "string":
                                    if not isinstance(value, str):
                                        raise TypeError(
                                            f"{field_name} expected to be string"
                                        )
                                case "number":
                                    # bools can count as ints, and need to be checked
                                    if not (
                                        isinstance(value, int)
                                        and not isinstance(value, bool)
                                    ) and not isinstance(value, float):
                                        raise TypeError(
                                            f"{field_name} expected to be number"
                                        )
                                case "boolean":
                                    if not isinstance(value, bool):
                                        raise TypeError(
                                            f"{field_name} expected to be boolean"
                                        )
                                case other:
                                    raise TypeError(
                                        f"{field_name} unexpected type: {other}"
                                    )
                        else:
                            self._check_input_typing(field_info, cred_type, value)
            elif (
                isinstance(field_info, list) and field_info[0].get("mandatory")
            ) or field_info.get("mandatory"):
                raise TypeError(f"{field_name} is mandatory and was not provided")
        for field_name in information:
            if field_name not in template:
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
        - `status`: A string representing the status of the application. Expected to be
           one of ACCEPTED, PENDING or DENIED.
        - `cred_type`: The type of credential that was requested.
        - `information`: Fields to be used in the new credential, once approved. Set as
          `None` otherwise.
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
