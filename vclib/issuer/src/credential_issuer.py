import json
import secrets
from base64 import urlsafe_b64decode
from datetime import UTC, datetime, timedelta
from time import mktime
from typing import Annotated, Any
from urllib.parse import quote, urlparse

import jwt
from fastapi import FastAPI, Form, Header, Response, status
from fastapi.responses import RedirectResponse
from jwcrypto.jwk import JWK
from pydantic import ValidationError
from requests import Session

from vclib.common import SDJWTVCIssuer
from vclib.common.src.metadata import (
    DIDConfigResponse,
    DIDJSONResponse,
    MetadataResponse,
    OAuthMetadataResponse,
)

from .models.exceptions import IssuerError
from .models.oauth import (
    AuthorizationDetails,
    OAuthTokenResponse,
    RegisteredClientMetadata,
    WalletClientMetadata,
)
from .models.requests import (
    AuthorizationRequestDetails,
    CredentialRequestBody,
    DeferredCredentialRequestBody,
)
from .models.responses import (
    FormResponse,
    StatusResponse,
)


class CredentialIssuer:
    # Time in seconds until token expires
    TOKEN_EXPIRY = 3600

    def __init__(
        self,
        key_pem_filepath: str,
        diddoc_path: str,
        did_config_path: str,
        metadata_path: str,
        oauth_metadata_path: str,
    ):
        """Base class used for the credential issuer agent.

        ### Parameters
        - key_pem_filepath(`str`): Path to PEM-encoded private JWT.
        - diddoc_path(`str`): Path to DIDDoc JSON object.
        - did_config_path(`str`): Path to DID configuraton JSON object.
        - metadata_path(`str`): Path to OpenID credential issuer metadata JSON object.
        - oauth_metadata_path(`str`): Path to OAuth metadata JSON object.
        """

        try:
            with open(key_pem_filepath, "rb") as key_file:
                self.jwk = JWK.from_pem(key_file.read())
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

        self.secret = secrets.token_hex(32)

    async def get_did_json(self) -> DIDJSONResponse:
        return self.diddoc

    async def get_did_config(self) -> DIDConfigResponse:
        return self.did_config

    async def get_issuer_metadata(self) -> MetadataResponse:
        return self.metadata

    async def get_oauth_metadata(self) -> OAuthMetadataResponse:
        return self.oauth_metadata

    async def register(
        self,
        response: Response,
        request: dict[Any, Any],
    ):
        """Receives a request to register a new client.

        ### Parameters
        - request(`WalletClientMetadata`): Expected metadata provided by
        the wallet, to be used in registering a new client.

        Returns a `RegisteredClientMetadata` object, containing all
        provided wallet metadata as well as the new client id, secret
        and the issuer's URI.
        """

        try:
            request = WalletClientMetadata.model_validate(request)
        except ValidationError:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"error": "invalid_client_metadata"}

        for uri in request.redirect_uris:
            if not self.validate_uri(uri):
                response.status_code = status.HTTP_400_BAD_REQUEST
                return {"error": "invalid_redirect_uri"}

        response.status_code = status.HTTP_201_CREATED

        try:
            return self.register_client(request)
        except IssuerError as e:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"error": e.message}

    async def authorize(
        self,
        response: Response,
        response_type: str | None = None,
        client_id: str | None = None,
        redirect_uri: str | None = None,
        state: str | None = None,
        authorization_details: str | None = None,
    ):
        """Receives requests to authorize the wallet.

        This is the first half of the authorization flow and is called
        when the wallet posts a `GET` request to the authorization
        endpoint.

        ### Parameters
        - response_type(`str`): Expected to be `"code"`.
        - client_id(`str`): Client ID as assigned by the issuer by
          registration.
        - redirect-uri(`str`): URI to redirect the wallet to after
          successful authorization.
        - state(`str`): A string used to verify the state of the request.
          It MUST remain
          the same throughout the authorization process and be returned
          to the wallet at the end of the process.
        - authorization_details(`str`): A string representing a list of
          JSON objects.
          Each object MUST have the two fields in order as follows:
           - `"type"`: Expected to be `"openid_credential"`.
           - `"credential_configuration_id"`: Contains the ID of a
             credential type taken from the issuer's metadata endpoint.

        Returns the schema of the `credential_configuration_id` given.

        ### Errors
        If the given redirect URI is invalid, returns a 400 error code.

        Otherwise, if an error occurs, returns a `RedirectResponse` with the
        following query parameters:
        - error: The error code of the error that occured.
        - state: The state value given to the endpoint.
        """
        try:
            self._check_authorization_details(
                response_type, client_id, redirect_uri, state, authorization_details
            )
        except IssuerError as e:
            if e.message == "invalid_uri":
                response.status_code = status.HTTP_400_BAD_REQUEST
                return {"error": "invalid_uri"}

            return RedirectResponse(
                url=f"{redirect_uri}?error={e.message}&state={state}",
                status_code=status.HTTP_302_FOUND,
            )

        cred_id = json.loads(authorization_details)[0]["credential_configuration_id"]

        try:
            return self.get_credential_form(cred_id)
        except IssuerError as e:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"error": e.message}

    async def receive_credential_request(
        self,
        response: Response,
        response_type: str | None = None,
        client_id: str | None = None,
        redirect_uri: str | None = None,
        state: str | None = None,
        authorization_details: str | None = None,
        information: dict | None = None,
    ) -> RedirectResponse:
        """Receives requests to authorize the wallet.

        This is the second half of the authorization flow and is called
        when the wallet posts a `POST` request to the authorization
        endpoint, with the information needed to issue a credential in
        the body.

        ### Parameters
        - response_type(`str`): Expected to be `"code"`.
        - client_id(`str`): Client ID as assigned by the issuer by
          registration.
        - redirect-uri(`str`): URI to redirect the wallet to after
          successful authorization.
        - state(`str`): A string used to verify the state of the request.
          It **MUST** remain the same throughout the authorization
          process and be returned to the wallet at the end of the
          process.
        - authorization_details(`str`): A string representing a list of
          JSON objects. Each object MUST have the two fields in order as
          follows:
          - `"type"`: Expected to be `"openid_credential"`.
          - `"credential_configuration_id"`: Contains the ID of a
            credential type taken from the issuer's metadata endpoint.
        - information(`dict`): Request body, containing information for
          the credential being requested.

        ### Return Values
        Returns a `RedirectResponse`, with the following query
        parameters:
        - code: The authorization code to be used at the access token
          endpoint.
        - state: The state value given to the endpoint.

        ### Errors
        If the given redirect URI is invalid, returns a 400 error code.

        Otherwise, if an error occurs, returns a `RedirectResponse` with the
        following query parameters:
        - error: The error code of the error that occured.
        - state: The state value given to the endpoint.
        """
        try:
            self._check_authorization_details(
                response_type, client_id, redirect_uri, state, authorization_details
            )
        except IssuerError as e:
            if e.message == "invalid_uri":
                response.status_code = status.HTTP_400_BAD_REQUEST
                return {"error": "invalid_uri"}

            return RedirectResponse(
                url=f"{redirect_uri}?error={e.message}&state={state}",
                status_code=status.HTTP_302_FOUND,
            )

        cred_type = json.loads(authorization_details)[0]["credential_configuration_id"]

        if cred_type not in self.credentials:
            return RedirectResponse(
                url=f"{redirect_uri}?error=invalid_request&error_description={
                    quote(f"Credential type {cred_type} not found")
                }&state={state}",
                status_code=status.HTTP_302_FOUND,
            )

        try:
            self._check_input_typing(
                self.get_credential_form(cred_type).form, cred_type, information
            )
        except TypeError:
            return RedirectResponse(
                url=f"""{redirect_uri}?error=invalid_request&error_description={
                    quote("Form response does not match required fields")
                }&state={state}""",
                status_code=status.HTTP_302_FOUND,
            )
        except IssuerError as e:
            return RedirectResponse(
                url=f"""{redirect_uri}?error={e.message}&error_description={
                    quote(e.details)
                }&state={state}""",
                status_code=status.HTTP_302_FOUND,
            )

        try:
            auth_code = self.get_credential_request(
                client_id, cred_type, redirect_uri, information
            )

            return RedirectResponse(
                url=f"{redirect_uri}?code={auth_code}&state={state}",
                status_code=status.HTTP_302_FOUND,
            )
        except IssuerError as e:
            return RedirectResponse(
                url=f"{redirect_uri}?error={e.message}&error_description={quote(e.details)}&state={state}",
                status_code=status.HTTP_302_FOUND,
            )

    async def token(
        self,
        response: Response,
        grant_type: Annotated[str | None, Form()] = None,
        code: Annotated[str | None, Form()] = None,
        redirect_uri: Annotated[str | None, Form()] = None,
        authorization: Annotated[str | None, Header()] = None,
    ):
        """Receives requests for access tokens.

        ### Parameters
        - grant_type(`str`): Expected to be `"authorization_code"`.
        - code(`str`): Authorization code given by the authorization
          endpoint.
        - redirect_uri(`str`): MUST be the same `redirect_uri` given to
          the authorization endpoint.
        - authorization(`str`): A Base64 encoded string containing
          `Basic client_id:client_secret`.

        Returns an `OAuthTokenResponse`.

        ### Errors
        If an error occurs, return a 400 code with following query parameters:
        - error: The name of the error that occurred, as a string.
        """

        if None in (grant_type, code, redirect_uri, authorization):
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"error": "invalid_request"}

        if grant_type != "authorization_code":
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"error": "unsupported_grant_type"}

        # TODO is this a correct variable name?
        payload = authorization.split(" ")[1]
        client_id, client_secret = (
            urlsafe_b64decode(payload.encode("utf-8") + b"==")
            .decode("utf-8")
            .split(":")
        )
        try:
            credential_info = self.check_auth_code(code, client_id, redirect_uri)
            if self.check_client_id(client_id) == client_secret:
                payload = {
                    "client_id": client_id,
                    "credential_id": credential_info["credential_id"],
                    "iat": mktime(datetime.now(tz=UTC).timetuple()),
                }

                secret = self.secret + client_secret

                access_token = jwt.encode(payload, secret, algorithm="HS256")

                auth_details = AuthorizationDetails(
                    type="openid_credential",
                    credential_configuration_id=credential_info["credential_type"],
                    credential_identifiers=[credential_info["credential_id"]],
                )

                return OAuthTokenResponse(
                    access_token=access_token,
                    token_type="bearer",
                    expires_in=self.TOKEN_EXPIRY,
                    c_nonce=None,
                    c_nonce_expires_in=None,
                    authorization_details=[auth_details],
                )
            raise IssuerError("invalid_client")
        except IssuerError as e:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"error": e.message}

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
          - Return a transaction ID to be used at the deferred endpoint,
          in the form `{"transaction_id": transaction_id}`.
        - If the credential is DENIED:
          - Return a 400, with `{"error": "credential_request_denied"}`.

        ### Errors
        If the access token cannot be authorized, return an authorization
        error as defined in RFC6750.

        Otherwise, return a 400 code with following query parameters:
        - error: The name of the error that occurred, as a string.
        """
        access_token_payload: dict

        try:
            access_token_payload = self._check_access_token(authorization)
        except IssuerError as e:
            response.headers["WWW-Authenticate"] = f'Bearer error="{e.message}"'
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return None

        try:
            CredentialRequestBody.model_validate(request)
        except ValidationError:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"error": "invalid_credential_request"}

        cred_id = access_token_payload["credential_id"]

        if cred_id != request["credential_identifier"]:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"error": "unsupported_credential_type"}

        cred_status = self.get_credential_status(cred_id)

        if cred_status.status == "ACCEPTED":
            credential = self.create_credential(
                request["credential_identifier"], cred_status.information
            )
            return {"credential": credential}

        if cred_status.status == "DENIED":
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"error": "credential_request_denied"}

        response.status_code = status.HTTP_202_ACCEPTED
        return {"transaction_id": cred_status.transaction_id}

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

        ### Errors
        If the access token cannot be authorized, return an authorization
        error as defined in RFC6750.

        Otherwise, return a 400 code with following query parameters:
        - error: The error code of the error that occured.
        """
        access_token_payload: dict

        try:
            access_token_payload = self._check_access_token(authorization)
        except IssuerError as e:
            response.headers["WWW-Authenticate"] = f'Bearer error="{e.message}"'
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return None

        try:
            DeferredCredentialRequestBody.model_validate(request)
        except ValidationError:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"error": "invalid_credential_request"}

        cred_status: StatusResponse

        cred_id = access_token_payload["credential_id"]

        try:
            cred_status = self.get_deferred_credential_status(
                request["transaction_id"], cred_id
            )
        except IssuerError as e:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"error": e.message}

        if cred_status.status == "ACCEPTED":
            credential = self.create_credential(
                cred_status.cred_type, cred_status.information
            )
            return {"credential": credential}

        response.status_code = status.HTTP_400_BAD_REQUEST

        if cred_status.status == "DENIED":
            return {"error": "credential_request_denied"}

        return {"error": "issuance_pending"}

    def get_server(self) -> FastAPI:
        """Gets the server for the issuer."""
        router = FastAPI()

        auth_endpoint = urlparse(self.oauth_metadata["authorization_endpoint"]).path
        token_endpoint = urlparse(self.oauth_metadata["token_endpoint"]).path
        register_endpoint = urlparse(self.oauth_metadata["registration_endpoint"]).path

        credential_endpoint = urlparse(self.metadata["credential_endpoint"]).path
        deferred_endpoint = urlparse(self.metadata["deferred_credential_endpoint"]).path

        # Metadata must be hosted at these endpoints
        router.get("/.well-known/did.json")(self.get_did_json)
        router.get("/.well-known/did-configuration")(self.get_did_config)
        router.get("/.well-known/openid-credential-issuer")(self.get_issuer_metadata)
        router.get("/.well-known/oauth-authorization-server")(self.get_oauth_metadata)

        # OAuth2 endpoints
        router.get(auth_endpoint)(self.authorize)
        router.post(auth_endpoint)(self.receive_credential_request)
        router.post(token_endpoint)(self.token)
        router.post(register_endpoint)(self.register)

        router.post(credential_endpoint)(self.get_credential)
        router.post(deferred_endpoint)(self.get_deferred_credential)

        return router

    def _check_authorization_details(
        self,
        response_type: str,
        client_id: str,
        redirect_uri: str,
        state,
        authorization_details: str,
    ):
        """Checks provided details to authorization endpoint are correct."""
        if None in (
            response_type,
            client_id,
            redirect_uri,
            state,
            authorization_details,
        ):
            raise IssuerError("invalid_request", "Missing required fields")

        if response_type != "code":
            raise IssuerError(
                "unsupported_response_type", "Response type must be 'code'"
            )

        self.check_client_id(client_id)

        if not self.validate_uri(redirect_uri):
            raise IssuerError(
                "invalid_uri", "Redirect URIs do not match"
            )  # NOT defined in spec, self added

        try:
            AuthorizationRequestDetails.model_validate(
                json.loads(authorization_details)[0]
            )
        except Exception:
            raise IssuerError("invalid_request")

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

    def _check_access_token(self, access_token: str) -> dict:
        """Checks if the provided access token is valid.
        Returns the contents of the token after verification.
        """
        if access_token is None or not access_token.startswith("Bearer "):
            raise IssuerError("invalid_request")

        ac = access_token.split(" ")[1]

        payload: dict
        try:
            client_id = jwt.decode(ac, options={"verify_signature": False})["client_id"]
            secret = self.secret + self.check_client_id(client_id)

            payload = jwt.decode(ac, secret, algorithms="HS256")
        except Exception:
            raise IssuerError("invalid_token")

        issue_time = datetime.fromtimestamp(payload["iat"], tz=UTC)

        if datetime.now(tz=UTC) - issue_time > timedelta(0, self.TOKEN_EXPIRY, 0):
            raise IssuerError("invalid_token")

        return payload

    ###
    ### User-defined functions, designed to be overwritten
    ###
    def register_client(self, data: WalletClientMetadata) -> RegisteredClientMetadata:
        """## !!! This function must be `@override`n !!!

        Function to register clients with the application.

        ### Parameters
        - data(`WalletClientMetadata`): Provided data by the requester for registration.

        Returns a `RegisteredClientMetadata` object containing the given wallet
        metadata, as well as client information as specified in
        [Section 3.2.1 of RFC7591](https://datatracker.ietf.org/doc/html/rfc7591#section-3.2.1).

        ### Errors
        Errors MUST conform to [Section 3.2.2 of RFC7591](https://datatracker.ietf.org/doc/html/rfc7591#section-3.2.2).
        Specifically, they MUST be declared by raising an `IssuerError` with the correct
        error code as a message.

        For example:
        ```python
        try:
            # ...
        except Exception:
            raise IssuerError("invalid_client_metadata")
        ```
        """

    def check_client_id(self, client_id: str) -> str:
        """## !!! This function must be `@override`n !!!

        Function to check client ids and corresponding secrets.

        ### Parameters
        - client_id(`str`): Client ID to check.

        Returns the associated client secret as a string.

        ### Errors
        If the ID does not exist or is malformed, an `"invalid_client"` error may
        be raised by using `IssuerError` with the correct error code as a message.

        For example:
        ```python
        try:
            # ...
        except Exception:
            raise IssuerError("invalid_client")
        ```
        """

    def get_credential_form(self, credential_config: str) -> FormResponse:
        pass

    def get_credential_request(
        self, _client_id: str, _cred_type: str, _redirect_uri: str, _information: dict
    ) -> str:
        """## !!! This function must be `@override`n !!!

        Function to accept and process credential requests.

        ### Parameters
        - client_id(`str`): Client ID of the requesting entity.
        - cred_type(`str`):  Type of credential being requested.
          This parameter is taken from the endpoint that was visited.
        - redirect_uri(`str`):
        - information(`dict`): Request body, containing information for the
        credential being requested.

        Returns the authorization code to be used by the client in the OAuth flow.
        """

    def check_auth_code(
        self, auth_code: str, client_id: str, redirect_uri: str
    ) -> dict:
        """## !!! This function must be `@override`n !!!

        Function to check and validate authorization codes.

        ### Parameters
        - auth_code(`str`): Authorization code to check.
        - client_id(`str`): Client ID provided with request.
        - redirect_uri(`str`): Redirect URI provided with request.

        ### Return value
        Returns a dictionary with the following fields:
        - credential_type(`str`): Type of credential
        - credential_id(`str`): Identifier of credential request

        ### Errors
        Errors MUST conform to [Section 5.2 of RFC6749](https://datatracker.ietf.org/doc/html/rfc6749#section-5.2).
        Specifically, they MUST be declared by raising an `IssuerError` with the correct
        error code as a message.

        For example:
        ```python
        try:
            # ...
        except Exception:
            raise IssuerError("invalid_request")
        ```
        """

    def get_credential_status(self, _cred_id: int) -> StatusResponse:
        """## !!! This function must be `@override`n !!!

        Function to process requests for credential application status updates, as
        well as returning credentials for successful applications.

        ### Parameters
        - cred_id(`str`): Credential identifier of the requested credential. This is a
          unique identifier in this implementation.

        ### Returns
        A `StatusResponse` object is returned, with the following fields:
        - `status`: A string representing the status of the application. Expected to be
           one of ACCEPTED, PENDING or DENIED.
        - `cred_type`: The type of credential that was requested.
        - `information`: Fields to be used in the new credential, once approved. Set as
          `None` otherwise.
        - `transaction_id`: The transaction ID of the request, if deferred. Set as
           `None` otherwise.

        ### Errors
        Errors MUST conform to [Section 7.3.1.2 of OpenIDv4VC's Verifiable Credential Issuance](https://openid.github.io/OpenID4VCI/openid-4-verifiable-credential-issuance-wg-draft.html#section-7.3.1.2)
        specifications. Specifically, they MUST be declared by raising an `IssuerError`
        with the correct error code as a message.

        For example:
        ```python
        try:
            # ...
        except Exception:
            raise IssuerError("invalid_credential_request")
        ```
        """

    def get_deferred_credential_status(
        self, _transaction_id: str, _credential_identifier: str
    ) -> StatusResponse:
        """## !!! This function must be `@override`n !!!

        Function to process referred requests for credential application status updates,
        as well as returning credentials for successful applications.

        ### Parameters
        - transaction_id(`str`): The transaction id of the credential being requested.
        - credential_identifier(`str`): The unique identifier of the credential being
          requested.

        ### Returns
        A `StatusResponse` object is returned, with the following fields:
        - `status`: A string representing the status of the application. Expected to be
           one of ACCEPTED, PENDING or DENIED.
        - `cred_type`: The type of credential that was requested.
        - `information`: Fields to be used in the new credential, once approved. Set as
          `None` otherwise.
        - `transaction_id`: The transaction ID of the request, if deferred. Set as
           `None` otherwise.

        ### Errors
        Errors MUST conform to [Section 9.3 of OpenIDv4VC's Verifiable Credential Issuance](https://openid.github.io/OpenID4VCI/openid-4-verifiable-credential-issuance-wg-draft.html#section-9.3)
        specifications. Specifically, they MUST be declared by raising an `IssuerError`
        with the correct error code as a message.

        For example:
        ```python
        try:
            # ...
        except Exception:
            raise IssuerError("invalid_credential_request")
        ```
        """

    def validate_uri(self, uri: str) -> bool:
        """Checks if a given redirect uri is valid.

        Overriding this function is *optional* - the default implementation only
        checks if `urlparse` throws an error.

        ### Parameters
        - uri(`str`): The URI to be checked."""
        try:
            urlparse(uri)
        except AttributeError:
            return False

        return True

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

        other = {
            "iss": self.uri,
            "vct": self.uri + "/" + cred_type,
            "iat": mktime(datetime.now(tz=UTC).timetuple()),
        }
        new_credential = SDJWTVCIssuer(disclosable_claims, other, self.jwk, None)

        return new_credential.sd_jwt_issuance

    async def offer_credential(self, uri: str, credential_offer: str):
        with Session() as s:
            s.get(f"{uri}?credential_offer={credential_offer}")
        return {uri: credential_offer}
