from jwcrypto.jwk import JWK
from jwcrypto.jwt import JWT
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

    _unverified_sd_jwt: JWT

    def __init__(self, sd_jwt_issuance: str, serialization_format: str = "compact", enforce_no_key_binding: bool = True):
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

        self._unverified_sd_jwt = JWT(jwt=self.serialized_sd_jwt)
        self._is_verified = False

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

    def create_keybound_presentation(self, claims_to_disclose: list | dict, nonce: str, aud: str, holder_key: JWK, sign_alg: None | str = None, unsafe = False):
        """
        Creates a verifiable presentation with a KB JWT.

        Creates a presentation, but differs from `create_presentation` as implemented
        in the parent class by enforcing the required variables to create a KB-JWT.
        For creating presentations without enforcing KB JWTs, use `create_presentation`

        TODO: Improve this so passing the claims_to_disclose obj doesn't suck

        ### Parameters
        - claims_to_disclose(`list | dict`): Claims to be disclosed in the presentation
        - nonce(`str`): The nonce value as supplied by the verifier (provider)
        - aud(`str`): The intended audience of this presentation
        - holder_key(`JWK`): The holder's private key, corresponding to the public key
        given in the `cnf` claim of the SD JWT
        - sign_alg(`str`): The signing algorithm to use, "ES256" by default.

        Does not return anything. Retrieve output from `sd_jwt_presentation` attribute.
        """
        if not unsafe and not self._is_verified:
            raise Exception

        super().create_presentation(claims_to_disclose, nonce, aud, holder_key, sign_alg)

    def verify_signature(self, pub_key: JWK) -> bool:
        """
        Checks for a valid signature.
        """
        try:
            self._unverified_sd_jwt.validate(pub_key)
            self._is_verified = True
        except Exception:
            raise Exception # TODO: Clearer exception type
