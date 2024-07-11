import datetime
import os
import time
from typing import Literal, Optional

import requests
from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.x509 import Certificate
from cryptography.x509.oid import NameOID, ObjectIdentifier
from fastapi import FastAPI, HTTPException

from .models.presentation_definition import PresentationDefinition
from .models.presentation_request_response import PresentationRequestResponse

class ServiceProvider:
    def __init__(self, ca_bundle, ca_path: str, presentation_definitions: dict[str, PresentationRequestResponse] = {}):
        """
        initialise the service provider with a list of CA bundle
        """
        self.presentation_definitions = presentation_definitions
        self.ca_bundle = ca_bundle
        self.ca_path = ca_path
        self.used_nonces = set()

    def get_server(self) -> FastAPI:
        router = FastAPI()
        router.get('/request/{request_type}')(self.get_presentation_request)
        router.post("/verify-certificate/{credential}")(self.try_verify_certificate)
        return router

    def add_presentation_definition(self, request_type: str, presentation_definition: PresentationDefinition) -> None:
        self.presentation_definitions[request_type] = presentation_definition

    async def get_presentation_request(self, request_type: str, client_id: str) -> PresentationRequestResponse:
        if request_type not in self.presentation_definitions:
            raise HTTPException(status_code=404, detail='Request type not found')

        return PresentationRequestResponse(client_id, self.presentation_definitions[request_type])

    def load_ca_bundle(self, path: str):
        """
        This method loads the CA bundle from a local file
        """
        ca_certs = []
        try:
            with open(path, 'rb') as bundle_file:
                certs = bundle_file.read()
                for cert in certs.split(b'-----END CERTIFICATE-----\n'):
                    if cert:
                        cert += b'-----END CERTIFICATE-----\n'
                        ca_certs.append(x509.load_pem_x509_certificate(cert))
        except FileNotFoundError as e:
            raise FileNotFoundError(f"CA bundle file not found: {e}")
        return ca_certs

    def verify_certificate(self, cert_pem: bytes, nonce: str, timestamp: float) -> bytes:
        """
        Verify the @credential take from owner
        """
        current_time = datetime.datetime.now(datetime.timezone.utc)
        timestamp_datetime = datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc)
        # Check if the nonce has been used or expired
        if (nonce in self.used_nonces or (current_time - timestamp_datetime).total_seconds() > 300):
            raise Exception("Certificate is being replayed")

        certificate = x509.load_pem_x509_certificate(cert_pem)
        ca_bundle = self.ca_bundle
        # Check each CA cert to see if it can validate the certificate
        for ca_cert in ca_bundle:
            # print(ca_cert.tbs_certificate_bytes)
            try:
                ca_cert.public_key().verify(certificate.signature, certificate.tbs_certificate_bytes, padding.PKCS1v15(), hashes.SHA256())
                # return True
                not_valid_before = certificate.not_valid_before.replace(tzinfo=datetime.timezone.utc)
                not_valid_after = certificate.not_valid_after.replace(tzinfo=datetime.timezone.utc)
                # Check the validity period of the certificate
                if not_valid_before <= current_time <= not_valid_after:
                    self.used_nonces.add(nonce)     # Mark nonce as used
                    # Print the issuer's details and return issuer's DID
                    return self.get_issuer_detail(ca_cert)
                else:
                    raise Exception("Certificate expired")
            except InvalidSignature:
                print("Signature is invalid.")
                continue
            except Exception as e:
                print(f"the erroris : {e}")
                continue    # Try next CA
        raise Exception("Failed to find certificate")     # No CA certificates matched

    def get_issuer_detail(self, issuer: Certificate) -> bytes:
        """
        Print details of the current issuer
        Return the issuer object contains all the information for future modification
        """
        did = None
        print("issuer detail")
        print("Issuer:")
        for name in issuer.issuer:
            print(f"{name.oid._name}: {name.value}")

        print("\nSubject:")
        for name in issuer.subject:
            print(f"{name.oid._name}: {name.value}")

        print("\nSerial Number:")
        print(issuer.serial_number)

        print("\nValidity:")
        print("Not Before:", issuer.not_valid_before)
        print("Not After:", issuer.not_valid_after)

        print("\nExtensions:")
        for ext in issuer.extensions:
            if isinstance(ext.value, x509.SubjectAlternativeName):
                print("Subject Alternative Name:",
                    ext.value.get_values_for_type(x509.DNSName))
            elif isinstance(ext.oid, ObjectIdentifier):
                did = ext.value.value
                print("Custom DID Extension:", ext.value)
            else:
                print(f"{ext.oid.dotted_string}: {ext.value}")
        # Add custom issuer detail print

        return did


    async def try_verify_certificate(self, certificate: bytes, nonce: str, timestamp: float):
        if not self.verify_certificate(certificate, nonce, timestamp):
            raise HTTPException(status_code=400, detail="Certificate verification failed")
        return {"status": "Certificate verified successfully"}
