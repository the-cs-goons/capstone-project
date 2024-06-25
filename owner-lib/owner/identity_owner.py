from fastapi import FastAPI
import httpx

class IdentityOwner:
    def __init__(self):
        # self.credentials: dict[str, VerifiableCredential] = {}
        pass

    def get_server(self) -> FastAPI:
        router = FastAPI()
        router.get("/")(self.hello)
        router.get('/yomama')(self.f)
        router.get("/pr")(self.temp_get_thingo)
        return router

    async def hello(self):
        return {"Hello" : "World"}

    async def f(self):
        return {"message": "YO MAMA FAT"}

    async def temp_get_thingo(self, url):
        client = httpx.AsyncClient()
        response = await client.get(url)
        return {'url': url}