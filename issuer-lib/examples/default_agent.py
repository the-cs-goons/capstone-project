from typing import Any, override

from issuer import CredentialIssuer


class DefaultIssuer(CredentialIssuer):
    """Example implementation of the `CredentialIssuer` base class.
    
    ### Added Attributes
    - statuses`(dict[int, (str, dict)])`: Dictionary storing the current status
      of active credential requests."""
    statuses: dict[int, (str, dict)]

    @override
    def get_request(self, ticket: int, cred_type: str, information: dict):
        self.statuses[ticket] = (cred_type, information)
        return

    @override
    def get_status(self, ticket: int) -> Any:
        return self.statuses[ticket]


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

credential_issuer = DefaultIssuer(credentials)
credential_issuer_server = credential_issuer.get_server()
