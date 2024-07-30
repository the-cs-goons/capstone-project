from datetime import UTC, datetime
from typing import Any, override
from uuid import uuid4

from vclib.issuer.src.models.exceptions import IssuerError
from vclib.issuer.src.models.responses import FormResponse

from .demo_agent import DefaultIssuer

MOCK_DATA = {
    123: {
        "vaccination_name": "ABC",
        "vaccination_date": 20240729,
    }
}

FORM = {
    "document_code": {"mandatory": True, "value_type": "number"},
    "given_name": {"mandatory": True, "value_type": "string"},
    "middle_initial": {"mandatory": False, "value_type": "string"},
    "family_name": {"mandatory": True, "value_type": "string"},
    "date_of_birth": {"mandatory": True, "value_type": "string"},
}


class VaccinationIssuer(DefaultIssuer):
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
        if credential_config == "VaccinationCertificate":
            return FormResponse(form=FORM)

        raise IssuerError(
            "invalid_request",
            f"Credential format {credential_config} not supported",
        )

    @override
    def get_credential_request(
        self, client_id: str, cred_type: str, redirect_uri: str, information: dict
    ) -> str:
        document_code = int(information.pop("document_code"))

        if document_code not in self.data:
            raise IssuerError("invalid_request", f"Code {document_code} is invalid")

        holder_information = information | self.data[document_code]
        holder_information["type"] = "VaccinationCertificate"

        self.ticket += 1
        auth_code = str(uuid4())
        self.auth_codes[auth_code] = client_id

        cred_id = f"{cred_type}_{uuid4()!s}"
        self.auths_to_ids[auth_code] = (cred_type, cred_id, redirect_uri)
        self.id_to_info[cred_id] = {"ticket": self.ticket, "transaction_id": None}

        self.statuses[self.ticket] = (cred_type, holder_information)
        self.time = datetime.now(tz=UTC)

        return auth_code


credential_issuer = VaccinationIssuer(
    "/usr/src/app/examples/demo_data/example_jwk_private.pem",
    "/usr/src/app/examples/demo_data/example_diddoc.json",
    "/usr/src/app/examples/demo_data/example_didconf.json",
    "/usr/src/app/examples/demo_data/example_metadata_vaccination.json",
    "/usr/src/app/examples/demo_data/example_oauth_metadata_vaccination.json",
    MOCK_DATA,
)
credential_issuer_server = credential_issuer.get_server()
