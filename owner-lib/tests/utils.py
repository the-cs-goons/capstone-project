import os

import requests

def get(url: str, *args, **kwargs) -> requests.Response:
    return requests.get(f"http://localhost:{os.getenv('CS3900_OWNER_AGENT_PORT')}/{url}", *args, **kwargs)
