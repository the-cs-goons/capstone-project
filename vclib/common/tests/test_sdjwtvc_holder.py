from datetime import date, datetime
from time import mktime

import pytest
from jwcrypto.jwk import JWK

from vclib.common import (
    SDJWTVCIssuer,
    SDJWTVCHolder,
    SDJWTVCNoHolderPublicKeyException,
    SDJWTVCRegisteredClaimsException,
)


@pytest.fixture
def issuer_jwk():
    return JWK(generate='EC')

@pytest.fixture
def holder_jwk():
    return JWK(generate='EC')

def test_load_credential(issuer_jwk, holder_jwk):
    disclosable_claims = {
        "given_name": "Bob", 
        "family_name": "Jones", 
        "dob": date.today().isoformat()}
    other = {"iat": mktime(datetime.now().timetuple())}

    issuance = SDJWTVCIssuer(disclosable_claims, other, issuer_jwk, holder_jwk).sd_jwt_issuance

    held_credential = SDJWTVCHolder(issuance)
    assert held_credential.serialized_sd_jwt == issuance.split('~')[0]


    # Check the signature matches
    assert held_credential.verify_signature(issuer_jwk.public())

    # Check that the signature does not match with an invalid key
    wrong_jwk = JWK(generate='EC')
    with pytest.raises(Exception):
        held_credential.verify_signature(wrong_jwk.public())

def test_create_presentation(issuer_jwk):
    pass