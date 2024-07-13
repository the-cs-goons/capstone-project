from enum import Enum

from pydantic import BaseModel


class TokenAuthMethod(Enum):
    CLIENT_SECRET_BASIC = "client_secret_basic"
    CLIENT_SECRET_POST = "client_secret_post"
    NONE = "none"


class WalletClientMetadata(BaseModel):
    redirect_uris: list[str]
    credential_offer_endpoint: str
    token_endpoint_auth_method: TokenAuthMethod | str
    grant_types: list[str]
    response_types: list[str]
    authorization_details_types: list[str]

    # Extra optional fields for human readability
    client_name: str | None
    client_uri: str | None
    logo_uri: str | None

class RegisteredClientMetadata(WalletClientMetadata):
    client_id: str
    client_secret: str
