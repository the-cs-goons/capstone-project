from datetime import date, datetime
from time import mktime

import pytest
from jwcrypto.jwk import JWK
from jwcrypto.jws import JWS

from vclib.common import SDJWTVC


@pytest.fixture
def jwk():
    return JWK(generate='EC')

def test_create_and_verify_credential(jwk):
    disclosable_claims = {
        "given_name": "Bob", 
        "family_name": "Jones", 
        "dob": date.today().isoformat()}
    other = {"iat": mktime(datetime.now().timetuple())}

    new_credential = SDJWTVC(disclosable_claims, other, jwk)

    public_key = JWK.from_json(jwk.export_public())

    disclosures: list = new_credential.get_disclosures()
    assert len(disclosures) == 3
    
    assert public_key.has_public
    # Assert no exception gets raised
    assert new_credential.sd_jwt.verify(public_key) is None
    
def test_registered_jwt_claims(jwk):
    disclosable_claims = {
        "given_name": "Bob", 
        "family_name": "Jones", 
        "iss": date.today().isoformat()}
    other = {"iat": mktime(datetime.now().timetuple())}
    with pytest.raises(Exception):
        SDJWTVC(disclosable_claims, other, jwk)



