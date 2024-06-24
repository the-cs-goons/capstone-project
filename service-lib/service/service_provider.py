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

    def get_server(self) -> FastAPI:
        router = FastAPI()
        router.get('/request/{request_type}')(self.get_presentation_request)
        return router

    def add_presentation_definition(
            self,
            request_type: str,
            presentation_definition: PresentationDefinition
            ) -> None:

        self.presentation_definitions[request_type] = presentation_definition

    async def get_presentation_request(
            self,
            request_type: str,
            client_id: str
            ) -> PresentationRequestResponse:

        if request_type not in self.presentation_definitions:
            raise HTTPException(status_code=404, detail='Request type not found')

        return PresentationRequestResponse(
            client_id,
            self.presentation_definitions[request_type])
