import datetime
import time
from datetime import timedelta

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID, ObjectIdentifier
from fastapi import FastAPI

from vclib.provider import ServiceProvider


@pytest.mark.asyncio()
async def test_server_exists():
    sp = ServiceProvider("test_bundle", "test_path")
    sp_server = sp.get_server()
    assert type(sp_server) == FastAPI

###################
### TESTING VPs ###
###################



############################
### TESTING CERTIFICATES ###
############################
def create_dummy_certificate(private_key, public_key):
    did_oid = ObjectIdentifier("1.3.6.1.4.1.99999.1")
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "San Diego"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "My Org"),
            x509.NameAttribute(NameOID.COMMON_NAME, "example.com"),
        ]
    )
    return (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(public_key)
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.UTC))
        .not_valid_after(datetime.datetime.now(datetime.UTC) + timedelta(days=1))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName("localhost")]), critical=False
        )
        .add_extension(
            x509.UnrecognizedExtension(
                did_oid, b"My DID: did:example:123456789abcdefghi"
            ),
            critical=False,
        )
        .sign(private_key=private_key, algorithm=hashes.SHA256())
    )


@pytest.fixture()
def service_provider():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    dummy_cert = create_dummy_certificate(private_key, public_key)
    cert_pem = dummy_cert.public_bytes(serialization.Encoding.PEM)

    ca_bundle = [dummy_cert]
    sp = ServiceProvider(ca_bundle=ca_bundle, ca_path="dummy_path")
    return sp, cert_pem


@pytest.mark.asyncio()
async def test_verify_certificate_valid(service_provider):
    sp, cert_pem = service_provider
    nonce = "unique_nonce"
    timestamp = time.time()
    did = None
    did_oid = ObjectIdentifier("1.3.6.1.4.1.99999.1")

    for ext in x509.load_pem_x509_certificate(cert_pem).extensions:
        if isinstance(ext.oid, ObjectIdentifier) and ext.oid == did_oid:
            did = ext.value.value

    assert (
        sp.verify_certificate(cert_pem=cert_pem, nonce=nonce, timestamp=timestamp)
        == did
    )
