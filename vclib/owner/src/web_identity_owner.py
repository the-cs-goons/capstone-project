from typing import override

from fastapi import FastAPI, HTTPException

from . import IdentityOwner
from .models.credentials import Credential
from .models.exceptions import (
    BadIssuerRequestException,
    CredentialIssuerException,
    IssuerTypeNotFoundException,
    IssuerURLNotFoundException,
)
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
            raise HTTPException(
                status_code=400, detail=f"Credential with ID {cred_id} not found."
            )
        return self.credentials[cred_id]

    def get_credentials(self) -> list[Credential]:
        """
        Gets all credentials

        ### Returns
        - `list[Credential]`: A list of credentials
        """
        return self.credentials.values()

    @override
    async def get_credential_request_schema(
        self, cred_type: str, issuer_url: str
    ) -> SchemaResponse:
        """
        Retrieves the required information needed to submit a request for some ID type
        from an issuer.

        ### Parameters
        - issuer_url(`str`): The issuer URL, as a URL Parameter
        - cred_type(`str`): The type of the credential schema request being asked for

        ### Returns
        - `SchemaResponse`: A list of credentials
        """
        try:
            req_schema = await super().get_credential_request_schema(
                cred_type, issuer_url
            )
            return SchemaResponse(request_schema=req_schema)
        except IssuerTypeNotFoundException:
            raise HTTPException(
                status_code=400, detail=f"Credential type {cred_type} not found."
            )
        except IssuerURLNotFoundException:
            raise HTTPException(status_code=404, detail="Issuer URL not found")
        except CredentialIssuerException:
            raise HTTPException(status_code=500, detail="Issuer API Error")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"{e}")

    @override
    async def apply_for_credential(
        self, issuer_url: str, cred_type: str, info: dict
    ) -> Credential:
        """
        Sends request for a new credential directly, then stores it

        ### Parameters
        - issuer_url(`str`): The issuer URL
        - cred_type(`str`): The type of the credential schema request being asked for
        - info(`dict`): The body of the request to forward on to the issuer, sent as
        JSON

        ### Returns
        - `Credential`: The new (pending) credential, if requested successfully
        """
        try:
            return super().apply_for_credential(cred_type, issuer_url, info)
        except IssuerTypeNotFoundException:
            raise HTTPException(
                status_code=400, detail=f"Credential type {cred_type} not found."
            )
        except IssuerURLNotFoundException:
            raise HTTPException(status_code=404, detail="Issuer URL not found")
        except BadIssuerRequestException:
            raise HTTPException(status_code=400, detail="Bad request to Issuer")
        except CredentialIssuerException:
            raise HTTPException(status_code=500, detail="Issuer API Error")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error: {e}")

    async def refresh_credential(self, cred_id) -> Credential:
        """
        Refreshes a specified credential and returns it

        ### Parameters
        - cred_id(`str`): The internal ID of the credential to refresh

        ### Returns
        - `Credential`: The updated credential, if it exists
        """
        if cred_id not in self.credentials.keys():
            raise HTTPException(
                status_code=400, detail=f"Credential with ID {cred_id} not found."
            )

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
        router.post("/request/{cred_type}")(self.apply_for_credential)
        router.get("/refresh/{cred_id}")(self.refresh_credential)
        router.get("/refresh/all")(self.refresh_all_pending_credentials)

        return router
