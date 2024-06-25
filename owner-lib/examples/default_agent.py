from owner import IdentityOwner
from owner.models.verifiable_credential import VerifiableCredential

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
