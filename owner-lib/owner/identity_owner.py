import html
import json
import os

import httpx
from fastapi import FastAPI, Form, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse
from jsonpath_ng import JSONPath, parse

from .models.verifiable_credential import (
    ParsedField,
    VerifiableCredential,
    VerifiablePresentation,
)


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
            url: str = f"http://service-lib:{os.getenv('CS3900_SERVICE_AGENT_PORT')}/request?request_type=example" # noqa E501
            ): # -> HTMLResponse:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            
            parsed_fields = self.__parse_authorization_request(response)

        return self.__present_selection_form(parsed_fields)
        

    def __parse_authorization_request(
            self, 
            response: httpx.Response
            ) -> list[ParsedField]:
        parsed_fields = []

        input_descriptors = json.loads(
            response.content)["presentation_definition"]["input_descriptors"]
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
                optional = " (optional)"
            else:
                optional = ""

            field_entries_html += f'<input class="field-checkbox" type="checkbox" value="{html.escape(field.model_dump_json())}">{field.name}{optional}<br>' # noqa E501

        all_fields_html = f'''<input type="hidden" name="parsed_fields" value=\'{
            json.dumps(field.model_dump())}\'>'''
        selected_fields_html = '<input type="hidden" id="selected_fields" name="selection">' # noqa E501

        html_content = f"""
        <html>
            <h3>Select fields to share</h3>
            <form id="selection_form" action="/authorize" 
                method="post" onsubmit="prepareSelection()"> 
                {field_entries_html}
                {all_fields_html}
                {selected_fields_html}
                <input type="submit" value="Submit">
            </form>
            <script>
                function prepareSelection() {{
                    var checkboxes = document.getElementsByClassName('field-checkbox');
                    var selected = [];
                    for (var i = 0; i < checkboxes.length; i++) {{
                        if (checkboxes[i].checked) {{
                            selected.push(checkboxes[i].value);
                        }}
                    }}
                    document.getElementById('selected_fields').value 
                        = JSON.stringify(selected);
                }}
            </script>
        </html>"""
        return HTMLResponse(content=html_content)

    def __create_presentation(
            self, 
            selection: str = Form(...), 
            parsed_fields: str = Form(...)): # -> VerifiablePresentation:
        
        # TODO: Implement presentation creation.
        # The below follows the path expression made using 
        # jsonpath_ng from the "path" property in a field

        # for credential in self.credentials:
        #     cred_dict = credential.model_dump(serialize_as_any=True, 
        #                   exclude_none=True)
        #     matches = path_exp.find(cred_dict)

        selection_list = json.loads(html.unescape(selection))
        selection = [json.loads(x) for x in selection_list]

        return {"selection": selection, #[json.loads(x) for x in selection], 
                "parsed_fields": json.loads(parsed_fields)}
