import pytest
from fastapi import HTTPException
from issuer import CredentialIssuer


@pytest.mark.asyncio
async def test_request_credential():
    credential_issuer = CredentialIssuer()

    info = {
        "string": "string",
        "number": 0,
        "boolean": True,
        "optional": None,
    }
    response = await credential_issuer.recieve_credential_request("default", info)
    assert response.ticket == 1
    assert response.link == "1"


@pytest.mark.asyncio
async def test_check_credential_status():
    credential_issuer = CredentialIssuer()

    info = {
        "string": "string",
        "number": 0,
        "boolean": True,
        "optional": None,
    }
    response = await credential_issuer.recieve_credential_request("default", info)
    assert response.ticket == 1
    assert response.link == "1"

    response = await credential_issuer.credential_status("1")
    assert response.ticket == 1
    assert response.status == "Pending"

@pytest.mark.asyncio
async def test_invalid_credentials():
    credential_issuer = CredentialIssuer()

    info = {
        "name": "Name Lastname"
    }
    with pytest.raises(HTTPException):
        await credential_issuer.recieve_credential_request("id", info)

@pytest.mark.asyncio
async def test_invalid_information():
    credential_issuer = CredentialIssuer()

    invalid_info_1 = {
        "string": "string",
        "not_a_field": False,
    }
    with pytest.raises(HTTPException):
        await credential_issuer.recieve_credential_request("default", invalid_info_1)

    invalid_info_2 = {
        "string": "string",
        "number": True,
        "boolean": False,
        "optional": None,
    }
    with pytest.raises(HTTPException):
        await credential_issuer.recieve_credential_request("default", invalid_info_2)

    invalid_info_3 = {
        "string": "string",
        "number": 0,
        "boolean": None,
        "optional": None,
    }
    with pytest.raises(HTTPException):
        await credential_issuer.recieve_credential_request("default", invalid_info_3)