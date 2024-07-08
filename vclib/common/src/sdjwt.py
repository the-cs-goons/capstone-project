from typing import Dict

from jwcrypto.jwk import JWK
from sd_jwt.common import SDObj
from sd_jwt.issuer import SDJWTIssuer


class SDJWTVC(SDJWTIssuer):
    """
    Selective Disclosure JWT for Verifiable Credentials

    Built upon the SDJWTIssuer class from `sd_jwt`.

    TODO: Document further
    """

    SD_JWT_HEADER = "vc+sd-jwt"
    NONDISCLOSABLE_CLAIMS = ["iss", "nbf", "exp", "cnf", "vct", "status"]

    def __init__(self, 
                 disclosable_claims: Dict,
                 oth_claims: Dict, 
                 issuer_key: JWK, 
                 **kwargs
                 ):
        payload = {}
        for key, value in disclosable_claims.items():
            # If the key of the claim is specifically of type SDJObj, 
            # it will be included in _sd + as a digest
            if key in self.NONDISCLOSABLE_CLAIMS:
                raise Exception
            payload[SDObj(key)] = value
        for key, value in oth_claims.items():
            payload[key] = value

        # TODO: specific checking for mandatory fields that SDJWTIssuer does not enforce
        # TODO: put the right stuff in the header

        super().__init__(payload, issuer_key, **kwargs)

    def get_disclosures(self):
        return [digest.json for digest in self.ii_disclosures]
