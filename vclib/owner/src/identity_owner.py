from base64 import b64decode, b64encode
from json import loads
from typing import Dict
from uuid import uuid4

from requests import Response, Session

from .models.credentials import Credential
from .models.client_metadata import RegisteredClientMetadata, WalletClientMetadata
from .models.credential_offer import CredentialOffer
from .models.exceptions import (
    BadIssuerRequestError,
    CredentialIssuerError,
    CredentialNotFoundError,
    IssuerTypeNotFoundError,
    IssuerURLNotFoundError,
)

class IdentityOwner:
    """Base Identity Owner class

    ### Attributes
    - credentials(`dict[str, Credential]`): A dictionary of credentials, mapped by
    their IDs
    - dev_mode(`bool`): Flag for running in development environment (currently
    unused)
    - storage_key(`str`): Key for encrypting stored credentials (currently unused)
    """

    client_metadata: WalletClientMetadata

    client_registrations: Dict

    # TODO: Enforce https

    def __init__(self, storage_key: str, *, dev_mode=False,):
        """Creates a new Identity Owner

        ### Parameters
        - storage_key(`str`): A key to encrypt/decrypt credentials when
        reading/writing from storage (CURRENTLY UNUSED)
        - dev_mode(`bool`): An optional parameter (CURRENTLY UNUSED)

        """
        self.client_registrations = {}
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

    async def get_credential_offer(self, credential_offer_uri: str | None, credential_offer: str | None):
        """
        Recieve a credential offer.

        ### Parameters
        - credential_offer_uri(`str | None`): A URL linking to a credential offer 
        object. If provided, `credential_offer` MUST be none. 
        - credential_offer(`str`): A URL-encoded credential offer object. If given,
        `credential_offer_uri` MUST be none. 
        """
        if credential_offer and credential_offer_uri:
            raise Exception("Can't accept both credential_offer and credential_offer_uri")
        
        if not credential_offer and not credential_offer_uri:
            raise Exception("Neither credential_offer nor credential_offer_uri were provided")
        
        offer: CredentialOffer
        if credential_offer_uri:
            # Create a credential offer obj from the URI
            with Session() as s:
                res: Response = s.get(credential_offer_uri)
                res.raise_for_status()
                offer = CredentialOffer.model_validate_json(res.content)
        else:
            offer = CredentialOffer.model_validate_json(credential_offer)

        issuer_uri = offer.credential_issuer


    async def get_issuer_metadata(self, issuer_uri):
        with Session() as s:
            s.get(f"{issuer_uri}/.well-known/openid-credential-issuer")

    async def register_client(self, registration_url, wallet_metadata=None):
        metadata = wallet_metadata
        if not metadata:
            metadata = self.client_metadata
        with Session() as s:
            res: Response = s.post(registration_url, json=metadata)
            body: dict = res.json()
            return RegisteredClientMetadata.model_validate_json(body)

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
