from pydantic import BaseModel

class HelloWorldResponse(BaseModel):
    hello: str
    world: str
