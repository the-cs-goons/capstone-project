class BaseIdentityOwnerError(Exception):
    """Base exception type"""


class IdentityOwnerError(BaseIdentityOwnerError):
    """Base exception type for when something goes wrong with the Identity Owner"""


class CredentialNotFoundError(IdentityOwnerError):
    """Exception type for trying to retrieve a non-existent credential"""


class BadIssuerRequestError(IdentityOwnerError):
    """Exception type for when ID Owner makes a bad request"""


class IssuerTypeNotFoundError(BadIssuerRequestError):
    """Exception type for when ID Owner requests an invalid credential type"""


class IssuerURLNotFoundError(BadIssuerRequestError):
    """Exception type for when given issuer url doesn't appear to exist"""


class CredentialIssuerError(BaseIdentityOwnerError):
    """Base exception type for when an error comes back from a credential issuer"""


class ServiceProviderError(BaseIdentityOwnerError):
    """Base exception type for when an error comes back from a service provider"""
