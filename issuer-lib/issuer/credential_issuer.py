from typing import Any

from fastapi import Body, FastAPI, HTTPException

from .models.responses import OptionsResponse, RequestResponse, UpdateResponse


class CredentialIssuer:
    """
    Base class used for the credential issuer agent.

    ### Attributes
    - credentials(`str`): A list of available credentials that can be issued
    - ticket(`int`): Internal tracking of current ticket number
    - link(`int`): Internal tracking of current used link, used to check status 
      of application
    - mapping(`dict[int, int]`): Mapping of links to tickets
    """

    def __init__(self):
        self.credentials = {
            "default": {
                "string": {
                    "type": "string",
                    "optional": False,
                },
                "number": {
                    "type": "number",
                    "optional": False,
                },
                "boolean": {
                    "type": "boolean",
                    "optional": False,
                },
                "optional": {
                    "type": "string",
                    "optional": True,
                },
            },
        }
        self.ticket = 0
        self.link = 0
        self.mapping = {}

    async def get_credential_options(self) -> OptionsResponse:
        """Retrieves available credentials that can be issues, 
        along with required fields and types."""
        return OptionsResponse(options=self.credentials)

    async def recieve_credential_request(
        self, cred_type: str, information: dict = Body(None)
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

        Valid credential formats and required fields can be accessed through 
        `get_credential_options()`.
        """
        cred_type = cred_type.lower()
        if cred_type not in self.credentials:
            raise HTTPException(status_code=404, detail="Item not found")

        if not information.keys() == self.credentials[
            cred_type
        ].keys() or not self.check_input_typing(cred_type, information):
            raise HTTPException(status_code=400, detail="Malformed request")

        self.ticket += 1
        self.link += 1
        self.mapping[str(self.link)] = self.ticket

        self.get_request(self.ticket, cred_type, information)
        return RequestResponse(ticket=self.ticket, link=str(self.link))

    async def credential_status(self, token: str) -> UpdateResponse:
        """Returns the current status of an active credential request.
        
        ### Parameters
        - token(`str`): Maps to a ticket number through the `mapping` attribute."""
        ticket = self.mapping[token]

        status = self.get_status(ticket)
        return UpdateResponse(ticket=ticket, status=status)

    def check_input_typing(self, cred_type: str, information: dict) -> bool:
        """Checks fields in the given information are of the correct type."""
        for field, value in information.items():
            if value is None:
                if not self.credentials[cred_type][field]["optional"]:
                    return False
            else:
                match self.credentials[cred_type][field]["type"]:
                    case "string":
                        if not isinstance(value, str):
                            return False
                    case "number":
                        # bools can count as ints, and need to be explicitly checked
                        if not (
                            isinstance(value, int) and not isinstance(value, bool)
                        ) and not isinstance(value, float):
                            return False
                    case "boolean":
                        if not isinstance(value, bool):
                            return False
                    case ["array[", _typ, "]"]:
                        pass
                    case ["optional[", _typ, "]"]:
                        pass
                    case "object":
                        pass
        return True

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
        - `Any`: A string representing the status of the application."""
        return "Pending"
