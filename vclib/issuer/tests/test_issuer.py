import json
import os
from base64 import urlsafe_b64encode

import pytest
from fastapi import Response

from vclib.issuer import CredentialIssuer
from vclib.issuer.src.models.oauth import WalletClientMetadata
from vclib.issuer.tests.test_issuer_class import TestIssuer

exp_diddoc: dict
exp_didconf: dict
exp_meta: dict
exp_ometa: dict

os.environ["TZ"] = "UTC"

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
    return TestIssuer(
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
        Response(),
        "code",
        client_id,
        "https://example.com",
        "xyz",
        """[{"type": "openid_credential", "credential_configuration_id": "default"}]""",
        info_1,
    )

    auth_code = response1.headers["location"].split("=")[1].split("&")[0]

    authorization = urlsafe_b64encode(f"{client_id}:{client_secret}".encode()).decode(
        "utf-8"
    )

    response1 = await credential_issuer.token(
        Response(),
        "authorization_code",
        auth_code,
        "https://example.com",
        "Basic " + authorization,
    )

    req = {
        "credential_identifier": response1.authorization_details[
            0
        ].credential_identifiers[0]
    }
    response = await credential_issuer.get_credential(
        Response(), req, "Bearer " + response1.access_token
    )
    assert response["credential"]


@pytest.mark.asyncio()
async def test_nonexistent_files():
    with pytest.raises(FileNotFoundError):
        CredentialIssuer(
            "not/a/key.pem",
            "vclib/issuer/tests/test_diddoc.json",
            "vclib/issuer/tests/test_didconf.json",
            "vclib/issuer/tests/test_metadata.json",
            "vclib/issuer/tests/test_oauth_metadata.json",
        )

    with pytest.raises(FileNotFoundError):
        CredentialIssuer(
            "vclib/issuer/tests/test_jwk_private.pem",
            "not/a/diddoc.json",
            "vclib/issuer/tests/test_didconf.json",
            "vclib/issuer/tests/test_metadata.json",
            "vclib/issuer/tests/test_oauth_metadata.json",
        )

    with pytest.raises(FileNotFoundError):
        CredentialIssuer(
            "vclib/issuer/tests/test_jwk_private.pem",
            "vclib/issuer/tests/test_diddoc.json",
            "not/a/didconf.json",
            "vclib/issuer/tests/test_metadata.json",
            "vclib/issuer/tests/test_oauth_metadata.json",
        )

    with pytest.raises(FileNotFoundError):
        CredentialIssuer(
            "vclib/issuer/tests/test_jwk_private.pem",
            "vclib/issuer/tests/test_diddoc.json",
            "vclib/issuer/tests/test_didconf.json",
            "not/metadata.json",
            "vclib/issuer/tests/test_oauth_metadata.json",
        )

    with pytest.raises(FileNotFoundError):
        CredentialIssuer(
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
            "vclib/issuer/tests/test_invalid_private_key.pem",
            "vclib/issuer/tests/test_diddoc.json",
            "vclib/issuer/tests/test_didconf.json",
            "vclib/issuer/tests/test_metadata.json",
            "vclib/issuer/tests/test_oauth_metadata.json",
        )

    with pytest.raises(ValueError):
        CredentialIssuer(
            "vclib/issuer/tests/test_jwk_private.pem",
            "vclib/issuer/tests/test_invalid_private_key.pem",
            "vclib/issuer/tests/test_didconf.json",
            "vclib/issuer/tests/test_metadata.json",
            "vclib/issuer/tests/test_oauth_metadata.json",
        )

    with pytest.raises(ValueError):
        CredentialIssuer(
            "vclib/issuer/tests/test_jwk_private.pem",
            "vclib/issuer/tests/test_diddoc.json",
            "vclib/issuer/tests/test_invalid_private_key.pem",
            "vclib/issuer/tests/test_metadata.json",
            "vclib/issuer/tests/test_oauth_metadata.json",
        )

    with pytest.raises(ValueError):
        CredentialIssuer(
            "vclib/issuer/tests/test_jwk_private.pem",
            "vclib/issuer/tests/test_diddoc.json",
            "vclib/issuer/tests/test_didconf.json",
            "vclib/issuer/tests/test_invalid_private_key.pem",
            "vclib/issuer/tests/test_oauth_metadata.json",
        )

    with pytest.raises(ValueError):
        CredentialIssuer(
            "vclib/issuer/tests/test_jwk_private.pem",
            "vclib/issuer/tests/test_diddoc.json",
            "vclib/issuer/tests/test_didconf.json",
            "vclib/issuer/tests/test_metadata.json",
            "vclib/issuer/tests/test_invalid_private_key.pem",
        )
