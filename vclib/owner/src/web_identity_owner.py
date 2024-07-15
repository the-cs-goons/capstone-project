import uuid
from typing import override

import httpx
from fastapi import Body, FastAPI, HTTPException

from . import IdentityOwner
from .models.authorization_request_object import AuthorizationRequestObject
from .models.authorization_response_object import AuthorizationResponseObject
from .models.credentials import Credential
from .models.exceptions import (
    BadIssuerRequestError,
    CredentialIssuerError,
    IssuerTypeNotFoundError,
    IssuerURLNotFoundError,
)
from .models.field_selection_object import FieldSelectionObject
from .models.presentation_submission_object import (
    DescriptorMapObject,
    PresentationSubmissionObject,
)
from .models.responses import SchemaResponse


class WebIdentityOwner(IdentityOwner):
    def __init__(self, storage_key, *, dev_mode=False):
        super().__init__(storage_key, dev_mode=dev_mode)
        self.current_transaction: AuthorizationRequestObject | None = None

    def get_server(self) -> FastAPI:
        router = FastAPI()

        router.get("/credential/{cred_id}")(self.get_credential)
        router.get("/credentials")(self.get_credentials)
        router.get("/request/{cred_type}")(self.get_credential_request_schema)
        router.post("/request/{cred_type}")(self.apply_for_credential)
        router.get("/refresh/{cred_id}")(self.refresh_credential)
        router.get("/refresh/all")(self.refresh_all_pending_credentials)
        router.get("/presentation/init")(self.get_auth_request)
        router.post("/presentation/")(self.present_selection)

        return router

    def get_credential(self, cred_id) -> Credential:
        """Gets a credential by ID, if one exists

        ### Parameters
        - cred_id(`str`): The ID of the credential, as kept by the owner

        ### Returns
        - `Credential`: The requested credential, if it exists
        """
        if cred_id not in self.credentials:
            raise HTTPException(
                status_code=400, detail=f"Credential with ID {cred_id} not found."
            )
        return self.credentials[cred_id]

    def get_credentials(self) -> list[Credential]:
        """Gets all credentials

        ### Returns
        - `list[Credential]`: A list of credentials
        """
        return self.credentials.values()

    @override
    async def get_credential_request_schema(
        self, cred_type: str, issuer_url: str
    ) -> SchemaResponse:
        """Retrieves the required information needed to submit request for some ID type
        from an issuer.

        ### Parameters
        - issuer_url(`str`): The issuer URL, as a URL Parameter
        - cred_type(`str`): The type of the credential schema request being asked for

        ### Returns
        - `SchemaResponse`: A list of credentials
        """
        try:
            req_schema = await super().get_credential_request_schema(
                cred_type, issuer_url
            )
            return SchemaResponse(request_schema=req_schema)
        except IssuerTypeNotFoundError:
            raise HTTPException(
                status_code=400, detail=f"Credential type {cred_type} not found."
            )
        except IssuerURLNotFoundError:
            raise HTTPException(status_code=404, detail="Issuer URL not found")
        except CredentialIssuerError:
            raise HTTPException(status_code=500, detail="Issuer API Error")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"{e}")

    @override
    async def apply_for_credential(
        self, issuer_url: str, cred_type: str, info: dict
    ) -> Credential:
        """Sends request for a new credential directly, then stores it

        ### Parameters
        - issuer_url(`str`): The issuer URL
        - cred_type(`str`): The type of the credential schema request being asked for
        - info(`dict`): The body of the request to forward on to the issuer, sent as
        JSON

        ### Returns
        - `Credential`: The new (pending) credential, if requested successfully
        """
        try:
            return super().apply_for_credential(cred_type, issuer_url, info)
        except IssuerTypeNotFoundError:
            raise HTTPException(
                status_code=400, detail=f"Credential type {cred_type} not found."
            )
        except IssuerURLNotFoundError:
            raise HTTPException(status_code=404, detail="Issuer URL not found")
        except BadIssuerRequestError:
            raise HTTPException(status_code=400, detail="Bad request to Issuer")
        except CredentialIssuerError:
            raise HTTPException(status_code=500, detail="Issuer API Error")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error: {e}")

    async def refresh_credential(self, cred_id) -> Credential:
        """Refreshes a specified credential and returns it

        ### Parameters
        - cred_id(`str`): The internal ID of the credential to refresh

        ### Returns
        - `Credential`: The updated credential, if it exists
        """
        if cred_id not in self.credentials:
            raise HTTPException(
                status_code=400, detail=f"Credential with ID {cred_id} not found."
            )

        await self.poll_credential_status(cred_id)
        return self.credentials[cred_id]

    async def refresh_all_pending_credentials(self):
        """Refreshes all PENDING credentials

        ### Returns
        - `list[Credential]`: A list of all saved credentials
        """
        await self.poll_all_pending_credentials()
        return self.credentials.values()

    async def present_selection(
        self, field_selections: FieldSelectionObject = Body(...)
    ):
        # find which attributes in which credentials fit the presentation definition
        # mark which credential and attribute for disclosure

        # list[Field]
        approved_fields = [
            x.field for x in field_selections.field_requests if x.approved
        ]
        pd = self.current_transaction.presentation_definition
        ids = pd.input_descriptors

        # list[tuple[input_descriptor_id, vp_token]]
        id_vp_tokens: list[tuple[str, str]] = []

        for id_object in ids:
            input_descriptor_id = id_object.id
            # dict[credential, [list[encoded disclosures]]]
            valid_credentials = {}
            ordered_approved_fields = [
                x for x in id_object.constraints.fields if x in approved_fields
            ]
            for field in ordered_approved_fields:
                paths = field.path
                # find all credentials with said field
                new_valid_creds = self._get_credentials_with_field(paths)

                if valid_credentials == {}:
                    valid_credentials = new_valid_creds
                    continue
                # make sure we keep creds with previously found fields
                for cred in valid_credentials:
                    if cred not in new_valid_creds:
                        new_valid_creds.pop(cred)
                # add the new disclosures to the old disclosures
                for cred in new_valid_creds:
                    new_valid_creds[cred] += valid_credentials[cred]
                # cull old creds that don't have all of the fields
                valid_credentials = new_valid_creds

                # no valid credentials found
                if valid_credentials == {}:
                    break

            # if no valid credentials found, go next
            if valid_credentials == {}:
                continue

            # create the vp_token
            credential, disclosures = valid_credentials.popitem()
            vp_token = f"{self._get_credential_payload(credential)}~"
            for disclosure in disclosures:
                vp_token += f"{disclosure}~"

            id_vp_tokens.append((input_descriptor_id, vp_token))

        final_vp_token = None
        descriptor_maps = []
        definition_id = self.current_transaction.presentation_definition.id
        transaction_id = self.current_transaction.state

        if len(id_vp_tokens) == 1:
            input_descriptor_id, vp_token = id_vp_tokens[0]
            final_vp_token = vp_token

            descriptor_map = {
                "id": input_descriptor_id,
                "format": "vc+sd-jwt",
                "path": "$",
            }
            descriptor_maps.append(DescriptorMapObject(**descriptor_map))
        elif len(id_vp_tokens) > 1:
            final_vp_token = []
            for input_descriptor_id, vp_token in id_vp_tokens:
                idx = len(final_vp_token)
                final_vp_token.append(vp_token)

                descriptor_map = {
                    "id": input_descriptor_id,
                    "format": "vc+sd-jwt",
                    "path": f"$[{idx}]",
                }
                descriptor_maps.append(DescriptorMapObject(**descriptor_map))

        presentation_submission = {
            "id": str(uuid.uuid4()),
            "definition_id": definition_id,
            "descriptor_map": descriptor_maps,
        }
        presentation_submission_object = PresentationSubmissionObject(
            **presentation_submission
        )

        authorization_response = {
            "vp_token": final_vp_token,
            "presentation_submission": presentation_submission_object,
            "state": transaction_id,
        }
        authorization_response_object = AuthorizationResponseObject(
            **authorization_response
        )

        response_uri = self.current_transaction.response_uri
        # make sure response_mode is direct_post
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{response_uri}", data=authorization_response_object.model_dump()
            )

        self.current_transaction = None
        return response.json()

    async def get_auth_request(
        self,
        request_uri=Body(...),
        client_id=Body(...),
        client_id_scheme=Body(...),
        request_uri_method=Body(...),
    ):  # -> PresentationDefinition:
        if client_id_scheme != "did":
            raise HTTPException(
                status_code=400,
                detail=f"client_id_scheme {client_id_scheme} not supported",
            )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                # f"http://provider-lib:{os.getenv('CS3900_SERVICE_AGENT_PORT')}/request/age_verification",
                f"{request_uri}",
                data={
                    "wallet_nonce": "nonce",  # replace this data with actual stuff
                    "wallet_metadata": "metadata",
                },
            )
        # just send the auth request to the frontend for now
        # what the backend sends to the fronend should be up to implementation
        # although it shouldn't include sensitive info unless the user has
        # opted to share that information
        auth_request = response.json()
        self.current_transaction = AuthorizationRequestObject(**auth_request)
        return auth_request
