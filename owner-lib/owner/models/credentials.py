from datetime import datetime
from base64 import b64decode, b64encode

from pydantic import BaseModel
from requests import Session

class Credential(BaseModel):
    issuer_url: str # Not super useful to have now, but will be necessary for key bound SD-JWTs later if retrieving JWKs
    type: str
    token: str | None = None
    status = "Pending" 
    request_url: str
    status_message: str | None = None
    issuer_name: str | None = None
    received_at: datetime | None = None

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
            self.state = response.json()

    async def retrieve_credential(self):
        pass

    def serialise_and_encrypt(self, key: str):
        """
        Converts the Credential object into some string value that can be stored and encrypts it

        TODO: Implement encryption
        """
        return b64encode(self.model_dump_json())


