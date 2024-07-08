from ast import Dict
from sd_jwt.common import SDObj
from sd_jwt.issuer import SDJWTIssuer as SDJWT
from jwcrypto.jwk import JWK


def create_sd_jwt(disclosable_claims: Dict, fields: Dict, signing_key: JWK):
    """
    Create a SD-JWT
    """
    payload = {}

    for key, value in disclosable_claims.items():
        payload[SDObj(key)] = value
    for key, value in fields:
        payload[key] = value

    # TODO: specific checking for mandatory fields that SDJWTIssuer does not enforce

    sd_jwt = SDJWT(payload, signing_key, extra_header_parameters={"typ": "vc+sd-jwt"})
    return sd_jwt