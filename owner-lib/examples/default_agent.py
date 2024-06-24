from typing import override
from owner import WebIdentityOwner, Credential

class DefaultWebIdentityOwner(WebIdentityOwner):
    
    @override
    def load_all_credentials_from_storage(self) -> list[Credential]:
        pass

    @override
    def load_credential_from_storage(self, cred_id: str) -> Credential:
        pass

    @override
    def store_credential(self, cred: Credential):
        pass

identity_owner = DefaultWebIdentityOwner("")
identity_owner_server = identity_owner.get_server()
