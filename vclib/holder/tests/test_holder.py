from datetime import UTC, datetime
from json import loads
from random import choice
from string import ascii_letters
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import HTTPException
from pytest_httpx import HTTPXMock

from vclib.common.src.data_transfer_objects.vp_auth_request import (
    AuthorizationRequestObject,
)
from vclib.holder import (
    AuthorizationMetadata,
    Credential,
    CredentialOffer,
    DeferredCredential,
    IssuerMetadata,
)
from vclib.holder.examples.demo_agent import DemoWebHolder
from vclib.holder.src.models.credentials import BaseCredential
from vclib.holder.src.models.field_selection_object import FieldSelectionObject
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

over_18_mock_field_selection = FieldSelectionObject(
    field_requests=[
        {
            "field": {
                "path": ["$.credentialSubject.is_over_18", "$.is_over_18"],
                "filter": {"type": "boolean", "const": True},
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
                            "filter": {"type": "boolean", "const": True},
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
    delete_1 = Credential.model_validate(MOCK_CREDENTIALS["example1"])
    delete_1.id = "delete_1"
    vp_flow_test = Credential(
        id="vp_flow_test",
        raw_sdjwtvc="eyJhbGciOiAiRVMyNTYiLCAidHlwIjogInZjK3NkLWp3dCJ9.eyJfc2QiOiBbIjFlZ0VpSl9Ga1pud0hwWnE4cklYd1ZLME5PVS1GNldTNVBxaVpsTm1tUkkiLCAiR3A1THpzOURES3pVcmJLT2dkMnJncEZNTGIyQzg5OHpiamtaeXdoeGtQUSIsICJKY1JPRHNGMGlaY1UybFVEWFB2M0pBWGFSZmhlNUNrREZNZkZuQXdtSzI0IiwgIlBiTUQ3ckZtWmJoMzhOREkwN3NzMGlXLUtGUWdvbmlwZzZlR1JkeGl5QTQiLCAiVklpYWo4Ukg0SUZKVE5FMXVibm9ReEtuc21Db3hkd3VOa2kxV1NmOTBxWSIsICJmM1NIWVhWc0tVcDRqeFZaS282bWZaTGhSV3NXTU52M0phVUtSN1ktSDBVIl0sICJpc3MiOiAiaHR0cHM6Ly9pc3N1ZXItbGliOjgwODIiLCAiaWF0IjogMTcyMjMyMDk4Mi4wLCAiX3NkX2FsZyI6ICJzaGEtMjU2In0.LCF0HaHb8rInRtTrO_S9dsJ6zOWsb5AMyY-Ue7LvG2Cjv-laD4he2eK1bhiEAlJeKpRdACvK7bOOl3E8BUI52A~WyJrUFdNT2ItNHkwY25fM0xvSTF0ckF3IiwgImdpdmVuX25hbWUiLCAiQUJDIl0~WyJxNGF2MnNFVldrM1NKc3FKLXFGWjZRIiwgImZhbWlseV9uYW1lIiwgIkQiXQ~WyJMVnBKUjFiRXBnejNlT0E2bk5YUS1BIiwgImNvdW50cnkiLCAiQXVzdHJhbGlhIl0~WyJ2dU40SU9YdDRPRmVmU19ZbjA2NGRnIiwgImFkZHJlc3MiLCB7Il9zZCI6IFsiNFZxZ3dmd2NKUGxQLTJNWXN6cTlGSFRjQ2l2VXpMWVI3Qmx3M1F1ZnFUQSJdfV0~WyJfWlBQakVYUmQwYjU0cGpRQlQ1Ri13IiwgIm5hdGlvbmFsaXRpZXMiLCBbIkFVIl1d~WyJabnRhclNRc2hBYW9MZTJPTmhGOWhBIiwgImJpcnRoZGF0ZSIsIDIwMDFd~WyIyOHBDdE5SN1k1OWI5WF85eWozUUhBIiwgImlzX292ZXJfMTgiLCB0cnVlXQ~",
        issuer_url="https://example.com",
        credential_configuration_id="sd+jwt_vc",
        is_deferred=False,
        received_at=datetime.now(tz=UTC).isoformat(),
        c_type="sd_jwt",
    )
    return [
        Credential.model_validate(MOCK_CREDENTIALS["example1"]),
        DeferredCredential.model_validate(MOCK_CREDENTIALS["example2"]),
        delete_1,
        vp_flow_test,
    ]


EXAMPLE_ISSUER = "https://example.com"
OWNER_HOST = "https://localhost"
OWNER_PORT = "8080"
OWNER_URI = f"{OWNER_HOST}:{OWNER_PORT}"


@pytest.fixture(scope="module")
def identity_owner(tmp_path_factory, example_credentials):
    tmpdir_name = "".join(choice(ascii_letters) for i in range(10))
    id_owner = DemoWebHolder(
        [f"{OWNER_URI}/add"],
        f"{OWNER_URI}/offer",
        LocalStorageProvider(storage_dir_path=tmp_path_factory.mktemp(tmpdir_name)),
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
    identity_owner: DemoWebHolder

    resp = await identity_owner.get_auth_request(
        "https://example.com/request/verify_over_18",
        authorization=auth_header,
    )
    over_18_mock_auth_req["nonce"] = resp.nonce  # we can't know nonce beforehand

    assert resp == AuthorizationRequestObject(**over_18_mock_auth_req)

    # TODO: make this return a redirect_uri
    httpx_mock.add_response(
        url="https://example.com/cb", json={"status": "OK"}, method="post"
    )

    resp = await identity_owner.present_selection(
        over_18_mock_field_selection, authorization=auth_header
    )

    assert resp == "success"


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
    identity_owner: DemoWebHolder
    credentials = await identity_owner.get_credentials(authorization=auth_header)
    cred_ids = [c.id for c in credentials]
    assert "example1" in cred_ids
    assert "example2" in cred_ids
    assert "vp_flow_test" in cred_ids


@pytest.mark.asyncio
async def test_authorize_issuer_initiated(identity_owner):
    identity_owner: DemoWebHolder
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
    identity_owner: DemoWebHolder
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


@pytest.mark.asyncio
async def test_delete_credential_fail(identity_owner, auth_header):
    identity_owner: DemoWebHolder
    with pytest.raises(Exception):
        await identity_owner.delete_credential("bad_id", authorization=auth_header)


@pytest.mark.asyncio
async def test_async_delete_credentials(identity_owner, auth_header):
    identity_owner: DemoWebHolder
    cred = await identity_owner.get_credential(
        "delete_1", authorization=auth_header, refresh=0
    )
    assert isinstance(cred, BaseCredential)
    await identity_owner.delete_credential("delete_1", authorization=auth_header)

    with pytest.raises(Exception):
        await identity_owner.get_credential("delete_1", authorization=auth_header)
    with pytest.raises(Exception):
        await identity_owner.delete_credential("delete_1", authorization=auth_header)
