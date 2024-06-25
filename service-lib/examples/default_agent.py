
from service import ServiceProvider
from service.models.presentation_definition import (
    PresentationDefinition,
    InputDescriptor,
    Field,
    Constraint
)

class DefaultServiceProvider(ServiceProvider):
    def __init__(self):
        self.client_id: str = 'barService'

        super().__init__()
        pd = PresentationDefinition(
            id='test_limit_disclosure_1',
            input_descriptors=[
                InputDescriptor(
                id='limit_disclosure_test',
                constraints=Constraint([
                    Field(['$.credentialSubject.dob', '$.dob', '$dateOfBirth', '$.credentialSubject.dateOfBirth'])],
                    limit_disclosure='required'))
            ]
        )

        self.add_presentation_definition('example', pd)

service_provider = DefaultServiceProvider()
service_provider_server = service_provider.get_server()
