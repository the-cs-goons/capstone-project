from pydantic import BaseModel


class Descriptor(BaseModel):
    id: str
    format: str
    path: str


class PresentationSubmission(BaseModel):
    id: str
    definition_id: str
    descriptor_map: list[Descriptor]
