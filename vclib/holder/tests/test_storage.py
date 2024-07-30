from datetime import UTC, datetime

import pytest

from vclib.common import credentials
from vclib.holder import LocalStorageProvider

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
            "expires_in": 99999999999,
        },
    },
    "example3": {
        "id": "example3",
        "issuer_url": "https://example.com",
        "issuer_name": "Example Issuer",
        "credential_configuration_id": "EVIL Driver's Licence",
        "is_deferred": True,
        "c_type": "openid_credential",
        "transaction_id": "0987654321",
        "deferred_credential_endpoint": "https://example.com/deferred",
        "last_request": "2024-07-15T02:54:13.634808+00:00",
        "access_token": {
            "access_token": "exampletoken2",
            "token_type": "bearer",
            "expires_in": 99999999999,
        },
    },
}


@pytest.fixture()
def storage_provider(tmpdir):
    return LocalStorageProvider(storage_dir_path=tmpdir)


@pytest.fixture()
def cred_1():
    return credentials.Credential.model_validate(MOCK_STORE["example1"])


@pytest.fixture()
def cred_2():
    return credentials.DeferredCredential.model_validate(MOCK_STORE["example2"])


@pytest.fixture()
def cred_3():
    return credentials.DeferredCredential.model_validate(MOCK_STORE["example3"])


def test_register_and_login(storage_provider):
    with pytest.raises(Exception):
        storage_provider.login("Steve", "hunter2")

    storage_provider.register("Steve", "hunter2")
    assert storage_provider.get_active_user_name() == "Steve"

    storage_provider.logout()
    assert not storage_provider.get_active_user_name()
    with pytest.raises(Exception):
        storage_provider.get_db_conn()

    with pytest.raises(Exception):
        storage_provider.register("Steve", "hunter2")
    with pytest.raises(Exception):
        storage_provider.login("Steve", "hunter3")
    with pytest.raises(Exception):
        storage_provider.login("steve", "hunter2")

    storage_provider.login("Steve", "hunter2")
    assert storage_provider.get_active_user_name() == "Steve"


def test_no_logged_out_access(storage_provider, cred_1):
    storage_provider.register("logout", "logout")
    storage_provider.add_credential(cred_1)
    storage_provider.logout()

    with pytest.raises(Exception):
        storage_provider.get_credential(cred_1.id)


def test_add_credential(storage_provider, cred_1):
    storage_provider.register("add_one", "add_one")
    storage_provider.add_credential(cred_1)

    storage_provider.logout()
    storage_provider.login("add_one", "add_one")

    c = storage_provider.get_credential(cred_1.id)
    assert c.id == cred_1.id
    assert c.received_at == cred_1.received_at


def test_add_credentials(storage_provider, cred_1, cred_2, cred_3):
    storage_provider.register("add_many", "add_many")
    storage_provider.add_many([cred_1, cred_2, cred_3])

    c = storage_provider.get_credential(cred_1.id)
    assert c.id == cred_1.id

    storage_provider.logout()
    storage_provider.login("add_many", "add_many")

    assert len(storage_provider.all_credentials()) == 3
    assert len(storage_provider.get_deferred_credentials()) == 2
    assert len(storage_provider.get_received_credentials()) == 1


def test_delete_credential(storage_provider, cred_1, cred_2, cred_3):
    storage_provider.register("delete", "delete")
    storage_provider.add_many([cred_1, cred_2, cred_3])

    storage_provider.delete_credential(cred_1.id)
    with pytest.raises(Exception):
        storage_provider.get_credential(cred_1.id)

    assert len(storage_provider.all_credentials()) == 2


def test_delete_credentials(storage_provider, cred_1, cred_2, cred_3):
    storage_provider.register("delete_many", "delete_many")
    storage_provider.add_many([cred_1, cred_2, cred_3])

    storage_provider.delete_many([cred_1.id, cred_2.id, cred_3.id])
    with pytest.raises(Exception):
        storage_provider.get_credential(cred_1.id)

    storage_provider.logout()
    storage_provider.login("delete_many", "delete_many")

    assert len(storage_provider.all_credentials()) == 0


def test_update_credential(storage_provider, cred_1, cred_2, cred_3):
    storage_provider.register("update", "update")
    storage_provider.add_many([cred_1, cred_2, cred_3])

    assert len(storage_provider.get_deferred_credentials()) == 2
    assert len(storage_provider.get_received_credentials()) == 1

    cred_2.is_deferred = False
    update_2 = credentials.Credential(
        **cred_2.model_dump(),
        raw_sdjwtvc="not_real_vc",
        received_at=datetime.now(tz=UTC).isoformat(),
    )
    storage_provider.update_credential(update_2)

    assert len(storage_provider.get_deferred_credentials()) == 1
    assert len(storage_provider.get_received_credentials()) == 2


def test_update_credentials(storage_provider, cred_1, cred_2, cred_3):
    storage_provider.register("update_many", "update_many")
    storage_provider.add_many([cred_1, cred_2, cred_3])

    assert len(storage_provider.get_deferred_credentials()) == 2
    assert len(storage_provider.get_received_credentials()) == 1

    cred_2.is_deferred = False
    update_2 = credentials.Credential(
        **cred_2.model_dump(),
        raw_sdjwtvc="not_real_vc",
        received_at=datetime.now(tz=UTC).isoformat(),
    )

    cred_3.is_deferred = False
    update_3 = credentials.Credential(
        **cred_3.model_dump(),
        raw_sdjwtvc="not_real_vc_2",
        received_at=datetime.now(tz=UTC).isoformat(),
    )
    storage_provider.update_many([update_2, update_3])

    assert len(storage_provider.get_deferred_credentials()) == 0
    assert len(storage_provider.get_received_credentials()) == 3


def test_upsert_credential(storage_provider, cred_1, cred_2, cred_3):
    storage_provider.register("upsert", "upsert")
    storage_provider.add_many([cred_1, cred_2])

    cred_2.is_deferred = False
    update_2 = credentials.Credential(
        **cred_2.model_dump(),
        raw_sdjwtvc="not_real_vc",
        received_at=datetime.now(tz=UTC).isoformat(),
    )
    storage_provider.upsert_credential(update_2)
    storage_provider.upsert_credential(cred_3)

    assert len(storage_provider.get_deferred_credentials()) == 1
    assert len(storage_provider.get_received_credentials()) == 2
    assert len(storage_provider.all_credentials()) == 3


def test_upsert_credentials(storage_provider, cred_1, cred_2, cred_3):
    storage_provider.register("upsert_many", "upsert_many")
    storage_provider.add_many([cred_1, cred_2])

    cred_2.is_deferred = False
    update_2 = credentials.Credential(
        **cred_2.model_dump(),
        raw_sdjwtvc="not_real_vc",
        received_at=datetime.now(tz=UTC).isoformat(),
    )
    storage_provider.upsert_many([update_2, cred_3])

    assert len(storage_provider.get_deferred_credentials()) == 1
    assert len(storage_provider.get_received_credentials()) == 2
    assert len(storage_provider.all_credentials()) == 3
