"""Common module used by `vclib`.

Contains classes, functions and other helpers used by multiple parties in
the VC model.
"""

# Add imports from `common/src` here to expose objects under vclib.common
from .src.data_transfer_objects import vp_auth_request as vp_auth_request
from .src.data_transfer_objects import vp_auth_response as vp_auth_response
from .src.hello_world import hello_world as hello_world
from .src.sdjwt_vc.exceptions import (
    SDJWTVCNoHolderPublicKeyError as SDJWTVCNoHolderPublicKeyError,
)
from .src.sdjwt_vc.exceptions import (
    SDJWTVCRegisteredClaimsError as SDJWTVCRegisteredClaimsError,
)
from .src.sdjwt_vc.holder import SDJWTVCHolder as SDJWTVCHolder
from .src.sdjwt_vc.issuer import SDJWTVCIssuer as SDJWTVCIssuer
