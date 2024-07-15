import json
from base64 import b64encode
from hashlib import sha256
from typing import Any

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes
from pydantic import BaseModel, PrivateAttr

class JsonWebKey(BaseModel):
    kty: str = "EC"
    crv: str = "P-256"
    x: str
    y: str

class SdjwtConfirmation(BaseModel):
    jwk: JsonWebKey

class Sdjwt(BaseModel):
    _sd: list[str]
    iss: str
    iat: int
    exp: int
    vct: str
    _sd_alg: str = "sha-256"
    cnf: SdjwtConfirmation

    fields: dict[str, str] = PrivateAttr()

    # def __init__(self, issuer_url: str, information: dict[str, Any]):
    #     self.iss = issuer_url
    #     self.iat = now
    #     self.exp = forever
    #     self.vct = credential_spec_url
    #     self.cnf = asdasd

    #     for field_name, field_value in self.information.items():
    #         field_json = json.dumps({field_name: field_value})
    #         self.fields[field_name] = field_json
    #         field_hash = sha256(bytes(field_json, encoding="utf8")).hexdigest()
    #         self._sd.append(field_hash)

    # def get_cred_string(self, private_key: PrivateKeyTypes, disclosed_fields: list[str]) -> str:
    #     credential = self.model_dump_json()

    #     signature = private_key.sign(
    #         bytes(credential, "utf-8"),
    #         padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
    #         hashes.SHA256(),
    #     )

    #     cred_string = b64encode(credential) + b"." + b64encode(signature)
    #     for field_name in disclosed_fields:
    #         cred_string += b"~" + b64encode(bytes(json.dumps(self.fields[field_name]), "utf-8"))

    #     return cred_string.decode("utf-8")
