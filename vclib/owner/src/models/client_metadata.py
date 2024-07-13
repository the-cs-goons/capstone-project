from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, AnyUrl

class TokenAuthMethod(Enum):
    CLIENT_SECRET_BASIC = "client_secret_basic"
    CLIENT_SECRET_POST = "client_secret_post"
    NONE = "none"


class WalletClientMetadata(BaseModel):
    redirect_uris: List[AnyUrl]
    credential_offer_endpoint: AnyUrl
    token_endpoint_auth_method: TokenAuthMethod | str
    grant_types: List[str]
    response_types: List[str]
    authorization_details_types: List[str]

    # Extra optional fields for human readability
    client_name: Optional[str]
    client_uri: Optional[str]
    logo_uri: Optional[str]

class RegisteredClientMetadata(WalletClientMetadata):
    client_id: str
    client_secret: str
