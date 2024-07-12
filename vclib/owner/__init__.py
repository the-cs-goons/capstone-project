"""Identity Owner module"""

# Add imports from `owner/src` here to expose objects under vclib.owner
from .src.identity_owner import IdentityOwner as IdentityOwner
from .src.models.credentials import Credential as Credential
from .src.web_identity_owner import WebIdentityOwner as WebIdentityOwner
