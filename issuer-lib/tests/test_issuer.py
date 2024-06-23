import json

import pytest
from fastapi import Request
from issuer import CredentialIssuer


@pytest.mark.asyncio
async def test_request_credential():
    credential_issuer = CredentialIssuer()

    response = await credential_issuer.recieve_credential_request("Test", "ABC")
    assert response.ticket == 1
    assert response.link == "1"

    information = json.dumps(
        {"name": "Name Lastname", "age": 30, "address": "123 Street St", "adult": True}
    )
    response = await credential_issuer.recieve_credential_request("ID", information)
    assert response.ticket == 2
    assert response.link == "2"

    response = await credential_issuer.recieve_credential_request("None")
    assert response.ticket == 3
    assert response.link == "3"

@pytest.mark.asyncio
async def test_check_credential_status():
    credential_issuer = CredentialIssuer()

    information = json.dumps(
        {"name": "Name Lastname", "age": 30, "address": "123 Street St", "adult": True}
    )
    response = await credential_issuer.recieve_credential_request("Test1", information)
    assert response.ticket == 1
    assert response.link == "1"

    response = await credential_issuer.recieve_credential_request("Test2", 20)
    assert response.ticket == 2
    assert response.link == "2"
    
    response = await credential_issuer.credential_status("1")
    assert response.ticket == 1
    assert response.status == "Pending"

    response = await credential_issuer.credential_status("2")
    assert response.ticket == 2
    assert response.status == "Pending"
