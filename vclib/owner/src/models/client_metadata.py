from typing import Optional

from pydantic import BaseModel

class WalletClientMetadata(BaseModel):
    redirect_uris: list[str]
    credential_offer_endpoint: str
    token_endpoint_auth_method: str
    grant_types: list[str]
    response_types: list[str]
    authorization_details_types: list[str]

    # Extra optional fields for human readability
    client_name: Optional[str]
    client_uri: Optional[str]
    logo_uri: Optional[str]

class RegisteredClientMetadata(WalletClientMetadata):
    client_id: str
    client_secret: str
    
    issuer_uri: str
