
from uuid import uuid4

import requests
from fastapi import FastAPI, HTTPException
from jose import jwk, jwt

from .models.presentation_definition import PresentationDefinition
from .models.presentation_request_response import PresentationRequestResponse


class ServiceProvider:
    def __init__(
        self,
        ca_bundle,
        ca_path: str,
        presentation_definitions: dict[str, PresentationRequestResponse] = {},
    ):
        """Initialise the service provider with a list of CA bundle"""
        self.presentation_definitions = presentation_definitions
        self.ca_bundle = ca_bundle
        self.ca_path = ca_path
        self.used_nonces = set()

    def get_server(self) -> FastAPI:
        router = FastAPI()
        router.get("/request/{request_type}")(self.get_presentation_request)
        # router.post("/verify-certificate/{credential}")(self.try_verify_certificate)
        return router

    def add_presentation_definition(
        self, request_type: str, presentation_definition: PresentationDefinition
    ) -> None:
        self.presentation_definitions[request_type] = presentation_definition

    async def get_presentation_request(
        self, request_type: str, client_id: str
    ) -> PresentationRequestResponse:
        if request_type not in self.presentation_definitions:
            raise HTTPException(status_code=404, detail="Request type not found")

        return PresentationRequestResponse(
            client_id, self.presentation_definitions[request_type]
        )

    def generate_nonce(self):
        return str(uuid4())

    def fetch_did_document(self, did_url):
        ''' fetch the did document from endpoint '''
        response = requests.get(did_url + '/did.json')
        if response.status_code == 200:
            return response.json()

        raise Exception(f"Failed to fetch DID document from {did_url}")

    def verify_jwt(self, token: str, did_url: str, nonce: str) -> dict:
        ''' Take in the JWT and verify with the did '''
        did_doc = self.fetch_did_document(did_url)
        header = jwt.get_unverified_header(token)
        kid = header['kid']

        for vm in did_doc['verificationMethod']:
            if vm['id'] == kid:
                public_key = jwk.construct(vm['publicKeyJwk'])
                # Verify the JWT using the public key
                return jwt.decode(token, public_key, algorithms=['HS256'])

        raise Exception("Verification method not found or invalid token.")
