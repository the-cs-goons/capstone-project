from datetime import UTC, datetime
from json import dumps, loads
from typing import Any
from urllib.parse import urlencode

import httpx
import jsonpath_ng
import jwt
from jsonschema import validate
from requests import Response, Session
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session
from sd_jwt.common import SDJWTCommon

from .models.client_metadata import RegisteredClientMetadata, WalletClientMetadata
from .models.credential_offer import CredentialOffer
from .models.credentials import Credential, DeferredCredential
from .models.issuer_metadata import AuthorizationMetadata, IssuerMetadata
from .models.oauth import AccessToken, OAuthTokenResponse
from .storage.abstract_storage_provider import AbstractStorageProvider


class Holder:
    """
    ## Base IdentityOwner class

    ### Attributes
    - oauth_clients(`dict[str, RegisteredClientMetadata]`): A dictionary of objects
    representing registered OAuth2 clients. At any given time, the user may have
    multiple OAuth contexts, for different issuers. During client registration &
    constructing the authorization redirect for the end user, the `state` parameter
    representing the new context is used as the key to store the relevant oauth client
    data. These only need to be stored in memory, they do not need to persist.

    - issuer_metadata_store(`dict[str, IssuerMetadata]`): A dictionary of objects
    containing an issuer's metadata, stored under the issuer's URI.

    - auth_metadata_store(`dict[str, AuthorizationMetadata]`): A dictionary of objects
    containing an issuer's authorization server, stored under the issuer's URI.
    """

    def __init__(
        self,
        oauth_client_metadata: dict[str, Any],
        storage_provider: AbstractStorageProvider,
    ):
        """
        Create a new Identity Owner

        ### Parameters
        - oauth_client_metadata(`dict`): A dictionary containing at minimum key/values
        "redirect_uris": `list[str]` and "credential_offer_endpoint": `str`.
        For additional entries, see `WalletClientMetadata`.
        - storage_provider(`AbstractStorageProvider`): An implementation of the
        `AbstractStorageProvider` abstract class.
        """
        self.client_metadata = WalletClientMetadata.model_validate(
            oauth_client_metadata
        )

        self.oauth_clients: dict[str, RegisteredClientMetadata] = {}
        self.issuer_metadata_store: dict[str, IssuerMetadata] = {}
        self.auth_metadata_store: dict[str, AuthorizationMetadata] = {}

        self.store = storage_provider

    def _get_credential_payload(self, sd_jwt_vc: str):
        return sd_jwt_vc.split("~")[0]

    def _get_decoded_credential_payload(self, sd_jwt_vc: str):
        payload = self._get_credential_payload(sd_jwt_vc)
        return jwt.decode(payload, options={"verify_signature": False})

    def _get_decoded_credential_disclosures(self, sd_jwt_vc: str):
        """Takes an SD-JWT Verifiable Credential (string) and returns its
        decoded disclosures (the disclosures between the first and last tilde)
        """
        # has_kb = False
        # if sd_jwt_vc[-1] != "~":
        #     has_kb = True
        parts = sd_jwt_vc.split("~")
        disclosures = parts[1:-1]
        # kb = None
        # if has_kb:
        #     kb = disclosures.pop()

        # dict[encoded_disclosure, decoded_disclosure]
        encoded_to_decoded_disclosures = {}
        for disclosure in disclosures:
            decoded_disclosure_bytes = SDJWTCommon._base64url_decode(disclosure)
            decoded_disclosure_str = decoded_disclosure_bytes.decode("utf-8")
            decoded_disclosure_list = loads(decoded_disclosure_str)
            decoded_disclosure_claim = {
                decoded_disclosure_list[1]: decoded_disclosure_list[2]
            }
            encoded_to_decoded_disclosures[disclosure] = decoded_disclosure_claim
        return encoded_to_decoded_disclosures

    def _validate_disclosure(self, disclosure: dict[str, Any], filter=None) -> bool:
        if filter:
            try:
                validate(disclosure, filter)
            except Exception:
                return False
        return True

    def _get_credentials_with_field(
        self,
        paths: list[str],  # list of jsonpath strings
        filter: dict,  # a jsonschema
    ) -> dict[str, list[str]]:
        """returns list(credential, [encoded disclosure])"""
        sdjwts = [
            credential.raw_sdjwtvc
            for credential in self.store.get_received_credentials()
            if "." in credential.raw_sdjwtvc
        ]  # dying because some of the example
        # raw sdjwts aren't sdjwts?
        # will ask mack l8r
        matched_credentials = {}
        for path in paths:
            expr = jsonpath_ng.parse(path)
            for credential in sdjwts:
                payload = self._get_decoded_credential_payload(credential)
                matches = expr.find(payload)
                if matches not in ([], None):
                    matched_credentials[credential] = []
                    continue

                encoded_to_decoded_disclosures = (
                    self._get_decoded_credential_disclosures(credential)
                )
                disclosures = encoded_to_decoded_disclosures.values()
                for disclosure in disclosures:
                    matches = expr.find(disclosure)
                    if matches not in ([], None):
                        disclosure_passes_filter = self._validate_disclosure(
                            next(iter(disclosure.values())), filter
                        )
                        if not disclosure_passes_filter:
                            continue
                        disclosure_idx = list(disclosures).index(disclosure)
                        encoded_disclosures = encoded_to_decoded_disclosures.keys()
                        encoded_disclosure = list(encoded_disclosures)[disclosure_idx]
                        matched_credentials[credential] = [encoded_disclosure]

        return matched_credentials

    ###
    ### Credential Issuance (OAuth2)
    ###

    async def get_credential_offer(
        self,
        credential_offer_uri: str | None = None,
        credential_offer: str | None = None,
    ) -> CredentialOffer:
        """
        Parses a credential offer.

        ### Parameters
        - credential_offer_uri(`str | None`): A URL linking to a credential offer
        object. If provided, `credential_offer` MUST be none.
        - credential_offer(`str`): A URL-encoded credential offer object. If given,
        `credential_offer_uri` MUST be none.

        ### Returns
        `CredentialOffer`: The credential offer.
        """
        # Interpret the credential offer
        if credential_offer and credential_offer_uri:
            raise Exception(
                "Can't accept both credential_offer and credential_offer_uri"
            )

        if not credential_offer and not credential_offer_uri:
            raise Exception(
                "Neither credential_offer nor credential_offer_uri were provided"
            )

        offer: CredentialOffer
        if credential_offer_uri:
            # Create a credential offer obj from the URI
            with Session() as s:
                res: Response = s.get(credential_offer_uri)
                res.raise_for_status()
                offer = CredentialOffer.model_validate_json(res.content)
        else:
            offer = CredentialOffer.model_validate_json(credential_offer)

        return offer

    async def get_issuer_and_auth_metadata(
        self, issuer_uri: str, *, force_refresh: bool = False
    ) -> tuple[IssuerMetadata, AuthorizationMetadata]:
        """
        Retrieves issuer metadata & authorization metadata, given a credential offer.
        Validates that the issuer_uri in the offer matches what's given in the
        credential offer.

        ### Parameters:
        - issuer_uri(`str`): The issuer's URI
        - force_refresh(`bool = False`): If `True`, will force the `IdentityOwner`
         to request from the issuer's metadata endpoints. Otherwise, it will
         attempt to load the metadata from memory, and only request it if it cannot
         be found.

        ### Returns:
        - Tuple[`IssuerMetadata`, `AuthorizationMetadata`]: A tuple containing two
        elements: The issuer's metadata, & the issuer's authorization server metadata.
        """
        issuer_metadata: IssuerMetadata | None = None
        auth_metadata: AuthorizationMetadata | None = None

        if not force_refresh:
            issuer_metadata = self.issuer_metadata_store.get(issuer_uri, None)
            auth_metadata = self.auth_metadata_store.get(issuer_uri, None)

        # If not already retrieved, get issuer metadata
        if not issuer_metadata:
            issuer_metadata = IssuerMetadata.model_validate(
                await self.get_issuer_metadata(issuer_uri)
            )
            # Check that the metadata matches
            if issuer_uri != issuer_metadata.credential_issuer:
                raise Exception("Bad Issuer Metadata")
            # Store it for easier access later if valid
            self.issuer_metadata_store[issuer_uri] = issuer_metadata

        # If not already retrieved, get authorization metadata
        if not auth_metadata:
            auth_metadata = AuthorizationMetadata.model_validate(
                await self.get_issuer_metadata(
                    issuer_uri, path="/.well-known/oauth-authorization-server"
                )
            )
            # Check that the metadata matches
            if issuer_uri != auth_metadata.issuer:
                raise Exception("Bad Issuer Authorization Metadata")
            # Store it for easier access later if valid
            self.auth_metadata_store[issuer_uri] = auth_metadata

        return (issuer_metadata, auth_metadata)

    async def get_auth_redirect_from_offer(
        self,
        credential_configuration_id: str,
        credential_offer: CredentialOffer,
    ):
        """
        Takes a user's selection of credential configurations for a previously
        received credential offer, and returns an OAuth2 authorization URL.

        OAuth2 Client parameters are stored in `self.oauth_clients` under the
        generated `state` as the key.

        ### Parameters:
        - credential_configuration_id: The selected credential configuration.
        - credential_offer(`CredentialOffer`): The credential

        ### Returns
        - `str`: The issuer authorization URL to redirect the end user to
        """

        offer = credential_offer

        if credential_configuration_id not in offer.credential_configuration_ids:
            raise Exception("Not a valid credential_configuration_id")

        return await self.get_auth_redirect(
            credential_configuration_id, offer.credential_issuer
        )

    async def get_auth_redirect(
        self, credential_configuration_id: str, issuer_url: str
    ):
        issuer_metadata: IssuerMetadata
        auth_metadata: AuthorizationMetadata
        (issuer_metadata, auth_metadata) = await self.get_issuer_and_auth_metadata(
            issuer_url
        )

        # Register as OAuth client
        wallet_metadata = await self.register_client(
            auth_metadata.registration_endpoint, issuer_metadata.credential_issuer
        )

        # Create an OAuth2 session.
        # Use as context so the session closes at the end of the function call
        with OAuth2Session(
            client_id=wallet_metadata.client_id,
            redirect_uri=wallet_metadata.redirect_uris[0],
        ) as oauth2_client:
            # create authorization_details parameter (url encoded JSON)
            auth_details = {
                "authorization_details": dumps(
                    [
                        {
                            "type": "openid_credential",
                            "credential_configuration_id": credential_configuration_id,
                        }
                    ]
                )
            }

            # Store OAuth2 client details
            (authorization_url, state) = oauth2_client.authorization_url(
                auth_metadata.authorization_endpoint, **auth_details
            )

            self.oauth_clients[state] = wallet_metadata
            return authorization_url

    async def get_access_token_and_credentials_from_callback(
        self,
        state: str,
        code: str | None = None,
        error: str | None = None,
    ) -> list[Credential | DeferredCredential]:
        """
        Retrieves an OAuth2 Access token from a successful authorization response, and
        then attempts to retrieve one or more credentials from the issuer, depending
        on what the end user authorized the wallet to access.

        The retrieved credentials are only saved if every credential request was
        successful.

        ### Parameters:
        - code(`str`): The authorization code, to be used in the token request.
        - state(`str`): An opaque string used to identify the context of the
        authorization response. In addition to the benefits of this parameter in
        OAuth2, the state identifies the issuer from where the response originated,
        and is used to identify the client registered for this response.

        ### Returns:
        - (`List[Credential | DeferredCredential]`): A list containing the
        credential(s) retrieved from the issuer using the acquired access token.
        """
        if error is not None:
            raise Exception(f"Bad Authorization Request: {error}")

        if code is None:
            raise Exception("Bad Authorization Request: Missing authorization code")

        oauth_client_info = self.oauth_clients.get(state, None)
        if not oauth_client_info:
            raise Exception("Bad Authorization Redirect")

        # Don't save any new credentials until everything is done.
        # Should avoid malformed credentials this way.
        new_credentials = []

        issuer_uri = oauth_client_info.issuer_uri

        with OAuth2Session(
            client_id=oauth_client_info.client_id,
            redirect_uri=oauth_client_info.redirect_uris[0],
            state=state,
        ) as oauth2_client:
            basic_auth = HTTPBasicAuth(
                oauth_client_info.client_id, oauth_client_info.client_secret
            )
            auth_metadata = self.auth_metadata_store.get(issuer_uri, None)
            if not auth_metadata:
                auth_metadata = AuthorizationMetadata.model_validate(
                    await self.get_issuer_metadata(
                        issuer_uri, path="/.well-known/oauth-authorization-server"
                    )
                )

            token_endpoint = auth_metadata.token_endpoint
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            }

            params = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": oauth_client_info.redirect_uris[0],
            }

            # Note - using post instead of fetch_token because fetch_token doesn't
            # return the full request body
            r: Response = oauth2_client.post(
                token_endpoint, data=urlencode(params), auth=basic_auth, headers=headers
            )
            r.raise_for_status()

            access_token_res = OAuthTokenResponse.model_validate_json(r.content)
            # Update session
            oauth2_client.token = access_token_res.model_dump()

            # Make requests for credentials
            issuer_metadata = self.issuer_metadata_store.get(issuer_uri, None)
            if not issuer_metadata:
                issuer_metadata = IssuerMetadata.model_validate(
                    await self.get_issuer_metadata(issuer_uri)
                )

            for detail in access_token_res.authorization_details:
                cred_type = detail.type
                # Check if type is supported by wallet, skip if not
                if cred_type not in self.client_metadata.authorization_details_types:
                    continue

                config_id = detail.credential_configuration_id
                for identifier in detail.credential_identifiers:
                    body = {"credential_identifier": identifier}
                    headers = {
                        "Authorization": f"Bearer {oauth2_client.token["access_token"]}",  # noqa e501
                    }
                    cred_response: Response = oauth2_client.request(
                        "POST", issuer_metadata.credential_endpoint, json=body
                    )
                    cred_response.raise_for_status()
                    # Determine if immediate or deferred
                    if cred_response.status_code == 200:
                        # Immediate - load right away
                        new = cred_response.json().get("credential", None)
                        if not new:
                            err = "Invalid credential response from issuer: "
                            err += "Value 'credential' missing from response."
                            raise Exception(err)

                        new_credential = Credential(
                            issuer_url=issuer_uri,
                            credential_configuration_id=config_id,
                            is_deferred=False,
                            c_type=cred_type,
                            received_at=datetime.now(tz=UTC).isoformat(),
                            raw_sdjwtvc=new,
                        )

                        new_credentials.append(new_credential)

                    elif cred_response.status_code == 202:
                        # Deferred - store tx id, access token, etc. to retrieve later.
                        tx_id = cred_response.json().get("transaction_id", None)
                        if not tx_id:
                            err = "Invalid credential response from issuer: "
                            err += "Value 'transaction_id' missing from response."
                            raise Exception(err)
                        deferred = issuer_metadata.deferred_credential_endpoint
                        token = AccessToken(
                            access_token=access_token_res.access_token,
                            token_type=access_token_res.token_type,
                            expires_in=access_token_res.expires_in,
                        )
                        new_credential = DeferredCredential(
                            issuer_url=issuer_uri,
                            credential_configuration_id=config_id,
                            is_deferred=True,
                            c_type=cred_type,
                            transaction_id=tx_id,
                            deferred_credential_endpoint=deferred,
                            access_token=token,
                            last_request=datetime.now(tz=UTC).isoformat(),
                        )

                        new_credentials.append(new_credential)

                    else:
                        raise Exception("Invalid credential response")

        self.store.add_many(new_credentials)
        return new_credentials

    async def get_issuer_metadata(
        self, issuer_uri, path="/.well-known/openid-credential-issuer"
    ):
        body: Any
        with httpx.AsyncClient() as client:
            res: Response = client.get(f"{issuer_uri}{path}")
            body = res.json()
        return body

    async def register_client(
        self, registration_url, issuer_uri, wallet_metadata=None
    ) -> RegisteredClientMetadata:
        metadata = wallet_metadata
        registered: RegisteredClientMetadata
        if not metadata:
            metadata = self.client_metadata.model_dump()
        async with httpx.AsyncClient() as client:
            res: httpx.Response = await client.post(registration_url, json=metadata)
            body: dict = res.json()
            body["issuer_uri"] = issuer_uri
            registered = RegisteredClientMetadata.model_validate(body)
        return registered

    ###
    ### Holder User Authentication (Internal)
    ###

    def login(self, username: str, password: str):
        self.store.login(username, password)

    def register(self, username: str, password: str):
        self.store.register(username, password)

    def logout(self):
        self.store.logout()

    ###
    ### Credential Management & Storage
    ###

    async def get_credential(
        self, cred_id: str, *, refresh: bool = True
    ) -> Credential | DeferredCredential:
        """
        Gets a credential by ID, if one exists

        ### Parameters
        - cred_id(`str`): The ID of the credential, as kept by the owner
        - refresh(`bool = True`): Whether or not to refresh the credential, if
        currently deferred. `True` by default.

        ### Returns
        - `Credential | DeferredCredential`: The requested credential, if it exists.
        """

        if refresh:
            return await self.refresh_credential(cred_id)

        return self.store.get_credential(cred_id)

    async def refresh_credential(self, cred_id: str) -> Credential | DeferredCredential:
        """
        Refreshes a credential.

        If the credential has already been retrieved, the credential
        will be returned unchanged.

        If the credential is deferred, it will be re-requested

        ### Parameters
        - cred_id(`str`): An identifier for the desired credential


        """
        cred = self.store.get_credential(cred_id)
        if isinstance(cred, Credential):
            return cred

        token = cred.access_token.model_dump()
        headers = {
            "Authorization": f"Bearer {cred.access_token.access_token}",
        }
        body = {"transaction_id": cred.transaction_id}
        with OAuth2Session(token=token) as s:
            s.headers = headers
            refresh: Response = s.request(
                "POST", cred.deferred_credential_endpoint, json=body
            )

            if (
                refresh.status_code == 400
                and refresh.json()["error"] == "issuance_pending"
            ):
                cred.last_request = datetime.now(tz=UTC).isoformat()
                self.store.update_credential(cred)
                return cred

            # Pending credentials also use 400
            refresh.raise_for_status()

            if refresh.status_code == 200:
                new = refresh.json().get("credential", None)
                if not new:
                    err = "Invalid credential response from issuer: "
                    err += "Value 'credential' missing from response."
                    raise Exception(err)

                new_credential = Credential(
                    id=cred_id,
                    issuer_url=cred.issuer_url,
                    credential_configuration_id=cred.credential_configuration_id,
                    is_deferred=False,
                    c_type=cred.c_type,
                    received_at=datetime.now(tz=UTC).isoformat(),
                    raw_sdjwtvc=new,
                )
                self.store.update_credential(new_credential)
                return new_credential

            raise Exception("Invalid credential response")

    async def refresh_all_deferred_credentials(self) -> list[str]:
        """
        Polls the issuer for updates on all outstanding credential requests.

        ### Returns
        - `list[str]` A list of credential IDs that a refresh was attempted on. Note
        that the IDs all credentials that were deferred before calling this method will
        be returned; even if the credential is still deferred, because the
        `last_request` attribute will be updated.
        """
        updated = []
        for cred in self.store.get_deferred_credentials():
            await self.refresh_credential(cred.id)
            updated.append(cred.id)

        return updated
