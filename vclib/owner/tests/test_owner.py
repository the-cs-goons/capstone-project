import pytest
from fastapi import HTTPException

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
            "expires_in": 99999999999
        }
    },
}


@pytest.fixture()
def identity_owner():
    return DefaultWebIdentityOwner("example", mock_data=MOCK_STORE)


def test_get_credential(identity_owner):
    credential1 = identity_owner.get_credential("example1")
    assert credential1.id == "example1"
    assert credential1.token == "qwertyuiop"
    assert credential1.status == "ACCEPTED"


def test_get_credential_error(identity_owner):
    with pytest.raises(HTTPException):
        identity_owner.get_credential("bad_id")


def test_get_pending_credentials(identity_owner):
    pending = identity_owner.get_pending_credentials()
    assert len(pending) == 1
    assert pending[0].status == "PENDING"
    assert pending[0].received_at is None
    assert pending[0].token is None


def test_get_credentials(identity_owner):
    credentials = identity_owner.get_credentials()
    assert len(credentials) == 2
