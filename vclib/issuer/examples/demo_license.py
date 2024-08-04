import datetime
import json
from typing import Any, override
from uuid import uuid4

from fastapi import Response
from fastapi.responses import HTMLResponse, RedirectResponse

from vclib.issuer import StatusResponse
from vclib.issuer.src.models.exceptions import IssuerError
from vclib.issuer.src.models.requests import AuthorizationRequestDetails
from vclib.issuer.src.models.responses import FormResponse

from .demo_agent import DefaultIssuer
from .example_license_form import html_license_form

MOCK_DATA = {
    123: {
        "given_name": "Holden",
        "family_name": "Walletson",
        "date_of_birth": "1999-01-01",
        "address": "123 A Street, A Suburb",
        "license_type": "C",
        "is_over_18": True,
    }
}

FORM = {
    "license_no": {"mandatory": True, "value_type": "number"},
    "date_of_birth": {"mandatory": True, "value_type": "string"},
}


class LicenseIssuer(DefaultIssuer):
    """Example implementation of the `CredentialIssuer` base class.

    ### Added Attributes
    - ticket(`int`): Internal system for tracking credential requests.
    - statuses(`dict[int, (str, dict)]`): Dictionary storing the current status
      of active credential requests.
    - client_ids(`dict[str, str]`): Mapping of client IDs to secrets.
    - auth_codes(`dict[str, str]`): Mapping of authorization codes to associated
      client ID.
    - auths_to_ids(`dict[str, (str, str, str)]`): Mapping of authorization codes
      to credential type, credential identifier and redirect URI used.
    - id_to_info(`dict[str, dict[str, str]]`): Mapping of credential identifiers
      to associated ticket and transaction ID.
    """

    @override
    def __init__(
        self,
        jwt_path: str,
        diddoc_path: str,
        did_config_path: str,
        metadata_path: str,
        oauth_metadata_path: str,
        data: dict[int, dict[str, Any]],
    ):
        super().__init__(
            jwt_path,
            diddoc_path,
            did_config_path,
            metadata_path,
            oauth_metadata_path,
        )
        self.data = data

    @override
    def get_credential_form(self, credential_config: str) -> FormResponse:
        if credential_config == "DriversLicense":
            return FormResponse(form=FORM)

        raise IssuerError(
            "invalid_request",
            f"Credential format {credential_config} not supported",
        )

    @override
    def get_credential_request(
        self, client_id: str, cred_type: str, redirect_uri: str, information: dict
    ) -> str:
        license_no, date_of_birth = (
            int(information["license_no"]),
            information["date_of_birth"],
        )

        if license_no not in self.data:
            raise IssuerError(
                "invalid_request", f"Licence number {license_no} does not exist"
            )

        holder_information = self.data[license_no]

        if date_of_birth != holder_information["date_of_birth"]:
            raise IssuerError("invalid_request", f"DOB {date_of_birth} does not match")

        holder_information["license_no"] = license_no
        holder_information["type"] = "DriversLicense"

        self.ticket += 1
        auth_code = str(uuid4())
        self.auth_codes[auth_code] = client_id

        cred_id = f"{cred_type}_{uuid4()!s}"
        self.auths_to_ids[auth_code] = (cred_type, cred_id, redirect_uri)
        self.id_to_info[cred_id] = {"ticket": self.ticket, "transaction_id": None}

        self.statuses[self.ticket] = (cred_type, holder_information)

        self.time = datetime.datetime.now(tz=datetime.UTC)

        return auth_code

    @override
    async def authorize(
        self,
        response: Response,
        response_type: str | None = None,
        client_id: str | None = None,
        redirect_uri: str | None = None,
        state: str | None = None,
        authorization_details: str | None = None
        ) -> Any:
        form = await super().authorize(
            response,
            response_type,
            client_id,
            redirect_uri,
            state,
            authorization_details
            )
        if isinstance(form, RedirectResponse):
            return form

        auth_details = AuthorizationRequestDetails.model_validate(
                json.loads(authorization_details)[0]
            )

        if "DriversLicense" in auth_details.credential_configuration_id:
            return HTMLResponse(content=html_license_form)

        return form


    @override
    def get_credential_status(self, cred_id: str) -> StatusResponse:
        cred_info = self.id_to_info[cred_id]
        ticket = cred_info["ticket"]
        cred_type, information = self.statuses[ticket]

        status = "ACCEPTED"

        return StatusResponse(
            status=status,
            cred_type=cred_type,
            information=information,
            transaction_id=cred_info["transaction_id"],
        )


credential_issuer = LicenseIssuer(
    "/usr/src/app/examples/demo_data/example_jwk_private.pem",
    "/usr/src/app/examples/demo_data/example_diddoc.json",
    "/usr/src/app/examples/demo_data/example_didconf.json",
    "/usr/src/app/examples/demo_data/example_metadata_license.json",
    "/usr/src/app/examples/demo_data/example_oauth_metadata_license.json",
    MOCK_DATA,
)
credential_issuer_server = credential_issuer.get_server()
