import json
from typing import override

from jwcrypto.jwk import JWK
from pydantic import ValidationError

from vclib.common import oauth2, oid4vci, responses
from vclib.common.src.metadata import (
    DIDConfigResponse,
    DIDJSONResponse,
)
from vclib.issuer.src.credential_issuer import CredentialIssuer
from vclib.issuer.src.models.exceptions import IssuerError


class TestIssuer(CredentialIssuer):
    __test__ = False

    statuses: dict[int, tuple[str, dict]]

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
        oid4vci_metadata: oid4vci.IssuerOpenID4VCIMetadata
        oauth2_metadata: oauth2.IssuerOAuth2ServerMetadata

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
                oid4vci_metadata = oid4vci.IssuerOpenID4VCIMetadata.model_validate(
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
                oauth2_metadata = oauth2.IssuerOAuth2ServerMetadata.model_validate(
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
        client_id = "client_id"
        client_secret = "client_secret"
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
        except IssuerError:
            raise IssuerError("invalid_client")

    @override
    def get_credential_request(
        self, client_id: str, cred_type: str, redirect_uri: str, information: dict
    ) -> str:
        self.ticket += 1
        auth_code = "auth_code"
        self.auth_codes[auth_code] = client_id

        cred_id = cred_type
        self.auths_to_ids[auth_code] = (cred_type, cred_id, redirect_uri)
        self.id_to_info[cred_id] = {"ticket": self.ticket, "transaction_id": None}

        self.statuses[self.ticket] = (cred_type, information)

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

        return responses.StatusResponse(
            status="ACCEPTED",
            cred_type=cred_type,
            information=information,
            transaction_id=None,
        )

    @override
    def get_deferred_credential_status(
        self, transaction_id: str
    ) -> responses.StatusResponse:
        try:
            cred_id = self.transaction_id_to_cred_id[transaction_id]
            status = self.get_credential_status(cred_id)
            if status.status == "ACCEPTED":
                self.transaction_id_to_cred_id.pop(transaction_id)
            return status
        except KeyError:
            raise IssuerError("invalid_transaction_id")
