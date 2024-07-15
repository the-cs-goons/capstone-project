from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OptionsResponse(BaseModel):
    options: dict[str, dict[str, dict[str, Any]]]


class RequestResponse(BaseModel):
    ticket: int
    link: str


# In theory used by the frontend to display status page
class UpdateResponse(BaseModel):
    ticket: int
    status: Any
    credential: str | None


class StatusResponse(BaseModel):
    status: Any
    cred_type: str | None
    information: dict[str, Any] | None


class UniqueCredentialIdentifier:
    format: str
    vct: str
    # scope: str
    cryptographic_binding_methods_supported: list[str]
    credential_signing_alg_values_supported: list[str]
    # todo: cleanup the following
    proof_types_supported: dict[str, dict[str, str]]
    claims: dict[str, dict[str, str]]


class MetadataResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    credential_issuer: str
    credential_endpoint: str
    # batch_credential_endpoint: str
    deferred_credential_endpoint: str
    # notification_endpoint: str
    credential_configurations_supported: dict[str, UniqueCredentialIdentifier]
    credential_identifiers_supported: str
    # display: str


class OAuthMetadataResponse(BaseModel):
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    registration_endpoint: str
    scopes_supported: str
    response_types_supported: str
    grant_types_supported: str
    authorization_details_types_supported: str
    anon_access_supported: str = Field(
        alias="pre-authorized_grant_anonymous_access_supported"
    )
