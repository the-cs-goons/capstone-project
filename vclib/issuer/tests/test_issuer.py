import json

import pytest
from fastapi import HTTPException, Response

from vclib.issuer import CredentialIssuer

MOCK_INFORMATION = {
    "default": {
        "string": {"mandatory": True, "value_type": "string"},
        "number": {"mandatory": True, "value_type": "number"},
        "boolean": {"mandatory": True, "value_type": "boolean"},
        "optional": {"mandatory": False, "value_type": "string"},
    },
}

exp_diddoc: dict
exp_didconf: dict
exp_meta: dict
exp_ometa: dict

with open("vclib/issuer/tests/test_diddoc.json", "rb") as diddoc_file:
    exp_diddoc = json.load(diddoc_file)

with open("vclib/issuer/tests/test_didconf.json", "rb") as didconf_file:
    exp_didconf = json.load(didconf_file)

with open("vclib/issuer/tests/test_metadata.json", "rb") as meta_file:
    exp_meta = json.load(meta_file)

with open("vclib/issuer/tests/test_oauth_metadata.json", "rb") as ometa_file:
    exp_ometa = json.load(ometa_file)


@pytest.fixture()
def credential_issuer():
    return CredentialIssuer(
        MOCK_INFORMATION,
        "vclib/issuer/tests/test_jwk_private.pem",
        "vclib/issuer/tests/test_diddoc.json",
        "vclib/issuer/tests/test_didconf.json",
        "vclib/issuer/tests/test_metadata.json",
        "vclib/issuer/tests/test_oauth_metadata.json",
    )


@pytest.mark.asyncio()
async def test_metadata(credential_issuer):
    diddoc = await credential_issuer.get_did_json()
    assert exp_diddoc == diddoc

    didconf = await credential_issuer.get_did_config()
    assert exp_didconf == didconf

    meta = await credential_issuer.get_issuer_metadata()
    assert exp_meta == meta

    ometa = await credential_issuer.get_oauth_metadata()
    assert exp_ometa == ometa


@pytest.mark.asyncio()
async def test_credential_options(credential_issuer):
    response = await credential_issuer.get_credential_options()
    assert response.options == MOCK_INFORMATION


@pytest.mark.asyncio()
async def test_request_credential(credential_issuer):
    info_1 = {"string": "string", "number": 0, "boolean": True, "optional": None}
    response1 = await credential_issuer.receive_credential_request("default", info_1)

    info_2 = {"string": "letters", "number": 20, "boolean": False, "optional": "None"}
    response2 = await credential_issuer.receive_credential_request("default", info_2)

    info_3 = {"string": "alphabet", "number": 50, "boolean": True}
    response3 = await credential_issuer.receive_credential_request("default", info_3)

    assert isinstance(response1.access_token, str)
    assert isinstance(response2.access_token, str)
    assert isinstance(response3.access_token, str)

    assert response1.access_token != response2.access_token
    assert response2.access_token != response3.access_token
    assert response3.access_token != response1.access_token


@pytest.mark.asyncio()
async def test_check_credential_status(credential_issuer):
    info = {"string": "string", "number": 0, "boolean": True}
    response = await credential_issuer.receive_credential_request("default", info)
    assert isinstance(response.access_token, str)

    req = {"credential_identifier": "default"}
    response = await credential_issuer.get_credential(
        Response(), req, "Bearer " + response.access_token
    )
    assert response["transaction_id"]


@pytest.mark.asyncio()
async def test_invalid_access_code(credential_issuer):
    info = {"string": "string", "number": 0, "boolean": True}
    response = await credential_issuer.receive_credential_request("default", info)
    assert isinstance(response.access_token, str)

    req = {"credential_identifier": "default"}
    with pytest.raises(HTTPException):
        await credential_issuer.get_credential(Response(), req, "Bearer " + "abc")


@pytest.mark.asyncio()
async def test_invalid_credentials():
    credential_issuer = CredentialIssuer(
        MOCK_INFORMATION,
        "vclib/issuer/tests/test_private_key.pem",
        "vclib/issuer/tests/test_diddoc.json",
        "vclib/issuer/tests/test_didconf.json",
        "vclib/issuer/tests/test_metadata.json",
        "vclib/issuer/tests/test_oauth_metadata.json",
    )

    info = {"name": "Name Lastname"}
    with pytest.raises(HTTPException):
        await credential_issuer.receive_credential_request("id", info)


