from datetime import datetime

from vclib.owner import Credential, IdentityOwner


def test_serialise_and_load_credentials():
    credential = Credential(
        id="example",
        issuer_url="https://example.com",
        type="Example",
        request_url="https://example.com/status?token=example",
        token="{'foo': 'bar'}",
        status="PENDING",
        status_message=None,
        issuer_name="Example Issuer",
        received_at=datetime.now(),
    )

    id_owner = IdentityOwner("example")
    store = id_owner.serialise_and_encrypt(credential)
    credential2 = id_owner.load_from_serial(store)

    assert credential.id == credential2.id
    assert credential.issuer_url == credential2.issuer_url
    assert credential.type == credential2.type
    assert credential.request_url == credential2.request_url
    assert credential.token == credential2.token
    assert credential.status == credential2.status
    assert credential.status_message == credential2.status_message
    assert credential.status == credential2.status
    assert credential.issuer_name == credential2.issuer_name
    assert credential.received_at == credential2.received_at
