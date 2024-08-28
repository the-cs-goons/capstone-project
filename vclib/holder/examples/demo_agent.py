from os import environ
from typing import override

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from vclib.holder import (
    AuthorizationMetadata,
    Credential,
    IssuerMetadata,
    RegisteredClientMetadata,
    WebHolder,
)
from vclib.holder.src.storage.local_storage_provider import LocalStorageProvider

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
OWNER_HOST = environ.get("CS3900_HOLDER_AGENT_HOST", "https://localhost")
OWNER_PORT = environ.get("CS3900_HOLDER_AGENT_PORT", "8081")
OWNER_URI = f"{OWNER_HOST}:{OWNER_PORT}"


class DemoWebHolder(WebHolder):
    def __init__(
        self,
        redirect_uris,
        cred_offer_endpoint,
        storage_provider,
        *,
        mock_uri=OWNER_URI,
        oauth_client_options={},
    ):
        self.mock_uri = mock_uri
        super().__init__(
            redirect_uris,
            cred_offer_endpoint,
            storage_provider,
            oauth_client_options=oauth_client_options,
        )

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

    @override
    def get_server(self) -> FastAPI:
        server = super().get_server()
        server.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        return server


WALLET_PATH = environ.get("CS3900_HOLDER_WALLET_PATH", None)
storage_provider = LocalStorageProvider(storage_dir_path=WALLET_PATH)

credential_holder = DemoWebHolder(
    [f"{OWNER_URI}/add"], f"{OWNER_URI}/offer", storage_provider
)
credential_holder.issuer_metadata_store[EXAMPLE_ISSUER] = IssuerMetadata(
    credential_issuer=EXAMPLE_ISSUER,
    credential_configurations_supported={"ExampleCredential": {}},
    credential_endpoint=EXAMPLE_ISSUER + "/get_credential",
)
credential_holder.auth_metadata_store[EXAMPLE_ISSUER] = AuthorizationMetadata(
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
    id="mock_photocard",
    raw_sdjwtvc="eyJhbGciOiAiRVMyNTYiLCAidHlwIjogInZjK3NkLWp3dCJ9.eyJfc2QiOiBbIjFlZ0VpSl9Ga1pud0hwWnE4cklYd1ZLME5PVS1GNldTNVBxaVpsTm1tUkkiLCAiR3A1THpzOURES3pVcmJLT2dkMnJncEZNTGIyQzg5OHpiamtaeXdoeGtQUSIsICJKY1JPRHNGMGlaY1UybFVEWFB2M0pBWGFSZmhlNUNrREZNZkZuQXdtSzI0IiwgIlBiTUQ3ckZtWmJoMzhOREkwN3NzMGlXLUtGUWdvbmlwZzZlR1JkeGl5QTQiLCAiVklpYWo4Ukg0SUZKVE5FMXVibm9ReEtuc21Db3hkd3VOa2kxV1NmOTBxWSIsICJmM1NIWVhWc0tVcDRqeFZaS282bWZaTGhSV3NXTU52M0phVUtSN1ktSDBVIl0sICJpc3MiOiAiaHR0cHM6Ly9pc3N1ZXItbGliOjgwODIiLCAiaWF0IjogMTcyMjMyMDk4Mi4wLCAiX3NkX2FsZyI6ICJzaGEtMjU2In0.LCF0HaHb8rInRtTrO_S9dsJ6zOWsb5AMyY-Ue7LvG2Cjv-laD4he2eK1bhiEAlJeKpRdACvK7bOOl3E8BUI52A~WyJrUFdNT2ItNHkwY25fM0xvSTF0ckF3IiwgImdpdmVuX25hbWUiLCAiQUJDIl0~WyJxNGF2MnNFVldrM1NKc3FKLXFGWjZRIiwgImZhbWlseV9uYW1lIiwgIkQiXQ~WyJMVnBKUjFiRXBnejNlT0E2bk5YUS1BIiwgImNvdW50cnkiLCAiQXVzdHJhbGlhIl0~WyJ2dU40SU9YdDRPRmVmU19ZbjA2NGRnIiwgImFkZHJlc3MiLCB7Il9zZCI6IFsiNFZxZ3dmd2NKUGxQLTJNWXN6cTlGSFRjQ2l2VXpMWVI3Qmx3M1F1ZnFUQSJdfV0~WyJfWlBQakVYUmQwYjU0cGpRQlQ1Ri13IiwgIm5hdGlvbmFsaXRpZXMiLCBbIkFVIl1d~WyJabnRhclNRc2hBYW9MZTJPTmhGOWhBIiwgImJpcnRoZGF0ZSIsIDIwMDFd~WyIyOHBDdE5SN1k1OWI5WF85eWozUUhBIiwgImlzX292ZXJfMTgiLCB0cnVlXQ~",
    issuer_url="https://example.com",
    credential_configuration_id="DriversLicense",
    is_deferred=False,
    received_at="12345",
    c_type="sd_jwt",
)

credential_holder.store._purge_db()
credential_holder.store.register("asdf", "1234567890")
credential_holder.store.add_credential(cred)
credential_holder_server = credential_holder.get_server()
