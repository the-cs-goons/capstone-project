from uuid import uuid4

from fastapi import FastAPI, HTTPException
from jsonpath_ng.ext import parse as parse_jsonpath
from jwcrypto.jwk import JWK

from vclib.common import SDJWTVCVerifier, vp_auth_request, vp_auth_response
from vclib.common.src.metadata import DIDJSONResponse


class Verifier:
    valid_nonces: set[str]

    def __init__(
        self,
        presentation_definitions: dict[str, vp_auth_request.PresentationDefinition],
        diddoc_path: str,
        base_url: str,
        extra_provider_metadata: dict = {},
    ):
        """
        Initialise the verifier (service provider).

        ### Parameters
        - presentation_definitions(`dict[str, PresentationDefinition]`): A map
          from a string identifying the request type to the corresponding
          presentation definition
        """
        self.valid_nonces = set()
        self.presentation_definitions = presentation_definitions
        self.base_url = base_url
        self.extra_provider_metadata = extra_provider_metadata

        try:
            with open(diddoc_path, "rb") as diddoc_file:
                self.diddoc = DIDJSONResponse.model_validate_json(diddoc_file.read())
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Could not find DIDDoc: {e}")
        except ValueError as e:
            raise ValueError(f"Invalid DIDDoc provided: {e}")

    def get_server(self) -> FastAPI:
        router = FastAPI()
        router.get("/.well-known/did.json")(self.get_did_json)
        router.get("/presentationdefs")(self.get_presentation_definition)
        router.post("/request/{ref}")(self.fetch_authorization_request)
        router.post("/cb")(self.parse_authorization_response)
        return router

    async def get_did_json(self) -> DIDJSONResponse:
        """
        Gets verifier's DIDDoc.

        ## Returns
        - `DIDJSONResponse`: DIDDoc
        """
        return self.diddoc

    async def get_presentation_definition(
        self, ref: str
    ) -> vp_auth_request.PresentationDefinition:
        """
        Gets presentation definition.

        ### Parameters
        - ref(`str`): Credential ID

        ### Returns
        - `PresentationDefinition`: Presentation definition
        """
        if ref not in self.presentation_definitions:
            raise HTTPException(
                status_code=404,
                detail=f"Presentation definition matching ref '{ref}' not found",
            )
        return self.presentation_definitions[ref]

    async def fetch_authorization_request(
        self,
        ref: str,
        wallet_metadata: dict | None = None,
        wallet_nonce: str | None = None,
    ) -> vp_auth_request.AuthorizationRequestObject:
        """
        Returns authorization request.

        ### Parameters
        - ref(`str`): Credential ID
        - wallet_metadata(`dict | None`): Any wallet metadata
        - wallet_nonce(`str | None`): A wallet-generated nonce to prevent replay attacks

        ### Returns
        - `AuthorizationRequestObject`: Authorization request information
        """
        if ref not in self.presentation_definitions:
            raise HTTPException(
                status_code=400,
                detail=f"Reference {ref} is not an accepted presentation definition",
            )

        while (nonce := str(uuid4())) in self.valid_nonces:
            pass
        self.valid_nonces.add(nonce)

        return vp_auth_request.AuthorizationRequestObject(
            client_id=self.diddoc.id,
            client_metadata=self.extra_provider_metadata,
            presentation_definition=self.presentation_definitions[ref],
            response_uri=f"{self.base_url}/cb",
            nonce=nonce,
            wallet_nonce=wallet_nonce,
        )

    async def parse_authorization_response(
        self, auth_response: vp_auth_response.AuthorizationResponseObject
    ):
        """
        Recieves authorization response and validates the disclosed fields.

        ### Body
        - vp_token(`str | list[str]`): Presented credentials
        - presentation_submission(`PresentationSubmissionObject`): Submission info
        - state(`str`)
        """

        # get presentation definition
        if (
            auth_response.presentation_submission.definition_id
            not in self.presentation_definitions
        ):
            raise HTTPException(
                status_code=400,
                detail="Specified definition_id does not match a supported presentation definition",  # noqa: E501
            )
        presentation_definition = self.presentation_definitions[
            auth_response.presentation_submission.definition_id
        ]

        # get presented fields
        presented_tokens = {}
        for descriptor in auth_response.presentation_submission.descriptor_map:
            try:
                match = parse_jsonpath(descriptor.path).find(auth_response.vp_token)
            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid JSONPath for descriptor {descriptor.id}",
                )
            if len(match) != 1:
                raise HTTPException(
                    status_code=400,
                    detail=f"JSONPath for descriptor {descriptor.id} did not match exactly one field",  # noqa: E501
                )
            presented_tokens[descriptor.id] = match[0].value

        # verify jwts
        disclosed_fields = {}
        try:
            for token in presented_tokens.values():
                disclosed_field = SDJWTVCVerifier(
                    token, self.cb_get_issuer_key
                ).get_verified_payload()
                if not isinstance(disclosed_fields, dict):
                    raise Exception("Selective disclosures not in key-value pairs")
                disclosed_fields |= disclosed_field
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"JWT verification failed: {e}")

        self.validate_disclosed_fields(presentation_definition, disclosed_fields)

        return {"status": "OK"}

    def create_presentation_qr_code(
        self, presentation_definition_key: str, image_path: str
    ):
        """### Parameters
        - presentation_definition_key(`str`): The key in the `presentation_definitions`
          dict matching the desired presentation definition
        - image_path(`str`): Where to save the QR code image
        """
        # img = qrcode.make(f"request_uri={self.base_url}/authorize/presentation_definition_uri={self.base_url}/presentationdefs?ref={presentation_definition_key}")  # noqa: E501
        # img.save(image_path)

    def cb_get_issuer_key(self, iss: str, headers: dict) -> JWK:
        """## !!! This function must be `@override`n !!!

        ### Parameters
        - iss(`str`): JWT issuer claim (URI)
        - headers(`dict`): Presented JWT headers

        ### Returns
        - `JWK`: The trusted issuer's JWK

        ### Raises
        - `Exception`: If the issuer is not trusted
        """

    def validate_disclosed_fields(
        self,
        presentation_definition: vp_auth_request.PresentationDefinition,
        disclosed_fields: dict,
    ) -> bool:
        """## !!! This function must be `@override`n !!!

        ### Parameters
        - presentation_definition(`PresentationDefinition`): Relevant presentation
          definition
        - disclosed_fields(`dict`): Fields disclosed in presentation

        ### Raises
        - `Exception`: If the disclosed fields are not satisfactory (by whatever
          standard)
        """
