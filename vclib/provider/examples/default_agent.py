import os
import time
import uuid
from typing import override

from fastapi import Form, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from vclib.provider import (
    AuthorizationRequestObject,
    PresentationDefinition,
    ServiceProvider,
)


class ExampleServiceProvider(ServiceProvider):
    # this is an example of how a service provider (verifier) might
    # send/request etc. their presentations etc.
    # For now, I will move forward using request URIs for the wallet
    # to fetch the authorization request
    def __init__(self):
        super().__init__()
        self.current_transactions = {}

        # mapping of req name to req
        self.auth_requests: dict[str, AuthorizationRequestObject] = {}
        self.request_history = []

    @override
    async def fetch_authorization_request(
        self,
        request_type: str,
        wallet_metadata: str = Form(...),
        wallet_nonce: str = Form(...),
    ) -> AuthorizationRequestObject:
        if request_type not in self.auth_requests:
            raise HTTPException(status_code=404, detail="Request type not found")

        # wallet metadata can be used for auth_request to
        # conform to wallet's capabilities
        request = self.auth_requests[request_type]

        transaction_id = f"{uuid.uuid4()}_{int(time.time())}"
        request.state = transaction_id
        request.wallet_nonce = wallet_nonce
        self.current_transactions[transaction_id] = "age_verification"
        response = jsonable_encoder(request, exclude_none=True)
        return JSONResponse(content=response)

    def __create_request_uri_qr(self, request_type: str):
        pass


service_provider = ExampleServiceProvider()

verify_over_18_pd = {
    "id": "verify_over_18",
    "input_descriptors": [
        {
            "id": "over_18_descriptor",
            "name": "Over 18 Verification",
            "purpose": "To verify that the individual is over 18 years old",
            "schema": [{"uri": "https://example.com/credentials/age"}],
            "constraints": {
                "fields": [
                    {
                        "path": ["$.credentialSubject.is_over_18", "$.is_over_18"],
                        "filter": {"type": "string", "enum": ["true"]},
                    }
                ]
            },
        },
        {
            "id": "dob_descriptor",
            "constraints": {
                "fields": [
                    {
                        "path": ["$.credentialSubject.birthdate", "$.birthdate"],
                        "filter": {"type": "string"},
                        "optional": True,
                    }
                ]
            },
            "name": "Birthdate Verification",
            "purpose": "To verify the individual's year of birth",
        },
    ],
}

verify_over_18_pd_object = PresentationDefinition(**verify_over_18_pd)

age_request_data = {
    "client_id": "some did",
    "client_id_scheme": "did",
    "client_metadata": {"data": "metadata in this object"},
    "presentation_definition": verify_over_18_pd_object,
    "response_uri": f"https://provider-lib:{os.getenv('CS3900_SERVICE_AGENT_PORT')}/cb",
    "response_type": "vp_token",
    "response_mode": "direct_post",
    "nonce": "some nonce",
    # wallet nonce will be set when transaction request is initiated
    # state will be set when transaction is initiated
}

age_request = AuthorizationRequestObject(**age_request_data)

service_provider.auth_requests["over_18"] = age_request

service_provider_server = service_provider.get_server()
