from typing import override

from fastapi import FastAPI

from vclib.common import hello_world
from vclib.owner import Credential, WebIdentityOwner

MOCK_STORE = {
    "example1": {
        "id": "example1",
        "issuer_url": "https://example.com",
        "type": "Passport",
        "request_url": "https://example.com/status?token=example1",
        "token":
            "eyJuYW1lIjoiTWFjayBDaGVlc2VNYW4iLCJkb2IiOiIwMS8wMS8wMSIsImV4cGlyeSI6IjEyLzEyLzI1In0=",
        "status":"ACCEPTED",
        "status_message":None,
        "issuer_name":"Example Issuer",
        "received_at":1719295821397
    },
    "example2": {
        "id": "example2",
        "issuer_url": "https://example.com",
        "type": "Driver's Licence",
        "request_url": "https://example.com/status?token=example2",
        "token": None,
        "status":"PENDING",
        "status_message":None,
        "issuer_name":"Example Issuer",
        "received_at":None
    }
}

class DefaultWebIdentityOwner(WebIdentityOwner):

    def __init__(self, storage_key, dev_mode=False, mock_data={}):
        self.MOCK_STORE = mock_data
        super().__init__(storage_key, dev_mode=dev_mode)
    
    @override
    def load_all_credentials_from_storage(self) -> list[Credential]:
        return [Credential.model_validate(cred) for cred in self.MOCK_STORE.values()]

    @override
    def load_credential_from_storage(self, cred_id: str) -> Credential:
        return self.MOCK_STORE[cred_id]

    @override
    def store_credential(self, cred: Credential):
        self.MOCK_STORE[cred.id] = cred

    @override
    def get_server(self) -> FastAPI:
        router = super().get_server()
        router.get("/hello")(hello_world)
        return router

identity_owner = DefaultWebIdentityOwner("", mock_data=MOCK_STORE)
identity_owner_server = identity_owner.get_server()
