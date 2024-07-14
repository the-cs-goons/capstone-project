from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from vclib.common.src.sdjwt_vc.holder import SDJWTVCHolder


class BaseCredential(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().bytes.decode("utf-8"))
    issuer_name: Optional[str]
    issuer_url: str
    credential_configuration_id: str
    credential_configuration_name: Optional[str]
    is_deferred: bool
    c_type: str

class DeferredCredential(BaseCredential):
    transaction_id: str
    deferred_credential_endpoint: str
    access_token: str
    last_request: str

class Credential(BaseCredential):
    raw_sdjwtvc: str
    received_at: str

    
