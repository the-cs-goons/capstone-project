from typing import override

from fastapi import FastAPI, HTTPException
from requests import Response, Session

from . import IdentityOwner
from .models.credentials import Credential
from .models.responses import SchemaResponse


class WebIdentityOwner(IdentityOwner):

    def __init__(self, storage_key, dev_mode=False):
        super().__init__(storage_key, dev_mode=dev_mode)

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
    
    def get_credentials(self) -> list[Credential]:
        """
        Gets all credentials

        ### Returns
        - `list[Credential]`: A list of credentials
        """
        return self.credentials.values()
    
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
        
    async def request_credential(self, cred_type: str, issuer_url: str, info: dict) -> Credential:
        """
        Sends request for a new credential directly, then stores it

        ### Parameters
        - issuer_url(`str`): The issuer URL
        - cred_type(`str`): The type of the credential schema request being asked for
        - info(`dict`): The body of the request to forward on to the issuer, sent as JSON

        ### Returns
        - `Credential`: The new (pending) credential, if requested successfully
        """
        #TODO: Implement error handling
        return self.apply_for_credential(cred_type, issuer_url, info)

    async def refresh_credential(self, cred_id) -> Credential:
        """
        Refreshes a specified credential and returns it

        ### Parameters
        - cred_id(`str`): The internal ID of the credential to refresh 
        
        ### Returns
        - `Credential`: The updated credential, if it exists
        """
        if cred_id not in self.credentials.keys():
            raise HTTPException(status_code=400, 
                                detail=f"Credential with ID {cred_id} not found.")
        
        await self.poll_credential_status(cred_id)
        return self.credentials[cred_id]
    
    async def refresh_all_pending_credentials(self):
        """
        Refreshes all PENDING credentials
        
        ### Returns
        - `list[Credential]`: A list of all saved credentials
        """
        await self.poll_all_pending_credentials()
        return self.credentials.values()

    def get_server(self) -> FastAPI:
        router = FastAPI()

        router.get("/credential/{cred_id}")(self.get_credential)
        router.get("/credentials")(self.get_credentials)
        router.get("/request/{cred_type}")(self.get_credential_request_schema)
        router.post("/request/{type}")(self.apply_for_credential)
        router.get("/refresh/{cred_id}")(self.refresh_credential)
        router.get("/refresh/all")(self.refresh_all_pending_credentials)

        return router