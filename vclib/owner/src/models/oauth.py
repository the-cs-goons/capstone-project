from typing import Any, List, Optional
from pydantic import BaseModel

class AuthorizationDetails(BaseModel):
    type: str
    credential_configuration_id: str
    credential_identifiers: List[str]

class OAuthTokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    c_nonce: Optional[Any]
    c_nonce_expires_in: Optional[Any]
    authorization_details: List[AuthorizationDetails]