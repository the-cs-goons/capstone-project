"""
Identity Owner module
"""

# Add imports from `owner/src` here to expose objects under vclib.owner
from .src.holder import Holder as Holder
from .src.models.credential_offer import CredentialOffer as CredentialOffer
from .src.models.credential_offer import CredentialSelection as CredentialSelection
from .src.models.oauth import AccessToken as AccessToken
from .src.models.oauth import AuthorizationDetails as AuthorizationDetails
from .src.models.oauth import OAuthTokenResponse as OAuthTokenResponse
from .src.storage.abstract_storage_provider import (
    AbstractStorageProvider as AbstractStorageProvider,
)
from .src.storage.local_storage_provider import (
    LocalStorageProvider as LocalStorageProvider,
)
from .src.web_holder import WebHolder as WebHolder
