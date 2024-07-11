from typing import Literal

from .base_model_json import BaseModelJson


class Filter(BaseModelJson):
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
    exclusive_minimum: bool | None = None
    maximum: int | None = None
    exclusive_maximum: bool | None = None

    def __init__(
        self,
        type: Literal["string", "number", "integer", "boolean", "array", "object"]
        | None = None,
        format: Literal["date", "date-time", "email", "uri"] | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
        pattern: str | None = None,
        minimum: int | None = None,
        exclusive_minimum: bool | None = None,
        maximum: int | None = None,
        exclusive_maximum: bool | None = None,
    ):
        super().__init__(
            type=type,
            format=format,
            min_length=min_length,
            max_length=max_length,
            pattern=pattern,
            minimum=minimum,
            exclusive_minimum=exclusive_minimum,
            maximum=maximum,
            exclusive_maximum=exclusive_maximum,
        )


class Field(BaseModelJson):
    """Each Field MUST contain a "path" property.\n
    Each Field MAY contain "id", "purpose", "name", "filter",
    and "optional" properties
    """

    path: list[str]
    id: str | None = None
    name: str | None = None
    filter: Filter | None = None
    optional: bool | None = False

    def __init__(
        self,
        path: list[str],
        id: str | None = None,
        name: str | None = None,
        filter: Filter | None = None,
        *,
        optional: bool | None = False,
    ):
        super().__init__(path=path, id=id, name=name, filter=filter, optional=optional)


class Constraint(BaseModelJson):
    """Each Constraint MAY have a "fields" property,
    and a "limit_disclosure" property
    """

    fields: list[Field] | None = None
    limit_disclosure: Literal["required", "preferred"] | None = None

    def __init__(
        self,
        fields: list[Field] | None = None,
        limit_disclosure: Literal["required", "preferred"] | None = None,
    ):
        super().__init__(fields=fields, limit_disclosure=limit_disclosure)


class InputDescriptor(BaseModelJson):
    """Each input_descriptor MUST contain an "id" and a "constraints" property.\n
    Each input_descriptor MAY contain "name", "purpose", and "format" properties
    """

    id: str
    constraints: Constraint
    name: str | None = None
    purpose: str | None = None
    format: str | None = None

    def __init__(
        self,
        id: str,
        constraints: Constraint,
        name: str | None = None,
        purpose: str | None = None,
        format: str | None = None,
    ):
        super().__init__(
            id=id, constraints=constraints, name=name, purpose=purpose, format=format
        )


class PresentationDefinition(BaseModelJson):
    """presentation_definitions MUST have an "id", and an "input_descriptors"
    property.\n presentation_definitions MAY have "name", "purpose", and
    "format" properties.
    """

    id: str
    input_descriptors: list[InputDescriptor]
    name: str | None = None
    purpose: str | None = None

    def __init__(
        self,
        id: str,
        input_descriptors: list[InputDescriptor],
        name: str | None = None,
        purpose: str | None = None,
    ):
        super().__init__(
            id=id, input_descriptors=input_descriptors, name=name, purpose=purpose
        )
