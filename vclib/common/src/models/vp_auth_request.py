from typing import Any, Literal

from pydantic import BaseModel


class Field(BaseModel):
    """Each Field **MAY** contain a "path" property.\n
    Each Field **MAY** contain "id", "purpose", "name", "filter",
    and "optional" properties
    """

    path: list[str]
    id: str | None = None
    name: str | None = None
    filter: dict | None = None
    optional: bool | None = False


class Constraints(BaseModel):
    """Each Constraint **MAY** have a "fields" property,
    and a "limit_disclosure" property"""

    fields: list[Field] | None = None
    limit_disclosure: Literal["required", "preferred"] | None = None


class InputDescriptor(BaseModel):
    """
    Each input_descriptor describes fields required from 1 type of
    credential.
    Each input_descriptor **MAY** contain an "id" and a "constraints"
    property.\n
    Each input_descriptor **MAY** contain "name", "purpose", and "format"
    properties\n"""

    id: str
    constraints: Constraints
    name: str | None = None
    purpose: str | None = None
    format: Any | None = None  # TODO ??


class PresentationDefinition(BaseModel):
    """presentation_definitions **MAY** have an "id", and an
    "input_descriptors" property.\n presentation_definitions **MAY**
    have "name", "purpose", and "format" properties.
    """

    id: str
    input_descriptors: list[InputDescriptor]
    name: str | None = None
    purpose: str | None = None


class AuthorizationRequestObject(BaseModel):
    client_id: str
    client_id_scheme: str = "did"
    client_metadata: dict
    presentation_definition: PresentationDefinition
    response_uri: str
    response_type: str = "vp_token"
    response_mode: str = "direct_post"
    nonce: str
    wallet_nonce: str | None = None
    state: str | None = None  # transaction id


class FieldRequest(BaseModel):
    field: Field
    input_descriptor_id: str
    approved: bool = False


class FieldSelectionObject(BaseModel):
    field_requests: list[FieldRequest]
