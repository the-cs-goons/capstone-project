from datetime import date, datetime
from time import mktime

import pytest
from jwcrypto.jwk import JWK

from vclib.common import SDJWTVCIssuer


@pytest.fixture
def jwk():
    return JWK(generate='EC')

def test_create_and_verify_credential(jwk):
    disclosable_claims = {
        "given_name": "Bob", 
        "family_name": "Jones", 
        "dob": date.today().isoformat()}
    other = {"iat": mktime(datetime.now().timetuple())}
    new_credential = SDJWTVCIssuer(disclosable_claims, other, jwk)

    # Test 3 disclosures
    disclosures: list = new_credential.get_disclosures()
    assert len(disclosures) == 3
    
    public_key = JWK.from_json(jwk.export_public())
    assert new_credential.verify_signature(public_key)

    wrong_jwk = JWK(generate='EC')
    wrong_pubkey = JWK.from_json(wrong_jwk.export_public())
    assert not new_credential.verify_signature(wrong_pubkey)
    
def test_registered_jwt_claims(jwk):
    disclosable_claims = {
        "given_name": "Bob", 
        "family_name": "Jones", 
        "iss": date.today().isoformat()}
    other = {"iat": mktime(datetime.now().timetuple())}
    with pytest.raises(Exception):
        SDJWTVCIssuer(disclosable_claims, other, jwk)



