#!/bin/bash

openssl req -nodes -x509 -sha256 -newkey rsa:4096 \
  -keyout vclib/holder/examples/example_ssl_keyfile.key \
  -out vclib/holder/examples/example_ssl_certfile.crt \
  -days 3650 \
  -subj "/C=AU/ST=New South Wales/L=Sydney/O=The CS Goons Pty Ltd/OU=/CN=holder-lib" \
  -addext "subjectAltName = DNS:localhost,DNS:holder-lib"

openssl req -nodes -x509 -sha256 -newkey rsa:4096 \
  -keyout vclib/issuer/examples/example_ssl_keyfile.key \
  -out vclib/issuer/examples/example_ssl_certfile.crt \
  -days 3650 \
  -subj "/C=AU/ST=New South Wales/L=Sydney/O=The CS Goons Pty Ltd/OU=/CN=issuer-lib" \
  -addext "subjectAltName = DNS:localhost,DNS:issuer-lib"

openssl req -nodes -x509 -sha256 -newkey rsa:4096 \
  -keyout vclib/verifier/examples/example_ssl_keyfile.key \
  -out vclib/verifier/examples/example_ssl_certfile.crt \
  -days 3650 \
  -subj "/C=AU/ST=New South Wales/L=Sydney/O=The CS Goons Pty Ltd/OU=/CN=verifier-lib" \
  -addext "subjectAltName = DNS:localhost,DNS:verifier-lib"

cat vclib/issuer/examples/example_ssl_certfile.crt > vclib/holder/examples/example_ssl_ca_bundle.crt
cat vclib/verifier/examples/example_ssl_certfile.crt >> vclib/holder/examples/example_ssl_ca_bundle.crt
