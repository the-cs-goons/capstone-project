from typing import override

from owner import Credential, WebIdentityOwner

MOCK_STORE = {
    "example1": {
        "id": "example1",
        "issuer_url": "https://example.com",
        "type": "Example",
        "request_url": "https://example.com/status?token=example1",
        "token": "qwertyuiop",
        "status":"ACCEPTED",
        "status_message":None,
        "issuer_name":"Example Issuer",
        "received_at":1719295821397
    },
    "example2": {
        "id": "example2",
        "issuer_url": "https://example.com",
        "type": "Example",
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

identity_owner = DefaultWebIdentityOwner("", mock_data=MOCK_STORE)
identity_owner_server = identity_owner.get_server()
