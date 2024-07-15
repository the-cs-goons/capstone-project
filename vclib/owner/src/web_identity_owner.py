from typing import Any
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse

from .identity_owner import IdentityOwner
from .models.credentials import Credential, DeferredCredential
from .models.request_body import CredentialSelection


class WebIdentityOwner(IdentityOwner):
    """
    IdentityOwner that implements a HTTP API interface.
    """

    def __init__(
        self,
        redirect_uris: list[str],
        cred_offer_endpoint: str,
        *,
        oauth_client_options: dict[str, Any] = {},
        dev_mode: bool = False,
    ):
        """
        Create a new Identity Owner

        ### Parameters
        - redirect_uris(`list[str]`): A list of redirect URIs to register with issuers.
        It is the caller's responsibility to ensure these match with the API.
        - cred_offer_endpoint(`str`): The credential offer URI, e.g.
        "https://example.com/offer". The routes for receiving credential offers, and
        redirecting the user to authorise based on a credential offer, are dynamically
        determined by parsing this URI with `urllib.parse.urlparse` and retrieving the
        path.
        - oauth_client_options(`dict = {}`): A dictionary containing optional overrides
        for the wallet's OAuth client info, used in registration of new clients. See
        `WalletClientMetadata` for accepted fields.
        Note that even if keys `"redirect_uris"` or `"credential_offer_endpoint"` are
        provided, they will be overwritten by their respective positional arguments.
        """

        # Referenced in `get_server`
        offer_path = urlparse(cred_offer_endpoint).path
        self._credential_offer_endpoint = offer_path

        oauth_client_info = oauth_client_options
        oauth_client_info["redirect_uris"] = redirect_uris
        oauth_client_info["credential_offer_endpoint"] = cred_offer_endpoint
        super().__init__(oauth_client_info, dev_mode=dev_mode)

    async def get_credential(
        self, cred_id: str, refresh: int = 1
    ) -> Credential | DeferredCredential:
        """
        Gets a credential by ID, if one exists

        ### Parameters
        - cred_id(`str`): The ID of the credential, as kept by the owner
        - refresh(`int = 1`): Whether or not to refresh the credential, if currently
        deferred. Expressed as an int for the purposes of making it easier to pass
        in the request URL as a query parameter. 0 is `False`, any other number is
        interpreted as `True` (default).

        ### Returns
        - `Credential | DeferredCredential`: The requested credential, if it exists.
        """
        r = refresh != 0
        try:
            return await super()._get_credential(cred_id, refresh=r)
        except Exception:
            raise HTTPException(
                status_code=400, detail=f"Credential with ID {cred_id} not found."
            )

    async def get_credentials(self) -> list[Credential | DeferredCredential]:
        """
        Gets all credentials
        TODO: Adjust when storage implemented

        ### Returns
        - `list[Credential | DeferredCredential]`: A list of credentials
        """
        return self.credentials.values()

    async def request_authorization(
        self, credential_selection: CredentialSelection
    ) -> RedirectResponse:
        """
        Redirects the user to authorize.
        """
        redirect_url: str
        if credential_selection.credential_offer:
            if credential_selection.issuer_uri:
                raise HTTPException(
                    status_code=400,
                    detail="Can't provide both issuer_uri and credential_offer.",
                )
            redirect_url = await self.get_auth_redirect_from_offer(
                credential_selection.credential_configuration_id,
                credential_selection.credential_offer,
            )
        elif credential_selection.issuer_uri:
            redirect_url = await self.get_auth_redirect(
                credential_selection.credential_configuration_id,
                credential_selection.issuer_uri,
            )

        else:
            raise HTTPException(
                status_code=400,
                detail="Please provide either issuer_uri or credential_offer.",
            )
        return RedirectResponse(redirect_url, status_code=302)

    def get_server(self) -> FastAPI:
        """
        Returns a FastAPI App instance.
        CAN be overriden to replace or add to the API interface.
        """
        router = FastAPI()

        router.get("/credentials/{cred_id}")(self.get_credential)
        router.get("/credentials")(self.get_credentials)
        router.get("/refresh/{cred_id}")(self.refresh_credential)
        router.get("/refresh")(self.refresh_all_deferred_credentials)

        # Issuance (offer) endpoints
        router.get(self._credential_offer_endpoint)(self.get_credential_offer)
        router.post(self._credential_offer_endpoint)(self.request_authorization)
        # Might change this later from /add to something else
        router.get("/add")(self.get_access_token_and_credentials_from_callback)

        return router
