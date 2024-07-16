from pydantic import BaseModel


class CredentialRequestBody(BaseModel):
    credential_identifier: str


class DeferredCredentialRequestBody(BaseModel):
    transaction_id: str
