from typing import Any, Optional

from pydantic import BaseModel, Field


class IssuerMetadata(BaseModel):
    credential_issuer: str
    credential_endpoint: str
    batch_credential_endpoint: Optional[str]
    deferred_credential_endpoint: Optional[str]
    notification_endpoint: Optional[str]
    credential_configurations_supported: list
    credential_identifiers_supported: Optional[bool]
    display: Optional[Any]

class AuthorizationMetadata(BaseModel):
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    registration_endpoint: str
    scopes_supported: Optional[Any]
    response_types_supported: list[str]
    grant_types_supported: list[str]
    authorization_details_types_supported: list[str]
    pre_authorized_supported: bool = Field(
        serialization_alias="pre-authorized_grant_anonymous_access_supported")
