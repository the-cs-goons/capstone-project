from typing import Any, List

from vclib.owner.src.models.credentials import Credential, DeferredCredential


class AbstractStorageProvider():

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        pass

    def __exit__(self):
        pass

    def register(self, *args, **kwargs):
        """
        Performs operations associated with registering a new user.
        Implementation specific.
        """
        pass

    def unlock(self, *args, **kwargs):
        """
        Performs operations needed to access some form of storage.
        Implementation specific.
        """
        pass

    def lock(self, *args, **kwargs):
        """
        Performs operations needed to remove access to some form of storage.
        Implementation specific.
        """
        pass

    def get(self, cred_id: str, *args, **kwargs) -> Credential | DeferredCredential:
        """
        Retrieves corresponding credential
        """
        pass

    def get_all(self, *args, **kwargs) -> List[Credential | DeferredCredential]:
        """
        Retrieves all credentials
        """
        pass

    def get_deferred(self, *args, **kwargs) -> List[DeferredCredential]:
        """
        Retrieves all deferred credentials
        """
        pass

    def add(self, cred: Credential | DeferredCredential, *args, **kwargs):
        """
        Adds a credential to storage
        """
        pass

    def update(self, cred: Credential | DeferredCredential, *args, **kwargsl):
        """
        Updates a credential already in storage.
        """
        pass

    def upsert(self, cred: Credential | DeferredCredential, *args, **kwargs):
        """
        Updates a credential already in storage if it exists, otherwise, adds it.
        """
        pass

    def save(self, *args, **kwargs):
        """
        Performs operations to push data to persistent storage (e.g. flushing to a 
        database).
        Implementation specific.
        """
        pass
