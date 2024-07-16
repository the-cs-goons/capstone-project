from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class PubKeyCredParam(BaseModel):
    alg: int
    type: str

class RelyingParty(BaseModel):
    name: str
    id: str

class PasskeyUser(BaseModel):
    id: str
    name: str
    displayName: str

class NewRegistrationResponse(BaseModel):
    challenge: str | bytes
    rp: RelyingParty
    pubKeyCredParams: List[PubKeyCredParam]
    timeout: int
    attestation: str
    excludeCredentials: List[Any]
    authenticatorSelection: Optional[Dict] = Field(default=None)

class ClientAttenstation(BaseModel):
    attestationObject: str
    clientDataJSON: str
    
class ParsedClientDataJSON(BaseModel):
    type: str
    challenge: str
    origin: str
    crossOrigin: Optional[str]

class VerifyRegistrationRequest(BaseModel):
    authenticatorAttachment: str
    id: str
    rawId: str
    response: ClientAttenstation
    transports: list[str]
    type: str

