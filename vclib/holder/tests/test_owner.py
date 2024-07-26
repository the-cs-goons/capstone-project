from json import loads
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import HTTPException
from pytest_httpx import HTTPXMock

from vclib.holder import (
    AuthorizationMetadata,
    Credential,
    CredentialOffer,
    DeferredCredential,
    IssuerMetadata,
)
from vclib.holder.examples.demo_agent import DemoWebIdentityOwner
from vclib.holder.src.models.field_selection_object import FieldSelectionObject

over_18_mock_auth_response = {
    "vp_token": "eyJhbGciOiAiRVMyNTYiLCAidHlwIjogInZjK3NkLWp3dCJ9.eyJfc2QiOiBbIktJMWx6b21fcVAwVzBKUDdaLVFYVkZrWmV1MElkajJKYTdLcmZPWFdORDQiLCAiUVhOUDk2TkUxZ21kdHdTTE4xeE9pbXZLX20wTVZ2czBBdTJUU1J0ZS1oOCIsICJTSHdLdjhKX09kQU1mS3NtOTJ3eHF0UXZRdFhyVWQwcm9ubkNGZXkySEJvIiwgInpaaFZVdkNodi1JSDBpaWRobFBQVDE1Zk5QbTRGZGRmMlREcG1EUllWUXciXSwgImlhdCI6IDE3MjA5NTIxMTYuMCwgIl9zZF9hbGciOiAic2hhLTI1NiJ9.fFbkA1FLMDT36Y48rxtOfUC76zgWxZAYLQnEWKgi02nubV2b7U7A45b3080USYGRxJ7AYi4GG-3vx1QPM_00lw~WyJaNFdITlBNWkZIM0JOS19haXVKZnBnIiwgImlzX292ZXJfMTgiLCAidHJ1ZSJd~",  # noqa: E501
    "presentation_submission": {
        "id": "f4c91058-d2de-42a2-be63-7946d7743a26",
        "definition_id": "verify_over_18",
        "descriptor_map": [
            {"id": "over_18_descriptor", "format": "vc+sd-jwt", "path": "$"}
        ],
    },
    "state": "ae4adb8b-d1f2-4eb9-baa3-73be30a7aa2a_1721042569",
}

over_18_mock_field_selection = FieldSelectionObject(
    field_requests=[
        {
            "field": {
                "path": ["$.credentialSubject.is_over_18", "$.is_over_18"],
                "filter": {"type": "string", "enum": ["true"]},
            },
            "input_descriptor_id": "over_18_descriptor",
            "approved": True,
        }
    ]
)

over_18_mock_auth_req = {
    "client_id": "some did",
    "client_id_scheme": "did",
    "client_metadata": {"data": "metadata in this object"},
    "presentation_definition": {
        "id": "verify_over_18",
        "input_descriptors": [
            {
                "id": "over_18_descriptor",
                "constraints": {
                    "fields": [
                        {
                            "path": [
                                "$.credentialSubject.is_over_18",
                                "$.is_over_18"
                                ],
                            "filter": {"type": "string"},
                            "optional": False,
                            }
                        ]
                    },
                "name": "Over 18 Verification",
                "purpose": "To verify that the individual is over 18 years old",
                }
            ],
        },
    "response_uri": "https://example.com/cb",
    "response_type": "vp_token",
    "response_mode": "direct_post",
    "nonce": "some nonce",
    "wallet_nonce": "nonce_here",
    "state": "d1d9846b-0f0e-4716-8178-88a6e76f1673_1721045932",
    }

