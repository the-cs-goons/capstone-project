from typing import Any, List, Optional
from pydantic import BaseModel, Field, HttpUrl

class IssuerMetadata(BaseModel):
    credential_issuer: HttpUrl
    credential_endpoint: str
    batch_credential_endpoint: Optional[str]
    deferred_credential_endpoint: Optional[str]
    notification_endpoint: Optional[str]
    credential_configurations_supported: List
    credential_identifiers_supported: Optional[bool]
    display: Optional[Any]

class AuthorizationMetadata(BaseModel):
    """
    "issuer": Credential Issuer Identifier
    "authorization_endpoint": "[Credential Issuer Identifier]/authorise"
    "token_endpoint": "[Credential Issuer Identifier]/token"
    "registration_endpoint": "[Credential Issuer Identifier]/register"
    "scopes_supported": unsure if anything needed here, if yes just put the credential names
    "response_types_supported": ["code"] // might change if doing pre-auth
    "grant_types_supported": ["authorization_code"} // ditto
    "authorization_details_types_supported": ["openid_credential"]
    "pre-authorized_grant_anonymous_access_supported": false (for now)

    """
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    registration_endpoint: str
    scopes_supported: Optional[Any]
    response_types_supported: List[str]
    grant_types_supported: List[str]
    authorization_details_types_supported: List[str]
    pre_authorized_supported: bool = Field(serialization_alias="pre-authorized_grant_anonymous_access_supported")
