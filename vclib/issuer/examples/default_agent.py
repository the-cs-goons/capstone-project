import datetime
import json
from typing import Any, override

from fastapi import FastAPI

from vclib.common import hello_world
from vclib.issuer import CredentialIssuer, StatusResponse


class DefaultIssuer(CredentialIssuer):
    """Example implementation of the `CredentialIssuer` base class.

    ### Added Attributes
    - statuses`(dict[int, (str, dict)])`: Dictionary storing the current status
    of active credential requests.
    """

    statuses: dict[int, (str, dict)]
    time: datetime

    @override
    def __init__(
        self,
        credentials: dict[str, dict[str, dict[str, Any]]],
        jwt_path: str,
        diddoc_path: str,
        did_config_path: str,
        metadata_path: str,
        oauth_metadata_path: str,
    ):
        super().__init__(
            credentials,
            jwt_path,
            diddoc_path,
            did_config_path,
            metadata_path,
            oauth_metadata_path,
        )
        self.statuses = {}

    @override
    def get_request(self, ticket: int, cred_type: str, information: dict):
        self.statuses[ticket] = (cred_type, information)
        self.time = datetime.datetime.now(tz=datetime.UTC)

    @override
    def get_credential_status(self, ticket: str) -> StatusResponse:
        cred_type, information = self.statuses[ticket]

        curr_time = datetime.datetime.now(tz=datetime.UTC)
        if curr_time - self.time < datetime.timedelta(0, 40, 0):
            return StatusResponse(status="PENDING", cred_type=None, information=None)

        return StatusResponse(
            status="ACCEPTED", cred_type=cred_type, information=information
        )

    async def credential_offer(self):
        cred_offer = {
            "credential_issuer": "https://issuer-lib:8082",
            "credential_configuration_ids": ["ID"],
        }
        await self.offer_credential(
            "https://owner-lib:8081/offer", json.dumps(cred_offer)
        )

    @override
    def get_server(self) -> FastAPI:
        router = super().get_server()
        router.get("/offer")(self.credential_offer)
        router.get("/hello")(hello_world)
        return router


credentials = {
    "ID": {
        "given_name": {"mandatory": True, "value_type": "string"},
        "family_name": {"mandatory": True, "value_type": "string"},
        "email": {"value_type": "string"},
        "phone_number": {"value_type": "number"},
        "address": {
            "street_address": {"value_type": "string"},
            "state": {"value_type": "string"},
            "country": {"value_type": "string"},
        },
        "birthdate": {"mandatory": True, "value_type": "number"},
        "is_over_18": {"mandatory": True, "value_type": "string"},
    }
}

credential_issuer = DefaultIssuer(
    credentials,
    # "https://issuer-lib:8082",
    "/usr/src/app/examples/example_jwk_private.pem",
    "/usr/src/app/examples/example_diddoc.json",
    "/usr/src/app/examples/example_didconf.json",
    "/usr/src/app/examples/example_metadata.json",
    "/usr/src/app/examples/example_oauth_metadata.json",
)
credential_issuer_server = credential_issuer.get_server()
