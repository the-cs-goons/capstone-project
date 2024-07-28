from typing import Any, List, Optional

from vclib.holder.src.models.credentials import Credential, DeferredCredential


class AbstractStorageProvider():

    def __init__(self, *args, **kwargs):
        pass

    def register(self, *args, **kwargs):
        """
        Performs operations associated with registering a new user.
        Implementation specific.
        """
        pass

    def login(self, *args, **kwargs):
        """
        Performs operations needed to access a user's wallet.
        """
        pass

    def logout(self, *args, **kwargs):
        """
        Performs operations needed to reverse the relevant operations performed during
        login/register
        """
        pass

    def get_credential(
            self, 
            cred_id: str, 
            *args, 
            **kwargs
            ) -> Optional[Credential | DeferredCredential]:
        """
        Retrieves corresponding credential
        """
        pass

    def get_received_credentials(
            self, 
            *args, 
            **kwargs
            ) -> List[Credential]:
        """
        Retrieves all credentials
        """
        pass

    def get_deferred_credentials(
            self, 
            *args, 
            **kwargs
            ) -> List[DeferredCredential]:
        """
        Retrieves all deferred credentials
        """
        pass

    def all_credentials(
            self, 
            *args, 
            **kwargs
            ) -> List[Credential | DeferredCredential]:
        """
        Retrieves all credentials
        """
        pass
    
    def add_credential(self, cred: Credential | DeferredCredential, *args, **kwargs):
        """
        Adds a credential to storage
        """
        pass

    def delete_credential(self, cred: Credential | DeferredCredential, *args, **kwargs):
        """
        Deletes a credential from storage
        """
        pass

    def update_credential(self, cred: Credential | DeferredCredential, *args, **kwargs):
        """
        Updates a credential already in storage.
        """
        pass

    def upsert_credential(self, cred: Credential | DeferredCredential, *args, **kwargs):
        """
        Updates a credential already in storage if it exists, otherwise, adds it.
        """
        pass

    def save(self):
        """
        Performs operations to push data to persistent storage (e.g. flushing to a 
        database).
        Implementation specific.
        """
        pass
