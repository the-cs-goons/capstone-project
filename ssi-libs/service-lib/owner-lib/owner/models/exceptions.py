class BaseIdentityOwnerException(Exception):
    """
    Base exception type
    """
    pass

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
    pass

class IssuerTypeNotFoundException(BadIssuerRequestException):
    """
    Exception type for when ID Owner requests an invalid credential type
    """
    pass

class IssuerURLNotFoundException(BadIssuerRequestException):
    """
    Exception type for when given issuer url doesn't appear to exist
    """
    pass

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