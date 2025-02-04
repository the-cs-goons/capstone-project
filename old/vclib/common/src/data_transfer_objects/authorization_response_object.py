from pydantic import BaseModel

from .presentation_submission import PresentationSubmission


class AuthorizationResponseObject(BaseModel):
    vp_token: str | list[str]
    presentation_submission: PresentationSubmission
    state: str
