
from service import ServiceProvider
from service.models.presentation_definition import (
    PresentationDefinition,
    InputDescriptor,
    Field,
    Constraint,
    Filter
)

class DefaultServiceProvider(ServiceProvider):
    def __init__(self):
        self.client_id: str = 'barService'

        super().__init__()
        self.create_pd(
            [
                Field(['$.credentialSubject.dob', 
                        '$.dob', 
                        '$.dateOfBirth', 
                        '$.credentialSubject.dateOfBirth'],
                        name="Date of birth"),
                Field(['$.name', '$.credentialSubject.name'],
                      name="Full name",
                      optional=True)
            ])

        

    def create_pd(self, fields: list[Field]):
        pd = PresentationDefinition(
            id=f'random_pd{len(self.presentation_definitions)}',
            input_descriptors=[
                InputDescriptor(
                id='random_pd',
                constraints=Constraint(
                    fields=fields,
                    limit_disclosure='required'))
            ]
        )

        self.add_presentation_definition('example', pd)


service_provider = DefaultServiceProvider()
service_provider_server = service_provider.get_server()
