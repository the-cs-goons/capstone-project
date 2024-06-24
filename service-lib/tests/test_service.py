import pytest
from service import ServiceProvider
from fastapi import FastAPI, HTTPException

@pytest.mark.asyncio
async def test_server_exists():
    sp = ServiceProvider()
    sp_server = sp.get_server()
    assert type(sp_server) == FastAPI

@pytest.mark.asyncio
async def test_basic_presentation_request():
    sp = ServiceProvider()
    sp.create_presentation_request(
        'test_empty',
        'tester',
        sp.create_presentation_definition(
            id='test1',
            input_descriptors=[]
        )
    )

    response = await sp.get_presentation_request('test_empty')
    assert response.client_id == 'tester'
    assert response.presentation_definition.id == 'test1'
    assert response.presentation_definition.input_descriptors == []

@pytest.mark.asyncio
async def test_multiple_presentation_requests():
    sp = ServiceProvider()
    sp.create_presentation_request(
        'test_1',
        'tester1',
        sp.create_presentation_definition(
            id='test1',
            input_descriptors=[]
        )
    )

    response = await sp.get_presentation_request('test_1')
    assert response.client_id == 'tester1'
    assert response.presentation_definition.id == 'test1'

    sp.create_presentation_request(
        'test_2',
        'tester2',
        sp.create_presentation_definition(
            id='test2',
            input_descriptors=[]
        )
    )

    response = await sp.get_presentation_request('test_1')
    assert response.client_id == 'tester1'
    assert response.presentation_definition.id == 'test1'

    response = await sp.get_presentation_request('test_2')
    assert response.client_id == 'tester2'
    assert response.presentation_definition.id == 'test2'

@pytest.mark.asyncio
async def test_presentation_request_limit_disclosure():
    sp = ServiceProvider()

    sp = ServiceProvider()
    sp.create_presentation_request(
        type='test_limit_disclosure',
        client_id='tester provider',
        presentation_definition=sp.create_presentation_definition(
            id='test_limit_disclosure_1',
            input_descriptors=[
                sp.create_input_descriptor(
                id='limit_disclosure_test',
                constraints=sp.create_constraint([
                    sp.create_field(['$.credentialSubject.active'])],
                    limit_disclosure='required'))
            ],
            name='required_limit_disclosure'
        )
    )
    response = await sp.get_presentation_request('test_limit_disclosure')

    assert response.presentation_definition.input_descriptors[0].constraints.limit_disclosure == 'required'

@pytest.mark.asyncio
async def test_presentation_request_two_fields_optional():
    sp = ServiceProvider()
    dob_field = sp.create_field(
        path=['$.credentialSubject.birthDate', 
            '$.credentialSubject.dob', 
            '$.credentialSubject.dateOfBirth'],
        name='date of birth check',
        id='dob')
    
    given_name_field = sp.create_field(
        path=['$.credentialSubject.givenName'],
        name='given name request',
        id='given_name',
        optional=True)
    
    constraint = sp.create_constraint(
        fields=[dob_field, given_name_field])
    
    input_descriptor = sp.create_input_descriptor(
        id='name_age_presentation_definition',
        name='name_age_presentation_definition',
        constraints=constraint,
        purpose='To be able to address the customer by name, and verify their age')
    
    pd = sp.create_presentation_definition(
        id='name_age_presentation_1',
        name='Age and Name request',
        purpose='To be able to address the customer by name, and verify their age',
        input_descriptors=[input_descriptor])

    sp.create_presentation_request('age_verification', 'BarBarBar', pd)

    response = await sp.get_presentation_request('age_verification')
    assert(response.client_id == 'BarBarBar')
    assert(response.presentation_definition.input_descriptors[0].constraints.fields[0].name == 'date of birth check')
    assert(response.presentation_definition.input_descriptors[0].constraints.fields[0].id == 'dob')
    assert(response.presentation_definition.input_descriptors[0].constraints.fields[1].name == 'given name request')
    assert(response.presentation_definition.input_descriptors[0].constraints.fields[1].id == 'given_name')
    assert(response.presentation_definition.input_descriptors[0].constraints.fields[1].optional)


@pytest.mark.asyncio
async def test_presetation_request_not_found():
    service_provider = ServiceProvider()

    with pytest.raises(HTTPException):
        await service_provider.get_presentation_request('age_verification')