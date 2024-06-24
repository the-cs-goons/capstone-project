from .base_model_json import BaseModelJson
from .presentation_definition import PresentationDefinition

class PresentationRequest(BaseModelJson):
    client_id: str
    presentation_definition:PresentationDefinition
    redirect_uri: str = None