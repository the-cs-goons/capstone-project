from typing import Any

from pydantic import BaseModel, Field

from vclib.common.src.models.oauth2 import (
    AuthorizationRequestObject,
    TokenResponseObject,
)


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
