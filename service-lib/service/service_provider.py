from typing import Literal, Optional

from fastapi import FastAPI, HTTPException

from .models.presentation_definition import PresentationDefinition
from .models.presentation_request_response import PresentationRequestResponse


class ServiceProvider:

    def __init__(
            self,
            presentation_definitions: dict[str, PresentationRequestResponse] = {}
            ):

        self.presentation_definitions = presentation_definitions
        self.client_id = 'exampleServiceProvider'

    def get_server(self) -> FastAPI:
        router = FastAPI()
        router.get('/request', response_model_exclude_none=True,
                   response_model=PresentationRequestResponse)(self.get_presentation_request)
        router.get('/definitions')(self.get_definitions)
        return router

    def add_presentation_definition(
            self,
            request_type: str,
            presentation_definition: PresentationDefinition
            ) -> None:

        self.presentation_definitions[request_type] = presentation_definition

    def get_definitions(self):
        return self.presentation_definitions

    async def get_presentation_request(
            self,
            request_type: str,
            client_id: Optional[str] = None
            ) -> PresentationRequestResponse:

        if request_type not in self.presentation_definitions:
            raise HTTPException(status_code=404, detail='Request type not found')

        if client_id is None:
            client_id = self.client_id

        dump = PresentationRequestResponse(
            client_id,
            self.presentation_definitions[request_type]
            )

        return dump