MOCK_STORE = {
    "example1": {
        "id": "example1",
        "issuer_url": "https://example.com",
        "issuer_name": "Example Issuer",
        "credential_configuration_id": "Passport",
        "is_deferred": False,
        "c_type": "openid_credential",
        "raw_sdjwtvc": "eyJuYW1lIjoiTWFjayBDaGVlc2VNYW4iLCJkb2IiOiIwMS8wMS8wMSIsImV4cGlyeSI6IjEyLzEyLzI1In0=",  # noqa: E501
        "received_at": "2024-07-15T02:54:13.634808+00:00",
        },
    "example2": {
        "id": "example2",
        "issuer_url": "https://example.com",
        "issuer_name": "Example Issuer",
        "credential_configuration_id": "Driver's Licence",
        "is_deferred": True,
        "c_type": "openid_credential",
        "transaction_id": "1234567890",
        "deferred_credential_endpoint": "https://example.com/deferred",
        "last_request": "2024-07-15T02:54:13.634808+00:00",
        "access_token": {
            "access_token": "exampletoken",
            "token_type": "bearer",
            "expires_in": 99999999999,
            },
        },
    }

EXAMPLE_ISSUER = "https://example.com"
OWNER_HOST = "https://localhost"
OWNER_PORT = "8080"
OWNER_URI = f"{OWNER_HOST}:{OWNER_PORT}"


###################
### TESTING VPs ###
###################
@pytest.mark.asyncio()
async def test_vp_flow(httpx_mock: HTTPXMock, identity_owner):
    httpx_mock.add_response(
        url="https://example.com/request/over_18", json=over_18_mock_auth_req
    )
    identity_owner: DemoWebIdentityOwner
    cred = Credential(
        id="yalo",
        raw_sdjwtvc="eyJhbGciOiAiRVMyNTYiLCAidHlwIjogInZjK3NkLWp3dCJ9.eyJfc2QiOiBbIktJMWx6b21fcVAwVzBKUDdaLVFYVkZrWmV1MElkajJKYTdLcmZPWFdORDQiLCAiUVhOUDk2TkUxZ21kdHdTTE4xeE9pbXZLX20wTVZ2czBBdTJUU1J0ZS1oOCIsICJTSHdLdjhKX09kQU1mS3NtOTJ3eHF0UXZRdFhyVWQwcm9ubkNGZXkySEJvIiwgInpaaFZVdkNodi1JSDBpaWRobFBQVDE1Zk5QbTRGZGRmMlREcG1EUllWUXciXSwgImlhdCI6IDE3MjA5NTIxMTYuMCwgIl9zZF9hbGciOiAic2hhLTI1NiJ9.fFbkA1FLMDT36Y48rxtOfUC76zgWxZAYLQnEWKgi02nubV2b7U7A45b3080USYGRxJ7AYi4GG-3vx1QPM_00lw~WyJNN01oQkhpVk5JYjBxMGFQS0ZkVnpBIiwgImdpdmVuX25hbWUiLCAiQSJd~WyJ1UGJaQUFHS0VjcGY2UzBHT3FMRFZ3IiwgImZhbWlseV9uYW1lIiwgIkIiXQ~WyJZQU12TWZnVW9OZW5HNm4xREY1bHlBIiwgImJpcnRoZGF0ZSIsIDIwMDBd~WyJaNFdITlBNWkZIM0JOS19haXVKZnBnIiwgImlzX292ZXJfMTgiLCAidHJ1ZSJd~",
        issuer_url="https://example.com",
        credential_configuration_id="sd+jwt_vc",
        is_deferred=False,
        received_at="12345",
        c_type="sd_jwt",
    )
    identity_owner.credentials["yalo"] = cred

    resp = await identity_owner.get_auth_request(
        "https://example.com/request/over_18", "some did", "did", "post"
    )

    assert resp == over_18_mock_auth_req

    # TODO: make this return a redirect_uri
    httpx_mock.add_response(
        url="https://example.com/cb", json={"status": "OK"}, method="post"
    )

    resp = await identity_owner.present_selection(over_18_mock_field_selection)

    assert resp == {"status": "OK"}


