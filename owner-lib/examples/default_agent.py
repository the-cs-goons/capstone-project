from owner import IdentityOwner
from owner.models.verifiable_credential import VerifiableCredential

class DefaultHolder(IdentityOwner):
    def __init__(self):
        super().__init__()
        self.credentials.append(
            VerifiableCredential(
                context = ["https://www.w3.org/ns/credentials/v2"],
                type = ["verifiableCredential", "nswDriverLicense"],
                issuer = "the-issuers-did",
                credentialSubject = {
                    "id" : "the-holders-did",
                    "dateOfBirth" : "2002-8-14",
                    "licenseNumber" : "12348765",
                    "address" : {
                        "postcode" : 2000,
                        "streetAddress" : "123 That St",
                        "city" : "ThatCity"
                    },
                    "name" : "Walter Black"
                }
            )
        )


identity_owner = DefaultHolder()
identity_owner_server = identity_owner.get_server()
