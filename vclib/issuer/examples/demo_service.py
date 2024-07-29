import json
from typing import Any, override
from uuid import uuid4

from fastapi import FastAPI

from vclib.common import hello_world
from vclib.issuer import CredentialIssuer, StatusResponse
from vclib.issuer.src.models.exceptions import IssuerError
from vclib.issuer.src.models.oauth import RegisteredClientMetadata, WalletClientMetadata
from vclib.issuer.src.models.responses import FormResponse

MOCK_DATA = {
    123: {
        "given_name": "Holden",
        "middle_initial": "A",
        "family_name": "Walletson",
        "date_of_birth": 19990101,
        "address": "123 A Street, A Suburb",
        "license_type": "C",
        "is_over_18": True,
    }
}

FORM = {
    "license_no": {"mandatory": True, "value_type": "number"},
    "date_of_birth": {"mandatory": True, "value_type": "number"},
}


class LicenseIssuer(CredentialIssuer):
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

    statuses: dict[int, (str, dict)]
    # time: datetime

    @override
    def __init__(
        self,
        jwt_path: str,
        diddoc_path: str,
        did_config_path: str,
        metadata_path: str,
        oauth_metadata_path: str,
        data: dict[int, dict[str, Any]],
    ):
        super().__init__(
            jwt_path,
            diddoc_path,
            did_config_path,
            metadata_path,
            oauth_metadata_path,
        )
        self.data = data
        self.ticket = 0

        self.statuses = {}
        self.client_ids = {}
        self.auth_codes = {}

        self.auths_to_ids = {}
        self.id_to_info = {}

        self.transaction_id_to_cred_id = {}

    @override
    def register_client(self, data: WalletClientMetadata) -> RegisteredClientMetadata:
        client_id = str(uuid4())
        client_secret = str(uuid4())
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
        except KeyError:
            raise IssuerError("invalid_client", "Client ID not valid")

    @override
    def get_credential_form(self, credential_config: str) -> FormResponse:
        # form = self.credentials[credential_config]
        # return FormResponse(form=form)
        return FormResponse(form=FORM)

    # TODO: update receive_credential_request to take errors from this function
    @override
    def get_credential_request(
        self, client_id: str, cred_type: str, redirect_uri: str, information: dict
    ) -> str:
        license_no, date_of_birth = (
            int(information["license_no"]),
            int(information["date_of_birth"]),
        )

        if license_no not in self.data:
            raise IssuerError(
                "invalid_request", f"Licence number {license_no} does not exist"
            )

        holder_information = self.data[license_no]

        if date_of_birth != holder_information["date_of_birth"]:
            raise IssuerError("invalid_request", f"DOB {date_of_birth} does not match")

        holder_information["license_no"] = license_no

        self.ticket += 1
        auth_code = str(uuid4())
        self.auth_codes[auth_code] = client_id

        cred_id = f"{cred_type}_{uuid4()!s}"
        self.auths_to_ids[auth_code] = (cred_type, cred_id, redirect_uri)
        self.id_to_info[cred_id] = {"ticket": self.ticket, "transaction_id": None}

        self.statuses[self.ticket] = (cred_type, holder_information)
        # self.time = datetime.datetime.now(tz=datetime.UTC)

        return auth_code

    @override
    def check_auth_code(
        self, auth_code: str, client_id: str, redirect_uri: str
    ) -> dict:
        if auth_code not in self.auths_to_ids:
            raise IssuerError("invalid_grant", "Authorization code not valid")

        if self.auth_codes[auth_code] != client_id:
            raise IssuerError(
                "invalid_client", "Authorization code does not match client ID"
            )

        cred_type, cred_id, re_uri = self.auths_to_ids[auth_code]

        if re_uri != redirect_uri:
            raise IssuerError("invalid_request", "Redirect URIs do not match")

        self.auths_to_ids.pop(auth_code)
        self.auth_codes.pop(auth_code)

        return {"credential_type": cred_type, "credential_id": cred_id}

    @override
    def get_credential_status(self, cred_id: str) -> StatusResponse:
        cred_info = self.id_to_info[cred_id]
        ticket = cred_info["ticket"]
        cred_type, information = self.statuses[ticket]

        status = "ACCEPTED"

        # curr_time = datetime.datetime.now(tz=datetime.UTC)
        # if curr_time - self.time < datetime.timedelta(0, 40, 0):
        #     if cred_info["transaction_id"] is None:
        #         transaction_id = str(uuid4())
        #         self.id_to_info[cred_id]["transaction_id"] = transaction_id
        #         self.transaction_id_to_cred_id[transaction_id] = cred_id
        #     status = "PENDING"

        return StatusResponse(
            status=status,
            cred_type=cred_type,
            information=information,
            transaction_id=cred_info["transaction_id"],
        )

    @override
    def get_deferred_credential_status(
        self, transaction_id: str, credential_identifier: str
    ) -> StatusResponse:
        try:
            cred_id = self.transaction_id_to_cred_id[transaction_id]
            if cred_id != credential_identifier:
                raise IssuerError(
                    "invalid_credential_request", "Credentials IDs do not match"
                )
            status = self.get_credential_status(cred_id)
            if status.status == "ACCEPTED":
                self.transaction_id_to_cred_id.pop(transaction_id)
            return status
        except KeyError:
            raise IssuerError("invalid_transaction_id", "Transaction ID is invalid")
        except IssuerError as e:
            raise IssuerError(e.message, e.details)

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


credential_issuer = LicenseIssuer(
    "/usr/src/app/examples/demo_data/example_jwk_private.pem",
    "/usr/src/app/examples/demo_data/example_diddoc.json",
    "/usr/src/app/examples/demo_data/example_didconf.json",
    "/usr/src/app/examples/demo_data/example_metadata_license.json",
    "/usr/src/app/examples/demo_data/example_oauth_metadata.json",
    MOCK_DATA,
)
credential_issuer_server = credential_issuer.get_server()