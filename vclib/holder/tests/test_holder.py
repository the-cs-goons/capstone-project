from datetime import UTC, datetime
from json import loads
from random import choice
from string import ascii_letters
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import HTTPException
from pytest_httpx import HTTPXMock

from vclib.common import credentials, oauth2, oid4vci, vp_auth_request
from vclib.holder.demo.demo_agent import DemoWebHolder
from vclib.holder.src.storage.local_storage_provider import LocalStorageProvider

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

over_18_mock_field_selection = vp_auth_request.FieldSelectionObject(
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
                            "path": ["$.credentialSubject.is_over_18", "$.is_over_18"],
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
    "nonce": "unique nonce",
    "wallet_nonce": None,
    "state": "d1d9846b-0f0e-4716-8178-88a6e76f1673_1721045932",
}

MOCK_CREDENTIALS = {
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


@pytest.fixture(scope="module")
def example_credentials():
    delete_1 = credentials.Credential.model_validate(MOCK_CREDENTIALS["example1"])
    delete_1.id = "delete_1"
    vp_flow_test = credentials.Credential(
        id="vp_flow_test",
        raw_sdjwtvc="eyJhbGciOiAiRVMyNTYiLCAidHlwIjogInZjK3NkLWp3dCJ9.eyJfc2QiOiBbIktJMWx6b21fcVAwVzBKUDdaLVFYVkZrWmV1MElkajJKYTdLcmZPWFdORDQiLCAiUVhOUDk2TkUxZ21kdHdTTE4xeE9pbXZLX20wTVZ2czBBdTJUU1J0ZS1oOCIsICJTSHdLdjhKX09kQU1mS3NtOTJ3eHF0UXZRdFhyVWQwcm9ubkNGZXkySEJvIiwgInpaaFZVdkNodi1JSDBpaWRobFBQVDE1Zk5QbTRGZGRmMlREcG1EUllWUXciXSwgImlhdCI6IDE3MjA5NTIxMTYuMCwgIl9zZF9hbGciOiAic2hhLTI1NiJ9.fFbkA1FLMDT36Y48rxtOfUC76zgWxZAYLQnEWKgi02nubV2b7U7A45b3080USYGRxJ7AYi4GG-3vx1QPM_00lw~WyJNN01oQkhpVk5JYjBxMGFQS0ZkVnpBIiwgImdpdmVuX25hbWUiLCAiQSJd~WyJ1UGJaQUFHS0VjcGY2UzBHT3FMRFZ3IiwgImZhbWlseV9uYW1lIiwgIkIiXQ~WyJZQU12TWZnVW9OZW5HNm4xREY1bHlBIiwgImJpcnRoZGF0ZSIsIDIwMDBd~WyJaNFdITlBNWkZIM0JOS19haXVKZnBnIiwgImlzX292ZXJfMTgiLCAidHJ1ZSJd~",
        issuer_url="https://example.com",
        credential_configuration_id="sd+jwt_vc",
        is_deferred=False,
        received_at=datetime.now(tz=UTC).isoformat(),
        c_type="sd_jwt",
    )
    return [
        credentials.Credential.model_validate(MOCK_CREDENTIALS["example1"]),
        credentials.DeferredCredential.model_validate(MOCK_CREDENTIALS["example2"]),
        delete_1,
        vp_flow_test,
    ]


EXAMPLE_ISSUER = "https://example.com"
OWNER_HOST = "https://localhost"
OWNER_PORT = "8080"
OWNER_URI = f"{OWNER_HOST}:{OWNER_PORT}"


@pytest.fixture(scope="module")
def identity_owner(tmp_path_factory, example_credentials):
    tmpdir_name = "".join(choice(ascii_letters) for _ in range(10))
    id_owner = DemoWebHolder(
        [f"{OWNER_URI}/add"],
        f"{OWNER_URI}/offer",
        LocalStorageProvider(storage_dir_path=tmp_path_factory.mktemp(tmpdir_name)),
        mock_uri=OWNER_URI,
    )

    id_owner.issuer_metadata_store[EXAMPLE_ISSUER] = oid4vci.IssuerOpenID4VCIMetadata(
        credential_issuer=EXAMPLE_ISSUER,
        credential_configurations_supported={
            "ExampleCredential": oid4vci.CredentialConfigurationsObject.model_validate(
                {"format": "vc+sd-jwt"}
            )
        },
        credential_endpoint=EXAMPLE_ISSUER + "/get_credential",
    )
    id_owner.auth_metadata_store[EXAMPLE_ISSUER] = oauth2.IssuerOAuth2ServerMetadata(
        issuer=EXAMPLE_ISSUER,
        authorization_endpoint=EXAMPLE_ISSUER + "/oauth2/authorize",
        registration_endpoint=EXAMPLE_ISSUER + "/oauth2/register",
        token_endpoint=EXAMPLE_ISSUER + "/oauth2/token",
        response_types_supported=["code"],
        grant_types_supported=["authorization_code"],
        authorization_details_types_supported=["openid_credential"],
        pre_authorized_supported=False,
    )
    print(id_owner)
    id_owner.register("test_holder", "test_holder")
    id_owner.store.add_many(example_credentials)

    return id_owner


@pytest.fixture(scope="module")
def auth_header(identity_owner):
    store: LocalStorageProvider = identity_owner.store
    uname = store.get_active_user_name()
    return f"Bearer {identity_owner._generate_jwt({"username": uname})}"


###################
### TESTING VPs ###
###################
@pytest.mark.asyncio()
async def test_vp_flow(httpx_mock: HTTPXMock, identity_owner, auth_header):
    httpx_mock.add_response(
        url="https://example.com/request/verify_over_18", json=over_18_mock_auth_req
    )

    resp = await identity_owner.get_auth_request(
        "https://example.com/request/verify_over_18",
        "some did",
        "did",
        "post",
        authorization=auth_header,
    )
    over_18_mock_auth_req["nonce"] = resp.nonce  # we can't know nonce beforehand

    assert resp == vp_auth_request.AuthorizationRequestObject(**over_18_mock_auth_req)

    # TODO: make this return a redirect_uri
    httpx_mock.add_response(
        url="https://example.com/cb", json={"status": "OK"}, method="post"
    )

    resp = await identity_owner.present_selection(
        over_18_mock_field_selection, authorization=auth_header
    )

    assert resp == {"status": "OK"}


@pytest.mark.asyncio
async def test_get_credential(identity_owner, auth_header):
    credential1 = await identity_owner.get_credential(
        "example1", authorization=auth_header, refresh=0
    )
    assert credential1.id == "example1"


@pytest.mark.asyncio
async def test_get_credential_error(identity_owner, auth_header):
    with pytest.raises(HTTPException):
        await identity_owner.get_credential("bad_id", authorization=auth_header)


@pytest.mark.asyncio
async def test_get_credentials(identity_owner, auth_header):
    credentials = await identity_owner.get_credentials(authorization=auth_header)
    cred_ids = [c.id for c in credentials]
    assert "example1" in cred_ids
    assert "example2" in cred_ids
    assert "vp_flow_test" in cred_ids


@pytest.mark.asyncio
async def test_authorize_issuer_initiated(identity_owner):
    cred_id = "Passport"

    select = oid4vci.CredentialOfferObject.model_validate(
        {
            "credential_issuer": "https://example.com",
            "credential_configuration_ids": [cred_id],
        }
    )

    redirect_url = await identity_owner.get_auth_redirect_from_offer(cred_id, select)

    parsed_url = urlparse(redirect_url)
    assert parsed_url.scheme == "https"
    assert parsed_url.hostname == "example.com"
    assert parsed_url.path == "/oauth2/authorize"
    query_params = parse_qs(parsed_url.query)

    assert query_params["response_type"][0] == "code"
    assert query_params["client_id"][0] == "example_client_id"
    assert query_params["redirect_uri"][0] == OWNER_URI + "/add"
    details = loads(query_params["authorization_details"][0])
    assert details[0]["credential_configuration_id"] == cred_id
    assert query_params["state"][0] in identity_owner.oauth_clients


@pytest.mark.asyncio
async def test_authorize_wallet_initiated(identity_owner):
    cred_id = "Passport"

    redirect_url = await identity_owner.get_auth_redirect(
        cred_id, "https://example.com"
    )

    parsed_url = urlparse(redirect_url)
    assert parsed_url.scheme == "https"
    assert parsed_url.hostname == "example.com"
    assert parsed_url.path == "/oauth2/authorize"
    query_params = parse_qs(parsed_url.query)

    assert query_params["response_type"][0] == "code"
    assert query_params["client_id"][0] == "example_client_id"
    assert query_params["redirect_uri"][0] == OWNER_URI + "/add"
    details = loads(query_params["authorization_details"][0])
    assert details[0]["credential_configuration_id"] == cred_id
    assert query_params["state"][0] in identity_owner.oauth_clients


@pytest.mark.asyncio
async def test_delete_credential_fail(identity_owner, auth_header):
    with pytest.raises(Exception):
        await identity_owner.delete_credential("bad_id", authorization=auth_header)


@pytest.mark.asyncio
async def test_async_delete_credentials(identity_owner, auth_header):
    cred = await identity_owner.get_credential(
        "delete_1", authorization=auth_header, refresh=0
    )
    assert isinstance(cred, credentials.BaseCredential)
    await identity_owner.delete_credential("delete_1", authorization=auth_header)

    with pytest.raises(Exception):
        await identity_owner.get_credential("delete_1", authorization=auth_header)
    with pytest.raises(Exception):
        await identity_owner.delete_credential("delete_1", authorization=auth_header)
