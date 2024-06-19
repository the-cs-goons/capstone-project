import pytest
from issuer import CredentialIssuer


@pytest.mark.asyncio
async def test_hello_world():
    credential_issuer = CredentialIssuer()
    response = await credential_issuer.hello_world()
    assert response.hello == "Hello"
    assert response.world == "World"
