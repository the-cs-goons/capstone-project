class SDJWTVCRegisteredClaimsException(Exception):
    """Exception raised when a registered JWT claim that cannot be disclosed is marked as disclosable."""

    def __init__(self, claim: str):
        super().__init__(
            f"Registered claim '{claim}' cannot be selectively disclosed."
        )

class SDJWTVCNoHolderPublicKey(Exception):
    """Exception raised when key binding is enforced and a holder key is expected, but 
    the holder key is `None`."""

    def __init__(self):
        super().__init__(
            f"Holder Key cannot be `None`."
        )

class SDJWTVCInvalidHolderPublicKey(Exception):
    """Exception raised when the holder public key referenced in an SDJWT is incorrect"""

    def __init__(self):
        super().__init__(
            f"Holder key referenced in `cnf` claim does not match expected value."
        )