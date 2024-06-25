from base64 import b64decode, b64encode
from json import loads
from uuid import uuid4

from requests import Response, Session

from .models import Credential


class IdentityOwner:
    """
    Base Identity Owner class

    ### Attributes
    - credentials(`dict[str, Credential]`): A dictionary of credentials, mapped by 
    their IDs
    - dev_mode(`bool`): Flag for running in development environment (currently 
    unused)
    - storage_key(`str`): Key for encrypting stored credentials (currently unused)
    """
    # TODO: Enforce https

    def __init__(self, storage_key: str, dev_mode=False):
        """
        Creates a new Identity Owner

        ### Parameters
        - storage_key(`str`): A key to encrypt/decrypt credentials when 
        reading/writing from storage (CURRENTLY UNUSED)
        - dev_mode(`bool`): An optional parameter (CURRENTLY UNUSED)

        """
        self.storage_key = storage_key
        self.dev_mode = dev_mode
        self.credentials: dict[str, Credential] = {}
        for cred in self.load_all_credentials_from_storage():
            self.credentials[cred.id] = cred

    def serialise_and_encrypt(self, cred: Credential):
        """
        # NOT YET IMPLEMENTED IN FULL
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
        """
        # NOT YET IMPLEMENTED IN FULL
        TODO: Implement decryption in accordance with implementation in 
        `serialise_and_encrypt`
        
        Static method that loads a credential from encrypted & serialised string
        
        ### Parameters
        - dump(`str` | `bytes` | `bytearray`): the serialised credential

        ### Returns
        - `Credential`: A Credential object
        """
        return Credential.model_validate(loads(b64decode(dump)))
    
    def get_pending_credentials(self) -> list[Credential]:
        """
        Retrieves all pending credentials. 
        
        ### Returns
        - `list[Credential]`: A list of Credential objects with status `"PENDING"`.
        """
        return [cred for cred in self.credentials.values() if cred.status == "PENDING"]
    
    async def poll_credential_status(self, cred_id: str):
        """
        Polls for a pending credential

        ### Parameters
        - cred_id(`str`): An identifier for the desired credential

        TODO:
        - enforce https for non-dev mode for security purposes
        - validate body comes in expected format
        """

        credential = self.credentials[cred_id]
        
        # Closes session afterwards
        with Session() as s:
            response: Response = await s.get(credential.request_url)
            if not response.ok:
                raise response.reason
            # TODO: Logic for updating state according to how Mal's structured things
            body: dict = response.json()
            self.status = body["status"]

            if self.status == "ACCEPTED":
                self.token = body["credential"]
            elif self.status == "REJECTED":
                self.status_message = body["detail"]

    async def poll_all_pending_credentials(self) -> list[str]:
        """
        Polls the issuer for updates on all outstanding credential requests.

        ### Returns
        - `list[str]` A list of credential IDs belonging to credentials that were
        updated.
        """
        updated = []
        for cred in self.get_pending_credentials():
            if cred.status == "Pending":
                await self.poll_credential_status(cred.id)
                updated.append(cred.id)

        return updated

    def add_credential_from_url(self, url: str):
        """
        Adds a credential to the Identity Owner from a request URL

        ### Parameters
        - url(`str`): The request URL to poll to for the credential's status
        """
        id = uuid4()
        # TODO: Poll issuer for type and base URL
        credential = Credential(id=id, issuer_url="", type="", request_url=url)
        self.credentials[id] = credential
        self.store_credential(credential)
        
    async def get_credential_request_schema(self, issuer_url: str, cred_type: str):
        """
        Retrieves the required information needed to submit a request for some ID type
        from an issuer.

        ### Parameters
        - issuer_url(`str`): The issuer URL
        - cred_type(`str`): The type of the credential schema request being asked for
        """
        with Session() as s:
            response: Response = await s.get(f"{issuer_url}/credentials")
            if not response.ok:
                raise f"Error: {response.status_code} Response - {response.reason}"
            
            body: dict = response.json()
            if "options" not in body.keys():
                raise "Error: Incorrect API Response"
            
            options: dict = body["options"]
            if type not in options.keys():
                raise f"Error: Credential type {cred_type} not found."
            
            return options[cred_type]

    def apply_for_credential(self, issuer_url: str, cred_type: str, info: dict):
        """
        Sends request for a new credential directly, then stores it

        ### Parameters
        - issuer_url(`str`): The issuer URL
        - cred_type(`str`): The type of the credential schema request being asked for
        - info(`dict`): The body of the request to forward on to the issuer, sent as JSON
        """
        with Session() as s:
            response: Response = s.post(f"{issuer_url}/request/{cred_type}", json=info)
            if not response.ok:
                raise f"Error: {response.status_code} - {response.json()["detail"]}"
            body: dict = response.json()

            # For internal use by the ID owner library/agent
            id = uuid4().hex
            req_url = f"{issuer_url}/status?token={body['link']}"

            credential = Credential(id=id, 
                                    issuer_url=issuer_url, 
                                    type=cred_type, 
                                    request_url=req_url)
            self.credentials[id] = credential
            self.store_credential(credential)

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