

from pydantic import BaseModel, Field


class CredentialOffer(BaseModel):
    """
    Credential Offer Type
    See secton 4.1.1 of
    https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0-ID1.html for
    further details
    - credential_issuer(`str`): The URL of the Credential Issuer. Used to obtain the
    issuer's metadata, and any credentials.
    - credential_configuration_ids(`list[str]`): An array of unique strings identifying
    the names of each key/value pair under `credential_configurations_supported` as
    given by the credential issuer's metadata.
    - Optional object indicating the Grant Types (OAuth 2.0) the Credential Issuer's
    Authorization Server accepts for this credential offer, plus extra parameters to
    use.
    """
    credential_issuer: str
    credential_configuration_ids: list[str]
    grants: dict | None = Field(default=None)


