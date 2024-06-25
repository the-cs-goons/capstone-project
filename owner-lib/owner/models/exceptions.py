class BaseIdentityOwnerException(BaseException):
    """
    Base exception type
    """
    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return f"{type(self).__name__}: {self.message}"

class IdentityOwnerException(BaseIdentityOwnerException):
    """
    Base exception type for when something goes wrong with the Identity Owner
    """
    pass

class CredentialNotFoundException(IdentityOwnerException):
    """
    Exception type for trying to retrieve a non-existent credential
    """
    pass

class BadIssuerRequestException(IdentityOwnerException):
    """
    Exception type for when ID Owner makes a bad request
    """

class CredentialIssuerException(BaseIdentityOwnerException):
    """
    Base exception type for when an error comes back from a credential issuer's API
    """
    pass

class ServiceProviderException(BaseIdentityOwnerException):
    """
    Base exception type for when an error comes back from a service provider
    """
    pass