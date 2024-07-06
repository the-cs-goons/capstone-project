"""
Identity Owner module
"""

# Add imports from `owner/src` here to expose objects under vclib.owner
from .src.identity_owner import IdentityOwner
from .src.models.credentials import Credential
from .src.web_identity_owner import WebIdentityOwner
