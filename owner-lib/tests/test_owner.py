import pytest

from owner import IdentityOwner

@pytest.mark.asyncio
async def test_hello_world():
    identity_owner = IdentityOwner()
    response = await identity_owner.hello_world()
    assert response.hello == "Hello"
    assert response.world == "World"
