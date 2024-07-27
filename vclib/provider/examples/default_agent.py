import os
import time
import uuid
from typing import override

from fastapi import Form, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from jwcrypto.jwk import JWK

from vclib.provider import (
    AuthorizationRequestObject,
    PresentationDefinition,
    InputDescriptor,
    Constraints,
    Field,
    Filter,
    ServiceProvider,
)


class ExampleServiceProvider(ServiceProvider):
    # this is an example of how a service provider (verifier) might
    # send/request etc. their presentations etc.
    # For now, I will move forward using request URIs for the wallet
    # to fetch the authorization request
    def __init__(self):
        verify_over_18_pd = PresentationDefinition(
            id="verify_over_18",
            input_descriptors=[
                InputDescriptor(
                    id="over_18_descriptor",
                    name="Over 18 Verification",
                    purpose="To verify that the individual is over 18 years old",
                    format=[{"uri": "https://example.com/credentials/age"}],
                    constraints=Constraints(
                        fields=[Field(
                            path=["$.credentialSubject.is_over_18", "$.is_over_18"],
                            filter=Filter(type="string", enum=["true"])
                        )]
                    )
                )
            ]
        )

        super().__init__(
            presentation_definitions={"verify_over_18": verify_over_18_pd},
            diddoc_path=f"{os.path.dirname(os.path.abspath(__file__))}/example_diddoc.json"
        )
    #     self.current_transactions = {}

    #     # mapping of req name to req
    #     self.auth_requests: dict[str, AuthorizationRequestObject] = {}
    #     self.request_history = []

    @override
    def cb_get_issuer_key(self, iss: str, headers: dict) -> JWK:
        with open(f"{os.path.dirname(os.path.abspath(__file__))}/example_issuer_jwk.json", "r") as f:
            return JWK.from_json(f.read()) # the only JWK we accept

    @override
    def validate_disclosed_fields(self, presentation_definition: PresentationDefinition, disclosed_fields: dict) -> bool:
        if disclosed_fields.get("is_over_18") != "true":
            raise Exception("Credential owner not over 18")

service_provider = ExampleServiceProvider()

# age_request_data = {
#     "client_id": "some did",
#     "client_id_scheme": "did",
#     "client_metadata": {"data": "metadata in this object"},
#     "presentation_definition": verify_over_18_pd_object,
#     "response_uri": f"https://provider-lib:{os.getenv('CS3900_SERVICE_AGENT_PORT')}/cb",
#     "response_type": "vp_token",
#     "response_mode": "direct_post",
#     "nonce": "some nonce",
#     # wallet nonce will be set when transaction request is initiated
#     # state will be set when transaction is initiated
# }

# age_request = AuthorizationRequestObject(**age_request_data)

# service_provider.auth_requests["over_18"] = age_request

service_provider_server = service_provider.get_server()
