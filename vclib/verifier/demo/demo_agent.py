import os

from vclib.common import vp_auth_request
from vclib.verifier import (
    Verifier,
)


class DemoVerifier(Verifier):
    # this is an example of how a service provider (verifier) might
    # send/request etc. their presentations etc.
    # For now, I will move forward using request URIs for the wallet
    # to fetch the authorization request
    def __init__(self):
        self.current_transactions = {}

        # mapping of req name to req
        self.auth_requests: dict[str, vp_auth_request.AuthorizationRequestObject] = {}
        self.request_history = []
        verify_over_18_pd = vp_auth_request.PresentationDefinition(
            id="verify_over_18",
            input_descriptors=[
                vp_auth_request.InputDescriptor(
                    id="over_18_descriptor",
                    name="Over 18 Verification",
                    purpose="To verify that the individual is over 18 years old",
                    format=[{"uri": "https://example.com/credentials/age"}],
                    constraints=vp_auth_request.Constraints(
                        fields=[
                            vp_auth_request.Field(
                                path=["$.credentialSubject.is_over_18", "$.is_over_18"],
                                filter=vp_auth_request.Filter(
                                    type="string", enum=["true"]
                                ),
                            )
                        ]
                    ),
                )
            ],
        )

        super().__init__(
            presentation_definitions={"verify_over_18": verify_over_18_pd},
            base_url=f"https://verifier-lib:{os.getenv('CS3900_VERIFIER_AGENT_PORT')}",
            diddoc_path=f"{os.path.dirname(os.path.abspath(__file__))}/demo_diddoc.json",
        )

    def __create_request_uri_qr(self, request_type: str):
        pass


verifier = DemoVerifier()

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
                        "path": ["$.credentialSubject.is_over_18", "$.is_over_18" "$"],
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

verify_over_18_pd_object = vp_auth_request.PresentationDefinition(**verify_over_18_pd)

age_request_data = {
    "client_id": "some did",
    "client_id_scheme": "did",
    "client_metadata": {"data": "metadata in this object"},
    "presentation_definition": verify_over_18_pd_object,
    "response_uri": f"https://verifier-lib:{os.getenv('CS3900_VERIFIER_AGENT_PORT')}/cb",
    "response_type": "vp_token",
    "response_mode": "direct_post",
    "nonce": "some nonce",
    # wallet nonce will be set when transaction request is initiated
    # state will be set when transaction is initiated
}

age_request = vp_auth_request.AuthorizationRequestObject(**age_request_data)

verifier.auth_requests["over_18"] = age_request

verifier_server = verifier.get_server()
