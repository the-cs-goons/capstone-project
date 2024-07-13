from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel


class Credential(BaseModel):
    id: str
    # Something arbitrary to identify the credential with. For the ID Owner's use only.
    issuer_name: Optional[str]
    issuer_url: str
    issuer_metadata_url: Optional[str]

    cred_type: str
    credential_configuration_id: str
    retrieve_from: Optional[str]
    sd_jwt_vc: Optional[str]
    credential_configuration: Dict

    received_at: int
    access_token: Optional[str]
