from typing import override

from owner import Credential, WebIdentityOwner


class DefaultWebIdentityOwner(WebIdentityOwner):
    
    @override
    def load_all_credentials_from_storage(self) -> list[Credential]:
        return []

    @override
    def load_credential_from_storage(self, cred_id: str) -> Credential:
        return None

    @override
    def store_credential(self, cred: Credential):
        return

identity_owner = DefaultWebIdentityOwner("")
identity_owner_server = identity_owner.get_server()
