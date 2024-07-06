import datetime
from typing import Any, override

from src import CredentialIssuer, StatusResponse


class DefaultIssuer(CredentialIssuer):
    """Example implementation of the `CredentialIssuer` base class.

    ### Added Attributes
    - statuses`(dict[int, (str, dict)])`: Dictionary storing the current status
      of active credential requests."""

    statuses: dict[int, (str, dict)]
    time: datetime

    @override
    def __init__(
        self, credentials: dict[str, dict[str, dict[str, Any]]], private_key_path: str
    ):
        super().__init__(credentials, private_key_path)
        self.statuses = {}

    @override
    def get_request(self, ticket: int, cred_type: str, information: dict):
        self.statuses[ticket] = (cred_type, information)
        self.time = datetime.datetime.now()
        return

    @override
    def get_status(self, ticket: int) -> StatusResponse:
        cred_type, information = self.statuses[ticket]

        curr_time = datetime.datetime.now()
        if curr_time - self.time < datetime.timedelta(0, 40, 0):
            return StatusResponse(status="PENDING", cred_type=None, 
                              information=None)
        
        return StatusResponse(status="ACCEPTED", cred_type=cred_type, 
                              information=information)


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

credential_issuer = DefaultIssuer(credentials, 
                                  "/usr/src/examples/example_private_key.pem")
credential_issuer_server = credential_issuer.get_server()