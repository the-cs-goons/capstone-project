from fastapi import FastAPI, HTTPException
import asyncio
import httpx
import os

from .models.verifiable_credential import VerifiableCredential

class IdentityOwner:
    def __init__(self):
        self.credentials: dict[str, VerifiableCredential] = {}
        pass

    def get_server(self) -> FastAPI:
        router = FastAPI()
        router.get("/")(self.hello)
        router.get('/yomama')(self.f)
        router.get("/pr")(self.get_presentation_request)
        return router

    async def hello(self):
        return {"Hello" : "World"}

    async def f(self):
        return {"message": "YO MAMA FAT"}

    async def get_presentation_request(
            self,
            url: str = f"http://service-lib:{os.getenv('CS3900_SERVICE_AGENT_PORT')}/request?request_type=example"
            ):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()  # Raises an exception if the request was unsuccessful
                data = response.json()
            return data
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=str(exc))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))