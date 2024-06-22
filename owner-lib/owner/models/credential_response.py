from pydantic import BaseModel
from enum import Enum
from requests import Response


class CredentialResponseState(Enum):
    PENDING = 0
    ACCEPTED = 1
    REJECTED = 2

class CredentialResponse(BaseModel):
    state: CredentialResponseState | None
    response_status: str
    rejection_msg: str | None
    sd_jwt: str | None
    response_obj: Response

