from pydantic import BaseModel
from typing import Any

class SchemaResponse(BaseModel):
    request_schema: dict[str, dict[str, Any]]