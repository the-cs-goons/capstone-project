from typing import Any, Literal, Self

from jsonschema.protocols import Validator
from pydantic import BaseModel, field_validator, model_validator


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

    @field_validator("filter")
    @classmethod
    def filter_is_valid_jsonschema(cls, v: dict | None) -> str:
        if v:
            Validator.check_schema(v)
        return v


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
    format: Any | None = None


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
    presentation_definition: PresentationDefinition | None = None
    presentation_definition_uri: str | None = None
    response_uri: str
    response_type: str = "vp_token"
    response_mode: str = "direct_post"
    nonce: str
    wallet_nonce: str | None = None
    state: str | None = None  # transaction id

    @model_validator(mode="after")
    def verify_pd_inputs_exclusive(self) -> Self:
        if (self.presentation_definition and self.presentation_definition_uri) or (
            not self.presentation_definition and not self.presentation_definition_uri
        ):
            raise ValueError(
                "Expected one of `presentation_definition` or `presentation_definition_uri` but not both"
            )  # noqa: E501
