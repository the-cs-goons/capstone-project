import sqlite3
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

    def __conform__(self, protocol):
        if protocol is sqlite3.PrepareProtocol:
            return self.model_dump_json()
        return None


class OAuthTokenResponse(AccessToken):
    c_nonce: Any | None
    c_nonce_expires_in: Any | None
    authorization_details: list[AuthorizationDetails]
