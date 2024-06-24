import pytest
from owner import IdentityOwner


@pytest.mark.asyncio
async def test_hello_world():
    identity_owner = IdentityOwner("hello")
    identity_owner.credentials

