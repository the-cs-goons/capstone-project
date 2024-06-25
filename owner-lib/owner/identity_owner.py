from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import HTMLResponse
from fastapi.encoders import jsonable_encoder
from jsonpath_ng import JSONPath, parse
import json
import httpx
import os
import html

from .models.verifiable_credential import VerifiableCredential, ParsedField, VerifiablePresentation

class IdentityOwner:
    def __init__(self):
        self.credentials: list[VerifiableCredential] = []

    def get_server(self) -> FastAPI:
        router = FastAPI()
        router.get("/")
        router.get("/authorize")(self.get_authorization_request)
        router.post("/authorize")(self.__create_presentation)
        return router

    async def hello(self):
        return {"Wallet home page"}

    async def get_authorization_request(
            self, 
            url: str = f"http://service-lib:{os.getenv('CS3900_SERVICE_AGENT_PORT')}/request?request_type=example"
            ): # -> HTMLResponse:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            
            parsed_fields = self.__parse_authorization_request(response)

        return self.__present_selection_form(parsed_fields)
        

    def __parse_authorization_request(
            self, 
            response: httpx.Response
            ): # -> list[ParsedField]:
        parsed_fields = []

        input_descriptors = json.loads(response.content)["presentation_definition"]["input_descriptors"]
        fields = []

        for input_descriptor in input_descriptors:
            for field in input_descriptor["constraints"]["fields"]:
                fields.append(field)

        for field in fields:
            name = field["path"][-1]
            if "name" in field and field["name"] is not None:
                name = field["name"]
            elif "id" in field and field["id"] is not None:
                name = field["id"]
            
            optional = False
            if "optional" in field and field["optional"] is not None:
                optional = field["optional"]

            condition = None
            if "filter" in field and field["filter"] is not None:
                condition = field

            paths = field["path"]
            parsed_fields.append(
                ParsedField(
                    name = name, 
                    condition = json.dumps(condition), 
                    paths = paths,
                    optional = optional,
                    original_field = json.dumps(field)))

        return parsed_fields

    def __present_selection_form(
            self, 
            parsed_fields: list[ParsedField]
            ) -> HTMLResponse:
        
        field_entries_html = ""
        for field in parsed_fields:
            if field.optional:
                optional = " Optional"
            else:
                optional = ""

            field_entries_html += f'<input type="checkbox" name="selection" value="{html.escape(field.model_dump_json())}">{field.name}{optional}<br>'

        html_ready_fields = [field.model_dump() for field in parsed_fields]
        all_fields_html = f'<input type="hidden" name="parsed_fields" value="{html.escape(json.dumps(html_ready_fields))}">'

        html_content = f"""
        <html>
            <h3>Select fields to share</h3>
            <form action="/authorize" method="post">
                {field_entries_html}
                {all_fields_html}
                <input type="submit" value="Submit">
            </form>
        </html>
        """
        return HTMLResponse(content=html_content)

    def __create_presentation(
            self, 
            selection: str = Form(...), 
            parsed_fields: str = Form(...)): # -> VerifiablePresentation:
        
        # TODO: Implement presentation creation.
        # The below follows the path expression made using 
        # jsonpath_ng from the "path" property in a field

        # for credential in self.credentials:
        #     cred_dict = credential.model_dump(serialize_as_any=True, exclude_none=True)
        #     matches = path_exp.find(cred_dict)

        return {"selection": json.loads(selection), 
                "parsed_fields": json.loads(parsed_fields)}
