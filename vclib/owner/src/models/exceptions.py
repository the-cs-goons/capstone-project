class BaseIdentityOwnerError(Exception):
    """
    Base exception type
    """

    pass


class IdentityOwnerError(BaseIdentityOwnerError):
    """
    Base exception type for when something goes wrong with the Identity Owner
    """

    pass


class CredentialNotFoundError(IdentityOwnerError):
    """
    Exception type for trying to retrieve a non-existent credential
    """

    pass


class BadIssuerRequestError(IdentityOwnerError):
    """
    Exception type for when ID Owner makes a bad request
    """

    pass


class IssuerTypeNotFoundError(BadIssuerRequestError):
    """
    Exception type for when ID Owner requests an invalid credential type
    """

    pass


class IssuerURLNotFoundError(BadIssuerRequestError):
    """
    Exception type for when given issuer url doesn't appear to exist
    """

    pass


class CredentialIssuerError(BaseIdentityOwnerError):
    """
    Base exception type for when an error comes back from a credential issuer's API
    """

    pass


class ServiceProviderError(BaseIdentityOwnerError):
    """
    Base exception type for when an error comes back from a service provider
    """

    pass
