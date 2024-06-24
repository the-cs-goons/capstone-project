import pytest
from service import ServiceProvider


@pytest.mark.asyncio
async def test_hello_world():
    service_provider = ServiceProvider("test_bundel", "/test_path")
    response = await service_provider.hello_world()
    assert response.hello == "Hello"
    assert response.world == "World"
