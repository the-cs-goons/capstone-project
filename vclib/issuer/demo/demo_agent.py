import datetime
import json
from typing import override
from uuid import uuid4

from fastapi import FastAPI
from jwcrypto.jwk import JWK
from pydantic import ValidationError

from vclib.common import hello_world, oauth2, responses
from vclib.common.src.metadata import (
    DIDConfigResponse,
    DIDJSONResponse,
    MetadataResponse,
    OAuthMetadataResponse,
)
from vclib.issuer import CredentialIssuer
from vclib.issuer.src.models.exceptions import IssuerError


class DefaultIssuer(CredentialIssuer):
    """Example implementation of the `CredentialIssuer` base class.

    ### Added Attributes
    - ticket(`int`): Internal system for tracking credential requests.
    - statuses(`dict[int, (str, dict)]`): Dictionary storing the current status
      of active credential requests.
    - client_ids(`dict[str, str]`): Mapping of client IDs to secrets.
    - auth_codes(`dict[str, str]`): Mapping of authorization codes to associated
      client ID.
    - auths_to_ids(`dict[str, (str, str, str)]`): Mapping of authorization codes
      to credential type, credential identifier and redirect URI used.
    - id_to_info(`dict[str, dict[str, str]]`): Mapping of credential identifiers
      to associated ticket and transaction ID.
    """

    statuses: dict[int, tuple[str, dict]]
    time: datetime.datetime

    @override
    def __init__(
        self,
        private_jwt_path: str,
        diddoc_path: str,
        did_config_path: str,
        oid4vci_metadata_path: str,
        oauth2_metadata_path: str,
    ):
        private_jwk: JWK
        diddoc: DIDJSONResponse
        did_config: DIDConfigResponse
        oid4vci_metadata: MetadataResponse
        oauth2_metadata: OAuthMetadataResponse

        try:
            with open(private_jwt_path, "rb") as key_file:
                private_jwk = JWK.from_pem(key_file.read())
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Could not find private jwt: {e}")
        except ValueError as e:
            raise ValueError(f"Invalid private jwt: {e}")

        try:
            with open(diddoc_path, "rb") as diddoc_file:
                diddoc = DIDJSONResponse.model_validate(json.load(diddoc_file))
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Could not find DIDDoc: {e}")
        except ValidationError as e:
            raise ValueError(f"Invalid DIDDoc provided: {e}")
        except ValueError as e:
            raise ValueError(f"Malformed DIDDoc json provided: {e}")

        try:
            with open(did_config_path, "rb") as did_config_file:
                did_config = DIDConfigResponse.model_validate(
                    json.load(did_config_file)
                )
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Could not find DID configuration json: {e}")
        except ValidationError as e:
            raise ValueError(f"Invalid DID configuration provided: {e}")
        except ValueError as e:
            raise ValueError(f"Malformed DID configuration json provided: {e}")

        try:
            with open(oid4vci_metadata_path, "rb") as oid4vci_metadata_file:
                oid4vci_metadata = MetadataResponse.model_validate(
                    json.load(oid4vci_metadata_file)
                )
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Could not find OID4VCI metadata json: {e}")
        except ValidationError as e:
            raise ValueError(f"Invalid OID4VCI metadata provided: {e}")
        except ValueError as e:
            raise ValueError(f"Malformed OID4VCI metadata json provided: {e}")

        try:
            with open(oauth2_metadata_path, "rb") as oauth2_metadata_file:
                oauth2_metadata = OAuthMetadataResponse.model_validate(
                    json.load(oauth2_metadata_file)
                )
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Could not find OAuth2 metadata json: {e}")
        except ValidationError as e:
            raise ValueError(f"Invalid OAuth2 metadata provided: {e}")
        except ValueError as e:
            raise ValueError(f"Invalid OAuth2 metadata json provided: {e}")

        super().__init__(
            private_jwk,
            diddoc,
            did_config,
            oid4vci_metadata,
            oauth2_metadata,
        )
        self.ticket = 0

        self.statuses = {}
        self.client_ids = {}
        self.auth_codes = {}

        self.auths_to_ids = {}
        self.id_to_info = {}

        self.transaction_id_to_cred_id = {}

    @override
    def register_client(
        self, data: oauth2.HolderOAuth2ClientMetadata
    ) -> oauth2.HolderOAuth2RegisteredClientMetadata:
        client_id = str(uuid4())
        client_secret = str(uuid4())
        self.client_ids[client_id] = client_secret

        client_info = {
            "client_id": client_id,
            "client_secret": client_secret,
            "issuer_uri": self.uri,
        }

        return oauth2.HolderOAuth2RegisteredClientMetadata.model_validate(
            data.model_dump() | client_info
        )

    @override
    def check_client_id(self, client_id: str) -> str:
        try:
            return self.client_ids[client_id]
        except KeyError:
            raise IssuerError("invalid_client")

    @override
    def get_credential_request(
        self, client_id: str, cred_type: str, redirect_uri: str, information: dict
    ) -> str:
        self.ticket += 1
        auth_code = str(uuid4())
        self.auth_codes[auth_code] = client_id

        cred_id = f"{cred_type}_{uuid4()!s}"
        self.auths_to_ids[auth_code] = (cred_type, cred_id, redirect_uri)
        self.id_to_info[cred_id] = {"ticket": self.ticket, "transaction_id": None}

        self.statuses[self.ticket] = (cred_type, information)
        self.time = datetime.datetime.now(tz=datetime.UTC)

        return auth_code

    @override
    def check_auth_code(
        self, auth_code: str, client_id: str, redirect_uri: str
    ) -> dict:
        if auth_code not in self.auths_to_ids:
            raise IssuerError("invalid_grant")

        if self.auth_codes[auth_code] != client_id:
            raise IssuerError("invalid_client")

        cred_type, cred_id, re_uri = self.auths_to_ids[auth_code]

        if re_uri != redirect_uri:
            raise IssuerError("invalid_request")

        self.auths_to_ids.pop(auth_code)
        self.auth_codes.pop(auth_code)

        return {"credential_type": cred_type, "credential_id": cred_id}

    @override
    def get_credential_status(self, cred_id: str) -> responses.StatusResponse:
        cred_info = self.id_to_info[cred_id]
        ticket = cred_info["ticket"]
        cred_type, information = self.statuses[ticket]

        status = "ACCEPTED"

        curr_time = datetime.datetime.now(tz=datetime.UTC)
        if curr_time - self.time < datetime.timedelta(0, 40, 0):
            if cred_info["transaction_id"] is None:
                transaction_id = str(uuid4())
                self.id_to_info[cred_id]["transaction_id"] = transaction_id
                self.transaction_id_to_cred_id[transaction_id] = cred_id
            status = "PENDING"

        return responses.StatusResponse(
            status=status,
            cred_type=cred_type,
            information=information,
            transaction_id=cred_info["transaction_id"],
        )

    @override
    def get_deferred_credential_status(
        self, transaction_id: str, credential_identifier: str
    ) -> responses.StatusResponse:
        try:
            cred_id = self.transaction_id_to_cred_id[transaction_id]
            if cred_id != credential_identifier:
                raise IssuerError("invalid_credential_request")
            status = self.get_credential_status(cred_id)
            if status.status == "ACCEPTED":
                self.transaction_id_to_cred_id.pop(transaction_id)
            return status
        except KeyError:
            raise IssuerError("invalid_transaction_id")
        except IssuerError as e:
            raise IssuerError(e.message)

    async def credential_offer(self):
        cred_offer = {
            "credential_issuer": "https://issuer-lib:8082",
            "credential_configuration_ids": ["ID"],
        }
        await self.offer_credential(
            "https://holder-lib:8081/offer", json.dumps(cred_offer)
        )

    @override
    def get_server(self) -> FastAPI:
        router = super().get_server()
        router.get("/offer")(self.credential_offer)
        router.get("/hello")(hello_world)
        return router


credential_issuer = DefaultIssuer(
    "/usr/src/app/examples/example_jwk_private.pem",
    "/usr/src/app/examples/example_diddoc.json",
    "/usr/src/app/examples/example_didconf.json",
    "/usr/src/app/examples/example_metadata.json",
    "/usr/src/app/examples/example_oauth_metadata.json",
)
credential_issuer_server = credential_issuer.get_server()
