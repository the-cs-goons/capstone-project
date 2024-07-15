import pytest

from vclib.owner import Credential, DeferredCredential, IdentityOwner

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
def credential_obj():
    return MOCK_STORE["example1"]

@pytest.fixture()
def deferred_credential_obj():
    return MOCK_STORE["example2"]

def test_serialise_and_load_credentials(credential_obj, deferred_credential_obj):
    credential = Credential.model_validate(credential_obj)
    deferred = DeferredCredential.model_validate(deferred_credential_obj)

    id_owner = IdentityOwner(
        {
            "redirect_uris": ["example"],
            "credential_offer_endpoint": "example"
            }
        )
    store = id_owner.serialise(credential)
    deferred_store = id_owner.serialise(deferred)
    credential2 = id_owner.load_from_serial(store)
    deferred2 = id_owner.load_from_serial(deferred_store)

    assert isinstance(credential2, Credential)
    assert not isinstance(credential2, DeferredCredential)

    assert isinstance(deferred2, DeferredCredential)
    assert not isinstance(deferred2, Credential)

    assert credential.id == credential2.id
    assert credential.issuer_url == credential2.issuer_url
    assert credential.c_type == credential2.c_type
    assert credential.raw_sdjwtvc == credential2.raw_sdjwtvc


    assert deferred.id == deferred2.id
    assert deferred.issuer_url == deferred2.issuer_url
    assert deferred.c_type == deferred2.c_type
    endpoint = deferred.deferred_credential_endpoint
    assert endpoint == deferred2.deferred_credential_endpoint
