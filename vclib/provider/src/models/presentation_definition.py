from typing import Literal, Optional

from .base_model_json import BaseModelJson


class Filter(BaseModelJson):
    """Filters allows providers to further restrict the field they are
    asking for to avoid excessively invading the credential-owner's privacy
    Filters must specify a "type" or "format" that the field must adhere to.
    They can further specify what value they need
    e.g. date.today - dateofbirth > 18 years"""

    type: Optional[
        Literal["string", "number", "integer", "boolean", "array", "object"]
    ] = None
    format: Optional[Literal["date", "date-time", "email", "uri"]] = None

    # String filters
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None  # regex match

    # Numeric filters
    # exclusive min/max denote whether the min or max should be included in the range
    # can be used on dates
    minimum: Optional[int] = None
    exclusive_minimum: Optional[bool] = None
    maximum: Optional[int] = None
    exclusive_maximum: Optional[bool] = None

    def __init__(
        self,
        type: Optional[
            Literal["string", "number", "integer", "boolean", "array", "object"]
        ] = None,
        format: Optional[Literal["date", "date-time", "email", "uri"]] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        minimum: Optional[int] = None,
        exclusive_minimum: Optional[bool] = None,
        maximum: Optional[int] = None,
        exclusive_maximum: Optional[bool] = None,
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
    and "optional" properties"""

    path: list[str]
    id: Optional[str] = None
    name: Optional[str] = None
    filter: Optional[Filter] = None
    optional: Optional[bool] = False

    def __init__(
        self,
        path: list[str],
        id: Optional[str] = None,
        name: Optional[str] = None,
        filter: Optional[Filter] = None,
        optional: Optional[bool] = False,
    ):
        super().__init__(path=path, id=id, name=name, filter=filter, optional=optional)


class Constraint(BaseModelJson):
    """Each Constraint MAY have a "fields" property,
    and a "limit_disclosure" property"""

    fields: Optional[list[Field]] = None
    limit_disclosure: Optional[Literal["required", "preferred"]] = None

    def __init__(
        self,
        fields: Optional[list[Field]] = None,
        limit_disclosure: Optional[Literal["required", "preferred"]] = None,
    ):
        super().__init__(fields=fields, limit_disclosure=limit_disclosure)


class InputDescriptor(BaseModelJson):
    """Each input_descriptor MUST contain an "id" and a "constraints" property.\n
    Each input_descriptor MAY contain "name", "purpose", and "format" properties"""

    id: str
    constraints: Constraint
    name: Optional[str] = None
    purpose: Optional[str] = None
    format: Optional[str] = None

    def __init__(
        self,
        id: str,
        constraints: Constraint,
        name: Optional[str] = None,
        purpose: Optional[str] = None,
        format: Optional[str] = None,
    ):
        super().__init__(
            id=id, constraints=constraints, name=name, purpose=purpose, format=format
        )


class PresentationDefinition(BaseModelJson):
    """presentation_definitions MUST have an "id", and an "input_descriptors"
    property.\n presentation_definitions MAY have "name", "purpose", and
    "format" properties."""

    id: str
    input_descriptors: list[InputDescriptor]
    name: Optional[str] = None
    purpose: Optional[str] = None

    def __init__(
        self,
        id: str,
        input_descriptors: list[InputDescriptor],
        name: Optional[str] = None,
        purpose: Optional[str] = None,
    ):
        super().__init__(
            id=id, input_descriptors=input_descriptors, name=name, purpose=purpose
        )
