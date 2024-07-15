from pydantic import BaseModel

from .presentation_definition import Field


class FieldRequest(BaseModel):
    field: Field
    input_descriptor_id: str
    approved: bool = False


class FieldSelectionObject(BaseModel):
    field_requests: list[FieldRequest]
