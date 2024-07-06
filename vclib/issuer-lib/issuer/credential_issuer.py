import json
from base64 import b64encode
from hashlib import sha256
from typing import Any
from uuid import uuid4

from common import hello_world
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from fastapi import FastAPI, HTTPException

from .models.responses import (
    OptionsResponse,
    RequestResponse,
    StatusResponse,
    UpdateResponse,
)


class CredentialIssuer:
    """
    Base class used for the credential issuer agent.

    ### Attributes
    - credentials(`dict`): A dictionary of available credentials that can be issued,
      with required fields and types
    - ticket(`int`): Internal tracking of current ticket number
    - mapping(`dict[str, int]`): Mapping of links to tickets
    - private_key: Private key used to sign credentials
    """

    def __init__(
        self, credentials: dict[str, dict[str, dict[str, Any]]], private_key_path: str
    ):
        self.credentials = credentials
        self.ticket = 0
        self.mapping = {}
        try:
            with open(private_key_path, "rb") as key_file:
                self.private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None,
                )
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Could not find private key: {e}")
        except ValueError as e:
            raise ValueError(f"Invalid private key provided: {e}")

    async def get_credential_options(self) -> OptionsResponse:
        """Retrieves available credentials that can be issued,
        along with required fields and types."""
        return OptionsResponse(options=self.credentials)

    async def recieve_credential_request(
        self, cred_type: str, information: dict = None
    ) -> RequestResponse:
        """Receives a request for credentials.

        ### Parameters
        - cred_type(`str`): Type of credential being requested.
          This parameter is taken from the endpoint that was visited.
        - information(`dict`): Request body, containing information for the
          credential being requested.

        ### `POST`-ing requests
        Requests must:
        - Come from an endpoint corresponding to a valid credential type;
          e.g. `/request/drivers_license`
        - Contain fields in the request body matching those of the credential
          being applied for
        - Contain the correct data types in said fields.

        A `HTTPException` will be thrown if any of these are not met.

        Valid credential formats and required fields can be accessed through
        `get_credential_options()`.
        """
        if cred_type not in self.credentials:
            raise HTTPException(
                status_code=404, detail=f"Credential type {cred_type} is not supported"
            )

        try:
            self.check_input_typing(cred_type, information)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Fields for credential type {cred_type} were formatted incorrectly: {e}",  # noqa E501
            )

        self.ticket += 1
        link = str(uuid4())
        self.mapping[link] = self.ticket

        self.get_request(self.ticket, cred_type, information)
        return RequestResponse(ticket=self.ticket, link=link)

    async def credential_status(self, token: str) -> UpdateResponse:
        """Returns the current status of an active credential request.

        ### Parameters
        - token(`str`): Maps to a ticket number through the `mapping` attribute."""
        ticket = self.mapping[token]

        status = self.get_status(ticket)
        credential = None
        if status.information is not None:
            self.mapping.pop(token)
            credential = self.create_credential(status.cred_type, status.information)
        return UpdateResponse(ticket=ticket, status=status.status, 
                              credential=credential)

    def check_input_typing(self, cred_type: str, information: dict):
        """Checks fields in the given information are of the correct type.
        Raises `TypeError` if types do not match."""
        if information is None:
            raise TypeError("No request body provided")

        for field_name, field_info in self.credentials[cred_type].items():
            if field_name in information:
                value = information[field_name]
                if value is None:
                    if not field_info["optional"]:
                        raise TypeError(f"{field_name} is non-optional and was null")
                else:
                    match field_info["type"]:
                        case "string":
                            if not isinstance(value, str):
                                raise TypeError(f"{field_name} expected to be string")
                        case "number":
                            # bools can count as ints, and need to be explicitly checked
                            if not (
                                isinstance(value, int) and not isinstance(value, bool)
                            ) and not isinstance(value, float):
                                raise TypeError(f"{field_name} expected to be number")
                        case "boolean":
                            if not isinstance(value, bool):
                                raise TypeError(f"{field_name} expected to be boolean")
                        # Unimplemented, will be in future sprint
                        case ["array[", _typ, "]"]:
                            raise NotImplementedError
                        case "object":
                            raise NotImplementedError
            elif not field_info["optional"]:
                raise TypeError(f"{field_name} is non-optional and was not provided")
        for field_name in information.keys():
            if field_name not in self.credentials[cred_type]:
                raise TypeError(f"{field_name} not required by {cred_type}")
        return

    def get_server(self) -> FastAPI:
        """Gets the server for the issuer."""
        router = FastAPI()
        router.get("/credentials/")(self.get_credential_options)
        router.post("/request/{cred_type}")(self.recieve_credential_request)
        router.get("/status/")(self.credential_status)
        router.get("/hello")(hello_world)
        return router

    ###
    ### User-defined functions, designed to be overwritten
    ###
    def get_request(self, _ticket: int, _cred_type: str, _information: dict):
        """## !!! This function must be `@override`n !!!

        Function to accept and process requests.

        ### Parameters
        - ticket(`int`): Ticket number of the request. This is generated by the class.
        - cred_type(`str`):  Type of credential being requested.
          This parameter is taken from the endpoint that was visited.
        - information(`dict`): Request body, containing information for the
          credential being requested."""
        return

    def get_status(self, _ticket: int) -> StatusResponse:
        """## !!! This function must be `@override`n !!!

        Function to process requests for credential application status updates, as
        well as returning credentials for successful applications.

        ### Parameters
        - ticket(`int`): Ticket number of the request. This is generated by the class.

        ### Returns
        A `StatusResponse` object is returned, with the following fields:
        - `Any`: A string representing the status of the application.
        - `str`: The type of credential that was requested.
        - `dict`: Fields to be used in the new credential, once approved. Set as
          `None` otherwise.

        IMPORTANT: The `Any` return value can be read by anyone with the link to
        specified ticket, and must not have any sensitive information contained."""
        return StatusResponse(status="PENDING", cred_type=None, information=None)

    def create_credential(self, cred_type: str, information: dict) -> str:
        """Function to generate credentials after being accepted.

        Overriding this function is *optional* - default implementation will be
        SD-JWT-VC, however a temporary mimicing algorithm is used in place for the
        time being.

        ### Parameters
        - cred_type(`str`):  Type of credential being requested.
          This parameter is taken from the endpoint that was visited.
        - information(`dict`): Contains information for the credential being
          constructed.

        ### Returns
        - `str`: A string containing the new issued credential.
        """
        items = []
        disclosures = []
        for field_name, field_value in information.items():
            json_rep = json.dumps({field_name: field_value})
            disclosures.append(json_rep)
            hashed = sha256(bytes(json_rep, encoding="utf8")).hexdigest()
            items.append(hashed)

        credential = bytes(json.dumps({"_fields": items, "_type": cred_type}), "utf8")

        signature = self.private_key.sign(
            credential,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256(),
        )

        cred_string = b64encode(credential) + b"." + b64encode(signature)
        for i in disclosures:
            cred_string += b"~" + b64encode(bytes(json.dumps(i), "utf-8"))

        return cred_string.decode("utf-8")
