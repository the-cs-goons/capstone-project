from typing import Dict

from jwcrypto.jwk import JWK
from sd_jwt.common import SDObj
from sd_jwt.issuer import SDJWTIssuer

from .exceptions import (
    SDJWTVCNoHolderPublicKeyException,
    SDJWTVCRegisteredClaimsException,
)


class SDJWTVCIssuer(SDJWTIssuer):
    """
    SD JWT VC class for credential issuers.

    Built upon the SDJWTIssuer class from `sd_jwt`. Adds some extra things, mostly 
    verification of things that the SD JWT specification leaves blank but the SD JWT VC
    specification requires. Actually attempts to document the parent class.

    TODO: Document further
    """

    SD_JWT_HEADER = "vc+sd-jwt"
    NONDISCLOSABLE_CLAIMS = ["iss", "nbf", "exp", "cnf", "vct", "status"]
    ENFORCE_KEY_BINDING = True # For extensibility; True by default, can be disabled

    def __init__(self, 
                 disclosable_claims: Dict,
                 oth_claims: Dict, 
                 issuer_key: JWK, 
                 holder_key: JWK | None,
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
        - issuer_key(`JWK`): The issuer's signing key, as a `JWK` (see `jwcrypto.jwk`)
        - holder_key(`JWK | Nonw`): The holder's public key, as a `JWK`, if required 
        (see `jwcrypto.jwk`). If `ENFORCE_KEY_BINDING` is enabled (default), an error
        will be thrown if `None` is given.

        ### Attributes
        The following come from the parent class from the sd-jwt module. They're 
        documented here for clarity and ease of use.
        - sd_jwt(`JWS`): A JSON Serialised JWS. If serialisation format is set to 
        `json`, will include disclosures under the member name `"disclosures"`. If 
        format is `compact` (default), the disclosures will not be present in this 
        format. 
        - serialized_sd_jwt(`str`): The SD JWT without the disclosures appended
        - sd_jwt_issuance(`str`): The SD JWT + encoded disclosures, separated by a `~`
        character.
        - sd_jwt_payload(`dict`): A dict representing the decoded payload of the SD JWT.
        
        
        Other keyword arguments that `SDJWTIssuer` accepts can be passed down as 
        keyword arguments - such as extra header options, or a holder key for KB JWTs
        """
        payload = {}
        for key, value in disclosable_claims.items():
            # Registered JWT claims are not disclosable
            if key in self.NONDISCLOSABLE_CLAIMS:
                raise SDJWTVCRegisteredClaimsException(key)
            # The base class checks for disclosable claims by checking for this 
            # wrapper class.
            # TODO: Improve this to work over arrays and objects
            payload[SDObj(key)] = value


        for key, value in oth_claims.items():
            payload[key] = value

        if self.ENFORCE_KEY_BINDING and holder_key is None:
            raise SDJWTVCNoHolderPublicKeyException
         
        # TODO: specific checking for mandatory fields that SDJWTIssuer does not enforce
        # TODO: verification of any registered JWT claims
        # TODO: put the right stuff in the headers

        super().__init__(payload, issuer_key, holder_key=holder_key, **kwargs)

    def get_disclosures(self):
        """
        TODO: Make this easier
        """
        return [digest.json for digest in self.ii_disclosures]
        