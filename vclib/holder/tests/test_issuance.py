import pytest
from fastapi import HTTPException

# from fastapi import HTTPException
from pytest_httpx import HTTPXMock

from vclib.holder import (
    AuthorizationMetadata,
    CredentialOffer,
    IssuerMetadata,
)
from vclib.holder.src.models.credential_offer import (
    # CredentialOffer,
    CredentialSelection,
)
from vclib.holder.src.storage.local_storage_provider import LocalStorageProvider
from vclib.holder.src.web_holder import WebHolder

EXAMPLE_ISSUER = "https://example.com"
OWNER_HOST = "https://localhost"
OWNER_PORT = "8080"
OWNER_URI = f"{OWNER_HOST}:{OWNER_PORT}"

@pytest.fixture
def holder(tmp_path_factory):
    holder = WebHolder(
        [f"{OWNER_URI}/add"],
        f"{OWNER_URI}/offer",
        LocalStorageProvider(storage_dir_path=tmp_path_factory.mktemp("test_storage"))
    )

    holder.issuer_metadata_store[EXAMPLE_ISSUER] = IssuerMetadata(
        credential_issuer=EXAMPLE_ISSUER,
        credential_configurations_supported={"ExampleCredential": {}},
        credential_endpoint=EXAMPLE_ISSUER + "/get_credential",
    )
    holder.auth_metadata_store[EXAMPLE_ISSUER] = AuthorizationMetadata(
        issuer=EXAMPLE_ISSUER,
        authorization_endpoint=EXAMPLE_ISSUER + "/oauth2/authorize",
        registration_endpoint=EXAMPLE_ISSUER + "/oauth2/register",
        token_endpoint=EXAMPLE_ISSUER + "/oauth2/token",
        response_types_supported=["code"],
        grant_types_supported=["authorization_code"],
        authorization_details_types_supported=["openid_credential"],
        **{"pre-authorized_grant_anonymous_access_supported": False},
    )
    return holder

@pytest.fixture
def auth_header(holder: WebHolder):
    holder.store.register("asdf", "1234567890")
    return f"Bearer {holder._generate_jwt({"username": "asdf"})}"

### Tests
@pytest.mark.asyncio()
async def test0_request_authorization_with_offer(
        httpx_mock: HTTPXMock, holder: WebHolder, auth_header: str):

    httpx_mock.add_response(
        url="https://example.com/oauth2/register",
        json={"client_id": "example",
              "client_secret": "secret",
              "issuer_uri": "https://example.com",
              "redirect_uris": ["https://example.com"],
              "credential_offer_endpoint": "somewhere.com"}
    )
    await holder.request_authorization(CredentialSelection(
        credential_configuration_id="DriversLicense",
        credential_offer=CredentialOffer(
            credential_issuer="https://example.com",
            credential_configuration_ids=["DriversLicense"]
        )
    ), auth_header)

@pytest.mark.asyncio()
async def test1_request_authorization_with_uri(
        httpx_mock: HTTPXMock, holder: WebHolder, auth_header: str):

    httpx_mock.add_response(
        url="https://example.com/oauth2/register",
        json={"client_id": "example",
              "client_secret": "secret",
              "issuer_uri": "https://example.com",
              "redirect_uris": ["https://example.com"],
              "credential_offer_endpoint": "somewhere.com"}
    )
    await holder.request_authorization(CredentialSelection(
        credential_configuration_id="DriversLicense",
        issuer_uri="https://example.com"
    ), auth_header)


@pytest.mark.asyncio()
async def test2_two_credential_offer_methods(
        httpx_mock: HTTPXMock, holder: WebHolder, auth_header: str):
    selection = CredentialSelection(
        credential_configuration_id="DriversLicense",
        issuer_uri="https://example.com",
        credential_offer={
            "credential_issuer": "Service NSW",
            "credential_configuration_ids": ["DriversLicense", "Passport"]
        })

    with pytest.raises(HTTPException):
        resp = await holder.request_authorization(selection, auth_header)
        assert resp.status_code == 400

@pytest.mark.asyncio()
async def test3_missing_offer_and_uri(
        httpx_mock: HTTPXMock, holder: WebHolder, auth_header: str):
    selection = CredentialSelection(
        credential_configuration_id="DriversLicense")

    with pytest.raises(HTTPException) as e:
        await holder.request_authorization(selection, auth_header)
    assert e.value.status_code == 400
