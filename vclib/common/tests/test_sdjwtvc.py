from datetime import date, datetime
from time import mktime

import pytest
from jwcrypto.jwk import JWK

from vclib.common import SDJWTVCIssuer, SDJWTVCRegisteredClaimsException, SDJWTVCNoHolderPublicKey


@pytest.fixture
def issuer_jwk():
    return JWK(generate='EC')

@pytest.fixture
def holder_jwk():
    return JWK(generate='EC').public()

def test_create_and_verify_credential(issuer_jwk, holder_jwk):
    disclosable_claims = {
        "given_name": "Bob", 
        "family_name": "Jones", 
        "dob": date.today().isoformat()}
    other = {"iat": mktime(datetime.now().timetuple())}
    new_credential = SDJWTVCIssuer(disclosable_claims, other, issuer_jwk, holder_jwk)

    # Test 3 disclosures
    disclosures: list = new_credential.get_disclosures()
    assert len(disclosures) == 3
    
    assert new_credential.verify_signature(issuer_jwk.public())

    wrong_jwk = JWK(generate='EC')
    assert not new_credential.verify_signature(wrong_jwk.public())
    
def test_registered_jwt_claims_exception(issuer_jwk, holder_jwk):
    disclosable_claims = {
        "given_name": "Bob", 
        "family_name": "Jones", 
        "iss": date.today().isoformat()}
    other = {"iat": mktime(datetime.now().timetuple())}
    with pytest.raises(SDJWTVCRegisteredClaimsException):
        SDJWTVCIssuer(disclosable_claims, other, issuer_jwk, holder_jwk)

def test_rno_holder_key_exception(issuer_jwk):
    disclosable_claims = {
        "given_name": "Bob", 
        "family_name": "Jones", 
        "dob": date.today().isoformat()}
    other = {"iat": mktime(datetime.now().timetuple())}
    with pytest.raises(SDJWTVCNoHolderPublicKey):
        SDJWTVCIssuer(disclosable_claims, other, issuer_jwk, None)



