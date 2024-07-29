from typing import override

from vclib.issuer.src.credential_issuer import CredentialIssuer
from vclib.issuer.src.models.exceptions import IssuerError
from vclib.issuer.src.models.oauth import RegisteredClientMetadata, WalletClientMetadata
from vclib.issuer.src.models.responses import FormResponse, StatusResponse


class TestIssuer(CredentialIssuer):
    __test__ = False

    statuses: dict[int, (str, dict)]

    @override
    def __init__(
        self,
        jwt_path: str,
        diddoc_path: str,
        did_config_path: str,
        metadata_path: str,
        oauth_metadata_path: str,
    ):
        super().__init__(
            jwt_path,
            diddoc_path,
            did_config_path,
            metadata_path,
            oauth_metadata_path,
        )
        self.ticket = 0

        self.statuses = {}
        self.client_ids = {}
        self.auth_codes = {}

        self.auths_to_ids = {}
        self.id_to_info = {}

        self.transaction_id_to_cred_id = {}

    @override
    def register_client(self, data: WalletClientMetadata) -> RegisteredClientMetadata:
        client_id = "client_id"
        client_secret = "client_secret"
        self.client_ids[client_id] = client_secret

        client_info = {
            "client_id": client_id,
            "client_secret": client_secret,
            "issuer_uri": self.uri,
        }

        return RegisteredClientMetadata.model_validate(data.model_dump() | client_info)

    @override
    def check_client_id(self, client_id: str) -> str:
        try:
            return self.client_ids[client_id]
        except IssuerError:
            raise IssuerError("invalid_client")

    @override
    def get_credential_form(self, credential_config: str) -> FormResponse:
        form = self.credentials[credential_config]
        return FormResponse(form=form)

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
    def get_credential_status(self, cred_id: str) -> StatusResponse:
        cred_info = self.id_to_info[cred_id]
        ticket = cred_info["ticket"]
        cred_type, information = self.statuses[ticket]

        return StatusResponse(
            status="ACCEPTED",
            cred_type=cred_type,
            information=information,
            transaction_id=None,
        )

    @override
    def get_deferred_credential_status(self, transaction_id: str) -> StatusResponse:
        try:
            cred_id = self.transaction_id_to_cred_id[transaction_id]
            status = self.get_credential_status(cred_id)
            if status.status == "ACCEPTED":
                self.transaction_id_to_cred_id.pop(transaction_id)
            return status
        except KeyError:
            raise IssuerError("invalid_transaction_id")
