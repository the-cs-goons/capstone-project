from owner import IdentityOwner
from owner.models.verifiable_credential import VerifiableCredential

MOCK_STORE = {
    "example1": {
        "id": "example1",
        "issuer_url": "https://example.com",
        "type": "Passport",
        "request_url": "https://example.com/status?token=example1",
        "token":
            "eyJuYW1lIjoiTWFjayBDaGVlc2VNYW4iLCJkb2IiOiIwMS8wMS8wMSIsImV4cGlyeSI6IjEyLzEyLzI1In0=",
        "status":"ACCEPTED",
        "status_message":None,
        "issuer_name":"Example Issuer",
        "received_at":1719295821397
    },
    "example2": {
        "id": "example2",
        "issuer_url": "https://example.com",
        "type": "Driver's Licence",
        "request_url": "https://example.com/status?token=example2",
        "token": None,
        "status":"PENDING",
        "status_message":None,
        "issuer_name":"Example Issuer",
        "received_at":None
    }
}

class DefaultHolder(IdentityOwner):
    def __init__(self):
        super().__init__()
        self.create_VC(
            {
                "id" : "the-holders-did",
                "dateOfBirth" : "2002-8-14",
                "licenseNumber" : "12348765",
                "address" : {
                    "postcode" : 2000,
                    "streetAddress" : "123 That St",
                    "city" : "ThatCity"
                },
                "name" : "Walter Black"
            })


    def create_VC(self, fields: dict, types:list = []):
        types.insert(0, "verifiableCredential")

        self.credentials.append(
            VerifiableCredential(
                context = ["https://www.w3.org/ns/credentials/v2"],
                type = types,
                issuer = f"the-issuers-did{len(self.credentials)}",
                credentialSubject = fields)
            )

identity_owner = DefaultHolder()
identity_owner_server = identity_owner.get_server()
