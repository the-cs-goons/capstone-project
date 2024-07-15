from pydantic import BaseModel, Field

from .credential_offer import CredentialOffer


class CredentialSelection(BaseModel):
    credential_configuration_id: str
    credential_offer: CredentialOffer | None = Field(default=None)
    issuer_uri: str | None = Field(default=None)
