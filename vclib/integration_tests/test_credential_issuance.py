from typing import NamedTuple

import pytest
from fastapi.testclient import TestClient

from vclib.integration_tests.test_issuer_class import TestIssuerBase
from vclib.integration_tests.test_owner_class import (
    MOCK_STORE,
    OWNER_URI,
    TestOwnerBase,
)


class IssuanceServers(NamedTuple):
    issuer: TestClient
    owner: TestClient


@pytest.fixture()
def vci_servers():
    issuer = TestIssuerBase(
        "vclib/issuer/tests/test_jwk_private.pem",
        "vclib/integration_tests/fixtures/test_diddoc.json",
        "vclib/integration_tests/fixtures/test_didconf.json",
        "vclib/integration_tests/fixtures/metadata/test_metadata_basic.json",
        "vclib/integration_tests/fixtures/test_oauth_metadata.json",
    )

    owner = TestOwnerBase(
        [f"{OWNER_URI}/add"], f"{OWNER_URI}/offer", mock_data=MOCK_STORE
    )

    return IssuanceServers(
        TestClient(issuer.get_server()), TestClient(owner.get_server())
    )


@pytest.mark.asyncio()
async def test_metadata(vci_servers):
    response = vci_servers.issuer.get("/.well-known/did.json")
    assert response.status_code == 200

