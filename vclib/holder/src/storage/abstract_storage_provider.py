
from vclib.holder.src.models.credentials import Credential, DeferredCredential


class AbstractStorageProvider:

    def __init__(self, *args, **kwargs):
        pass

    def register(self, *args, **kwargs):
        """
        Performs operations associated with registering a new user.
        Implementation specific.
        """

    def login(self, *args, **kwargs):
        """
        Performs operations needed to access a user's wallet.
        """

    def logout(self, *args, **kwargs):
        """
        Performs operations needed to reverse the relevant operations performed during
        login/register
        """

    def get_credential(
            self,
            cred_id: str,
            *args,
            **kwargs
            ) -> Credential | DeferredCredential | None:
        """
        Retrieves corresponding credential
        """

    def get_received_credentials(
            self,
            *args,
            **kwargs
            ) -> list[Credential]:
        """
        Retrieves all credentials
        """

    def get_deferred_credentials(
            self,
            *args,
            **kwargs
            ) -> list[DeferredCredential]:
        """
        Retrieves all deferred credentials
        """

    def all_credentials(
            self,
            *args,
            **kwargs
            ) -> list[Credential | DeferredCredential]:
        """
        Retrieves all credentials
        """

    def add_credential(self, cred: Credential | DeferredCredential, *args, **kwargs):
        """
        Adds a credential to storage
        """

    def delete_credential(self, cred: Credential | DeferredCredential, *args, **kwargs):
        """
        Deletes a credential from storage
        """

    def update_credential(self, cred: Credential | DeferredCredential, *args, **kwargs):
        """
        Updates a credential already in storage.
        """

    def upsert_credential(self, cred: Credential | DeferredCredential, *args, **kwargs):
        """
        Updates a credential already in storage if it exists, otherwise, adds it.
        """

    def save(self):
        """
        Performs operations to push data to persistent storage (e.g. flushing to a
        database).
        Implementation specific.
        """
