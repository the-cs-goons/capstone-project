from pydantic import BaseModel


class Presentation(BaseModel):
    credential_tokens: list[str]
