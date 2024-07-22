from pydantic import BaseModel

class VPCredentialAuthorization(BaseModel):
    approved: bool