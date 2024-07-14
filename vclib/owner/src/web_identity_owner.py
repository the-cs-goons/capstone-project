from typing import override

from fastapi import FastAPI, HTTPException

from . import IdentityOwner
from .models.credentials import Credential
from .models.exceptions import (
    BadIssuerRequestError,
    CredentialIssuerError,
    IssuerTypeNotFoundError,
    IssuerURLNotFoundError,
)
from .models.responses import SchemaResponse


class WebIdentityOwner(IdentityOwner):
    def __init__(self, storage_key, *args, dev_mode=False):
        super().__init__(storage_key, dev_mode=dev_mode)

    def get_credential(self, cred_id) -> Credential:
        """Gets a credential by ID, if one exists

        ### Parameters
        - cred_id(`str`): The ID of the credential, as kept by the owner

        ### Returns
        - `Credential`: The requested credential, if it exists
        """
        if cred_id not in self.credentials:
            raise HTTPException(
                status_code=400, detail=f"Credential with ID {cred_id} not found."
            )
        return self.credentials[cred_id]

    def get_credentials(self) -> list[Credential]:
        """Gets all credentials

        ### Returns
        - `list[Credential]`: A list of credentials
        """
        return self.credentials.values()

    async def refresh_all_pending_credentials(self):
        """Refreshes all PENDING credentials

        ### Returns
        - `list[Credential]`: A list of all saved credentials
        """
        await self.poll_all_pending_credentials()
        return self.credentials.values()

    def get_server(self) -> FastAPI:
        router = FastAPI()

        router.get("/credential/{cred_id}")(self.get_credential)
        router.get("/credentials")(self.get_credentials)
        router.get("/refresh/{cred_id}")(self.refresh_credential)
        router.get("/refresh/all")(self.refresh_all_pending_credentials)

        router.get("/offer")(self.get_credential_offer)
        router.post("/offer")(self.get_offer_oauth_url)

        return router
