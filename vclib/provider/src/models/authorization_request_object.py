from pydantic import BaseModel

from .presentation_definition import PresentationDefinition


class AuthorizationRequestObject(BaseModel):
    client_id: str
    client_id_scheme: str = "did"
    client_metadata: dict
    presentation_definition: PresentationDefinition
    response_uri: str
    response_type: str = "vp_token"
    response_mode: str = "direct_post"
    nonce: str
    wallet_nonce: str | None = None
    state: str | None = None  # transaction id
