import os
from typing import override

from jwcrypto.jwk import JWK

from vclib.common import vp_auth_request
from vclib.verifier import Verifier


class CarRental(Verifier):
    # this is an example of how a service provider (verifier) might
    # send/request etc. their presentations etc.
    # For now, I will move forward using request URIs for the wallet
    # to fetch the authorization request
    def __init__(self):
        rental_car_eligibility = vp_auth_request.PresentationDefinition(
            id="eligability_to_rent_car_definition",
            name="Car rental eligibility check",
            purpose="To check if the customer is eligible to rent a car at Cass' Cars",
            input_descriptors=[
                vp_auth_request.InputDescriptor(
                    id="RequestDriversLicense",
                    name="Driver's License Request",
                    constraints=vp_auth_request.Constraints(
                        fields=[
                            vp_auth_request.Field(
                                path=["$.credentialSubject.type", "$.type"],
                                name="Driver's License",
                                filter={"type": "string", "const": "DriversLicense"},
                            ),
                            vp_auth_request.Field(
                                path=["$.credentialSubject.license_no", "$.license_no"],
                                name="License number",
                                filter={"type": "number"},
                            ),
                            vp_auth_request.Field(
                                path=["$.credentialSubject.given_name", "$.given_name"],
                                name="First name",
                                filter={"type": "string"},
                            ),
                            vp_auth_request.Field(
                                path=[
                                    "$.credentialSubject.family_name",
                                    "$.family_name",
                                ],
                                name="Family name",
                                filter={"type": "string"},
                            ),
                            vp_auth_request.Field(
                                path=[
                                    "$.credentialSubject.middle_initial",
                                    "$.middle_initial",
                                ],
                                name="Middle name",
                                filter={"type": "string"},
                                optional=True,
                            ),
                            vp_auth_request.Field(
                                path=[
                                    "$.credentialSubject.date_of_birth",
                                    "$.date_of_birth",
                                ],
                                name="DOB",
                                filter={"type": "number"},
                            ),
                            vp_auth_request.Field(
                                path=["$.credentialSubject.address", "$.address"],
                                name="Address",
                                filter={"type": "string"},
                            ),
                            vp_auth_request.Field(
                                path=[
                                    "$.credentialSubject.license_type",
                                    "$.license_type",
                                ],
                                name="License type",
                                filter={
                                    "type": "string",
                                    "enum": ["Car", "car", "C", "c"],
                                },
                            ),
                        ]
                    ),
                )
            ],
        )
        super().__init__(
            presentation_definitions={"rental_eligibility": rental_car_eligibility},
            base_url=f"https://verifier-lib:{os.getenv('CS3900_CAR_RENTAL_VERIFIER_DEMO_AGENT_PORT')}",
            diddoc_path=f"{os.path.dirname(os.path.abspath(__file__))}/example_diddoc.json",
        )

    @override
    def cb_get_issuer_key(self, iss: str, headers: dict) -> JWK:
        with open(
            f"{os.path.dirname(os.path.abspath(__file__))}/example_issuer_jwk.json"
        ) as f:
            return JWK.from_json(f.read())  # the only JWK we accept


verifier = CarRental()

verifier_server = verifier.get_server()
