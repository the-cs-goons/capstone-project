from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PublicKeyJwk(BaseModel):
    kty: str
    use: str
    alg: str
    crv: str
    x: str
    y: str
    kid: str


class VerificationMethod(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    type: str
    controller: str
    publicKeyJwk: PublicKeyJwk  # noqa: N815


class DIDJSONResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    context: list[str] = Field(alias="@context")
    id: str
    # alsoKnownAs: list[str] | None = Field(default=None)
    verificationMethod: list[VerificationMethod] | None = Field(default=None)  # noqa: N815
    # authentication: list[str | VerificationMethod] | None = Field(default=None)
    assertionMethod: list[str | VerificationMethod] | None = Field(default=None)  # noqa: N815
    # keyAgreement: list[str | VerificationMethod] | None = Field(default=None)
    # capabilityInvocation: list[str | VerificationMethod] | None = Field(default=None)
    # capabilityDelegation: list[str | VerificationMethod] | None = Field(default=None)


class ConfigEntries(BaseModel):
    did: str
    jwt: str


class DIDConfigResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    entries: list[ConfigEntries]


class ProofTypesSupported(BaseModel):
    proof_signing_alg_values_supported: str


class UniqueCredentialIdentifier(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    format: str
    vct: str
    # scope: str
    cryptographic_binding_methods_supported: list[str]
    credential_signing_alg_values_supported: list[str]
    proof_types_supported: dict[str, ProofTypesSupported]
    claims: dict[str, dict[str, Any] | list[dict[str, Any]]]
