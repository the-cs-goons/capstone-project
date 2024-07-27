from typing import ClassVar

from jwcrypto.jwk import JWK
from sd_jwt.common import SDObj
from sd_jwt.issuer import SDJWTIssuer

from .exceptions import (
    SDJWTVCNoHolderPublicKeyError,
    SDJWTVCRegisteredClaimsError,
)


class SDJWTVCIssuer(SDJWTIssuer):
    """SD JWT VC class for credential issuers.

    Built upon the SDJWTIssuer class from `sd_jwt`. Adds some extra things, mostly
    verification of things that the SD JWT specification leaves blank but the SD JWT VC
    specification requires. Actually attempts to document the parent class.

    TODO: Document further
    """

    SD_JWT_HEADER = "vc+sd-jwt"
    NONDISCLOSABLE_CLAIMS: ClassVar = ["iss", "nbf", "exp", "cnf", "vct", "status"]
    ENFORCE_KEY_BINDING = False  # For extensibility; False by default, can be enabled

    def __init__(
        self,
        disclosable_claims: dict,
        oth_claims: dict,
        issuer_key: JWK,
        holder_key: JWK | None,
        extra_header_parameters: dict = {},
        **kwargs,
    ):
        """Creates new SDJWT from a set of disclosable/non-disclosable claims and signs
        it.

        ### Parameters
        - disclosable_claims(`dict`): A dict representing key/value pairs that the
        recipient of this credential should be able to **selectively disclose**.
        - oth_claims(`dict`): A dict representing key/value pairs that the recipient
        of this credential should NOT be able to selectively disclose (e.g. the `exp`
        expiry claim.)
        - issuer_key(`JWK`): The issuer's signing key, as a `JWK` (see `jwcrypto.jwk`)
        - holder_key(`JWK | None`): The holder's public key, as a `JWK`, if required
        (see `jwcrypto.jwk`). If `ENFORCE_KEY_BINDING` is enabled (default), an error
        will be thrown if `None` is given.

        ### Attributes
        The following come from the parent class from the sd-jwt module. They're
        documented here for clarity and ease of use.
        - sd_jwt(`JWS`): A JSON Serialised JWS. If serialisation format is set to
        `json`, will include disclosures under the member name `"disclosures"`. If
        format is `compact` (default), the disclosures will not be present in this
        format.
        - serialized_sd_jwt(`str`): The SD JWT without the disclosures appended
        - sd_jwt_issuance(`str`): The SD JWT + encoded disclosures, separated by a `~`
        character.
        - sd_jwt_payload(`dict`): A dict representing the decoded payload of the SD JWT.
        - extra_header_parameters(`dict`): A dict with other parameters to put in the
        SD JWT header. For now, you can add the `kid` of the issuer key here

        Other keyword arguments that `SDJWTIssuer` accepts can be passed down as
        keyword arguments - such as extra header options, or a holder key for KB JWTs
        """
        payload = self._wrap_dict(disclosable_claims)

        payload = payload | oth_claims

        if self.ENFORCE_KEY_BINDING and holder_key is None:
            raise SDJWTVCNoHolderPublicKeyError

        # TODO: specific checking for mandatory fields that SDJWTIssuer does not enforce
        # TODO: verification of any registered JWT claims
        # TODO: put the right stuff in the headers

        super().__init__(
            payload,
            issuer_key,
            holder_key=holder_key,
            extra_header_parameters=extra_header_parameters,
            **kwargs,
        )

    def get_disclosures(self):
        """TODO: Make this easier"""
        return [digest.json for digest in self.ii_disclosures]

    def _wrap_dict(self, disclosable_claims) -> dict:
        payload = {}
        for key, value in disclosable_claims.items():
            # Registered JWT claims are not disclosable
            if key in self.NONDISCLOSABLE_CLAIMS:
                raise SDJWTVCRegisteredClaimsError(key)
            # The base class checks for disclosable claims by checking for this
            # wrapper class. If there are nested objects or objects within lists,
            # handle them as well.
            if isinstance(value, list):
                value_list = []
                for v in value:
                    if isinstance(v, dict):
                        value_list.append(self._wrap_dict(v))
                    else:
                        value_list.append(v)
                payload[SDObj(key)] = value_list
            elif isinstance(value, dict):
                payload[SDObj(key)] = self._wrap_dict(value)
            else:
                payload[SDObj(key)] = value
        return payload
