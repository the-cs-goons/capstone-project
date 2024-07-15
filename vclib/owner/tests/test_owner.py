from json import loads
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import HTTPException

from vclib.owner import (
    AuthorizationMetadata,
    CredentialOffer,
    DeferredCredential,
    IssuerMetadata,
)
from vclib.owner.examples.default_agent import DefaultWebIdentityOwner

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
OWNER_HOST = "http://localhost"
OWNER_PORT = "8080"
OWNER_URI = f"{OWNER_HOST}:{OWNER_PORT}"


@pytest.fixture()
def identity_owner():
    id_owner = DefaultWebIdentityOwner(
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
    identity_owner: DefaultWebIdentityOwner
    credential1 = await identity_owner.get_credential("example1", refresh=0)
    assert credential1.id == "example1"


@pytest.mark.asyncio
async def test_get_credential_error(identity_owner):
    identity_owner: DefaultWebIdentityOwner
    with pytest.raises(HTTPException):
        await identity_owner.get_credential("bad_id")


def test_get_pending_credentials(identity_owner):
    identity_owner: DefaultWebIdentityOwner
    pending: list[DeferredCredential] = identity_owner.get_deferred_credentials()
    assert len(pending) == 1
    assert pending[0].is_deferred
    assert pending[0].deferred_credential_endpoint == "https://example.com/deferred"
    assert pending[0].transaction_id == "1234567890"


@pytest.mark.asyncio
async def test_get_credentials(identity_owner):
    identity_owner: DefaultWebIdentityOwner
    credentials = await identity_owner.get_credentials()
    assert len(credentials) == 2


@pytest.mark.asyncio
async def test_authorize_issuer_initiated(identity_owner):
    identity_owner: DefaultWebIdentityOwner
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
    identity_owner: DefaultWebIdentityOwner
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
