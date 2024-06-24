from datetime import datetime
from enum import Enum

from pydantic import BaseModel
from requests import Session

class CredentialResponseState(Enum):
    Pending = 0
    Accepted = 1
    Rejected = 2

class Credential(BaseModel):
    issuer_url: str
    sd_jwt: str | None
    status: CredentialResponseState
    request_url: str
    status_message: str
    issuer_name: str
    received_at: datetime

    attributes: dict[str: object]

    async def poll_status(self):
        """
        Makes a request for a pending credential
        TODO:
        - enforce https for non-dev mode for security purposes
        - validate body comes in expected format
        """
        # Closes session afterwards
        with Session() as s:
            response = await s.get(self.request_url)
            if not response.ok:
                raise response.error
            # TODO: Logic for updating state according to how Mal's structured things
            self.state = response

    async def retrieve_credential(self):
        pass
