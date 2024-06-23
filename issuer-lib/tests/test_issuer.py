import pytest
from fastapi import HTTPException
from issuer import CredentialIssuer

MOCK_INFORMATION = {
    "default": {
        "string": {
            "type": "string",
            "optional": False,
        },
        "number": {
            "type": "number",
            "optional": False,
        },
        "boolean": {
            "type": "boolean",
            "optional": False,
        },
        "optional": {
            "type": "string",
            "optional": True,
        },
    },
}

@pytest.mark.asyncio
async def test_request_credential():
    credential_issuer = CredentialIssuer(MOCK_INFORMATION)

    info_1 = {
        "string": "string",
        "number": 0,
        "boolean": True,
        "optional": None,
    }
    response = await credential_issuer.recieve_credential_request("default", info_1)
    assert response.ticket == 1
    # assert response.link == "1"

    info_2 = {
        "string": "letters",
        "number": 20,
        "boolean": False,
        "optional": "None",
    }
    response = await credential_issuer.recieve_credential_request("default", info_2)
    assert response.ticket == 2
    # assert response.link == "2"


@pytest.mark.asyncio
async def test_check_credential_status():
    credential_issuer = CredentialIssuer(MOCK_INFORMATION)

    info = {
        "string": "string",
        "number": 0,
        "boolean": True,
    }
    response = await credential_issuer.recieve_credential_request("default", info)
    assert response.ticket == 1
    # assert response.link == "1"

    response = await credential_issuer.credential_status(response.link)
    assert response.ticket == 1
    assert response.status == "Pending"


@pytest.mark.asyncio
async def test_invalid_credentials():
    credential_issuer = CredentialIssuer(MOCK_INFORMATION)

    info = {"name": "Name Lastname"}
    with pytest.raises(HTTPException):
        await credential_issuer.recieve_credential_request("id", info)


@pytest.mark.asyncio
async def test_invalid_information():
    credential_issuer = CredentialIssuer(MOCK_INFORMATION)

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
