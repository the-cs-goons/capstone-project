from sd_jwt.holder import SDJWTHolder
from jwcrypto.jwk import JWK

from .exceptions import SDJWTVCNoHolderPublicKey
from .issuer import SDJWTVCIssuer

class SDJWTVCHolder(SDJWTHolder):
    """
    SD JWT VC class for credential holders (identity owners).

    Built upon the SDJWTHolder class from `sd_jwt`. Adds some extra things, mostly 
    verification of things that the SD JWT specification leaves blank but the SD JWT VC
    specification requires. Actually attempts to document the parent class.

    TODO: Document further
    """

    EXPECT_HOLDER_PUB_KEY = True

    def __init__(self, 
                 sd_jwt_issuance: str, 
                 holder_key: JWK | None,
                 serialization_format: str = "compact"):
        """
        TODO: Docs
        """

        if self.EXPECT_HOLDER_PUB_KEY and holder_key is None:
            raise SDJWTVCNoHolderPublicKey
        super().__init__(sd_jwt_issuance, serialization_format)
