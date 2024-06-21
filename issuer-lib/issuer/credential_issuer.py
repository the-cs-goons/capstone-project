from typing import Any
from fastapi import FastAPI
from pydantic import BaseModel

from .models.responses import RequestResponse, UpdateResponse


class CredentialIssuer:
    async def landing(self):
        return {"message": "Hello World"}

    async def recieve_credential_request(self, cred_type: str) -> Any:
        return {"ticket": 1,
                "link": cred_type}

    async def credential_status(self, token: str) -> Any:
        return UpdateResponse(ticket=1, status=token)

    def credential_validation(self, information: object) -> bool:
        pass

    def get_server(self) -> FastAPI:
        router = FastAPI()
        router.get("/request/{cred_type}", response_model=RequestResponse)(self.recieve_credential_request)
        router.get("/status/", response_model=UpdateResponse)(self.credential_status)
        router.get("/")(self.landing)
        return router
