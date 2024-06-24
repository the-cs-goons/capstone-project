import os
import time

import requests
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from fastapi import FastAPI, HTTPException

from .models.hello_world import HelloWorldResponse


class ServiceProvider:
    def __init__(self, ca_bundle, ca_path):
        """
        initialise the service provider with a list of CA bundle
        """
        self.ca_bundle = ca_bundle
        self.ca_path = ca_path
        self.used_nonces = {}

    def load_ca_bundle(self, path):
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
                        ca_certs.append(x509.load_pem_x509_certificate(
                            cert, default_backend()
                        ))
        except FileNotFoundError:
            print("CA bundle file not found.")
        return ca_certs

    def update_ca_bundle(self, url):
        """
        This method updates the CA bundle from a URL
        """
        response = requests.get(url, verify=True)
        if response.status_code == 200:
            with open(self.ca_bundle_path, 'wb') as f:
                f.write(response.content)
            # Reload the ca_bundle attribute with the new data
            self.ca_bundle = self.load_ca_bundle(self.ca_bundle_path)
        else:
            print("Failed to download CA bundle")

    async def hello_world(self) -> HelloWorldResponse:
        return HelloWorldResponse(hello="Hello", world="World")

    def verify_certificate(self, credential, nonce, timestamp):
        """
        Verify the @credential take from owner
        """
        current_time = time.time()
        # Check if the nonce has been used or expired
        if nonce in self.used_nonces or current_time - timestamp > 300:
            return False

        ca_bundle = self.ca_bundle
        try:
            # Attempt to find the issuer in the provided CA bundle
            issuer_certificate = None
            for ca in ca_bundle:
                if credential.issuer == ca.subject:
                    issuer_certificate = ca
                    break

            # No valid issuer found
            if issuer_certificate is None:
                return False

            # Verify the certificate's signature using the isser's public key
            issuer_certificate.public_key().verify(
                credential.signature,
                credential.tbs_certificate_bytes,
                padding.PKCS1v15(),
                credential.signature_hash_algorithm
            )

            # If the issuer is a root CA, no need to go further
            if (issuer_certificate in ca_bundle
                    and issuer_certificate.subject == issuer_certificate.issuer):
                self.used_nonces[nonce] = True  # Mark nonce as used
                return True
            else:
                # Continue verification up the chain
                return self.verify_certificate(issuer_certificate)
        except Exception as e:
            print(f"Verification failed: {e}")
            return False

    async def try_verify_certificate(self, credential):
        nonce = credential.nonce
        timestamp = credential.timestamp
        if not self.verify_certificate(credential, nonce, timestamp):
            raise HTTPException(
                status_code=400, detail="Certificate verification failed"
            )
        return {"status": "Certificate verified successfully"}

    async def try_update_ca_bundle(self, url):
        try:
            self.update_ca_bundle(url)
            return {"status": "CA bundle updated successfully"}
        except Exception as e:
            return {"error": str(e)}

    def get_server(self) -> FastAPI:
        router = FastAPI()
        router.get("/")(self.hello_world)
        router.post("/verify-certificate/{credential}")(self.try_verify_certificate)
        router.post("/update-ca-bundle/{url}")(self.try_update_ca_bundle)
        return router