class SDJWTVCRegisteredClaimsException(Exception):
    """
    Exception raised when a registered JWT claim that cannot be disclosed is marked as
    disclosable.
    """

    def __init__(self, claim: str):
        super().__init__(f"Registered claim '{claim}' cannot be selectively disclosed.")


class SDJWTVCNoHolderPublicKeyException(Exception):
    """
    Exception raised when key binding is enforced and a holder key is expected, but the
    holder key is `None`.
    """

    def __init__(self):
        super().__init__("Holder Key cannot be `None`.")


class SDJWTVCInvalidHolderPublicKeyException(Exception):
    """
    Exception raised when the holder public key referenced in an SDJWT is incorrect
    """

    def __init__(self):
        super().__init__(
            "Holder key referenced in `cnf` claim does not match expected value."
        )


class SDJWTVCNewHolderVCHasKBJWTException(Exception):
    """
    Exception raised when a credential received from an issuer has a KB JWT attached
    (the specification states that in this instance the credential MUST be ignored)
    """

    def __init__(self):
        super().__init__("Issued credential contains a KB JWT.")
