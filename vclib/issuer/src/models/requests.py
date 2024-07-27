from pydantic import BaseModel


class CredentialRequestBody(BaseModel):
    credential_identifier: str


class DeferredCredentialRequestBody(BaseModel):
    transaction_id: str


class AuthorizationRequestDetails(BaseModel):
    type: str
    credential_configuration_id: str
