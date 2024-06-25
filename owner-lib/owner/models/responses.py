from typing import Any

from pydantic import BaseModel

class SchemaResponse(BaseModel):
    request_schema: dict[str, dict[str, Any]]
