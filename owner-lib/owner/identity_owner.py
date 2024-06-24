from models.credentials import Credential
from requests import Session, Response

class IdentityOwner:
    credentials: list[Credential]
    dev_mode: False # HTTPS not enforced if running in development context
    # TODO: Enforce https

    def poll_credential_staus(self, cred: Credential):
        pass

    def add_credential_from_url(self, url: str):
        pass

    async def get_credential_application_schema(self, issuer_url: str, cred_type: str):
        with Session() as s:
            response: Response = await s.get(f"{issuer_url}/credentials")
            if not response.ok:
                raise f"Error: {response.status_code} Response - {response.reason}"
            
            body: dict = response.json()
            if "options" not in body.keys():
                raise "Error: Incorrect API Response"
            
            options: dict = body["options"]
            if type not in options.keys():
                raise f"Error: Credential type {cred_type} not found."
            
            return options[cred_type]


    def apply_for_credential(self, issuer_url: str, cred_type: str, request_body: dict):
        with Session() as s:
            response: Response = s.post(f"{issuer_url}/request/{cred_type}", json=request_body)
            if not response.ok:
                raise f"Error: {response.status_code} Response - {response.reason} {response.json()}"
            
            body: dict = response.json()
            req_url = f"{issuer_url}/status?token={body["link"]}"
            credential = Credential(issuer_url=issuer_url, type=cred_type, request_url=req_url)
            self.credentials.append(credential)
            
