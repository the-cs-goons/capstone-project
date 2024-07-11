from datetime import date, datetime
from time import mktime
import pytest

from jwcrypto.jwk import JWK
from jwcrypto.jwt import JWT

from vclib.common import (
    SDJWTVCHolder,
    SDJWTVCIssuer,
)

@pytest.fixture
def issuer_jwk():
    return JWK(generate='EC')

@pytest.fixture
def holder_jwk():
    return JWK(generate='EC')

def test_get_and_verify_credential(issuer_jwk, holder_jwk):
    disclosable_claims = {"given_name": "Bob", "family_name": "Jones", "dob": "1970-01-01"}
    other = {"iat": mktime(datetime.now().timetuple())}

    issuance = SDJWTVCIssuer(disclosable_claims, other, issuer_jwk, holder_jwk).sd_jwt_issuance

    held_credential = SDJWTVCHolder(issuance)
    assert held_credential.serialized_sd_jwt == issuance.split('~')[0]

    assert not held_credential._is_verified

    # Check the signature matches
    held_credential.verify_signature(issuer_jwk.public())
    assert held_credential._is_verified

    # Check that the signature does not match with an invalid key
    wrong_jwk = JWK(generate='EC')
    with pytest.raises(Exception):
        held_credential.verify_signature(wrong_jwk.public())

def test_serialise_and_load_credential(issuer_jwk, holder_jwk):
    disclosable_claims = {"given_name": "Bob", "family_name": "Jones", "dob": date.today().isoformat()}
    other = {"iat": mktime(datetime.now().timetuple())}

    issuance = SDJWTVCIssuer(disclosable_claims, other, issuer_jwk, holder_jwk).sd_jwt_issuance

    held_credential = SDJWTVCHolder(issuance)
    serialised = held_credential.serialise_issuance_compact()

    # No KB-JWT should be included here.
    assert serialised[-1] == "~"

    # Check that the SD JWT and all disclosures match what was given
    held_array = serialised[:-1].split("~")
    issued_array = serialised[:-1].split("~")

    assert len(held_array) == len(issued_array)
    for item in held_array:
        assert item in issued_array

    # Check that the credential loaded from this is the same
    deserialised = SDJWTVCHolder(serialised)
    for item in deserialised._hash_to_disclosure.values():
        assert item in issued_array
        assert item in held_array

    # Once more for good measure
    assert deserialised.serialise_issuance_compact().split('~')[0] == issued_array[0]

def test_create_presentation(issuer_jwk, holder_jwk):
    disclosable_claims = {"given_name": "Bob", "family_name": "Jones", "dob": "1970-01-01"}
    other = {"iat": mktime(datetime.now().timetuple())}

    issuance = SDJWTVCIssuer(disclosable_claims, other, issuer_jwk, holder_jwk).sd_jwt_issuance

    held_credential = SDJWTVCHolder(issuance)
    held_credential.verify_signature(issuer_jwk.public())

    to_disclose = {"dob": "literally anything goes here, I'm so tired of this library"}

    held_credential.create_keybound_presentation(to_disclose, "deadbeef", "provider", holder_jwk)

    presentation = held_credential.sd_jwt_presentation

    presentation_parts = presentation.split("~")
    kb_jwt = presentation_parts[-1]

    # Implicit assertion, shouldn't throw error
    JWT(jwt=kb_jwt, key=holder_jwk)

    assert len(presentation_parts) == 3
