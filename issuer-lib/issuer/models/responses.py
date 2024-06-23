from typing import Any

from pydantic import BaseModel


class OptionsResponse(BaseModel):
    options: dict[str, dict[str, dict[str, Any]]]


class RequestResponse(BaseModel):
    ticket: int
    link: str


# In theory used by the frontend to display status page
class UpdateResponse(BaseModel):
    ticket: int
    status: Any
