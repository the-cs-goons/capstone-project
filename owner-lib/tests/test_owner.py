import pytest
from examples.default_agent import DefaultWebIdentityOwner
from fastapi import HTTPException


def test_get_credential():
    MOCK_STORE = {
        "example1": {
            "id": "example1",
            "issuer_url": "https://example.com",
            "type": "Example",
            "request_url": "https://example.com/status?token=example1",
            "token": "qwertyuiop",
            "status":"ACCEPTED",
            "status_message":None,
            "issuer_name":"Example Issuer",
            "received_at":1719295821397
        },
        "example2": {
            "id": "example2",
            "issuer_url": "https://example.com",
            "type": "Example",
            "request_url": "https://example.com/status?token=example2",
            "token": None,
            "status":"PENDING",
            "status_message":None,
            "issuer_name":"Example Issuer",
            "received_at":None
        }
    }
    identity_owner = DefaultWebIdentityOwner("hello", mock_data=MOCK_STORE)
    credential1 = identity_owner.get_credential("example1")
    assert credential1.id == "example1"
    assert credential1.token == "qwertyuiop"
    assert credential1.status == "ACCEPTED"

def test_get_credential_error():
    MOCK_STORE = {
        "example1": {
            "id": "example1",
            "issuer_url": "https://example.com",
            "type": "Example",
            "request_url": "https://example.com/status?token=example1",
            "token": "qwertyuiop",
            "status":"ACCEPTED",
            "status_message":None,
            "issuer_name":"Example Issuer",
            "received_at":1719295821397
        },
        "example2": {
            "id": "example2",
            "issuer_url": "https://example.com",
            "type": "Example",
            "request_url": "https://example.com/status?token=example2",
            "token": None,
            "status":"PENDING",
            "status_message":None,
            "issuer_name":"Example Issuer",
            "received_at":None
        }
    }
    identity_owner = DefaultWebIdentityOwner("hello", mock_data=MOCK_STORE)
    with pytest.raises(HTTPException):
        identity_owner.get_credential("bad_id")

def test_get_pending_credentials():
    MOCK_STORE = {
        "example1": {
            "id": "example1",
            "issuer_url": "https://example.com",
            "type": "Example",
            "request_url": "https://example.com/status?token=example1",
            "token": "qwertyuiop",
            "status":"ACCEPTED",
            "status_message":None,
            "issuer_name":"Example Issuer",
            "received_at":1719295821397
        },
        "example2": {
            "id": "example2",
            "issuer_url": "https://example.com",
            "type": "Example",
            "request_url": "https://example.com/status?token=example2",
            "token": None,
            "status":"PENDING",
            "status_message":None,
            "issuer_name":"Example Issuer",
            "received_at":None
        }
    }
    identity_owner = DefaultWebIdentityOwner("hello", mock_data=MOCK_STORE)
    pending = identity_owner.get_pending_credentials()
    assert len(pending) == 1
    assert pending[0].status == "PENDING"
    assert pending[0].received_at is None
    assert pending[0].token is None

def test_get_credentials():
    MOCK_STORE = {
        "example1": {
            "id": "example1",
            "issuer_url": "https://example.com",
            "type": "Example",
            "request_url": "https://example.com/status?token=example1",
            "token": "qwertyuiop",
            "status":"ACCEPTED",
            "status_message":None,
            "issuer_name":"Example Issuer",
            "received_at":1719295821397
        },
        "example2": {
            "id": "example2",
            "issuer_url": "https://example.com",
            "type": "Example",
            "request_url": "https://example.com/status?token=example2",
            "token": None,
            "status":"PENDING",
            "status_message":None,
            "issuer_name":"Example Issuer",
            "received_at":None
        }
    }
    identity_owner = DefaultWebIdentityOwner("hello", mock_data=MOCK_STORE)
    credentials = identity_owner.get_credentials()
    assert len(credentials) == 2

