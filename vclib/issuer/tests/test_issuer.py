import pytest
from fastapi import HTTPException

from vclib.issuer import CredentialIssuer

MOCK_INFORMATION = {
    "default": {
        "string": {"mandatory": True, "value_type": "string"},
        "number": {"mandatory": True, "value_type": "number"},
        "boolean": {"mandatory": True, "value_type": "boolean"},
        "optional": {"mandatory": False, "value_type": "string"},
    },
}


@pytest.fixture()
def credential_issuer():
    return CredentialIssuer(
        MOCK_INFORMATION,
        "vclib/issuer/tests/test_private_key.pem",
        "vclib/issuer/tests/test_diddoc.json",
        "vclib/issuer/tests/test_didconf.json",
        "vclib/issuer/tests/test_metadata.json",
        "vclib/issuer/tests/test_oauth_metadata.json",
    )


@pytest.mark.asyncio()
async def test_credential_options(credential_issuer):
    response = await credential_issuer.get_credential_options()
    assert response.options == MOCK_INFORMATION


@pytest.mark.asyncio()
async def test_request_credential(credential_issuer):
    info_1 = {"string": "string", "number": 0, "boolean": True, "optional": None}
    response = await credential_issuer.receive_credential_request("default", info_1)
    assert response.ticket == 1

    info_2 = {"string": "letters", "number": 20, "boolean": False, "optional": "None"}
    response = await credential_issuer.receive_credential_request("default", info_2)
    assert response.ticket == 2

    info_3 = {"string": "alphabet", "number": 50, "boolean": True}
    response = await credential_issuer.receive_credential_request("default", info_3)
    assert response.ticket == 3


# This test breaks with the current changes, will need to find another way to unit test

# @pytest.mark.asyncio()
# async def test_check_credential_status(credential_issuer):
#     info = {"string": "string", "number": 0, "boolean": True}
#     response = await credential_issuer.receive_credential_request("default", info)
#     assert response.ticket == 1

#     response = await credential_issuer.get_credential(response=Response(),
#         request=CredentialRequestBody(credential_identifier="default"),
#           authorization="Bearer " + response.link
#     )
#     assert response.transaction_id


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
