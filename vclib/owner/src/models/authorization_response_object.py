from pydantic import BaseModel
from .presentation_submission_object import PresentationSubmissionObject

class AuthorizationResponseObject(BaseModel):
    vp_token: str | list[str]
    presentation_submission: PresentationSubmissionObject
    state: str
