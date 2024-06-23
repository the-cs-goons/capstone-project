from typing import Any, override

from issuer import CredentialIssuer


class DefaultIssuer(CredentialIssuer):
    def __init__(self):
        super().__init__()
        self.statuses = {}

    @override
    def get_request(self, ticket: int, cred_type: str, information: object) -> Any:
        self.statuses[ticket] = (cred_type, information)
        return

    @override
    def get_status(self, ticket: int) -> Any:
        return self.statuses[ticket]


credential_issuer = DefaultIssuer()
credential_issuer_server = credential_issuer.get_server()
