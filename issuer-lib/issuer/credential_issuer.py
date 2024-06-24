from typing import Any
from uuid import uuid4

from fastapi import Body, FastAPI, HTTPException

from .models.responses import OptionsResponse, RequestResponse, UpdateResponse


class CredentialIssuer:
    """
    Base class used for the credential issuer agent.

    ### Attributes
    - credentials(`dict`): A dictionary of available credentials that can be issued,
      with required fields and types
    - ticket(`int`): Internal tracking of current ticket number
    - mapping(`dict[str, int]`): Mapping of links to tickets
    """

    def __init__(self, credentials: dict[str, dict[str, dict[str, Any]]]):
        self.credentials = credentials
        self.ticket = 0
        self.mapping = {}

    async def get_credential_options(self) -> OptionsResponse:
        """Retrieves available credentials that can be issues, 
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
            raise HTTPException(status_code=404, 
                                detail=f"Credential type {cred_type} is not supported")

        try:
            self.check_input_typing(cred_type, information)
        except Exception as e:
            raise HTTPException(status_code=400, 
                                detail=f"Fields for credential type {cred_type} were formatted incorrectly: {e}") # noqa E501

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
        return UpdateResponse(ticket=ticket, status=status)

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

    def get_status(self, _ticket: int) -> Any:
        """## !!! This function must be `@override`n !!!

        Function to process requests for credential application status updates.
        
        ### Parameters
        - ticket(`int`): Ticket number of the request. This is generated by the class.
        
        ### Returns
        - `Any`: A string representing the status of the application.
        
        IMPORTANT: The return value can be read by anyone with the link to specified
        ticket, and must not have any sensitive information contained."""
        return "Pending"
