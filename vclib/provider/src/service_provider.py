import os
from uuid import uuid4

import httpx
from fastapi import FastAPI, HTTPException
from jsonpath_ng.ext import parse as parse_jsonpath
from jwcrypto.jwk import JWK
from pydantic import ValidationError

from vclib.common import SDJWTVCVerifier
from vclib.common.src.metadata import DIDJSONResponse

from .models.authorization_request_object import AuthorizationRequestObject
from .models.authorization_response_object import AuthorizationResponseObject
from .models.presentation_definition import PresentationDefinition


class ServiceProvider:
    valid_nonces: set[str]

    def __init__(
        self,
        presentation_definitions: dict[str, PresentationDefinition],
        diddoc_path: str,
        extra_provider_metadata: dict = {},
    ):
        """
        Initialise the service provider.

        ### Parameters
        - presentation_definitions(`dict[str, PresentationDefinition]`): A map
          from a string identifying the request type to the corresponding
          presentation definition
        """
        self.valid_nonces = set()
        self.presentation_definitions = presentation_definitions
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
        router.get("/authorize")(self.fetch_authorization_request)
        router.post("/cb")(self.parse_authorization_response)
        return router

    async def get_did_json(self) -> DIDJSONResponse:
        return self.diddoc

    async def get_presentation_definition(self, ref: str) -> PresentationDefinition:
        if ref not in self.presentation_definitions:
            raise HTTPException(
                status_code=404,
                detail=f"Presentation definition matching ref '{ref}' not found",
            )
        return self.presentation_definitions[ref]

    # TODO doc string
    async def fetch_authorization_request(
        self,
        presentation_definition: str | None = None,
        presentation_definition_uri: str | None = None,
        wallet_nonce: str | None = None,
    ) -> AuthorizationRequestObject:
        if presentation_definition is None and presentation_definition_uri is None:
            raise HTTPException(
                status_code=400,
                detail="Either presentation_definition or presentation_definition_uri must be provided", # noqa: E501
            )
        if (
            presentation_definition is not None
            and presentation_definition_uri is not None
        ):
            raise HTTPException(
                status_code=400,
                detail="Only one of presentation_definition or presentation_definition_uri should be provided", # noqa: E501
            )

        if presentation_definition_uri is not None:
            try:
                async with httpx.AsyncClient() as client:
                    res = await client.get(presentation_definition_uri)
                res.raise_for_status()
                parsed_presentation_definition = (
                    PresentationDefinition.model_validate_json(json_data=res.json())
                )
            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=e.response.status_code, detail=e.response.reason_phrase
                )
            except ValidationError as e:
                raise HTTPException(
                    status_code=400, detail=f"Presentation definition is malformed: {e}"
                )
        else:
            parsed_presentation_definition = PresentationDefinition.model_validate_json(
                presentation_definition
            )

        while (nonce := str(uuid4())) in self.valid_nonces:
            pass
        self.valid_nonces.add(nonce)

        return AuthorizationRequestObject(
            client_id=self.diddoc.id,
            client_metadata=self.extra_provider_metadata,
            presentation_definition=parsed_presentation_definition,
            response_uri=f"https://provider-lib:{os.getenv('CS3900_SERVICE_AGENT_PORT')}/cb",
            nonce=nonce,
            wallet_nonce=wallet_nonce,
        )

    # TODO doc string
    async def parse_authorization_response(
        self, auth_response: AuthorizationResponseObject
    ):
        # get presentation definition
        if (
            auth_response.presentation_submission.definition_id
            not in self.presentation_definitions
        ):
            raise HTTPException(
                status_code=400,
                detail="Specified definition_id does not match a supported presentation definition", # noqa: E501
            )
        presentation_definition = self.presentation_definitions[
            auth_response.presentation_submission.definition_id
        ]

        # get presented fields
        presented_tokens = {}
        for descriptor in auth_response.presentation_submission.descriptor_map:
            try:
                match = parse_jsonpath(descriptor.path).find(dict(auth_response))
            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid JSONPath for descriptor {descriptor.id}",
                )
            if len(match) != 1:
                raise HTTPException(
                    status_code=400,
                    detail=f"JSONPath for descriptor {descriptor.id} did not match exactly one field", # noqa: E501
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
        # img = qrcode.make(f"request_uri=https://provider-lib:8083/authorize/presentation_definition_uri=https://provider-lib:8083/presentationdefs?ref={presentation_definition_key}")  # noqa: E501
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
        self, presentation_definition: PresentationDefinition, disclosed_fields: dict
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
