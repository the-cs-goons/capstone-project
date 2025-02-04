from pydantic import BaseModel, Field


class WalletClientMetadata(BaseModel):
    redirect_uris: list[str]
    credential_offer_endpoint: str
    token_endpoint_auth_method: str = Field(default="client_secret_basic")
    grant_types: list[str] = Field(default=["authorization_code"])
    response_types: list[str] = Field(["code"])
    authorization_details_types: list[str] = Field(default=["openid_credential"])

    # Extra optional fields for human readability
    client_name: str | None = Field(default=None)
    client_uri: str | None = Field(default=None)
    logo_uri: str | None = Field(default=None)


class RegisteredClientMetadata(WalletClientMetadata):
    client_id: str
    client_secret: str

    issuer_uri: str
