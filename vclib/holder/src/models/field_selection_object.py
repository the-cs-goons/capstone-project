from pydantic import BaseModel

from vclib.common import vp_auth_request


class FieldRequest(BaseModel):
    field: vp_auth_request.Field
    input_descriptor_id: str
    approved: bool = False


class FieldSelectionObject(BaseModel):
    field_requests: list[FieldRequest]
