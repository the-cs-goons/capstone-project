from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel


class Credential(BaseModel):
    id: str

    issuer_name: Optional[str]
    issuer_url: str
    issuer_metadata_url: Optional[str]

    is_deferred: bool
    transaction_id: Optional[str]
    deferred_credential_endpoint: Optional[str]

    cred_type: str
    credential_configuration_id: str
    retrieve_from: Optional[str]
    sd_jwt_vc: Optional[str]
    credential_configuration: Dict

    received_at: Optional[int]
    access_token: Optional[str]
