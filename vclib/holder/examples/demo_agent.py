from os import environ
from typing import override

from vclib.holder import (
    AuthorizationMetadata,
    Credential,
    IssuerMetadata,
    RegisteredClientMetadata,
    WebIdentityOwner,
)
from vclib.holder.src.models.credentials import DeferredCredential

MOCK_STORE = {
    "example1": {
        "id": "example1",
        "issuer_url": "https://example.com",
        "issuer_name": "Example Issuer",
        "credential_configuration_id": "Passport",
        "is_deferred": False,
        "c_type": "openid_credential",
        # TODO: Make this a proper sdjwt?
        "raw_sdjwtvc": "eyJuYW1lIjoiTWFjayBDaGVlc2VNYW4iLCJkb2IiOiIwMS8wMS8wMSIsImV4cGlyeSI6IjEyLzEyLzI1In0=",  # noqa: E501
        "received_at": "2024-07-15T02:54:13.634808+00:00",
    },
    # "example2": {
    #     "id": "example2",
    #     "issuer_url": "https://example.com",
    #     "issuer_name": "Example Issuer",
    #     "credential_configuration_id": "DriverLicence",
    #     "is_deferred": True,
    #     "c_type": "openid_credential",
    #     "transaction_id": "1234567890",
    #     "deferred_credential_endpoint": "https://example.com/deferred",
    #     "last_request": "2024-07-15T02:54:13.634808+00:00",
    #     "access_token": {
    #         "access_token": "exampletoken",
    #         "token_type": "bearer",
    #         "expires_in": 99999999999,
    #     },
    # },
}

EXAMPLE_ISSUER = "https://example.com"
OWNER_HOST = environ.get("CS3900_OWNER_AGENT_HOST", "https://localhost")
OWNER_PORT = environ.get("CS3900_OWNER_AGENT_PORT", "8081")
OWNER_URI = f"{OWNER_HOST}:{OWNER_PORT}"


class DemoWebIdentityOwner(WebIdentityOwner):
    def __init__(
        self,
        redirect_uris,
        cred_offer_endpoint,
        *,
        mock_uri=OWNER_URI,
        oauth_client_options={},
        mock_data={},
        dev_mode=False,
    ):
        self.MOCK_STORE: dict = mock_data
        self.mock_uri = mock_uri
        super().__init__(
            redirect_uris,
            cred_offer_endpoint,
            oauth_client_options=oauth_client_options,
            dev_mode=dev_mode,
        )

    @override
    def load_all_credentials_from_storage(
        self,
    ) -> list[Credential | DeferredCredential]:
        creds = []
        cred: dict
        for cred in self.MOCK_STORE.values():
            new: Credential | DeferredCredential
            if cred.get("is_deferred"):
                new = DeferredCredential.model_validate(cred)
            else:
                new = Credential.model_validate(cred)
            creds.append(new)
        return creds

    @override
    def load_credential_from_storage(self, cred_id: str) -> Credential:
        return self.MOCK_STORE[cred_id]

    @override
    def store_credential(self, cred: Credential):
        self.MOCK_STORE[cred.id] = cred

    @override
    async def register_client(
        self, registration_url, issuer_uri, wallet_metadata=None
    ) -> RegisteredClientMetadata:
        if registration_url == "https://example.com/oauth2/register":
            return RegisteredClientMetadata(
                redirect_uris=[f"{self.mock_uri}/add"],
                credential_offer_endpoint=f"{self.mock_uri}/offer",
                issuer_uri=issuer_uri,
                client_id="example_client_id",
                client_secret="example_client_secret",
            )
        return await super().register_client(
            registration_url, issuer_uri, wallet_metadata=wallet_metadata
        )
    



identity_owner = DemoWebIdentityOwner(
    [f"{OWNER_URI}/add"], f"{OWNER_URI}/offer", mock_data=MOCK_STORE
)
identity_owner.issuer_metadata_store[EXAMPLE_ISSUER] = IssuerMetadata(
    credential_issuer=EXAMPLE_ISSUER,
    credential_configurations_supported={"ExampleCredential": {}},
    credential_endpoint=EXAMPLE_ISSUER + "/get_credential",
)
identity_owner.auth_metadata_store[EXAMPLE_ISSUER] = AuthorizationMetadata(
    issuer=EXAMPLE_ISSUER,
    authorization_endpoint=EXAMPLE_ISSUER + "/oauth2/authorize",
    registration_endpoint=EXAMPLE_ISSUER + "/oauth2/register",
    token_endpoint=EXAMPLE_ISSUER + "/oauth2/token",
    response_types_supported=["code"],
    grant_types_supported=["authorization_code"],
    authorization_details_types_supported=["openid_credential"],
    **{"pre-authorized_grant_anonymous_access_supported": False},
)

cred = Credential(
    id="yalo",
    raw_sdjwtvc="eyJhbGciOiAiRVMyNTYiLCAidHlwIjogInZjK3NkLWp3dCJ9.eyJfc2QiOiBbIktJMWx6b21fcVAwVzBKUDdaLVFYVkZrWmV1MElkajJKYTdLcmZPWFdORDQiLCAiUVhOUDk2TkUxZ21kdHdTTE4xeE9pbXZLX20wTVZ2czBBdTJUU1J0ZS1oOCIsICJTSHdLdjhKX09kQU1mS3NtOTJ3eHF0UXZRdFhyVWQwcm9ubkNGZXkySEJvIiwgInpaaFZVdkNodi1JSDBpaWRobFBQVDE1Zk5QbTRGZGRmMlREcG1EUllWUXciXSwgImlhdCI6IDE3MjA5NTIxMTYuMCwgIl9zZF9hbGciOiAic2hhLTI1NiJ9.fFbkA1FLMDT36Y48rxtOfUC76zgWxZAYLQnEWKgi02nubV2b7U7A45b3080USYGRxJ7AYi4GG-3vx1QPM_00lw~WyJNN01oQkhpVk5JYjBxMGFQS0ZkVnpBIiwgImdpdmVuX25hbWUiLCAiQSJd~WyJ1UGJaQUFHS0VjcGY2UzBHT3FMRFZ3IiwgImZhbWlseV9uYW1lIiwgIkIiXQ~WyJZQU12TWZnVW9OZW5HNm4xREY1bHlBIiwgImJpcnRoZGF0ZSIsIDIwMDBd~WyJaNFdITlBNWkZIM0JOS19haXVKZnBnIiwgImlzX292ZXJfMTgiLCAidHJ1ZSJd~",
    issuer_url="https://example.com",
    credential_configuration_id="ExampleCredential",
    is_deferred=False,
    received_at="12345",
    c_type="sd_jwt",
)
identity_owner.credentials["yalo"] = cred

identity_owner_server = identity_owner.get_server()


