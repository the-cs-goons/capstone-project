from collections.abc import Callable

from sd_jwt.verifier import SDJWTVerifier


class SDJWTVCVerifier(SDJWTVerifier):
    def __init__(
        self,
        sd_jwt_presentation: str,
        cb_get_issuer_key: Callable[[str, dict], str],
        expected_aud: str | None = None,
        expected_nonce: str | None = None,
        serialization_format: str = "compact",
        cb_get_holder_key: None | Callable[[str, dict], str] = None,
        *,
        expect_kb_jwt: bool = True,
    ):
        """### Parameters
        - sd_jwt_presentation(`str`): A presentation from a credential
        holder
        - cb_get_issuer_key(`(str, Dict) -> str`): A callback function
        that takes two parameters: an issuer identifier and a `dict` of
        the SD JWT header parameters. Should return a JSON Web Key. (The
        type hint might be incorrect, it might need to be a `JWK`.
        - expected_aud(`str`): The expected `aud` claim of the KB JWT if
        applicable
        - expected_nonce(`str`): The expected `nonce` claim of the KB JWT
        if applicable
        - serialization_format(`str`): "compact" (default) or "json"
        """
        super().__init__(
            sd_jwt_presentation,
            cb_get_issuer_key,
            expected_aud,
            expected_nonce,
            serialization_format,
        )
