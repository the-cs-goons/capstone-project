import base64
import json
from unittest.mock import patch

import pytest
from fastapi import FastAPI

from vclib.verifier import ServiceProvider


@pytest.mark.asyncio()
async def test_server_exists():
    sp = ServiceProvider()
    sp_server = sp.get_server()
    assert isinstance(sp_server, FastAPI)


@pytest.fixture
def service_provider():
    return ServiceProvider()


def test_fetch_did_document_success(service_provider):
    with patch("requests.get") as mock_get:
        example_did_document = {
            "@context": ["https://www.w3.org/ns/did/v1"],
            "id": "did:web:example.com",
            "verificationMethod": [
                {
                    "id": "did:web:example.com#key-1",
                    "type": "JsonWebKey2020",
                    "controller": "did:web:example.com",
                    "publicKeyJwk": {
                        "kty": "EC",
                        "crv": "P-256",
                        "x": "abc",
                        "y": "def",
                    },
                }
            ],
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = example_did_document

        result = service_provider.fetch_did_document("https://example.com")

        assert result == example_did_document


def base64url_encode(data):
    """Encode data in a base64url-safe manner, without padding."""
    base64_encoded = base64.urlsafe_b64encode(data.encode()).decode("utf-8")
    return base64_encoded.rstrip("=")


def create_test_jwt():
    header = {"kid": "did:web:example.com#key-1", "alg": "ES256"}
    payload = {"sub": "123", "nonce": "nonce-value"}

    encoded_header = base64url_encode(json.dumps(header))
    encoded_payload = base64url_encode(json.dumps(payload))

    signature = base64url_encode("signature-placeholder")

    return f"{encoded_header}.{encoded_payload}.{signature}"


def test_verify_jwt_success(service_provider):
    with (
        patch.object(service_provider, "fetch_did_document") as mock_fetch,
        patch("jwt.decode") as mock_decode,
        patch("jwt.algorithms.ECAlgorithm.from_jwk") as mock_from_jwk,
    ):
        example_did_document = {
            "@context": "https://www.w3.org/ns/did/v1",
            "id": "did:web:example.com",
            "verificationMethod": [
                {
                    "id": "did:web:example.com#key-1",
                    "type": "JsonWebKey2020",
                    "controller": "did:web:example.com",
                    "publicKeyJwk": {
                        "kty": "EC",
                        "crv": "P-256",
                        "x": "abc",
                        "y": "def",
                    },
                }
            ],
        }
        mock_fetch.return_value = example_did_document
        mock_decode.return_value = {"sub": "123"}
        fake_token = create_test_jwt()
        fake_did_url = "https://example.com"

        result = service_provider.verify_jwt(
            fake_token,
            fake_did_url,
            "nonce-value"
            )

        mock_from_jwk.assert_called_once_with(
            example_did_document["verificationMethod"][0]["publicKeyJwk"]
        )
        mock_decode.assert_called_once()
        assert result == {"sub": "123"}
