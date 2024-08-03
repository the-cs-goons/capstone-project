If you need to regenerate QR codes because you specified alternative ports, you should only need to alter the ports in the below examples.

### Issuance

The issuance QR codes looks like:

```
credential_offer=%7B%22credential_issuer%22%3A%20%22https%3A%2F%2Fissuer-lib%3A8082%22%2C%20%22credential_configuration_ids%22%3A%20%5B%22DriversLicense%22%5D%7D
```
- `credential_offer`: A URL encoded JSON object representing the credential offer:

```json
{
    "credential_issuer": "https://issuer-lib:8082",
    "credential_configuration_ids": ["DriversLicense"]
}
```
The fields in this JSON object are:
- `credential_issuer`: the credential issuer's URI. This should be `https://verifier-lib:{CS3900_LICENSE_ISSUER_DEMO_AGENT_PORT | CS3900_VACCINATION_ISSUER_DEMO_AGENT_PORT}`
-  `credential_configuration_ids`: An array of strings that represent the kinds of credential on offer. Our example that runs provides a `DriversLicense`.

### Presentation

The verification QR codes looks like:

```
request_uri=https%3A%2F%2Fverifier-lib%3A8084%2Frequest%2Fverify_over_18
```
This is a url-encoded query parameter string with the following parameters:
- `request_uri`: The URL of the verifier's request. This should look something like:
    `https://verifier-lib:{CS3900_BAR_VERIFIER_DEMO_AGENT_PORT | CS3900_CAR_RENTAL_VERIFIER_DEMO_AGENT_PORT}/request/verify_over_18`
    Note that the domain is `verifier-lib`, NOT `localhost`.