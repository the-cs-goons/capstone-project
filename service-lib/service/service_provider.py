from fastapi import FastAPI, HTTPException
from typing import Literal

from .models.presentation_definition import PresentationDefinition, InputDescriptor, Constraint, Field
from .models.presentation_request import PresentationRequest

class ServiceProvider:

    def __init__(self):
        self.presentation_requests: dict[str, PresentationRequest]= {}

    def get_server(self) -> FastAPI:
        router = FastAPI()
        router.get('/request/{request_type}')(self.get_presentation_request)
        return router

    async def get_presentation_request(self, request_type:str) -> PresentationRequest:

        if request_type not in self.presentation_requests:
            raise HTTPException(status_code=404, detail='Request type not found')
        
        return self.presentation_requests[request_type]

    def create_presentation_request(self, 
            request_type: str,
            client_id: str, 
            presentation_definition: PresentationDefinition
            ) -> PresentationRequest:
        
        self.presentation_requests[request_type] = PresentationRequest(client_id=client_id, presentation_definition=presentation_definition)
        return self.presentation_requests[request_type]
    
    def create_presentation_definition(
            self, 
            id: str, 
            input_descriptors: list[InputDescriptor], 
            name: str = None, 
            purpose: str = None
            ) -> PresentationDefinition:
        
        presentation_definition = PresentationDefinition(
            id=id, 
            input_descriptors=input_descriptors)

        if name:
            presentation_definition.name = name
        if purpose:
            presentation_definition.purpose = purpose

        return presentation_definition
    
    def create_input_descriptor(
            self, 
            id: str, 
            constraints: list[Constraint], 
            name: str = None, 
            purpose: str = None, 
            format: str = None
            ) -> InputDescriptor:
        
        input_descriptor = InputDescriptor(id=id, constraints=constraints)

        if name:
            input_descriptor.name = name
        if purpose:
            input_descriptor.purpose = purpose

        # TODO: Implement format specification
        # if format:
        #     input_descriptor.format = format

        return input_descriptor
    
    def create_constraint(
            self, 
            fields: list[Field] = None, 
            limit_disclosure: Literal['required', 'preferred'] = None
            ) -> Constraint:
        
        constraint = Constraint()
        
        if fields is not None:
            constraint.fields = fields
        if limit_disclosure:
            constraint.limit_disclosure = limit_disclosure
        
        return constraint
    
    def create_field(
            self, 
            path: list[str], 
            id: str = None, 
            name: str = None, 
            filter: filter = None, 
            optional: bool = None
            ) -> Field:
        
        field = Field(path=path)

        if id:
            field.id = id
        if name:
            field.name = name
        if optional is not None:
            field.optional = optional

        return field
        
        





    