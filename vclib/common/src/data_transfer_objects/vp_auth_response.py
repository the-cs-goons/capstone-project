from pydantic import BaseModel


class DescriptorMapObject(BaseModel):
    id: str
    format: str = "vc+sd-jwt"
    path: str  # json string expression
    # path will be "$" for single vcs or
    # "$.verifiableCredential[n]" if there are
    # multiple in a presentation

    # path_nested: any  ## TODO: implement nested paths

class PresentationSubmissionObject(BaseModel):
    id: str
    definition_id: str
    descriptor_map: list[DescriptorMapObject]


class AuthorizationResponseObject(BaseModel):
    vp_token: str | list[str]
    presentation_submission: PresentationSubmissionObject
    state: str
