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
    def __init__(self, ca_bundle, ca_path):
        super().__init__(ca_bundle, ca_path)
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
            raise HTTPException(
                status_code=404,
                detail="Request type not found"
            )

        # wallet metadata can be used for auth_request to
        # conform to wallet's capabilities
        request = self.auth_requests[request_type]

        transaction_id = f"{uuid.uuid4()}_{int(time.time())}"
        request.state = transaction_id
        request.wallet_nonce = wallet_nonce
        self.current_transactions[transaction_id] = "age_verification"
        response = jsonable_encoder(request, exclude_none = True)
        return JSONResponse(content=response)

    def __create_request_uri_qr(self, request_type: str):
        pass

service_provider = ExampleServiceProvider([], "test")

age_request_pd_data = {
    "id": "age-verification",
    "input_descriptors": [
        {
            "id": "age_descriptor",
            "name": "Age Verification",
            "purpose": "To verify if the individual is over 18 years old",
            "schema": [
                {
                    "uri": "https://example.com/credentials/age"
                }
            ],
            "constraints": {
                "fields": [
                    {
                        "path": ["$.credentialSubject.age"],
                        "filter": {
                            "type": "number",
                            "minimum": 18
                        }
                    }
                ]
            }
        }
    ]
}

age_request_pd = PresentationDefinition(**age_request_pd_data)

age_request_data = {
    "client_id": "some did",
    "client_id_scheme": "did",
    "client_metadata": {"data" : "metadata in this object"},
    "presentation_definition": age_request_pd,
    "redirect_uri": f"http://owner-lib:{os.getenv('CS3900_OWNER_AGENT_PORT')}/cb",
    "response_type": "vp_token",
    "response_mode": "direct_post",
    "nonce": "some nonce",
    # wallet nonce will be set when transaction request is initiated
    # state will be set when transaction is initiated
}

age_request = AuthorizationRequestObject(**age_request_data)

service_provider.auth_requests['age_verification'] = age_request

service_provider_server = service_provider.get_server()
