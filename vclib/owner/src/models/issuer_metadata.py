from typing import Any

from pydantic import BaseModel, Field


class IssuerMetadata(BaseModel):
    credential_issuer: str
    credential_endpoint: str
    batch_credential_endpoint: str | None = Field(default=None)
    deferred_credential_endpoint: str | None = Field(default=None)
    notification_endpoint: str | None = Field(default=None)
    credential_configurations_supported: dict
    credential_identifiers_supported: bool | None = Field(default=None)
    display: Any | None = Field(default=None)

class AuthorizationMetadata(BaseModel):
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    registration_endpoint: str
    scopes_supported: Any | None = Field(default=None)
    response_types_supported: list[str]
    grant_types_supported: list[str]
    authorization_details_types_supported: list[str]
    pre_authorized_supported: bool = Field(
        serialization_alias="pre-authorized_grant_anonymous_access_supported")
