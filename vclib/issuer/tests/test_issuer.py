import json
from base64 import urlsafe_b64encode

import pytest
from fastapi import Response

from vclib.issuer import CredentialIssuer
from vclib.issuer.src.models.oauth import WalletClientMetadata

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
        "https://issuer-lib:8082",
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
    metadata = WalletClientMetadata(
        redirect_uris=[],
        credential_offer_endpoint="",
        token_endpoint_auth_method="",
        grant_types=[],
        response_types=[],
        authorization_details_types=[],
        client_name=None,
        client_uri=None,
        logo_uri=None,
    )

    client = await credential_issuer.register(Response(), metadata)
    client_id, client_secret = client.client_id, client.client_secret

    info_1 = {"string": "string", "number": 0, "boolean": True, "optional": None}
    response1 = await credential_issuer.receive_credential_request(
        "code",
        client_id,
        "aaa",  # TODO: modify to valid url
        "xyz",
        """[{"type": "openid_credential", "credential_configuration_id": "default"}]""",
        info_1,
    )

    auth_code = response1.headers["location"].split("=")[1].split("&")[0]
    print(auth_code)

    authorization = urlsafe_b64encode(f"{client_id}:{client_secret}".encode()).decode(
        "utf-8"
    )

    response1 = await credential_issuer.token(
        "authorization_code", auth_code, "aaa", "Basic " + authorization
    )

    req = {
        "credential_identifier": response1.authorization_details[
            0
        ].credential_identifiers[0]
    }
    response = await credential_issuer.get_credential(
        Response(), req, "Bearer " + response1.access_token
    )
    print(response)
    assert response["transaction_id"]

    # info_2 = {"string": "letters", "number": 20, "boolean": False, "optional": "None"}
    # response2 = await credential_issuer.receive_credential_request("default", info_2)

    # info_3 = {"string": "alphabet", "number": 50, "boolean": True}
    # response3 = await credential_issuer.receive_credential_request("default", info_3)

    # assert isinstance(response1.access_token, str)
    # assert isinstance(response2.access_token, str)
    # assert isinstance(response3.access_token, str)

    # assert response1.access_token != response2.access_token
    # assert response2.access_token != response3.access_token
    # assert response3.access_token != response1.access_token


# @pytest.mark.asyncio()
# async def test_check_credential_status(credential_issuer):
#     info = {"string": "string", "number": 0, "boolean": True}
#     response = await credential_issuer.receive_credential_request("default", info)
#     assert isinstance(response.access_token, str)

#     req = {"credential_identifier": "default"}
#     response = await credential_issuer.get_credential(
#         Response(), req, "Bearer " + response.access_token
#     )
#     assert response["transaction_id"]


# @pytest.mark.asyncio()
# async def test_invalid_access_code(credential_issuer):
#     info = {"string": "string", "number": 0, "boolean": True}
#     response = await credential_issuer.receive_credential_request("default", info)
#     assert isinstance(response.access_token, str)

#     req = {"credential_identifier": "default"}
#     with pytest.raises(HTTPException):
#         await credential_issuer.get_credential(Response(), req, "Bearer " + "abc")


# @pytest.mark.asyncio()
# async def test_invalid_credentials():
#     credential_issuer = CredentialIssuer(
#         MOCK_INFORMATION,
#         "https://issuer-lib:8082",
#         "vclib/issuer/tests/test_private_key.pem",
#         "vclib/issuer/tests/test_diddoc.json",
#         "vclib/issuer/tests/test_didconf.json",
#         "vclib/issuer/tests/test_metadata.json",
#         "vclib/issuer/tests/test_oauth_metadata.json",
#     )

#     info = {"name": "Name Lastname"}
#     with pytest.raises(HTTPException):
#         await credential_issuer.receive_credential_request("id", info)


# @pytest.mark.asyncio()
# async def test_invalid_information(credential_issuer):
#     invalid_info_1 = {"string": "string", "not_a_field": False}
#     with pytest.raises(HTTPException):
#         await credential_issuer.receive_credential_request("default", invalid_info_1)

#     invalid_info_2 = {
#         "string": "string",
#         "number": True,
#         "boolean": False,
#         "optional": None,
#     }
#     with pytest.raises(HTTPException):
#         await credential_issuer.receive_credential_request("default", invalid_info_2)

#     invalid_info_3 = {
#         "string": "string",
#         "number": 0,
#         "boolean": None,
#         "optional": None,
#     }
#     with pytest.raises(HTTPException):
#         await credential_issuer.receive_credential_request("default", invalid_info_3)

