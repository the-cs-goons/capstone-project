from typing import Any, override

from fastapi import FastAPI, HTTPException
from requests import Response, Session

from . import IdentityOwner
from .models.credentials import Credential
from .models.responses import SchemaResponse


class WebIdentityOwner(IdentityOwner):

    router = FastAPI()

    def __init__(self, storage_key, dev_mode=False):
        super().__init__(storage_key, dev_mode=dev_mode)

    @router.get("/credential/{cred_id}")
    def get_credential(self, cred_id) -> Credential:
        """
        Gets a credential by ID, if one exists

        ### Parameters
        - cred_id(`str`): The ID of the credential, as kept by the owner

        ### Returns
        - `Credential`: The requested credential, if it exists
        """
        if cred_id not in self.credentials.keys():
            raise HTTPException(status_code=400, 
                                detail=f"Credential with ID {cred_id} not found.")
        return self.credentials[id]
    
    @router.get("/credentials")
    def get_credentials(self) -> list[Credential]:
        """
        Gets all credentials

        ### Returns
        - `list[Credential]`: A list of credentials
        """
        return self.credentials.values()
    
    @router.get("/request/{cred_type}")
    @override
    async def get_credential_request_schema(self, 
                                            cred_type: str, 
                                            issuer_url: str) -> SchemaResponse:
        """
        Retrieves the required information needed to submit a request for some ID type
        from an issuer.

        ### Parameters
        - issuer_url(`str`): The issuer URL, as a URL Parameter
        - cred_type(`str`): The type of the credential schema request being asked for

        ### Returns
        - `SchemaResponse`: A list of credentials
        """
        with Session() as s:
            response: Response = await s.get(f"{issuer_url}/credentials")
            if not response.ok:
                raise HTTPException(status_code=response.status_code, 
                                detail=f"Error: {response.reason}")
            
            body: dict = response.json()
            if "options" not in body.keys():
                raise HTTPException(status_code=500, 
                                detail="Issuer API Error: Incorrect API response")
            
            options: dict = body["options"]
            if type not in options.keys():
                raise HTTPException(status_code=400, 
                                detail=f"Error: Credential type {cred_type} not found")
            
            return SchemaResponse(request_schema=options[cred_type])
        
    @router.post("/request/{type}")
    async def request_credential(self, cred_type: str, issuer_url: str, info: dict):
        """
        Sends request for a new credential directly, then stores it

        ### Parameters
        - issuer_url(`str`): The issuer URL
        - cred_type(`str`): The type of the credential schema request being asked for
        - info(`dict`): The body of the request to forward on to the issuer, sent as JSON
        """
        #TODO: Implement error handling
        self.apply_for_credential(cred_type, issuer_url, info)

    def get_server(self) -> FastAPI:
        return self.router