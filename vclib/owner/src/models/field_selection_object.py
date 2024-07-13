from pydantic import BaseModel

from .presentation_definition import Filter

class FieldRequest(BaseModel):
    path: list[str]
    approved: bool
    id: str | None = None
    name: str | None = None
    filter: Filter | None = None
    optional: bool | None = False

class FieldSelectionObject(BaseModel):
    fields: list[FieldRequest]
