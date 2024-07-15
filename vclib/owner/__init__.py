"""
Identity Owner module
"""

# Add imports from `owner/src` here to expose objects under vclib.owner
from .src.identity_owner import IdentityOwner as IdentityOwner
from .src.models.client_metadata import (
    RegisteredClientMetadata as RegisteredClientMetadata,
)
from .src.models.client_metadata import WalletClientMetadata as WalletClientMetadata
from .src.models.credential_offer import CredentialOffer as CredentialOffer
from .src.models.credentials import Credential as Credential
from .src.models.credentials import DeferredCredential as DeferredCredential
from .src.models.issuer_metadata import AuthorizationMetadata as AuthorizationMetadata
from .src.models.issuer_metadata import IssuerMetadata as IssuerMetadata
from .src.models.oauth import AccessToken as AccessToken
from .src.models.oauth import AuthorizationDetails as AuthorizationDetails
from .src.models.oauth import OAuthTokenResponse as OAuthTokenResponse
from .src.models.request_body import CredentialSelection as CredentialSelection
from .src.web_identity_owner import WebIdentityOwner as WebIdentityOwner
