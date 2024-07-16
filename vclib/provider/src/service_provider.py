from uuid import uuid4

import jsonpath_ng
import jwt
import requests
from fastapi import FastAPI, HTTPException, Form

from .models.authorization_request_object import AuthorizationRequestObject
from .models.authorization_response_object import AuthorizationResponseObject
from .models.presentation_definition import PresentationDefinition
from .models.presentation_submission import PresentationSubmission


class ServiceProvider:
    def __init__(
        self,
        presentation_definitions: dict[str, PresentationDefinition],
        ca_cert_path: str
    ):
        """Initialise the service provider with a list of CA bundle"""

        self.presentation_definitions = presentation_definitions

        with open(ca_cert_path, "r") as f:
            self.ca_certs = f.read()
        # TODO verify public keys

    def get_server(self) -> FastAPI:
        router = FastAPI()
        router.get("/presentationdefs")(self.get_presentation_definition)
        router.post("/request/{request_type}")(self.fetch_authorization_request)
        router.post("/cb")(self.parse_authorization_response)
        # TODO serve did
        return router

    async def get_presentation_definition(self, request_type: str) -> PresentationDefinition:
        if request_type not in self.presentation_definitions:
            raise HTTPException(status_code=404, detail=f"Presentation definition matching request_type '{request_type}' not found")

        return self.presentation_definitions_by_id[request_type]

    # fetches and sends back the requested request object
    # accessed through request_uri embedded in QR code
    # should be overridden to fit verifier's needs
    async def fetch_authorization_request(
        self,
        request_type: str,
        wallet_metadata: str = Form(...),
        wallet_nonce: str = Form(...),
    ) -> AuthorizationRequestObject:
        if request_type not in self.presentation_definitions:
            raise HTTPException(status_code=404, detail=f"Presentation definition matching request_type '{request_type}' not found")

        return AuthorizationRequestObject(
            client_id="did:web:example.com", # TODO
            client_metadata={"name": "Example"}, # TODO
            presentation_definition=self.presentation_definitions[request_type],
            response_uri="https://example.com/cb",
            nonce=self.generate_nonce(),
            wallet_nonce=wallet_nonce,
        )

    async def parse_authorization_response(self, auth_response: AuthorizationResponseObject):
        # TODO: verify the auth_response and tell the wallet whether or not
        # it has been successful or not

        # get presentation definition
        if auth_response.presentation_submission.definition_id not in self.presentation_definitions:
            raise HTTPException(status_code=400, detail="Specified definition_id does not match a supported presentation definition")
        presentation_definition = self.presentation_definitions[auth_response.presentation_submission.definition_id]

        # get presented fields
        presented_tokens = {}
        for descriptor in auth_response.presentation_submission.descriptor_map:
            if descriptor.format != "jwt_vc":
                raise HTTPException(status_code=400, detail=f"Descriptor {descriptor.id} has format other than 'jwt_vc'")
            try:
                match = jsonpath_ng.parse(descriptor.path).find(auth_response)
            except:
                raise HTTPException(status_code=400, detail=f"Invalid JSONPath for descriptor {descriptor.id}")
            if len(match) != 1:
                raise HTTPException(status_code=400, detail=f"JSONPath for descriptor {descriptor.id} did not match exactly one field")
            presented_tokens[descriptor.id] = match[0].value

        # verify jwts
        jwt_payloads = []
        try:
            for token in presented_tokens:
                jwt_payloads.append(self.verify_jwt(token, None, None)) # TODO
        except Exception:
            raise HTTPException(status_code=400, detail="JWT verification failed")
        print(jwt_payloads)

    def generate_nonce(self):
        return str(uuid4())

    def fetch_did_document(self, did_url):
        """fetch the did document from endpoint"""
        response = requests.get(did_url + "./well-known/did.json")
        if response.status_code == 200:
            return response.json()

        raise Exception(f"Failed to fetch DID document from {did_url}")

    def verify_jwt(self, token: str, did_url: str, nonce: str) -> dict:
        """Take in the JWT and verify with the did"""
        did_doc = self.fetch_did_document(did_url)
        header = jwt.get_unverified_header(token)
        kid = header["kid"]

        # Find the public key in the DID document
        for vm in did_doc["verificationMethod"]:
            if vm["id"] == kid:
                public_key = vm["publicKeyJwk"]
                # Convert public key into a format usable by PyJWT
                public_key = jwt.algorithms.ECAlgorithm.from_jwk(public_key)

                # Verify the JWT using the public key
                try:
                    return jwt.decode(
                        token,
                        key=public_key,
                        algorithms=["ES256"],
                        options={"verify_exp": False},
                    )
                except Exception as e:
                    raise Exception("JWT verification failed: " + str(e))

        raise Exception("Verification method not found or invalid token.")
