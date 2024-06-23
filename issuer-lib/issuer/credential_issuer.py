from typing import Any

from fastapi import Body, FastAPI, HTTPException

from .models.responses import OptionsResponse, RequestResponse, UpdateResponse


class CredentialIssuer:
    def __init__(self):
        self.credentials = {
            "default": {
                "string": {
                    "type": "string",
                    "optional": False,
                },
                "number": {
                    "type": "number",
                    "optional": False,
                },
                "boolean": {
                    "type": "boolean",
                    "optional": False,
                },
                "optional": {
                    "type": "string",
                    "optional": True,
                },
            },
        }
        self.ticket = 0
        self.link = 0
        self.mapping = {}

    async def get_credential_options(self) -> OptionsResponse:
        return OptionsResponse(options=self.credentials)

    def check_input_typing(self, cred_type: str, information: dict) -> bool:
        for field, value in information.items():
            if value is None:
                if not self.credentials[cred_type][field]["optional"]:
                    return False
            else:
                match self.credentials[cred_type][field]["type"]:
                    case "string":
                        if not isinstance(value, str):
                            return False
                    case "number":
                        if (not (isinstance(value, int) 
                                 and not isinstance(value, bool)) 
                            and not isinstance(value, float)):
                            return False
                    case "boolean":
                        if not isinstance(value, bool):
                            return False
                    # case ["array[", typ, "]"]:
                    #     pass
                    # case ["optional[", typ, "]"]:
                    #     pass
                    # case "object":
                    #     pass
        return True

    async def recieve_credential_request(
        self, cred_type: str, information: dict = Body(None)
    ) -> RequestResponse:
        cred_type = cred_type.lower()
        if cred_type not in self.credentials:
            raise HTTPException(status_code=404, detail="Item not found")

        if (not information.keys() == self.credentials[cred_type].keys() 
                or not self.check_input_typing(cred_type, information)):
            raise HTTPException(status_code=400, detail="Malformed request")

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
        router.get("/credentials/")(self.get_credential_options)
        router.post("/request/{cred_type}")(self.recieve_credential_request)
        router.get("/status/")(self.credential_status)
        return router