@pytest.mark.asyncio()
async def test_invalid_information(credential_issuer):
    invalid_info_1 = {"string": "string", "not_a_field": False}
    with pytest.raises(HTTPException):
        await credential_issuer.receive_credential_request("default", invalid_info_1)

    invalid_info_2 = {
        "string": "string",
        "number": True,
        "boolean": False,
        "optional": None,
    }
    with pytest.raises(HTTPException):
        await credential_issuer.receive_credential_request("default", invalid_info_2)

    invalid_info_3 = {
        "string": "string",
        "number": 0,
        "boolean": None,
        "optional": None,
    }
    with pytest.raises(HTTPException):
        await credential_issuer.receive_credential_request("default", invalid_info_3)

    invalid_info_4 = {
        "string": "string",
        "number": 0,
        "boolean": True,
        "optional": None,
        "not_field": True,
    }
    with pytest.raises(HTTPException):
        await credential_issuer.receive_credential_request("default", invalid_info_4)

    with pytest.raises(HTTPException):
        await credential_issuer.receive_credential_request("default")


@pytest.mark.asyncio()
async def test_nonexistent_files():
    with pytest.raises(FileNotFoundError):
        CredentialIssuer(
            MOCK_INFORMATION,
            "not/a/key.pem",
            "vclib/issuer/tests/test_diddoc.json",
            "vclib/issuer/tests/test_didconf.json",
            "vclib/issuer/tests/test_metadata.json",
            "vclib/issuer/tests/test_oauth_metadata.json",
        )

    with pytest.raises(FileNotFoundError):
        CredentialIssuer(
            MOCK_INFORMATION,
            "vclib/issuer/tests/test_jwk_private.pem",
            "not/a/diddoc.json",
            "vclib/issuer/tests/test_didconf.json",
            "vclib/issuer/tests/test_metadata.json",
            "vclib/issuer/tests/test_oauth_metadata.json",
        )

    with pytest.raises(FileNotFoundError):
        CredentialIssuer(
            MOCK_INFORMATION,
            "vclib/issuer/tests/test_jwk_private.pem",
            "vclib/issuer/tests/test_diddoc.json",
            "not/a/didconf.json",
            "vclib/issuer/tests/test_metadata.json",
            "vclib/issuer/tests/test_oauth_metadata.json",
        )

    with pytest.raises(FileNotFoundError):
        CredentialIssuer(
            MOCK_INFORMATION,
            "vclib/issuer/tests/test_jwk_private.pem",
            "vclib/issuer/tests/test_diddoc.json",
            "vclib/issuer/tests/test_didconf.json",
            "not/metadata.json",
            "vclib/issuer/tests/test_oauth_metadata.json",
        )

    with pytest.raises(FileNotFoundError):
        CredentialIssuer(
            MOCK_INFORMATION,
            "vclib/issuer/tests/test_jwk_private.pem",
            "vclib/issuer/tests/test_diddoc.json",
            "vclib/issuer/tests/test_didconf.json",
            "vclib/issuer/tests/test_metadata.json",
            "not/oauth/metadata.json",
        )


@pytest.mark.asyncio()
async def test_invalid_files():
    with pytest.raises(ValueError):
        CredentialIssuer(
            MOCK_INFORMATION,
            "vclib/issuer/tests/test_invalid_private_key.pem",
            "vclib/issuer/tests/test_diddoc.json",
            "vclib/issuer/tests/test_didconf.json",
            "vclib/issuer/tests/test_metadata.json",
            "vclib/issuer/tests/test_oauth_metadata.json",
        )

    with pytest.raises(ValueError):
        CredentialIssuer(
            MOCK_INFORMATION,
            "vclib/issuer/tests/test_jwk_private.pem",
            "vclib/issuer/tests/test_invalid_private_key.pem",
            "vclib/issuer/tests/test_didconf.json",
            "vclib/issuer/tests/test_metadata.json",
            "vclib/issuer/tests/test_oauth_metadata.json",
        )

    with pytest.raises(ValueError):
        CredentialIssuer(
            MOCK_INFORMATION,
            "vclib/issuer/tests/test_jwk_private.pem",
            "vclib/issuer/tests/test_diddoc.json",
            "vclib/issuer/tests/test_invalid_private_key.pem",
            "vclib/issuer/tests/test_metadata.json",
            "vclib/issuer/tests/test_oauth_metadata.json",
        )

    with pytest.raises(ValueError):
        CredentialIssuer(
            MOCK_INFORMATION,
            "vclib/issuer/tests/test_jwk_private.pem",
            "vclib/issuer/tests/test_diddoc.json",
            "vclib/issuer/tests/test_didconf.json",
            "vclib/issuer/tests/test_invalid_private_key.pem",
            "vclib/issuer/tests/test_oauth_metadata.json",
        )

    with pytest.raises(ValueError):
        CredentialIssuer(
            MOCK_INFORMATION,
            "vclib/issuer/tests/test_jwk_private.pem",
            "vclib/issuer/tests/test_diddoc.json",
            "vclib/issuer/tests/test_didconf.json",
            "vclib/issuer/tests/test_metadata.json",
            "vclib/issuer/tests/test_invalid_private_key.pem",
        )
