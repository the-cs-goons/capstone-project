from vclib.common import SDJWTVC
from jwcrypto.jwk import JWK

from datetime import date, datetime
from time import mktime

import pytest

@pytest.fixture
def jwk():
    return JWK(generate='EC')

def test_create_credential(jwk):
    disclosable_claims = {"given_name": "Bob", "family_name": "Jones", "dob": date.today().isoformat()}
    other = {"iat": mktime(datetime.now().timetuple())}

    new_credential = SDJWTVC(disclosable_claims, other, jwk)

    assert len(new_credential.get_disclosures()) == 3

    

