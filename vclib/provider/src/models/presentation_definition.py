from typing import Literal

from pydantic import BaseModel

## To see how to create an instance of one of these models
## using optional fields, take a look at the link below
## https://www.geeksforgeeks.org/make-every-field-optional-with-pydantic-in-python/


class Filter(BaseModel):
    """Filters allows providers to further restrict the field they are
    asking for to avoid excessively invading the credential-owner's privacy
    Filters must specify a "type" or "format" that the field must adhere to.
    They can further specify what value they need
    e.g. date.today - dateofbirth > 18 years
    """

    type: (
        Literal["string", "number", "integer", "boolean", "array", "object"] | None
    ) = None
    format: Literal["date", "date-time", "email", "uri"] | None = None

    # String filters
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None  # regex match

    # Numeric filters
    # exclusive min/max denote whether the min or max should be included in the range
    # can be used on dates
    minimum: int | None = None
    exclusiveMinimum: bool | None = None  # noqa: N815
    maximum: int | None = None
    exclusiveMaximum: bool | None = None  # noqa: N815


class Field(BaseModel):
    """Each Field MUST contain a "path" property.\n
    Each Field MAY contain "id", "purpose", "name", "filter",
    and "optional" properties
    """

    path: list[str]
    id: str | None = None
    name: str | None = None
    filter: Filter | None = None
    optional: bool | None = False


class Constraint(BaseModel):
    """Each Constraint MAY have a "fields" property,
    and a "limit_disclosure" property"""

    fields: list[Field] | None = None
    limit_disclosure: Literal["required", "preferred"] | None = None


class InputDescriptor(BaseModel):
    """Each input_descriptor MUST contain an "id" and a "constraints" property.\n
    Each input_descriptor MAY contain "name", "purpose", and "format" properties"""

    id: str
    constraints: Constraint
    name: str | None = None
    purpose: str | None = None
    format: str | None = None


class PresentationDefinition(BaseModel):
    """presentation_definitions MUST have an "id", and an "input_descriptors"
    property.\n presentation_definitions MAY have "name", "purpose", and
    "format" properties.
    """

    id: str
    input_descriptors: list[InputDescriptor]
    name: str | None = None
    purpose: str | None = None
