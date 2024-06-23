from typing import Any

from fastapi import Body, FastAPI, Request
from pydantic import BaseModel

from .models.responses import RequestResponse, UpdateResponse


class CredentialIssuer:
    def __init__(self):
        self.ticket = 0
        self.link = 0
        self.mapping = {}

    async def recieve_credential_request(
        self, cred_type: str, information: Any = Body(None)
    ) -> RequestResponse:
        self.ticket += 1
        self.link += 1
        self.mapping[str(self.link)] = self.ticket

        self.get_request(self.ticket, cred_type, information)
        return RequestResponse(ticket=self.ticket, link=str(self.link))

    async def credential_status(self, token: str) -> UpdateResponse:
        ticket = self.mapping[token]

        status = self.get_status(ticket)
        return UpdateResponse(ticket=ticket, status=status)

    ###
    ### User-defined functions, designed to be overwritten
    ###
    def get_request(self, ticket: int, cred_type: str, information: object) -> Any:
        return

    def get_status(self, ticket: int) -> str:
        return "Pending"

    def get_server(self) -> FastAPI:
        router = FastAPI()
        router.post("/request/{cred_type}")(self.recieve_credential_request)
        router.get("/status/")(self.credential_status)
        return router
