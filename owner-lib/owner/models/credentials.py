from pydantic import BaseModel
from enum import Enum

class CredentialResponseState(Enum):
    PENDING = 0
    ACCEPTED = 1
    REJECTED = 2

class Credential(BaseModel):
    issuer_url: str
    sd_jwt: str | None
    state: CredentialResponseState
    status_message: str
    issuer_name: str

    attributes: dict[str: object]

    def update_state(self):
        pass