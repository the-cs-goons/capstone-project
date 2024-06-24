from typing import Any, override
from . import IdentityOwner
from .models.credentials import Credential
from .models.responses import SchemaResponse
from fastapi import FastAPI, HTTPException
from requests import Session, Response

class WebIdentityOwner(IdentityOwner):

    router = FastAPI()

    def __init__(self, storage_key, dev_mode=False):
        super().__init__(storage_key, dev_mode=dev_mode)

    @router.get("/credential/{cred_id}")
    def get_credential(self, cred_id) -> Credential:
        """
        Gets a credential by ID, if one exists
        """
        if cred_id not in self.credentials.keys():
            raise HTTPException(status_code=400, 
                                detail=f"Credential with ID {cred_id} not found.")
        return self.credentials[id]
    
    @router.get("/credentials")
    def get_credentials(self) -> list[Credential]:
        return self.credentials.values()
    
    @router.get("/request/{cred_type}")
    @override
    async def get_credential_request_schema(self, cred_type: str, issuer_url: str) -> SchemaResponse:
        """
        Retrieves the required information needed to submit a request for some ID type
        from an issuer.

        ### Parameters
        - issuer_url(`str`): The issuer URL, as a URL Parameter
        - cred_type(`str`): The type of the credential schema request being asked for
        """
        with Session() as s:
            response: Response = await s.get(f"{issuer_url}/credentials")
            if not response.ok:
                raise HTTPException(status_code=response.status_code, 
                                detail=f"Error: {response.reason}")
            
            body: dict = response.json()
            if "options" not in body.keys():
                raise HTTPException(status_code=500, 
                                detail=f"Issuer API Error: Incorrect API response")
            
            options: dict = body["options"]
            if type not in options.keys():
                raise HTTPException(status_code=400, 
                                detail=f"Error: Credential type {type} not found")
            
            return SchemaResponse(request_schema=options[type])
        
    @router.post("/request/{type}")
    async def request_credential(self, cred_type: str, issuer_url: str, info: dict):
        self.apply_for_credential(cred_type, issuer_url, info)

    def get_server(self) -> FastAPI:
        return self.router