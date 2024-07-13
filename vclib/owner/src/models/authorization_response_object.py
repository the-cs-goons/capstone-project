from pydantic import BaseModel

class AuthorizationRequestObject(BaseModel):
    vp_token: str
    presentation_submission: str
    state: str