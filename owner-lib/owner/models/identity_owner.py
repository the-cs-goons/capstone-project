from credentials import Credential
from abc import abstractmethod

class IdentityOwner:
    credentials: list[Credential]
    dev_mode: False # HTTPS not enforced if running in development context

    @abstractmethod
    def retrieve_credentials_from_storage(self):
        return NotImplementedError

    @abstractmethod
    def save_credentials_to_storage(self):
        return NotImplementedError

    def refresh_credential(self, cred: Credential):
        pass


