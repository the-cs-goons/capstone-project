from ast import Dict
from typing import Dict
from sd_jwt.common import SDObj
from sd_jwt.issuer import SDJWTIssuer
from jwcrypto.jwk import JWK

class SDJWTVC(SDJWTIssuer):

    SD_JWT_HEADER = "vc+sd-jwt"

    def __init__(self, 
                 disclosable_claims: Dict,
                 oth_claims: Dict, 
                 issuer_key: JWK, 
                 **kwargs
                 ):
        payload = {}
        for key, value in disclosable_claims.items():
            payload[SDObj(key)] = value
        for key, value in oth_claims.items():
            payload[key] = value

        # TODO: specific checking for mandatory fields that SDJWTIssuer does not enforce
        # TODO: put the right stuff in the header

        super().__init__(payload, issuer_key, **kwargs)


    def get_header(self):
        pass

    def get_payload(self):
        pass

    def get_disclosures(self):
        return [digest.json for digest in self.ii_disclosures]
