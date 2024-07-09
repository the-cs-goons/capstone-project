from jwcrypto.jwk import JWK
from sd_jwt.holder import SDJWTHolder

from .exceptions import SDJWTVCNewHolderVCHasKBJWTException


class SDJWTVCHolder(SDJWTHolder):
    """
    SD JWT VC class for credential holders (identity owners).

    Built upon the SDJWTHolder class from `sd_jwt`. Adds some extra things, mostly 
    verification of things that the SD JWT specification leaves blank but the SD JWT VC
    specification requires. Actually attempts to document the parent class.

    TODO: Document further
    """

    VERIFY_HOLDER_KEY = True

    def __init__(self, 
                 sd_jwt_issuance: str, 
                 serialization_format: str = "compact",
                 enforce_no_key_binding: bool = False):
        """
        TODO: Docs
        """
        super().__init__(sd_jwt_issuance, serialization_format)
        # Most of what's required is already implemented, we don't have to check 
        # `status` because revocation is out of scope for this project.
        # There's some missing verification we could implement but for now I'm leaving
        # that out

        # When receiving the credential from the issuer, this should be enforced
        if enforce_no_key_binding and self._unverified_input_key_binding_jwt != '':
            raise SDJWTVCNewHolderVCHasKBJWTException
        
    def serialise_issuance_compact(self) -> str:
        """
        Serialises the credential in a manner that can be stored, in compact format.
        NOT for creating a verifiable presentation.

        ### Returns
        - `str`: A serialised SD-JWT-VC
        """
        sep = self.COMBINED_SERIALIZATION_FORMAT_SEPARATOR
        serialised = self.serialized_sd_jwt + sep
        serialised += sep.join(self._hash_to_disclosure.values()) + sep
        return serialised
    
    def create_verifiable_presentation(self, 
                            claims_to_disclose: list | dict, 
                            nonce=None, 
                            aud=None, 
                            holder_key=None, 
                            sign_alg=None):
        """
        Creates a verifiable presentation.

        Uses the method of the parent class, defined separately here for now to better
        document it.

        ### Parameters
        - claims_to_disclose(`list | dict`): Claims to be disclosed
        - nonce(`str`)
        """
        return super().create_presentation(claims_to_disclose, 
                                           nonce, 
                                           aud, 
                                           holder_key, 
                                           sign_alg)


