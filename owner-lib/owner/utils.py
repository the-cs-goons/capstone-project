from requests import Session, Response, get

async def poll_credential(url: str):
    """
    Makes a request for a pending credential
    TODO:
      - enforce https for non-dev mode for security purposes
      - validate body comes in expected format
    """
    # Closes session afterwards
    with Session() as s:
        response = await get(url)
        assert isinstance(response, Response)
        body = response.json()
        return body

def validate_jwt_signature():
    pass

def validate_disclosures():
    pass

def validate_issuer():
    pass