#     invalid_info_4 = {
#         "string": "string",
#         "number": 0,
#         "boolean": True,
#         "optional": None,
#         "not_field": True,
#     }
#     with pytest.raises(HTTPException):
#         await credential_issuer.receive_credential_request("default", invalid_info_4)

#     with pytest.raises(HTTPException):
#         await credential_issuer.receive_credential_request("default")


@pytest.mark.asyncio()
async def test_nonexistent_files():
    with pytest.raises(FileNotFoundError):
        CredentialIssuer(
            MOCK_INFORMATION,
            "https://issuer-lib:8082",
            "not/a/key.pem",
            "vclib/issuer/tests/test_diddoc.json",
            "vclib/issuer/tests/test_didconf.json",
            "vclib/issuer/tests/test_metadata.json",
            "vclib/issuer/tests/test_oauth_metadata.json",
        )

    with pytest.raises(FileNotFoundError):
        CredentialIssuer(
            MOCK_INFORMATION,
            "https://issuer-lib:8082",
            "vclib/issuer/tests/test_jwk_private.pem",
            "not/a/diddoc.json",
            "vclib/issuer/tests/test_didconf.json",
            "vclib/issuer/tests/test_metadata.json",
            "vclib/issuer/tests/test_oauth_metadata.json",
        )

    with pytest.raises(FileNotFoundError):
        CredentialIssuer(
            MOCK_INFORMATION,
            "https://issuer-lib:8082",
            "vclib/issuer/tests/test_jwk_private.pem",
            "vclib/issuer/tests/test_diddoc.json",
            "not/a/didconf.json",
            "vclib/issuer/tests/test_metadata.json",
            "vclib/issuer/tests/test_oauth_metadata.json",
        )

    with pytest.raises(FileNotFoundError):
        CredentialIssuer(
            MOCK_INFORMATION,
            "https://issuer-lib:8082",
            "vclib/issuer/tests/test_jwk_private.pem",
            "vclib/issuer/tests/test_diddoc.json",
            "vclib/issuer/tests/test_didconf.json",
            "not/metadata.json",
            "vclib/issuer/tests/test_oauth_metadata.json",
        )

    with pytest.raises(FileNotFoundError):
        CredentialIssuer(
            MOCK_INFORMATION,
            "https://issuer-lib:8082",
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
            "https://issuer-lib:8082",
            "vclib/issuer/tests/test_invalid_private_key.pem",
            "vclib/issuer/tests/test_diddoc.json",
            "vclib/issuer/tests/test_didconf.json",
            "vclib/issuer/tests/test_metadata.json",
            "vclib/issuer/tests/test_oauth_metadata.json",
        )

    with pytest.raises(ValueError):
        CredentialIssuer(
            MOCK_INFORMATION,
            "https://issuer-lib:8082",
            "vclib/issuer/tests/test_jwk_private.pem",
            "vclib/issuer/tests/test_invalid_private_key.pem",
            "vclib/issuer/tests/test_didconf.json",
            "vclib/issuer/tests/test_metadata.json",
            "vclib/issuer/tests/test_oauth_metadata.json",
        )

    with pytest.raises(ValueError):
        CredentialIssuer(
            MOCK_INFORMATION,
            "https://issuer-lib:8082",
            "vclib/issuer/tests/test_jwk_private.pem",
            "vclib/issuer/tests/test_diddoc.json",
            "vclib/issuer/tests/test_invalid_private_key.pem",
            "vclib/issuer/tests/test_metadata.json",
            "vclib/issuer/tests/test_oauth_metadata.json",
        )

    with pytest.raises(ValueError):
        CredentialIssuer(
            MOCK_INFORMATION,
            "https://issuer-lib:8082",
            "vclib/issuer/tests/test_jwk_private.pem",
            "vclib/issuer/tests/test_diddoc.json",
            "vclib/issuer/tests/test_didconf.json",
            "vclib/issuer/tests/test_invalid_private_key.pem",
            "vclib/issuer/tests/test_oauth_metadata.json",
        )

    with pytest.raises(ValueError):
        CredentialIssuer(
            MOCK_INFORMATION,
            "https://issuer-lib:8082",
            "vclib/issuer/tests/test_jwk_private.pem",
            "vclib/issuer/tests/test_diddoc.json",
            "vclib/issuer/tests/test_didconf.json",
            "vclib/issuer/tests/test_metadata.json",
            "vclib/issuer/tests/test_invalid_private_key.pem",
        )
