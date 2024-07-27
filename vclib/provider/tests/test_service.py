import os

import pytest
from fastapi import HTTPException
from jwcrypto.jwk import JWK
from pytest_httpx import HTTPXMock

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
        await service_provider.get_presentation_definition("non-existent definition")


@pytest.mark.asyncio
async def test_fetch_authorization_request_by_json(
    service_provider, presentation_definition
):
    res = await service_provider.fetch_authorization_request(
        presentation_definition=presentation_definition.model_dump_json()
    )
    assert res.presentation_definition == presentation_definition


@pytest.mark.asyncio
async def test_fetch_authorization_request_by_uri(
    httpx_mock: HTTPXMock, service_provider, presentation_definition
):
    httpx_mock.add_response(
        url="https://getdefinition", json=presentation_definition.model_dump_json()
    )
    res = await service_provider.fetch_authorization_request(
        presentation_definition_uri="https://getdefinition"
    )
    assert res.presentation_definition == presentation_definition


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
                    Descriptor(id="licence", format="jwt_vc", path="$.vp_token")
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
                        Descriptor(id="licence", format="jwt_vc", path="$.vp_token")
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
                        Descriptor(id="licence", format="jwt_vc", path="$.vp_token")
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
                        Descriptor(id="licence", format="jwt_vc", path="$.vp_token")
                    ],  # invalid path
                ),
                state="",
            )
        )
