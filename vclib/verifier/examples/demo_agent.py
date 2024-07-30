import os
from typing import override

from jwcrypto.jwk import JWK

from vclib.common import vp_auth_request
from vclib.verifier import Verifier


class DemoVerifier(Verifier):
    # this is an example of how a service provider (verifier) might
    # send/request etc. their presentations etc.
    # For now, I will move forward using request URIs for the wallet
    # to fetch the authorization request
    def __init__(self):
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
                                path=["$.credentialSubject.is_over_18",
                                      "$.is_over_18"],
                                filter={"type": "boolean", "const": True}
                            )
                        ]
                    ),
                ),
                vp_auth_request.InputDescriptor(
                    id="dob_descriptor",
                    name="Birthdate Verification",
                    purpose="To verify the individual's year of birth",
                    constraints=vp_auth_request.Constraints(
                        fields=[
                            vp_auth_request.Field(
                                path=["$.credentialSubject.birthdate", "$.birthdate"],
                                filter={"type": "number"},
                                optional=True,
                            )
                        ]
                    ),
                ),
            ],
        )

        super().__init__(
            presentation_definitions={"verify_over_18": verify_over_18_pd},
            base_url=f"https://verifier-lib:{os.getenv('CS3900_VERIFIER_AGENT_PORT')}",
            diddoc_path=f"{os.path.dirname(os.path.abspath(__file__))}/example_diddoc.json",
        )

    @override
    def cb_get_issuer_key(self, iss: str, headers: dict) -> JWK:
        with open(
            f"{os.path.dirname(os.path.abspath(__file__))}/example_issuer_jwk.json"
        ) as f:
            return JWK.from_json(f.read())  # the only JWK we accept

verifier = DemoVerifier()

verifier_server = verifier.get_server()
