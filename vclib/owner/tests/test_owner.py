import pytest
from fastapi import HTTPException
from pytest_httpx import HTTPXMock

from vclib.owner.examples.default_agent import DefaultWebIdentityOwner
from vclib.owner.src.models.field_selection_object import FieldSelectionObject

over_18_mock_auth_response = {
    "vp_token": "eyJhbGciOiAiRVMyNTYiLCAidHlwIjogInZjK3NkLWp3dCJ9.eyJfc2QiOiBbIktJMWx6b21fcVAwVzBKUDdaLVFYVkZrWmV1MElkajJKYTdLcmZPWFdORDQiLCAiUVhOUDk2TkUxZ21kdHdTTE4xeE9pbXZLX20wTVZ2czBBdTJUU1J0ZS1oOCIsICJTSHdLdjhKX09kQU1mS3NtOTJ3eHF0UXZRdFhyVWQwcm9ubkNGZXkySEJvIiwgInpaaFZVdkNodi1JSDBpaWRobFBQVDE1Zk5QbTRGZGRmMlREcG1EUllWUXciXSwgImlhdCI6IDE3MjA5NTIxMTYuMCwgIl9zZF9hbGciOiAic2hhLTI1NiJ9.fFbkA1FLMDT36Y48rxtOfUC76zgWxZAYLQnEWKgi02nubV2b7U7A45b3080USYGRxJ7AYi4GG-3vx1QPM_00lw~WyJaNFdITlBNWkZIM0JOS19haXVKZnBnIiwgImlzX292ZXJfMTgiLCAidHJ1ZSJd~", # noqa: E501
    "presentation_submission": {
        'id': 'f4c91058-d2de-42a2-be63-7946d7743a26',
        'definition_id': 'verify_over_18',
        'descriptor_map': [
            {
                'id': 'over_18_descriptor',
                'format': 'vc+sd-jwt',
                'path': '$'
            }
        ]
    },
    "state": "ae4adb8b-d1f2-4eb9-baa3-73be30a7aa2a_1721042569"
}

over_18_mock_field_selection = FieldSelectionObject(field_requests=[
        {
            "field": {
                "path": ["$.credentialSubject.is_over_18", "$.is_over_18"],
                "filter": {
                    "type": "string",
                    "enum": ["true"]
                }
            },
            "input_descriptor_id": "over_18_descriptor",
            "approved": True
        }
    ])

over_18_mock_auth_req = {
    "client_id": "some did",
    "client_id_scheme": "did",
    "client_metadata": {
        "data": "metadata in this object"
    },
    "presentation_definition": {
        "id": "verify_over_18",
        "input_descriptors": [
            {
                "id": "over_18_descriptor",
                "constraints": {
                    "fields": [
                        {
                            "path": [
                                "$.credentialSubject.is_over_18",
                                "$.is_over_18"
                            ],
                            "filter": {
                                "type": "string"
                            },
                            "optional": False
                        }
                    ]
                },
                "name": "Over 18 Verification",
                "purpose": "To verify that the individual is over 18 years old"
            }
        ]
    },
    "response_uri": "http://example.com/cb",
    "response_type": "vp_token",
    "response_mode": "direct_post",
    "nonce": "some nonce",
    "wallet_nonce": "nonce_here",
    "state": "d1d9846b-0f0e-4716-8178-88a6e76f1673_1721045932"
}

MOCK_STORE = {
    "example1": {
        "id": "example1",
        "issuer_url": "https://example.com",
        "type": "Example",
        "request_url": "https://example.com/status?token=example1",
        "token": "qwertyuiop",
        "status": "ACCEPTED",
        "status_message": None,
        "issuer_name": "Example Issuer",
        "received_at": 1719295821397,
    },
    "example2": {
        "id": "example2",
        "issuer_url": "https://example.com",
        "type": "Example",
        "request_url": "https://example.com/status?token=example2",
        "token": None,
        "status": "PENDING",
        "status_message": None,
        "issuer_name": "Example Issuer",
        "received_at": None,
    },
}

###################
### TESTING VPs ###
###################
@pytest.mark.asyncio()
async def test_vp_flow(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="http://example.com/request/over_18",
        json=over_18_mock_auth_req)
    identity_owner = DefaultWebIdentityOwner("", mock_data=MOCK_STORE)
    identity_owner.vc_credentials.append(
        "eyJhbGciOiAiRVMyNTYiLCAidHlwIjogInZjK3NkLWp3dCJ9.eyJfc2QiOiBbIktJMWx6b21fcVAwVzBKUDdaLVFYVkZrWmV1MElkajJKYTdLcmZPWFdORDQiLCAiUVhOUDk2TkUxZ21kdHdTTE4xeE9pbXZLX20wTVZ2czBBdTJUU1J0ZS1oOCIsICJTSHdLdjhKX09kQU1mS3NtOTJ3eHF0UXZRdFhyVWQwcm9ubkNGZXkySEJvIiwgInpaaFZVdkNodi1JSDBpaWRobFBQVDE1Zk5QbTRGZGRmMlREcG1EUllWUXciXSwgImlhdCI6IDE3MjA5NTIxMTYuMCwgIl9zZF9hbGciOiAic2hhLTI1NiJ9.fFbkA1FLMDT36Y48rxtOfUC76zgWxZAYLQnEWKgi02nubV2b7U7A45b3080USYGRxJ7AYi4GG-3vx1QPM_00lw~WyJNN01oQkhpVk5JYjBxMGFQS0ZkVnpBIiwgImdpdmVuX25hbWUiLCAiQSJd~WyJ1UGJaQUFHS0VjcGY2UzBHT3FMRFZ3IiwgImZhbWlseV9uYW1lIiwgIkIiXQ~WyJZQU12TWZnVW9OZW5HNm4xREY1bHlBIiwgImJpcnRoZGF0ZSIsIDIwMDBd~WyJaNFdITlBNWkZIM0JOS19haXVKZnBnIiwgImlzX292ZXJfMTgiLCAidHJ1ZSJd~"
    )
    resp = await identity_owner.get_auth_request(
        "http://example.com/request/over_18",
        "some did",
        "did",
        "post")

    assert resp == over_18_mock_auth_req

    httpx_mock.add_response(
        url="http://example.com/cb",
        json={"status": "OK"},
        method='post')

    resp = await identity_owner.present_selection(over_18_mock_field_selection)

    assert resp == {"status": "OK"}


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
