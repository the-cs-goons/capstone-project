from base64 import b64decode, b64encode
from datetime import datetime
from json import dumps, loads
from typing import Any, Tuple, Dict
from urllib.parse import urlencode

from requests import Response, Session
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import WebApplicationClient

from .models.client_metadata import RegisteredClientMetadata, WalletClientMetadata
from .models.credential_offer import CredentialOffer
from .models.credentials import Credential, DeferredCredential
from .models.issuer_metadata import AuthorizationMetadata, IssuerMetadata
from .models.oauth import OAuthTokenResponse
from vclib.owner.src.models import issuer_metadata


class IdentityOwner:
    """Base Identity Owner class

    ### Attributes
    - credentials(`dict[str, Credential]`): A dictionary of credentials, mapped by
    their IDs
    - dev_mode(`bool`): Flag for running in development environment (currently
    unused)
    - storage_key(`str`): Key for encrypting stored credentials (currently unused)
    """

    # TODO: Enforce https

    def __init__(self,
                 oauth_client_metadata: dict,
                 *,
                 dev_mode=False,):
        """
        Creates a new Identity Owner

        ### Parameters

        """
        self.client_metadata = WalletClientMetadata.model_validate(
            oauth_client_metadata
            )

        self.oauth_clients: Dict[str, RegisteredClientMetadata] = {}
        self.issuer_metadata_store: Dict[str, IssuerMetadata] = {}
        self.auth_metadata_store: Dict[str, AuthorizationMetadata] = {}

        
        self.dev_mode = dev_mode
        self.credentials: dict[str, Credential] = {}
        for cred in self.load_all_credentials_from_storage():
            self.credentials[cred.id] = cred

    def serialise_and_encrypt(self, cred: Credential):
        """# NOT YET IMPLEMENTED IN FULL
        TODO: Implement encryption for safe storage using key attr
        Converts the Credential object into some string value that can be stored
        and encrypts it

        ### Parameters
        - cred(`Credential`): Credential to serialise and encrypt

        ### Returns
        - `bytes`: A base64 encoded Credential
        """
        return b64encode(cred.model_dump_json().encode())

    def load_from_serial(self, dump: str | bytes | bytearray) -> Credential:
        """# NOT YET IMPLEMENTED IN FULL
        TODO: Implement decryption in accordance with implementation in
        `serialise_and_encrypt`

        Static method that loads a credential from encrypted & serialised string

        ### Parameters
        - dump(`str` | `bytes` | `bytearray`): the serialised credential

        ### Returns
        - `Credential`: A Credential object
        """
        return Credential.model_validate(loads(b64decode(dump)))

    async def get_credential_offer(self,
                                   credential_offer_uri: str | None,
                                   credential_offer: str | None
                                   ) -> CredentialOffer:
        """
        Parses a credential offer.

        ### Parameters
        - credential_offer_uri(`str | None`): A URL linking to a credential offer
        object. If provided, `credential_offer` MUST be none.
        - credential_offer(`str`): A URL-encoded credential offer object. If given,
        `credential_offer_uri` MUST be none.

        ### Returns
        `CredentialOffer`: The credential offer.
        """
        # Interpret the credential offer
        if credential_offer and credential_offer_uri:
            raise Exception(
                "Can't accept both credential_offer and credential_offer_uri")

        if not credential_offer and not credential_offer_uri:
            raise Exception(
                "Neither credential_offer nor credential_offer_uri were provided")

        offer: CredentialOffer
        if credential_offer_uri:
            # Create a credential offer obj from the URI
            with Session() as s:
                res: Response = s.get(credential_offer_uri)
                res.raise_for_status()
                offer = CredentialOffer.model_validate_json(res.content)
        else:
            offer = CredentialOffer.model_validate_json(credential_offer)

        return offer
    
    async def get_credential_offer_metadata(self, 
                                            offer: CredentialOffer, 
                                            force_refresh: bool = False
                                            ) -> Tuple[
                                                IssuerMetadata, 
                                                AuthorizationMetadata
                                                ]:
        """
        Retrieves issuer metadata & authorization metadata, given a credential offer.
        Validates that the issuer_uri in the offer matches what's given in the
        credential offer.

        ### Parameters:
        - offer(`CredentialOffer`): The credential offer.
        - force_refresh(`bool = False`): If `True`, will force the `IdentityOwner`
         to request from the issuer's metadata endpoints. Otherwise, it will
         attempt to load the metadata from memory, and only request it if it cannot
         be found.

        ### Returns:
        - Tuple[`IssuerMetadata`, `AuthorizationMetadata`]: A tuple containing two
        elements: The issuer's metadata, & the issuer's authorization server metadata.
        """
        # Retrieve Metadata
        issuer_uri = offer.credential_issuer
        issuer_metadata: IssuerMetadata | None = None
        auth_metadata: AuthorizationMetadata | None = None

        if not force_refresh:
            issuer_metadata = self.issuer_metadata_store.get(issuer_uri, None)
            auth_metadata = self.auth_metadata_store.get(issuer_uri, None)

        # If not already retrieved, get issuer metadata
        if not issuer_metadata: 
            issuer_metadata = IssuerMetadata.model_validate(
                await self.get_issuer_metadata(issuer_uri))
            # Check that the metadata matches
            if issuer_uri != issuer_metadata.credential_issuer:
                raise Exception(
                    "Bad Issuer Metadata")
            # Store it for easier access later if valid
            self.issuer_metadata_store[issuer_uri] = issuer_metadata

        # If not already retrieved, get authorization metadata
        if not auth_metadata:
            auth_metadata = AuthorizationMetadata.model_validate(
                await self.get_issuer_metadata(
                    issuer_uri,
                    path="/.well-known/oauth-authorization-server"))
            # Check that the metadata matches
            if issuer_uri != auth_metadata.issuer:
                raise Exception(
                    "Bad Issuer Authorization Metadata")
            # Store it for easier access later if valid
            self.auth_metadata_store[issuer_uri] = auth_metadata
        
        return (issuer_metadata, auth_metadata)

    async def get_offer_oauth_url(self,
                                  credential_offer_uri: str | None,
                                  credential_offer: str | None,
                                  credential_configuration_id: str):
        """
        Takes a user's selection of credential configurations for a previously
        received credential offer, and returns an OAuth2 authorization URL.

        OAuth2 Client parameters (WILL BE) stored in some persistent fashion.
        This is to enable requests for deferred credentials.

        TODO: Docs
        """

        offer = await self.get_credential_offer(
            credential_offer=credential_offer,
            credential_offer_uri=credential_offer_uri
            )

        issuer_metadata: IssuerMetadata
        auth_metadata: AuthorizationMetadata
        (issuer_metadata, auth_metadata) = await self.get_credential_offer_metadata(offer)

        if credential_configuration_id not in offer.credential_configuration_ids:
            raise Exception("Not a valid credential_configuration_id")

        # Register as OAuth client
        wallet_metadata = await self.register_client(
            auth_metadata.registration_endpoint, issuer_metadata.credential_issuer
            )
        
        # Create an OAuth2 session.
        # Use as context so the session closes at the end of the function call
        with OAuth2Session(
            client_id=wallet_metadata.client_id, 
            client=WebApplicationClient,
            redirect_uri=wallet_metadata.redirect_uris[0]) as oauth2_client:

        # create authorization_details parameter (url encoded JSON)
            auth_details = {
                'authorization_details': urlencode(dumps(
                    [
                        {
                            'type': 'openid_credential',
                            'credential_configuration_id': credential_configuration_id
                            }
                        ]
                    ))
                }

            # Store OAuth2 client details
            (
                authorization_url, 
                state
            ) = oauth2_client.authorization_url(
                auth_metadata.authorization_endpoint, 
                **auth_details
                )

            self.oauth_clients[state] = wallet_metadata
            return authorization_url


    async def get_access_token_and_credentials_from_callback(self, 
                        code: str, 
                        state: str,
                        ):
        """
        Gets OAuth2 Access token
        """
        oauth_client_info = self.oauth_clients.get(state, None)
        if not oauth_client_info:
            raise Exception("Bad Authorization Redirect")
        
        # Don't save any new credentials until everything is done.
        # Should avoid malformed credentials this way.
        new_credentials = []

        issuer_uri = oauth_client_info.issuer_uri

        with OAuth2Session(
            client_id=oauth_client_info.client_id, 
            client=WebApplicationClient,
            redirect_uri=oauth_client_info.redirect_uris[0],
            state=state
            ) as oauth2_client:

            basic_auth = HTTPBasicAuth(oauth_client_info.client_id, oauth_client_info.client_secret)
            auth_metadata = self.auth_metadata_store.get(issuer_uri, None)
            if not auth_metadata:
                auth_metadata = AuthorizationMetadata.model_validate(
                    await self.get_issuer_metadata(
                        issuer_uri,
                        path="/.well-known/oauth-authorization-server")
                        )
                
            token_endpoint = auth_metadata.token_endpoint
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            }
            # TODO: Extra args for verifying

            # Note - using post instead of fetch_token because fetch_token doesn't
            # return the full request body
            r: Response = oauth2_client.post(
                token_endpoint,
                code=code,
                auth=basic_auth,
                headers=headers)
            r.raise_for_status()
            oauth2_client
            
            access_token_res = OAuthTokenResponse.model_validate_json(r.content)
            # Update session
            oauth2_client.token(access_token_res.model_dump())

            # Make requests for credentials
            issuer_metadata = self.issuer_metadata_store.get(issuer_uri, None)
            if not issuer_metadata:
                issuer_metadata = IssuerMetadata.model_validate(
                    await self.get_issuer_metadata(issuer_uri)
                        )

            for detail in access_token_res.authorization_details:
                cred_type = detail.type
                config_id = detail.credential_configuration_id
                for identifier in detail.credential_identifiers:
                    body = { "credential_identifier": identifier }
                    cred_response: Response = oauth2_client.request(
                        'POST',
                        issuer_metadata.credential_endpoint,
                        json = body
                    )
                    cred_response.raise_for_status()
                    # Determine if immediate or deferred
                    if cred_response.status_code == 200:
                        # Immediate
                        new = cred_response.json().get("credential", None)
                        if not new:
                            err = "Invalid credential response from issuer: "
                            err += "Value 'credential' missing from response."
                            raise Exception(err)
                        
                        new_credential = Credential(
                            issuer_url=issuer_uri,
                            credential_configuration_id=config_id,
                            is_deferred=False,
                            c_type=cred_type,
                            received_at=datetime.now().isoformat(),
                            raw_sdjwtvc=new,
                            )
                        
                        new_credentials.append(new_credential)

                    elif cred_response.status_code == 202:
                        tx_id = cred_response.json().get("transaction_id", None)
                        if not tx_id:
                            err = "Invalid credential response from issuer: "
                            err += "Value 'transaction_id' missing from response."
                            raise Exception(err)
                        deferred = issuer_metadata.deferred_credential_endpoint
                        
                        new_credential = DeferredCredential(
                            issuer_url=issuer_uri,
                            credential_configuration_id=config_id,
                            is_deferred=True,
                            c_type=cred_type,
                            transaction_id=tx_id,
                            deferred_credential_endpoint=deferred,
                            access_token=access_token_res.access_token,
                            last_request=datetime.now().isoformat(),
                        )
                        
                        new_credentials.append(new_credential)

                    else:
                        raise Exception("Invalid credential response")
        c: Credential | DeferredCredential
        for c in new_credentials:
            self.credentials[c.id]
            self.store_credential(c)

    async def get_issuer_metadata(self,
                                  issuer_uri,
                                  path="/.well-known/openid-credential-issuer"):
        body: Any
        with Session() as s:
            res: Response = s.get(f"{issuer_uri}{path}")
            body = res.json()
        return body

    async def register_client(self, 
                              registration_url, 
                              issuer_uri, 
                              wallet_metadata=None
                              ) -> RegisteredClientMetadata:
        metadata = wallet_metadata
        registered: RegisteredClientMetadata
        if not metadata:
            metadata = self.client_metadata.model_dump()
        with Session() as s:
            res: Response = s.post(registration_url, json=metadata)
            body: dict = res.json()
            body["issuer_uri"] = issuer_uri
            registered = RegisteredClientMetadata.model_validate(body)
        return registered
    
    def get_deferred_credentials(self) -> list[Credential]:
        """Retrieves all pending credentials.

        ### Returns
        - `list[Credential]`: A list of credentials that have been deferred.
        """
        return [cred for cred in self.credentials.values() if cred.is_deferred]

    async def refresh_credential(self, cred_id: str):
        """Polls for a pending credential

        ### Parameters
        - cred_id(`str`): An identifier for the desired credential

        Todo:
        ----
        - enforce https for non-dev mode for security purposes
        - validate body comes in expected format

        """
        credential = self.credentials.get(cred_id, None)

        if not credential:
            raise Exception("Credential Not Found")
        
        if not credential.is_deferred:
            return credential

        # TODO: Re-implement

        return credential

    async def poll_all_pending_credentials(self) -> list[str]:
        """Polls the issuer for updates on all outstanding credential requests.

        ### Returns
        - `list[str]` A list of credential IDs belonging to credentials that were
        updated.
        """
        updated = []
        for cred in self.get_deferred_credentials():
            await self.refresh_credential(cred.id)
            updated.append(cred.id)

        return updated

    ###
    ### User-defined functions, designed to be overwritten
    ###

    def store_credential(self, cred: Credential):
        """## !!! This function MUST be `@override`n !!!

        Function to store a serialised credential in some manner.

        ### Parameters
        - cred(`Credential`): A `Credential`

        IMPORTANT: Do not store unsecured credentials in a production environment.
        Use `self.serialise_and_encrypt` to convert the `Credential` to
        something that can be stored.
        """
        return

    def load_credential_from_storage(self, cred_id: str) -> Credential:
        """## !!! This function MUST be `@override`n !!!

        Function to load a specific credential from storage.
        Use `self.load_from` to convert the stored credential to a `Credential` object.

        ### Parameters
        - cred_id(`str`): an identifier for the credential

        ### Returns
        - `Credential`: The requested credential, if it exists.
        """
        return None

    def load_all_credentials_from_storage(self) -> list[Credential]:
        """## !!! This function MUST be `@override`n !!!

        Function to retrieve all credentials. Overwrite this method
        to retrieve all credentials.

        ### Returns
        - `list[Credential]`: A list of Credential objects.
        """
        return []
