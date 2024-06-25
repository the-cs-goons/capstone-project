from typing import Literal, Optional

from pydantic import BaseModel, Field

# for specification see https://www.w3.org/TR/vc-data-model-2.0/#status

class VerifiableCredential(BaseModel):

    type: list[str]
    credentialSubject: dict[str, dict | str]
    issuer: str | dict[str, dict | str]
    context: list[str] #= Field(serialization_alias='@context')
    id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    validFrom: Optional[str] = None
    validUntil: Optional[str] = None
    credentialStatus: Optional[str] = None

    def __init__(
            self,
            type: list[str],
            credentialSubject: dict, #dict[str, dict | str],
            issuer: str | dict[str, dict | str],
            context: list[str],
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
    verifiableCredential: Optional[list[dict[str, str | dict]]] = None
    id: Optional[str] = None
    holder: Optional[str] = None

    def __init__(
            self,
            type: list[str] | str,
            verifiableCredential: Optional[list[dict[str, dict | str]]] = None,
            id: Optional[str] = None,
            holder: Optional[str] = None
            ):
        super().__init__(
            type = type,
            verifiableCredential = verifiableCredential,
            id = id,
            holder = holder
        )

class ParsedField(BaseModel):
    name: str
    condition: str
    paths: list[str]
    optional: bool
    original_field: str