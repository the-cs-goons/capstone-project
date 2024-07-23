from typing import Any

from .abstract_storage_provider import AbstractStorageProvider
from vclib.owner.src.models.credentials import Credential, DeferredCredential

class LocalStorageProvider(AbstractStorageProvider):

    storage_dir: str
    active_user_store: str

    def __init__(self):
        pass

    def __enter__(self):
        pass

    def __exit__(self):
        pass

    def register(self, username: str):
        pass

    def unlock(self, *args, **kwargs):
        pass

    def get(self, cred_id: str):
        """
        Retrieves corresponding credential
        """
        pass

    def get_all(self):
        pass

    def get_deferred(self):
        pass

    def lock(self):
        pass

    def add(self, cred):
        pass

    def update(self, cred):
        pass

    def upsert(self, cred):
        pass

    def save(self, cred):
        pass