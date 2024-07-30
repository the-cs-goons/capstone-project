from abc import ABCMeta, abstractmethod

from vclib.common import credentials


class AbstractStorageProvider(metaclass=ABCMeta):
    @abstractmethod
    def register(self, *args, **kwargs):
        """
        Performs operations associated with registering a new user.
        Implementation specific.
        """
        raise NotImplementedError

    @abstractmethod
    def login(self, *args, **kwargs):
        """
        Performs operations needed to access a user's wallet.
        """
        raise NotImplementedError

    @abstractmethod
    def logout(self, *args, **kwargs):
        """
        Performs operations needed to reverse the relevant operations performed during
        login/register
        """
        raise NotImplementedError

    @abstractmethod
    def get_credential(
        self, cred_id: str, *args, **kwargs
    ) -> credentials.Credential | credentials.DeferredCredential | None:
        """
        Retrieves corresponding credential
        """
        raise NotImplementedError

    @abstractmethod
    def get_received_credentials(self, *args, **kwargs) -> list[credentials.Credential]:
        """
        Retrieves all credentials
        """
        raise NotImplementedError

    @abstractmethod
    def get_deferred_credentials(
        self, *args, **kwargs
    ) -> list[credentials.DeferredCredential]:
        """
        Retrieves all deferred credentials
        """
        raise NotImplementedError

    @abstractmethod
    def all_credentials(
        self, *args, **kwargs
    ) -> list[credentials.Credential | credentials.DeferredCredential]:
        """
        Retrieves all credentials
        """
        raise NotImplementedError

    @abstractmethod
    def add_credential(
        self,
        cred: credentials.Credential | credentials.DeferredCredential,
        *args,
        **kwargs,
    ):
        """
        Adds a credential to storage
        """
        raise NotImplementedError

    @abstractmethod
    def add_many(
        self,
        creds: list[credentials.Credential | credentials.DeferredCredential],
        *args,
        **kwargs,
    ):
        """
        Adds many credentials to storage.
        """
        [self.add_credential(c, *args, **kwargs) for c in creds]

    @abstractmethod
    def delete_credential(self, cred_id: str, *args, **kwargs):
        """
        Deletes a credential from storage
        """
        raise NotImplementedError

    @abstractmethod
    def delete_many(self, cred_ids: list[str], *args, **kwargs):
        """
        Deletes many credentials from storage
        """
        [self.delete_credential(c, *args, **kwargs) for c in cred_ids]

    @abstractmethod
    def update_credential(
        self,
        cred: credentials.Credential | credentials.DeferredCredential,
        *args,
        **kwargs,
    ):
        """
        Updates a credential already in storage.
        """

    @abstractmethod
    def update_many(
        self,
        creds: list[credentials.Credential | credentials.DeferredCredential],
        *args,
        **kwargs,
    ):
        """
        Update many credentials.
        """
        [self.update_credential(c, *args, **kwargs) for c in creds]

    @abstractmethod
    def upsert_credential(
        self,
        cred: credentials.Credential | credentials.DeferredCredential,
        *args,
        **kwargs,
    ):
        """
        Updates a credential already in storage if it exists, otherwise, adds it.
        """
        raise NotImplementedError

    @abstractmethod
    def upsert_many(
        self,
        creds: list[credentials.Credential | credentials.DeferredCredential],
        *args,
        **kwargs,
    ):
        """
        Add or update many credentials.
        """
        [self.upsert_credential(c, *args, **kwargs) for c in creds]

    @abstractmethod
    def save(self):
        """
        Performs operations to push data to persistent storage (e.g. flushing to a
        database).
        Implementation specific.
        """
        raise NotImplementedError