@pytest.fixture()
def identity_owner():
    id_owner = DemoWebIdentityOwner(
        [f"{OWNER_URI}/add"],
        f"{OWNER_URI}/offer",
        mock_data=MOCK_STORE,
        mock_uri=OWNER_URI,
    )

    id_owner.issuer_metadata_store[EXAMPLE_ISSUER] = IssuerMetadata(
        credential_issuer=EXAMPLE_ISSUER,
        credential_configurations_supported={"ExampleCredential": {}},
        credential_endpoint=EXAMPLE_ISSUER + "/get_credential",
    )
    id_owner.auth_metadata_store[EXAMPLE_ISSUER] = AuthorizationMetadata(
        issuer=EXAMPLE_ISSUER,
        authorization_endpoint=EXAMPLE_ISSUER + "/oauth2/authorize",
        registration_endpoint=EXAMPLE_ISSUER + "/oauth2/register",
        token_endpoint=EXAMPLE_ISSUER + "/oauth2/token",
        response_types_supported=["code"],
        grant_types_supported=["authorization_code"],
        authorization_details_types_supported=["openid_credential"],
        **{"pre-authorized_grant_anonymous_access_supported": False},
    )
    return id_owner


@pytest.mark.asyncio
async def test_get_credential(identity_owner):
    identity_owner: DemoWebIdentityOwner
    credential1 = await identity_owner.get_credential("example1", refresh=0)
    assert credential1.id == "example1"


@pytest.mark.asyncio
async def test_get_credential_error(identity_owner):
    identity_owner: DemoWebIdentityOwner
    with pytest.raises(HTTPException):
        await identity_owner.get_credential("bad_id")


def test_get_pending_credentials(identity_owner):
    identity_owner: DemoWebIdentityOwner
    pending: list[DeferredCredential] = identity_owner.get_deferred_credentials()
    assert len(pending) == 1
    assert pending[0].is_deferred
    assert pending[0].deferred_credential_endpoint == "https://example.com/deferred"
    assert pending[0].transaction_id == "1234567890"


@pytest.mark.asyncio
async def test_get_credentials(identity_owner):
    identity_owner: DemoWebIdentityOwner
    credentials = await identity_owner.get_credentials()
    assert len(credentials) == 2


@pytest.mark.asyncio
async def test_authorize_issuer_initiated(identity_owner):
    identity_owner: DemoWebIdentityOwner
    id = "Passport"

    select = CredentialOffer.model_validate(
        {
            "credential_issuer": "https://example.com",
            "credential_configuration_ids": [id],
        }
    )

    redirect_url = await identity_owner.get_auth_redirect_from_offer(id, select)

    parsed_url = urlparse(redirect_url)
    assert parsed_url.scheme == "https"
    assert parsed_url.hostname == "example.com"
    assert parsed_url.path == "/oauth2/authorize"
    query_params = parse_qs(parsed_url.query)

    assert query_params["response_type"][0] == "code"
    assert query_params["client_id"][0] == "example_client_id"
    assert query_params["redirect_uri"][0] == OWNER_URI + "/add"
    details = loads(query_params["authorization_details"][0])
    assert details[0]["credential_configuration_id"] == id
    assert query_params["state"][0] in identity_owner.oauth_clients


@pytest.mark.asyncio
async def test_authorize_wallet_initiated(identity_owner):
    identity_owner: DemoWebIdentityOwner
    id = "Passport"

    redirect_url = await identity_owner.get_auth_redirect(id, "https://example.com")

    parsed_url = urlparse(redirect_url)
    assert parsed_url.scheme == "https"
    assert parsed_url.hostname == "example.com"
    assert parsed_url.path == "/oauth2/authorize"
    query_params = parse_qs(parsed_url.query)

    assert query_params["response_type"][0] == "code"
    assert query_params["client_id"][0] == "example_client_id"
    assert query_params["redirect_uri"][0] == OWNER_URI + "/add"
    details = loads(query_params["authorization_details"][0])
    assert details[0]["credential_configuration_id"] == id
    assert query_params["state"][0] in identity_owner.oauth_clients
