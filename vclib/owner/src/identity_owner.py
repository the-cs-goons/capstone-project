from base64 import b64decode, b64encode, urlsafe_b64encode
from hashlib import sha256
from json import dumps, loads
from urllib.parse import urlencode
from uuid import uuid4

from requests import Response, Session

from .models.client_metadata import RegisteredClientMetadata, WalletClientMetadata
from .models.credential_offer import CredentialOffer
from .models.credentials import Credential
from .models.issuer_metadata import AuthorizationMetadata, IssuerMetadata


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
                 storage_key: str,
                 oauth_client_metadata: dict,
                 *,
                 dev_mode=False,):
        """Creates a new Identity Owner

        ### Parameters
        - storage_key(`str`): A key to encrypt/decrypt credentials when
        reading/writing from storage (CURRENTLY UNUSED)
        - dev_mode(`bool`): An optional parameter (CURRENTLY UNUSED)

        """
        self.client_states = {}
        self.credential_offers = {}
        self.client_metadata = WalletClientMetadata.model_validate(
            oauth_client_metadata
            )
        self.storage_key = storage_key
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
                                   credential_offer: str | None):
        """
        Recieve a credential offer.

        ### Parameters
        - credential_offer_uri(`str | None`): A URL linking to a credential offer
        object. If provided, `credential_offer` MUST be none.
        - credential_offer(`str`): A URL-encoded credential offer object. If given,
        `credential_offer_uri` MUST be none.
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


        # Retrieve Metadata
        issuer_uri = offer.credential_issuer
        issuer_metadata = IssuerMetadata.model_validate_json(
            await self.get_issuer_metadata(issuer_uri)
            )

        auth_metadata = AuthorizationMetadata.model_validate_json(
            await self.get_issuer_metadata(issuer_uri,
                                     path="/.well-known/oauth-authorization-server"))

        if issuer_uri != issuer_metadata.credential_issuer:
            raise Exception(
                "Bad Issuer Metadata")

        if issuer_uri != auth_metadata.issuer:
            raise Exception(
                "Bad Issuer Authorization Metadata")

        offer_id = uuid4().bytes.strip(b'=')
        self.credential_offers[offer_id] = {
            'offer': offer,
            'auth_metadata': auth_metadata,
            'issuer_metadata': issuer_metadata
        }

        return {
            'offer_id': offer_id.decode(),
            'credential_configuration_ids': offer.credential_configuration_ids
        }


    async def get_offer_oauth_url(self,
                                  offer_id: str,
                                  credential_configuration_id: str):
        """
        TODO: Docs
        """

        credential_offer = self.credential_offers.get(offer_id, None)
        if not credential_offer:
            raise Exception("Invalid offer ID")

        auth_metadata: AuthorizationMetadata = credential_offer["auth_metadata"]

        # Register as OAuth client
        wallet_metadata = await self.register_client(
            auth_metadata.registration_endpoint)

        # Keep track of state
        state = urlsafe_b64encode(sha256(wallet_metadata.model_dump_json()).digest())
        state = state.strip(b'=').decode()
        self.client_states[state] = credential_offer
        # Delete from credential offers
        del self.credential_offers[credential_offer]

        self.client_states[state]['wallet_metadata'] = wallet_metadata

        # Redirect end user
        auth_details = [{
                'type': 'openid_credential',
                'credential_configuration_id': credential_configuration_id
                }]

        auth_redirect_params = {
            'client_id': wallet_metadata.client_id,
            'redirect_uri': wallet_metadata.redirect_uris[0],
            'response_type': 'code',
            'authorization_details': urlencode(dumps(auth_details)),
            'state': state
            }
        base_url = auth_metadata.authorization_endpoint + '?'
        return base_url + urlencode(auth_redirect_params)


    async def get_credential_from_code(self, code: str, state: str):
        auth_state = self.client_states.get(state, None)
        if not auth_state:
            raise Exception("Bad Authorization Redirect")

        auth_metadata: AuthorizationMetadata = auth_state["auth_metadata"]
        issuer_metadata: IssuerMetadata = auth_state["issuer_metadata"]
        wallet_metadata: RegisteredClientMetadata = auth_state["wallet_metadata"]
        auth_metadata.token_endpoint

        # Get access token
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': wallet_metadata.redirect_uris[0]
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        with Session() as s:
            s.auth = (wallet_metadata.client_id, wallet_metadata.client_secret)
            res: Response = s.post(auth_metadata.token_endpoint,
                                   data=data,
                                   headers=headers)
            res.raise_for_status()
            body: dict = res.json()

            token = body.get("access_token")
            # TODO: ADD CREDENTIALS
            for cred_id in body.get("authorization_details")["credential_identifiers"]:
                cred = Credential(uuid4().hex, 
                                  issuer_url=issuer_metadata.credential_issuer,
                                  cred_type=cred_id,
                                  credential_configuration_id=cred_id
                                  )






    async def get_issuer_metadata(self,
                                  issuer_uri,
                                  path="/.well-known/openid-credential-issuer"):
        with Session() as s:
            res: Response = s.get(f"{issuer_uri}{path}")
            return res.json()

    async def register_client(self, registration_url, wallet_metadata=None):
        metadata = wallet_metadata
        registered: RegisteredClientMetadata
        if not metadata:
            metadata = self.client_metadata
        with Session() as s:
            res: Response = s.post(registration_url, json=metadata)
            body: dict = res.json()
            registered = RegisteredClientMetadata.model_validate_json(body)
        return registered

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
