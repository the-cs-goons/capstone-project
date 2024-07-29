# TODO: uncomment these once they can be handled properly
from jwcrypto.jwk import JWKSet
from pydantic import BaseModel, ConfigDict, Field


class AuthorizationServerMetadata(BaseModel):
    issuer: str
    authorization_endpoint: str | None = Field(default=None)
    token_endpoint: str | None = Field(default=None)
    # jwks_uri: str | None = Field(default=None)
    registration_endpoint: str | None = Field(default=None)
    scopes_supported: list[str] | None = Field(default=None)
    response_types_supported: list[str]
    # response_modes_supported: list[str] = Field(default=["query", "fragment"])
    grant_types_supported: list[str] = Field(default=["authorization_code", "implicit"])
    # token_endpoint_auth_methods_supported: list[str] = Field(
    #     default=["client_secret_basic"]
    # )
    # token_endpoint_auth_signing_alg_values_supported: list[str] | None = Field(
    #     default=None
    # )
    # service_documentation: str | None = Field(default=None)
    # ui_locales_supported: list[str] | None = Field(default=None)
    # op_policy_uri: str | None = Field(default=None)
    # op_tos_uri: str | None = Field(default=None)
    # revocation_endpoint: str | None = Field(default=None)
    # revocation_endpoint_auth_methods_supported: list[str] | None = Field(default=None)
    # revocation_endpoint_auth_signing_alg_values_supported: list[str] | None = Field(
    #     default=None
    # )
    # introspection_endpoint: str | None = Field(default=None)
    # introspection_endpoint_auth_methods_supported: list[str] | None = Field(
    #    default=None
    # )
    # introspection_endpoint_auth_signing_alg_values_supported: list[str]| None = Field(
    #    default=None
    # )
    # code_challenge_methods_supported: list[str] | None = Field(default=None)
    # request_object_signing_alg_values_supported: list[str] | None= Field(default=None)


class IssuerOAuth2ServerMetadata(AuthorizationServerMetadata):
    pre_authorized_supported: bool = Field(
        serialization_alias="pre-authorized_grant_anonymous_access_supported",
        default=False,
    )
    authorization_details_types_supported: list[str] | None = Field(default=None)


class HolderOAuth2ServerMetadata(AuthorizationServerMetadata):
    request_object_signing_alg_values_supported: list[str] | None = Field(default=None)
    presentation_definition_uri_supported: bool = Field(default=True)
    vp_formats_supported: dict[str, dict[str, list[str]]]
    client_id_schemes_supported: list[str] = Field(default=["pre-registered"])


class ClientMetadata(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    redirect_uris: list[str]
    token_endpoint_auth_method: str = Field(default="client_secret_basic")
    grant_types: list[str] = Field(default=["authorization_code"])
    response_types: list[str] = Field(["code"])
    client_name: str | None = Field(default=None)
    client_uri: str | None = Field(default=None)
    logo_uri: str | None = Field(default=None)
    scope: str | None = Field(default=None)
    contacts: list[str] | None = Field(default=None)
    tos_uri: str | None = Field(default=None)
    policy_uri: str | None = Field(default=None)
    jwks_uri: str | None = Field(default=None)
    jwks: JWKSet | None = Field(default=None)
    software_id: str | None = Field(default=None)
    software_version: str | None = Field(default=None)


class RegisteredClientMetadata(ClientMetadata):
    client_id: str
    client_secret: str | None = Field(default=None)
    client_id_issued_at: int | None = Field(default=None)
    client_secret_expires_at: int | None = Field(default=None)

    # present here to allow mapping of metadata to issuer the client registered with
    issuer_uri: str


class HolderOAuth2ClientMetadata(ClientMetadata):
    credential_offer_endpoint: str | None = Field(default=None)
    authorization_details_types: list[str] | None = Field(default=None)


class HolderOAuth2RegisteredClientMetadata(
    HolderOAuth2ClientMetadata, RegisteredClientMetadata
):
    pass


class AuthorizationDetailsObject(BaseModel):
    type: str
    locations: list[str] | None = Field(default=None)
    actions: list[str] | None = Field(default=None)
    datatypes: list[str] | None = Field(default=None)
    identifier: str | None = Field(default=None)
    privileges: list[str] | None = Field(default=None)


# if using format, intended to be extended for different credential format types
class OpenIDAuthorizationDetailsObject(AuthorizationDetailsObject):
    credential_configuration_id: str | None = Field(default=None)
    format: str | None = Field(default=None)
    credential_identifiers: list[str] | None = Field(default=None)


class AuthorizationRequestObject(BaseModel):
    response_type: str
    response_mode: str | None = Field(default=None)
    scope: str | None = Field(default=None)
    authorization_details: list[OpenIDAuthorizationDetailsObject] | None = Field(
        default=None
    )
    redirect_uri: str | None = Field(default=None)
    state: str | None = Field(default=None)
    client_id: str


class AuthorizationResponseObject(BaseModel):
    state: str | None = Field(default=None)
    scope: str | None = Field(default=None)
    error: str | None = Field(default=None)
    error_description: str | None = Field(default=None)
    error_uri: str | None = Field(default=None)


class AuthorizationCodeResponseObject(AuthorizationResponseObject):
    code: str


class ImplicitResponseObject(AuthorizationResponseObject):
    access_token: str
    token_type: str
    expires_in: int


class TokenRequestObject(BaseModel):
    grant_type: str
    redirect_uri: str | None = Field(default=None)
    scope: str | None = Field(default=None)
    authorization_details: list[OpenIDAuthorizationDetailsObject] | None = Field(
        default=None
    )
    code: str | None = Field(default=None)
    username: str | None = Field(default=None)
    password: str | None = Field(default=None)


class TokenResponseObject(BaseModel):
    access_token: str | None = Field(default=None)
    token_type: str | None = Field(default=None)
    expires_in: int | None = Field(default=None)
    scope: str | None = Field(default=None)
    authorization_details: list[OpenIDAuthorizationDetailsObject] | None = Field(
        default=None
    )
    error: str | None = Field(default=None)
    error_description: str | None = Field(default=None)
    error_uri: str | None = Field(default=None)
