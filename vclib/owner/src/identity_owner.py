import json
from base64 import b64decode, b64encode
from json import loads
from uuid import uuid4

import jsonpath_ng
import jwt
from requests import Response, Session
from sd_jwt.common import SDJWTCommon

from .models import Credential
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

    # TODO: Enforce https

    def __init__(self, storage_key: str, *, dev_mode=False):
        """Creates a new Identity Owner

        ### Parameters
        - storage_key(`str`): A key to encrypt/decrypt credentials when
        reading/writing from storage (CURRENTLY UNUSED)
        - dev_mode(`bool`): An optional parameter (CURRENTLY UNUSED)

        """
        self.vc_credentials: list[str] = []
        self.storage_key = storage_key
        self.dev_mode = dev_mode
        self.credentials: dict[str, Credential] = {}
        for cred in self.load_all_credentials_from_storage():
            self.credentials[cred.id] = cred

    def _get_credential_payload(self, sd_jwt_vc: str):
        return sd_jwt_vc.split("~")[0]

    def _get_decoded_credential_payload(self, sd_jwt_vc: str):
        payload = self._get_credential_payload(sd_jwt_vc)
        return jwt.decode(payload, options={"verify_signature": False})

    def _get_decoded_credential_disclosures(self, sd_jwt_vc: str):
        """Takes an SD-JWT Verifiable Credential (string) and returns its
        decoded disclosures (the disclosures between the first and last tilde)
        """
        # has_kb = False
        # if sd_jwt_vc[-1] != "~":
        #     has_kb = True
        parts = sd_jwt_vc.split("~")
        disclosures = parts[1:-1]
        # kb = None
        # if has_kb:
        #     kb = disclosures.pop()

        # dict[encoded_disclosure, decoded_disclosure]
        encoded_to_decoded_disclosures = {}
        for disclosure in disclosures:
            decoded_disclosure_bytes = SDJWTCommon._base64url_decode(disclosure)
            decoded_disclosure_str = decoded_disclosure_bytes.decode("utf-8")
            decoded_disclosure_list = json.loads(decoded_disclosure_str)
            decoded_disclosure_claim = {
                decoded_disclosure_list[1]: decoded_disclosure_list[2]
            }
            encoded_to_decoded_disclosures[disclosure] = decoded_disclosure_claim
        return encoded_to_decoded_disclosures

    def _get_credentials_with_field(
        self,
        paths: list[str],  # list of jsonpath strings
    ) -> dict[str, list[str]]:
        """returns list(credential, [encoded disclosure])"""

        matched_credentials = {}
        for path in paths:
            expr = jsonpath_ng.parse(path)
            for credential in self.vc_credentials:
                payload = self._get_decoded_credential_payload(credential)
                matches = expr.find(payload)
                if matches not in ([], None):
                    matched_credentials[credential] = []
                    continue

                encoded_to_decoded_disclosures = (
                    self._get_decoded_credential_disclosures(credential)
                )
                disclosures = encoded_to_decoded_disclosures.values()
                for disclosure in disclosures:
                    matches = expr.find(disclosure)
                    if matches not in ([], None):
                        disclosure_idx = list(disclosures).index(disclosure)
                        encoded_disclosures = encoded_to_decoded_disclosures.keys()
                        encoded_disclosure = list(encoded_disclosures)[disclosure_idx]
                        matched_credentials[credential] = [encoded_disclosure]

        return matched_credentials

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

    def get_pending_credentials(self) -> list[Credential]:
        """Retrieves all pending credentials.

        ### Returns
        - `list[Credential]`: A list of Credential objects with status `"PENDING"`.
        """
        return [cred for cred in self.credentials.values() if cred.status == "PENDING"]

    async def poll_credential_status(self, cred_id: str):
        """Polls for a pending credential

        ### Parameters
        - cred_id(`str`): An identifier for the desired credential

        Todo:
        ----
        - enforce https for non-dev mode for security purposes
        - validate body comes in expected format

        """
        if cred_id not in self.credentials:
            raise CredentialNotFoundError
        credential = self.credentials[cred_id]

        # Closes session afterwards
        with Session() as s:
            response: Response = s.get(credential.request_url)
            if not response.ok:
                raise CredentialIssuerError
            # TODO: Logic for updating state according to how Mal's structured things
            body: dict = response.json()
            credential.status = body["status"]

            if credential.status == "ACCEPTED":
                credential.token = body["credential"]
            elif credential.status == "REJECTED":
                credential.status_message = body["detail"]

            return credential

    async def poll_all_pending_credentials(self) -> list[str]:
        """Polls the issuer for updates on all outstanding credential requests.

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
        """Adds a credential to the Identity Owner from a request URL

        ### Parameters
        - url(`str`): The request URL to poll to for the credential's status
        """
        id = uuid4()
        # TODO: Poll issuer for type and base URL
        credential = Credential(id=id, issuer_url="", type="", request_url=url)
        self.credentials[id] = credential
        self.store_credential(credential)

    async def get_credential_request_schema(self, cred_type: str, issuer_url: str):
        """Retrieves required information needed to submit a request for some ID type
        from an issuer.

        ### Parameters
        - issuer_url(`str`): The issuer URL
        - cred_type(`str`): The type of the credential schema request being asked for
        """
        with Session() as s:
            response: Response = s.get(f"{issuer_url}/credentials")
            if not response.ok:
                raise IssuerURLNotFoundError

            body: dict = response.json()
            if "options" not in body:
                raise CredentialIssuerError

            options: dict = body["options"]
            if cred_type not in options:
                raise IssuerTypeNotFoundError

            return options[cred_type]

    def apply_for_credential(
        self, cred_type: str, issuer_url: str, info: dict
    ) -> Credential:
        """Sends request for a new credential directly, then stores it

        ### Parameters
        - issuer_url(`str`): The issuer URL
        - cred_type(`str`): The type of the credential schema request being asked for
        - info(`dict`): The body of the request to forward on to the issuer, sent as
        JSON

        ### Returns
        - `Credential`: The new (pending) credential, if requested successfully
        """
        body: dict
        with Session() as s:
            response: Response = s.post(f"{issuer_url}/request/{cred_type}", json=info)
            if not response.ok:
                if response.status_code < 500:
                    if "detail" not in response.json():
                        raise IssuerTypeNotFoundError
                    if response.status_code == 404:
                        raise IssuerURLNotFoundError
                    raise BadIssuerRequestError
                raise CredentialIssuerError
            body = response.json()

        # For internal use by the ID owner library/agent
        id = uuid4().hex
        # TODO: Verify
        req_url = f"{issuer_url}/status?token={body['link']}"

        credential = Credential(
            id=id, issuer_url=issuer_url, type=cred_type, request_url=req_url
        )
        self.credentials[id] = credential
        self.store_credential(credential)
        return self.credentials[id]

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
