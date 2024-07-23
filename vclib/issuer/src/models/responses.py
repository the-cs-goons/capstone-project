from typing import Any

from pydantic import BaseModel


class FormResponse(BaseModel):
    form: dict[str, dict[str, Any] | list[dict[str, Any]]]


class StatusResponse(BaseModel):
    status: str
    cred_type: str | None
    information: dict[str, Any] | None
