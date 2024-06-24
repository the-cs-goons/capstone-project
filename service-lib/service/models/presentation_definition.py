from .base_model_json import BaseModelJson
from typing import Literal
    

class Filter(BaseModelJson):
    '''Filters allows providers to further restrict the field they are 
    asking for to avoid excessively invading the credential-owner's privacy
    Filters must specify a "type" or "format" that the field must adhere to.
    They can further specify what value they need
    e.g. date.today - dateofbirth > 18 years'''
    type:Literal['string', 'number', 'integer', 'boolean', 'array', 'object'] = None
    format:Literal['date', 'date-time', 'email', 'uri'] = None
    
    # String filters
    minLength:int = None
    maxLength:int = None
    pattern:str = None # regex match

    # Numeric filters
    # exclusive min/max denote whether the min or max should be included in the range
    # can be used on dates
    minimum:int = None
    exclusiveMinimum:bool = None
    maximum:int = None
    exclusiveMaximum:bool = None


class Field(BaseModelJson):
    '''Each Field MUST contain a "path" property.\n
    Each Field MAY contain "id", "purpose", "name", "filter", 
    and "optional" properties'''
    path:list[str]
    id:str = None
    name:str = None
    filter:Filter = None
    optional:bool = False


class Constraint(BaseModelJson):
    '''Each Constraint MAY have a "fields" property, and a "limit_disclosure" property'''
    fields:list[Field] = None  
    limit_disclosure:Literal['required', 'preferred'] = None


class InputDescriptor(BaseModelJson):
    '''Each input_descriptor MUST contain an "id" and a "constraints" property.\n
    Each input_descriptor MAY contain "name", "purpose", and "format" properties'''

    id:str
    constraints:Constraint
    name:str = None
    purpose:str = None
    format:str = None

class PresentationDefinition(BaseModelJson):
    '''presentation_definitions MUST have an "id", and an "input_descriptors" property.\n
    presentation_definitions MAY have "name", "purpose", and "format" properties.'''

    id:str
    input_descriptors:list[InputDescriptor]
    name:str = None
    purpose:str = None