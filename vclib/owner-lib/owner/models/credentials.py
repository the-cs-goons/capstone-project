from datetime import datetime

from pydantic import BaseModel


class Credential(BaseModel):
    id: str 
    # Something arbitrary to identify the credential with. For the ID Owner's use only.
    issuer_url: str 
    # Not super useful to have now, but may be necessary later for retrieving JWKs
    type: str
    request_url: str
    token: str | None = None
    status: str = "PENDING"
    status_message: str | None = None
    issuer_name: str | None = None
    received_at: datetime | None = None


