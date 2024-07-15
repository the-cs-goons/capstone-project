from typing import Any

from pydantic import BaseModel


class AuthorizationDetails(BaseModel):
    type: str
    credential_configuration_id: str
    credential_identifiers: list[str]

class AccessToken(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class OAuthTokenResponse(AccessToken):
    c_nonce: Any | None
    c_nonce_expires_in: Any | None
    authorization_details: list[AuthorizationDetails]
