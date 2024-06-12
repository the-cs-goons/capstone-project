from .utils import get

def test_hello_world():
    res = get("/")
    assert res.status_code == 200
    assert res.json() == {"hello": "Hello", "world": "World"}
