"""Service Provider (Credential Verifier) module"""

# Add imports from `provider/src` here to expose objects under vclib.provider
from .src.models.authorization_request_object import (
    AuthorizationRequestObject as AuthorizationRequestObject,
)
from .src.models.presentation_definition import (
    PresentationDefinition as PresentationDefinition,
)
from .src.service_provider import ServiceProvider as ServiceProvider
