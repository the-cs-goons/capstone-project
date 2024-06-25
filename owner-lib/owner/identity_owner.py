from fastapi import FastAPI, HTTPException
from jsonpath_ng import JSONPath, parse
import json
import httpx
import os

from .models.verifiable_credential import VerifiableCredential

class IdentityOwner:
    def __init__(self):
        self.credentials: list[VerifiableCredential] = []

    def get_server(self) -> FastAPI:
        router = FastAPI()
        router.get("/")(self.hello)
        router.get('/yomama')(self.f)
        router.get("/pr")(self.get_presentation_request)
        return router

    async def hello(self):
        return {"Hello" : "World"}

    async def f(self):
        return {"message": "YO MAMA FAT"}

    async def get_presentation_request(
            self,
            url: str = f"http://service-lib:{os.getenv('CS3900_SERVICE_AGENT_PORT')}/request?request_type=example"
            ):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()  # Raises an exception if the request was unsuccessful
                data = self.__parse_response(response)
            return data
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=str(exc))

    def __parse_response(self, response: httpx.Response):
        """FOR NOW: field will be satisfied if path is found"""
        data = {'fields': []} # this is meant to be fields, and shows if a field has been satisfied

        input_descriptors = json.loads(response.content)['presentation_definition']['input_descriptors']
        for input_descriptor in input_descriptors:
            fields = input_descriptor['constraints']['fields']
            for field in fields:
                data['fields'].append(self.__parse_field(field))
        return data

    def __parse_field(self, field):
        for path in field['path']:
            path_expression = parse(path)
            search_result = self.__credential_search_path(path_expression)
            if search_result['result'] is not None:
                return {
                    'field': path,
                    'result': search_result['result'],
                    'from': search_result['from']
                }
        return {
            'field': field,
            'result': None,
            'from': None
        }

    # yomamafat
    def __credential_search_path(self, path_exp: JSONPath):
        """Searches every cred for a matching field"""
        for cred in self.credentials:
            cred_dict = cred.model_dump(serialize_as_any=True, exclude_none=True)

            matches = path_exp.find(cred_dict)
            # get the first match
            for match in matches:
                return {
                    'result': match.value,
                    'from' : cred
                    }
        return {
            'result': None,
            'from': None
        }
