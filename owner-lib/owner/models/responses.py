from pydantic import BaseModel
from typing import Any

class SchemaResponse(BaseModel):
    schema: dict[str, dict[str, Any]]


class RequestResponse(BaseModel):
    ticket: int
    link: str


# In theory used by the frontend to display status page
class UpdateResponse(BaseModel):
    ticket: int
    status: Any