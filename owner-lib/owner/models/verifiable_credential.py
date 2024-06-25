from pydantic import BaseModel, Field
from typing import Optional, Literal

# for specification see https://www.w3.org/TR/vc-data-model-2.0/#status

class VerifiableCredential(BaseModel):

    context: list[str] = Field(alias='@context')
    type: list[str]
    credentialSubject: dict[str, any] | list[dict[str, any]]
    issuer: str | dict[str, any] # has to contain a URL or DID or JWK identifying the issuer
    id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    validFrom: Optional[str] = None # must be a date-time-stamp
    validUntil: Optional[str] = None # can be found https://www.w3.org/TR/xmlschema11-2/#dateTime
    credentialStatus: Optional[str] = None

    def __init__(
            self,
            type: list[str],
            credentialSubject: dict[str, any] | list[dict[str, any]],
            issuer: str | dict[str, any],
            context: list[str] = Field(alias='@context'),
            id: Optional[str] = None,
            name: Optional[str] = None,
            description: Optional[str] = None,
            validFrom: Optional[str] = None,
            validUntil: Optional[str] = None,
            credentialStatus: Optional[str] = None
            ):
        super().__init__(
            context = context,
            type = type,
            credentialSubject = credentialSubject,
            issuer = issuer,
            id = id,
            name = name,
            description = description,
            validFrom = validFrom,
            validUntil = validUntil,
            credentialStatus = credentialStatus
        )

class VerifiablePresentation(BaseModel):
    type: list[str] | str
    verifiableCredential: Optional[list[dict[str, any]]] = None
    id: Optional[str] = None
    holder: Optional[str] = None

    def __init__(
            self,
            type: list[str] | str,
            verifiableCredential: Optional[list[dict[str, any]]] = None,
            id: Optional[str] = None,
            holder: Optional[str] = None
            ):
        super().__init__(
            type = type,
            verifiableCredential = verifiableCredential,
            id = id,
            holder = holder
        )