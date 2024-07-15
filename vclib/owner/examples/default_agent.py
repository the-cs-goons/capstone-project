from typing import override

import httpx
from fastapi import Body, FastAPI, HTTPException
import jsonpath_ng

from vclib.common import hello_world
from vclib.owner import Credential, WebIdentityOwner
from vclib.owner.src.models.authorization_request_object import (
    AuthorizationRequestObject,
)
from vclib.owner.src.models.field_selection_object import FieldSelectionObject

MOCK_STORE = {
    "example1": {
        "id": "example1",
        "issuer_url": "https://example.com",
        "type": "Passport",
        "request_url": "https://example.com/status?token=example1",
        "token": "eyJuYW1lIjoiTWFjayBDaGVlc2VNYW4iLCJkb2IiOiIwMS8wMS8wMSIsImV4cGlyeSI6IjEyLzEyLzI1In0=",  # noqa: E501
        "status": "ACCEPTED",
        "status_message": None,
        "issuer_name": "Example Issuer",
        "received_at": 1719295821397,
    },
    "example2": {
        "id": "example2",
        "issuer_url": "https://example.com",
        "type": "Driver's Licence",
        "request_url": "https://example.com/status?token=example2",
        "token": None,
        "status": "PENDING",
        "status_message": None,
        "issuer_name": "Example Issuer",
        "received_at": None,
    },
}


class DefaultWebIdentityOwner(WebIdentityOwner):
    def __init__(self, storage_key, mock_data=None, *, dev_mode=False):
        if mock_data is None:
            mock_data = {}
        self.MOCK_STORE = mock_data
        super().__init__(storage_key, dev_mode=dev_mode)

    @override
    def load_all_credentials_from_storage(self) -> list[Credential]:
        return [Credential.model_validate(cred) for cred in self.MOCK_STORE.values()]

    @override
    def load_credential_from_storage(self, cred_id: str) -> Credential:
        return self.MOCK_STORE[cred_id]

    @override
    def store_credential(self, cred: Credential):
        self.MOCK_STORE[cred.id] = cred

    @override
    def get_server(self) -> FastAPI:
        router = super().get_server()
        router.get("/hello")(hello_world)
        return router

    @override
    async def get_auth_request(
            self,
            request_uri = Body(...),
            client_id = Body(...),
            client_id_scheme = Body(...),
            request_uri_method = Body(...)
            ): #-> PresentationDefinition:

        if client_id_scheme != "did":
            raise HTTPException(
                status_code=400,
                detail=f"client_id_scheme {client_id_scheme} not supported")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                # f"http://provider-lib:{os.getenv('CS3900_SERVICE_AGENT_PORT')}/request/age_verification",
                f"{request_uri}",
                data={
                    "wallet_nonce": "nonce", # replace this data with actual stuff
                    "wallet_metadata": "metadata"
                })
        # just send the presentation definition to the frontend for now
        # what the backend sends to the fronend should be up to implementation
        auth_request = response.json()
        self.current_transaction = AuthorizationRequestObject(**auth_request)
        return auth_request



identity_owner = DefaultWebIdentityOwner("", mock_data=MOCK_STORE)

identity_owner.vc_credentials.append("eyJhbGciOiAiRVMyNTYiLCAidHlwIjogInZjK3NkLWp3dCJ9.eyJfc2QiOiBbIktJMWx6b21fcVAwVzBKUDdaLVFYVkZrWmV1MElkajJKYTdLcmZPWFdORDQiLCAiUVhOUDk2TkUxZ21kdHdTTE4xeE9pbXZLX20wTVZ2czBBdTJUU1J0ZS1oOCIsICJTSHdLdjhKX09kQU1mS3NtOTJ3eHF0UXZRdFhyVWQwcm9ubkNGZXkySEJvIiwgInpaaFZVdkNodi1JSDBpaWRobFBQVDE1Zk5QbTRGZGRmMlREcG1EUllWUXciXSwgImlhdCI6IDE3MjA5NTIxMTYuMCwgIl9zZF9hbGciOiAic2hhLTI1NiJ9.fFbkA1FLMDT36Y48rxtOfUC76zgWxZAYLQnEWKgi02nubV2b7U7A45b3080USYGRxJ7AYi4GG-3vx1QPM_00lw~WyJNN01oQkhpVk5JYjBxMGFQS0ZkVnpBIiwgImdpdmVuX25hbWUiLCAiQSJd~WyJ1UGJaQUFHS0VjcGY2UzBHT3FMRFZ3IiwgImZhbWlseV9uYW1lIiwgIkIiXQ~WyJZQU12TWZnVW9OZW5HNm4xREY1bHlBIiwgImJpcnRoZGF0ZSIsIDIwMDBd~WyJaNFdITlBNWkZIM0JOS19haXVKZnBnIiwgImlzX292ZXJfMTgiLCAidHJ1ZSJd~")

identity_owner_server = identity_owner.get_server()
