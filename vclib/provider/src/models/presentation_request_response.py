from typing import Optional

from .base_model_json import BaseModelJson
from .presentation_definition import PresentationDefinition

class PresentationRequestResponse(BaseModelJson):
    client_id: str
    presentation_definition: PresentationDefinition
    redirect_uri: Optional[str] = None

    def __init__(self, client_id: str, presentation_definition: PresentationDefinition, redirect_uri: Optional[str] = None):
        super().__init__(client_id = client_id, presentation_definition = presentation_definition, redirect_uri = redirect_uri)
