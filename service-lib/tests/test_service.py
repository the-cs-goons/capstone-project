from base64 import b64encode
import datetime
import json
import time
from datetime import timedelta
from unittest.mock import MagicMock

import pytest
from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.x509 import Certificate
from cryptography.x509.oid import NameOID
from fastapi import FastAPI, HTTPException
from service import ServiceProvider
from service.models.presentation import Presentation
from service.models.presentation_definition import (
    Constraint,
    Field,
    Filter,
    InputDescriptor,
    PresentationDefinition,
)


@pytest.mark.asyncio
async def test_server_exists():
    sp = ServiceProvider("test_bundle", "test_path")
    sp_server = sp.get_server()
    assert type(sp_server) == FastAPI

@pytest.mark.asyncio
async def test_basic_presentation_request():
    sp = ServiceProvider("test_bundle", "test_path")

    pd = PresentationDefinition(
        id='test1',
        input_descriptors=[]
    )

    sp.add_presentation_definition('test_empty', pd)

    response = await sp.get_presentation_request('test_empty', 'tester')
    assert response.client_id == 'tester'
    assert response.presentation_definition.id == 'test1'
    assert response.presentation_definition.input_descriptors == []

@pytest.mark.asyncio
async def test_multiple_presentation_requests():
    sp = ServiceProvider("test_bundle", "test_path")

    pd1= PresentationDefinition(
        id='test1',
        input_descriptors=[]
    )

    request_type1 = 'test_1'
    sp.add_presentation_definition(request_type1, pd1)

    response0 = await sp.get_presentation_request('test_1', 'tester1')
    assert response0.client_id == 'tester1'
    assert response0.presentation_definition.id == 'test1'


    pd2 = PresentationDefinition(
        id='test2',
        input_descriptors=[]
    )

    request_type2 = 'test_2'
    sp.add_presentation_definition(request_type2, pd2)

    response1 = await sp.get_presentation_request(request_type1, 'tester1')
    assert response1.client_id == 'tester1'
    assert response1.presentation_definition.id == 'test1'

    response2 = await sp.get_presentation_request(request_type2, 'tester2')
    assert response2.client_id == 'tester2'
    assert response2.presentation_definition.id == 'test2'

@pytest.mark.asyncio
async def test_presentation_request_limit_disclosure():
    sp = ServiceProvider("test_bundle", "test_path")

    pd = PresentationDefinition(
        id='test_limit_disclosure_1',
        input_descriptors=[
            InputDescriptor(
            id='limit_disclosure_test',
            constraints=Constraint([
                Field(['$.credentialSubject.active'])],
                limit_disclosure='required'))
        ],
        name='required_limit_disclosure'
    )

    sp.add_presentation_definition('test_limit_disclosure', pd)

    response = await sp.get_presentation_request('test_limit_disclosure', 'ld_tester')

    presentation_definition = response.presentation_definition
    response_constraint = presentation_definition.input_descriptors[0].constraints
    assert response_constraint.limit_disclosure == 'required'

@pytest.mark.asyncio
async def test_presentation_request_two_fields_optional():
    sp = ServiceProvider("test_bundle", "test_path")

    pd = PresentationDefinition(
        id='name_age_presentation_1',
        name='Age and Name request',
        purpose='To be able to address the customer by name, and verify their age',
        input_descriptors=[InputDescriptor(
            id='name_age_presentation_definition',
            name='name_age_presentation_definition',
            constraints=Constraint(
                fields=[
                    Field(
                        path=['$.credentialSubject.birthDate',
                            '$.credentialSubject.dob',
                            '$.credentialSubject.dateOfBirth'],
                        name='date of birth check',
                        id='dob'
                    ),
                    Field(
                        path=['$.credentialSubject.givenName'],
                        name='given name request',
                        id='given_name',
                        optional=True
                    )]
            ),
            purpose='To be able to address the customer by name, and verify their age'
            )
        ])

    sp.add_presentation_definition('age_verification', pd)

    response = await sp.get_presentation_request('age_verification', 'BarBarBar')
    assert(response.client_id == 'BarBarBar')
    input_descriptor = response.presentation_definition.input_descriptors[0]
    assert(input_descriptor.constraints.fields[0].name == 'date of birth check')
    assert(input_descriptor.constraints.fields[0].id == 'dob')
    assert(input_descriptor.constraints.fields[1].name == 'given name request')
    assert(input_descriptor.constraints.fields[1].id == 'given_name')
    assert(input_descriptor.constraints.fields[1].optional)


@pytest.mark.asyncio
async def test_presentation_request_not_found():
    service_provider = ServiceProvider("test_bundle", "test_path")

    with pytest.raises(HTTPException):
        await service_provider.get_presentation_request(
            'non_existent',
            'example_client_id')

@pytest.mark.asyncio
async def test_presentation_request_filter():
    sp = ServiceProvider("test_bundle", "test_path")

    pd = PresentationDefinition(
        id='test_filter',
        input_descriptors=[
            InputDescriptor(
            id='credit_card_test',
            constraints=Constraint([
                Field(
                    path=['$.type'],
                    filter=Filter(
                        type='string',
                        pattern='creditCard'
                    )
                    )
                ]
            ))
        ],
        name='required_limit_disclosure'
    )

    sp.add_presentation_definition('hasCreditCard', pd)

    response = await sp.get_presentation_request('hasCreditCard', 'some_bank')
    constraints = response.presentation_definition.input_descriptors[0].constraints
    assert constraints.fields[0].filter.type == 'string'
    assert constraints.fields[0].filter.pattern == 'creditCard'

@pytest.mark.asyncio
async def test_basic_presentation(service_provider):
    sp, cert_pem, private_key = service_provider

    pd = PresentationDefinition(
        id='test_start',
        input_descriptors=[
            InputDescriptor(
                id='name',
                constraints=Constraint([
                    Field(path=['$.type'])
                ])
            )
        ],
    )
    sp.add_presentation_definition("name_presentation", pd)

    credential = bytes(json.dumps({"_fields": {"name": "Abc"}, "_type": "my_licence"}), "utf8")
    signature = private_key.sign(
        credential,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256(),
    )
    cred_string = b64encode(credential) + b"." + b64encode(signature)
    cred_string += b"~" + b64encode(bytes(json.dumps({"name": "Abc"}), "utf-8"))
    p = Presentation(credential_tokens=[cred_string.decode("utf-8")])

    response = await sp.start_presentation('hasCreditCard', p)
    print(response)

@pytest.mark.asyncio
async def test_verify_certificate_valid(service_provider):
    sp, cert_pem, _ = service_provider
    nonce = "unique_nonce"
    timestamp = time.time()

    assert sp.verify_certificate(
        cert_pem=cert_pem,
        nonce=nonce,
        timestamp=timestamp
    )

def create_dummy_certificate(private_key, public_key):
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"California"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u"San Diego"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"My Org"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"example.com"),
    ])
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        public_key
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.now(datetime.timezone.utc)
    ).not_valid_after(
        datetime.datetime.now(datetime.timezone.utc) + timedelta(days=1)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
        critical=False,
    ).sign(private_key=private_key, algorithm=hashes.SHA256())

    return cert

@pytest.fixture
def service_provider():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    dummy_cert = create_dummy_certificate(private_key, public_key)
    cert_pem = dummy_cert.public_bytes(serialization.Encoding.PEM)

    ca_bundle = [dummy_cert]
    sp = ServiceProvider(ca_bundle=ca_bundle, ca_path="dummy_path")
    return sp, cert_pem, private_key
