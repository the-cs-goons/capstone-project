from uuid import uuid4

from pydantic import BaseModel, Field

from vclib.common.src.models.oid4vci import (
    CredentialOfferObject,
    HolderOpenID4VCITokenResponseObject,
)


class BaseCredential(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    issuer_name: str | None = Field(default=None)
    issuer_url: str
    credential_configuration_id: str
    credential_configuration_name: str | None = Field(default=None)
    is_deferred: bool
    c_type: str


class DeferredCredential(BaseCredential):
    transaction_id: str
    deferred_credential_endpoint: str
    last_request: str
    access_token: HolderOpenID4VCITokenResponseObject


class Credential(BaseCredential):
    raw_sdjwtvc: str
    received_at: str


class CredentialSelection(BaseModel):
    credential_configuration_id: str
    credential_offer: CredentialOfferObject | None = Field(default=None)
    issuer_uri: str | None = Field(default=None)
