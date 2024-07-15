"""Identity Owner module"""

# Add imports from `owner/src` here to expose objects under vclib.owner
from .src.identity_owner import IdentityOwner as IdentityOwner
from .src.models.authorization_request_object import AuthorizationRequestObject
from .src.models.credentials import Credential as Credential
from .src.models.presentation_definition import PresentationDefinition
from .src.web_identity_owner import WebIdentityOwner as WebIdentityOwner
