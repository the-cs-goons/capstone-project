from uuid import uuid4

import jwt
import requests
from fastapi import FastAPI, Form

from .models.authorization_request_object import AuthorizationRequestObject


class ServiceProvider:
    def __init__(
        self,
    ):
        """Initialise the service provider with a list of CA bundle"""
        self.used_nonces = set()

    def get_server(self) -> FastAPI:
        router = FastAPI()
        router.post("/request/{request_type}")(self.fetch_authorization_request)
        router.post("/cb")(self.parse_authorization_response)
        return router

    async def parse_authorization_response(
        self,
        vp_token: str | list[str] = Form(...),
        presentation_submission=Form(...),
        state=Form(...),
    ):
        # TODO: verify the auth_response and tell the wallet whether or not
        # it has been successful or not
        return {
            "vp_token": vp_token,
            "presentation_submission": presentation_submission,
            "state": state,
        }

    # fetches and sends back the requested request object
    # accessed through request_uri embedded in QR code
    # should be overridden to fit verifier's needs
    async def fetch_authorization_request(
        self,
        request_type: str,
        wallet_metadata: str = Form(...),
        wallet_nonce: str = Form(...),
    ) -> AuthorizationRequestObject:
        pass

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
