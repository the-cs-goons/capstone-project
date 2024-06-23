from fastapi import FastAPI
from cryptography import x509
from .models.hello_world import HelloWorldResponse


class ServiceProvider:
    def __init__(selt, ca_bundle):
        """
        initialise the service provider with a list of CA bundle
        """
        self.ca_bundle = ca_bundle

    async def hello_world(self) -> HelloWorldResponse:
        return HelloWorldResponse(hello="Hello", world="World")

    def get_server(self) -> FastAPI:
        router = FastAPI()
        router.get("/")(self.hello_world)
        return router

    def verify_certificate(self, credential):
        """
        verify the @credential take from owner
        """
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

            # Verify the certificate's signature
            issuer_certificate.public_key().verify(
                credential.signature,
                credential.tbs_certificate_bytes,
                padding.PKCS1v15(),
                credential.signature_hash_algorithm
            )

            # If the issuer is a root CA, no need to go further
            if issuer_certificate in ca_certs and issuer_certificate.subject == issuer_certificate.issuer:
                return True
            else:
                # Continue verification up the chain
                return self.verify_certificate(issuer_certificate)
        except Exception as e:
            print(f"Verification failed: {e}")
            return False