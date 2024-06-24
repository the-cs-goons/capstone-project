from datetime import datetime
from base64 import b64decode, b64encode
from json import loads

from pydantic import BaseModel
from requests import Session

class Credential(BaseModel):
    id: str # Something arbitrary to identify the credential with. For the ID Owner's use only.
    issuer_url: str # Not super useful to have now, but will be necessary for key bound SD-JWTs later if retrieving JWKs
    type: str
    request_url: str
    token: str | None = None
    status = "PENDING" 
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
            body: dict = response.json()
            self.status = body["status"]

            if self.status == "ACCEPTED":
                self.token = body["credential"]
            elif self.status == "REJECTED":
                self.status_message = body["detail"]

    def serialise_and_encrypt(self, key: str):
        """
        # NOT YET IMPLEMENTED IN FULL
        TODO: Implement encryption
        Converts the Credential object into some string value that can be stored and encrypts it
        
        ### Parameters
        - key(`str`): password for encrypting credential
        """
        return b64encode(self.model_dump_json())
    
    @staticmethod
    def load_from(dump: str):
        """
        # NOT YET IMPLEMENTED IN FULL
        TODO: Implement decryption
        Loads a credential from encrypted & serialised string
        
        ### Parameters
        - key(`str`): password for decrypting credential
        """
        return Credential.model_validate(loads(b64decode(dump)))


