import os

import pytest
from fastapi import HTTPException
from jwcrypto.jwk import JWK

from vclib.provider import (
    Constraints,
    Field,
    Filter,
    InputDescriptor,
    PresentationDefinition,
    ServiceProvider,
)
from vclib.provider.src.models.authorization_response_object import (
    AuthorizationResponseObject,
)
from vclib.provider.src.models.presentation_submission import (
    Descriptor,
    PresentationSubmission,
)


@pytest.fixture
def presentation_definition() -> PresentationDefinition:
    return PresentationDefinition(
        id="verify_over_18",
        input_descriptors=[
            InputDescriptor(
                id="over_18_descriptor",
                name="Over 18 Verification",
                purpose="To verify that the individual is over 18 years old",
                format=[{"uri": "https://example.com/credentials/age"}],
                constraints=Constraints(
                    fields=[
                        Field(
                            path=["$.credentialSubject.is_over_18", "$.is_over_18"],
                            filter=Filter(type="string", enum=["true"]),
                        )
                    ]
                ),
            )
        ],
    )


@pytest.fixture
def service_provider(presentation_definition) -> ServiceProvider:
    class ExampleServiceProvider(ServiceProvider):
        def cb_get_issuer_key(self, iss: str, headers: dict) -> JWK:
            with open(
                f"{os.path.dirname(os.path.abspath(__file__))}/test_issuer_jwk.json"
            ) as f:
                return JWK.from_json(f.read())  # the only JWK we accept

    return ExampleServiceProvider(
        presentation_definitions={presentation_definition.id: presentation_definition},
        diddoc_path=f"{os.path.dirname(os.path.abspath(__file__))}/test_diddoc.json",
    )


@pytest.fixture
def vp_token() -> str:
    with open(f"{os.path.dirname(os.path.abspath(__file__))}/test_vp_token.txt") as f:
        return f.read()


@pytest.mark.asyncio
async def test_get_valid_presentation_definition(
    service_provider, presentation_definition
):
    assert (
        await service_provider.get_presentation_definition(presentation_definition.id)
        == presentation_definition
    )


@pytest.mark.asyncio
async def test_get_invalid_presentation_definition(service_provider):
    with pytest.raises(HTTPException):
        await service_provider.get_presentation_definition("invalid_definition_id")


@pytest.mark.asyncio
async def test_fetch_valid_authorization_request(
    service_provider, presentation_definition
):
    res = await service_provider.fetch_authorization_request(
        ref=presentation_definition.id
    )
    assert res.presentation_definition == presentation_definition


@pytest.mark.asyncio
async def test_fetch_invalid_authorization_request(
    service_provider, presentation_definition
):
    with pytest.raises(HTTPException):
        await service_provider.fetch_authorization_request(ref="invalid_definition_id")


@pytest.mark.asyncio
async def test_parse_valid_authorization_response(
    service_provider, presentation_definition, vp_token
):
    res = await service_provider.parse_authorization_response(
        auth_response=AuthorizationResponseObject(
            vp_token=vp_token,
            presentation_submission=PresentationSubmission(
                id="submission_id",
                definition_id=presentation_definition.id,
                descriptor_map=[
                    Descriptor(id="licence", format="jwt_vc", path="$")
                ],
            ),
            state="",
        )
    )
    assert res == {"status": "OK"}


@pytest.mark.asyncio
async def test_parse_authorization_response_with_invalid_jwt(
    service_provider, presentation_definition, vp_token
):
    with pytest.raises(HTTPException):
        await service_provider.parse_authorization_response(
            auth_response=AuthorizationResponseObject(
                vp_token=vp_token.capitalize(),  # invalid jwt
                presentation_submission=PresentationSubmission(
                    id="random_id",
                    definition_id=presentation_definition.id,
                    descriptor_map=[
                        Descriptor(id="licence", format="jwt_vc", path="$")
                    ],
                ),
                state="",
            )
        )


@pytest.mark.asyncio
async def test_parse_authorization_response_with_invalid_id(
    service_provider, presentation_definition, vp_token
):
    with pytest.raises(HTTPException):
        await service_provider.parse_authorization_response(
            auth_response=AuthorizationResponseObject(
                vp_token=vp_token,
                presentation_submission=PresentationSubmission(
                    id="random_id",
                    definition_id="random_id",  # invalid id
                    descriptor_map=[
                        Descriptor(id="licence", format="jwt_vc", path="$")
                    ],
                ),
                state="",
            )
        )


@pytest.mark.asyncio
async def test_parse_authorization_response_with_invalid_path(
    service_provider, presentation_definition, vp_token
):
    with pytest.raises(HTTPException):
        await service_provider.parse_authorization_response(
            auth_response=AuthorizationResponseObject(
                vp_token=vp_token,
                presentation_submission=PresentationSubmission(
                    id="random_id",
                    definition_id="random_id",
                    descriptor_map=[
                        Descriptor(id="licence", format="jwt_vc", path="$")
                    ],  # invalid path
                ),
                state="",
            )
        )
