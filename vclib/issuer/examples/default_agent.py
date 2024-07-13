import datetime
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
        private_key_path: str,
        diddoc_path: str,
        did_config_path: str,
        metadata_path: str,
        oauth_metadata_path: str,
    ):
        super().__init__(
            credentials,
            private_key_path,
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
    def get_status(self, ticket: int) -> StatusResponse:
        cred_type, information = self.statuses[ticket]

        curr_time = datetime.datetime.now(tz=datetime.UTC)
        if curr_time - self.time < datetime.timedelta(0, 40, 0):
            return StatusResponse(status="PENDING", cred_type=None, information=None)

        return StatusResponse(
            status="ACCEPTED", cred_type=cred_type, information=information
        )

    @override
    def get_server(self) -> FastAPI:
        router = super().get_server()
        router.get("/hello")(hello_world)
        return router


credentials = {
    "id": {
        "name": {
            "type": "string",
            "optional": False,
        },
        "age": {
            "type": "number",
            "optional": False,
        },
    },
    "id2": {
        "firstname": {
            "type": "string",
            "optional": False,
        },
        "lastname": {
            "type": "string",
            "optional": True,
        },
        "adult": {
            "type": "boolean",
            "optional": False,
        },
    },
}

credential_issuer = DefaultIssuer(
    credentials, "/usr/src/app/examples/example_private_key.pem",
    "/usr/src/app/examples/example_diddoc.json",
    "/usr/src/app/examples/example_didconf.json",
    "/usr/src/app/examples/example_metadata.json",
    "/usr/src/app/examples/example_oauth_metadata.json",
)
credential_issuer_server = credential_issuer.get_server()
