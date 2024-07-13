from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class IssuerMetadata(BaseModel):
    credential_issuer: HttpUrl
    credential_endpoint: str
    batch_credential_endpoint: str | None
    deferred_credential_endpoint: str | None
    notification_endpoint: str | None
    credential_configurations_supported: list
    credential_identifiers_supported: bool | None
    display: Any | None

class AuthorizationMetadata(BaseModel):
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    registration_endpoint: str
    scopes_supported: Any | None
    response_types_supported: list[str]
    grant_types_supported: list[str]
    authorization_details_types_supported: list[str]
    pre_authorized_supported: bool = Field(
        serialization_alias="pre-authorized_grant_anonymous_access_supported")
