from fastapi import FastAPI

from .models.hello_world import HelloWorldResponse

class CredentialIssuer:
    async def hello_world(self) -> HelloWorldResponse:
        return HelloWorldResponse(hello="Hello", world="World")

    def get_server(self) -> FastAPI:
        router = FastAPI()
        router.get("/")(self.hello_world)
        return router
