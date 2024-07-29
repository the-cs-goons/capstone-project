from typing import Any

from pydantic import BaseModel, Field

from vclib.common.src.models.oauth2 import (
    AuthorizationRequestObject,
    TokenResponseObject,
)


class DisplayMetadataObject(BaseModel):
    name: str | None = Field(default=None)
    locale: str | None = Field(default=None)
    logo: dict[str, Any] | None = Field(default=None)


class CredentialDisplayMetadataObject(DisplayMetadataObject):
    description: str | None = Field(default=None)
    background_color: str | None = Field(default=None)
    text_color: str | None = Field(default=None)
    background_image: dict[str, Any] | None = Field(default=None)


class CredentialConfigurationsObject(BaseModel):
    format: str
    scope: str | None = Field(default=None)
    cryptographic_binding_methods_supported: list[str] | None = Field(default=None)
    credential_signing_alg_values_supported: list[str] | None = Field(default=None)
    proof_types_supported: dict[str, dict[str, list[str]]] | None = Field(default=None)
    display: list[CredentialDisplayMetadataObject] | None = Field(default=None)


class SDJWTVCCredentialConfigurationsObject(CredentialConfigurationsObject):
    vct: str
    claims: dict[str, Any] | None = Field(default=None)
    order: list[str] | None = Field(default=None)


class IssuerOpenID4VCIMetadata(BaseModel):
    credential_issuer: str
    authorization_servers: list[str] | None = Field(default=None)
    credential_endpoint: str
    deferred_credential_endpoint: str | None = Field(default=None)
    notification_endpoint: str | None = Field(default=None)
    credential_response_encryption: dict | None = Field(default=None)
    batch_credential_issuance: dict | None = Field(default=None)
    signed_metadata: str | None = Field(default=None)
    display: list[DisplayMetadataObject] | None = Field(default=None)
    credential_configurations_supported: dict[
        str, CredentialConfigurationsObject | SDJWTVCCredentialConfigurationsObject
    ] = Field(discriminator="format")


class CredentialOfferObject(BaseModel):
    credential_issuer: str
    credential_configuration_ids: list[str]
    grants: dict[str, dict] | None = Field(default=None)


class HolderOpenID4VCIAuthorizationRequestObject(AuthorizationRequestObject):
    wallet_issuer: str | None = Field(default=None)
    user_hint: str | None = Field(default=None)
    issuer_state: str | None = Field(default=None)


class HolderOpenID4VCITokenResponseObject(TokenResponseObject):
    c_nonce: str | None = Field(default=None)
    c_nonce_expires_in: int | None = Field(default=None)


class ProofObject(BaseModel):
    proof_type: str


class JWTProofObject(ProofObject):
    jwt: str


class CredentialRequestObject(BaseModel):
    credential_identifier: str | None = Field(default=None)
    format: str | None = Field(default=None)
    proof: ProofObject | None = Field(default=None)
    proofs: dict[str, list[Any]] | None = Field(default=None)
    credential_response_encryption: dict[str, Any] | None = Field(default=None)


class DeferredCredentialRequestObject(BaseModel):
    transaction_id: str


class CredentialResponseObject(BaseModel):
    credential: str | dict | None = Field(default=None)
    credentials: list[str | dict] | None = Field(default=None)
    transaction_id: str | None = Field(default=None)
    c_nonce: str | None = Field(default=None)
    c_nonce_expires_in: int | None = Field(default=None)
    notification_id: str | None = Field(default=None)
