from typing import Dict

from jwcrypto.jwk import JWK
from sd_jwt.common import SDObj
from sd_jwt.issuer import SDJWTIssuer


class SDJWTVCIssuer(SDJWTIssuer):
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
        """
        Creates a new SDJWT from a set of disclosable/non-disclosable claims and signs 
        it.

        ### Parameters
        - disclosable_claims(`dict`): A dict representing key/value pairs that the
        recipient of this credential should be able to **selectively disclose**.
        - oth_claims(`dict`): A dict representing key/value pairs that the recipient
        of this credential should NOT be able to selectively disclose (e.g. the `exp` 
        expiry claim.)
        - issuer_key(`JWK`): The issuer's signing key, as a `JWK` 
        (from the `jwcrypto` library)

        ### Attributes
        - sd_jwt(`JWS`): The signed SD JWT itself, without any disclosures.
        - sd_jwt_issuance(`str`): The SD JWT + encoded disclosures, separated by a `~`
        character.
        
        Other keyword arguments that `SDJWTIssuer` accepts can be passed down as 
        keyword arguments.
        """
        payload = {}
        for key, value in disclosable_claims.items():
            # Registered JWT claims are not disclosable
            if key in self.NONDISCLOSABLE_CLAIMS:
                raise Exception
            # The base class checks for disclosable claims by checking for this 
            # wrapper class.
            # TODO: Improve this to work over deeper dicts (supported by the base class)
            payload[SDObj(key)] = value
        for key, value in oth_claims.items():
            payload[key] = value

        # TODO: specific checking for mandatory fields that SDJWTIssuer does not enforce
        # TODO: put the right stuff in the header

        super().__init__(payload, issuer_key, **kwargs)

    def get_disclosures(self):
        return [digest.json for digest in self.ii_disclosures]
    
    def verify_signature(self, pub_key: JWK) -> bool:
        try:
            self.sd_jwt.verify(pub_key)
            return True
        except Exception:
            return False

