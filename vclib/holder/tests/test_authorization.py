import pytest
from fastapi import HTTPException

from vclib.holder.src.models.login_register import LoginRequest, RegisterRequest

# from fastapi import HTTPException
from vclib.holder.src.storage.local_storage_provider import LocalStorageProvider
from vclib.holder.src.web_holder import WebHolder

EXAMPLE_ISSUER = "https://example.com"
OWNER_HOST = "https://localhost"
OWNER_PORT = "8080"
OWNER_URI = f"{OWNER_HOST}:{OWNER_PORT}"


@pytest.fixture
def holder(tmp_path_factory):
    return WebHolder(
        [f"{OWNER_URI}/add"],
        f"{OWNER_URI}/offer",
        LocalStorageProvider(storage_dir_path=tmp_path_factory.mktemp("test_storage")),
    )


@pytest.fixture
def auth_header(holder: WebHolder):
    holder.store.register("asdf", "1234567890")
    return f"Bearer {holder._generate_jwt({"username": "asdf"})}"


@pytest.mark.asyncio()
async def test_correctly_authorizes(holder: WebHolder, auth_header: str):
    await holder.refresh_all(auth_header)


@pytest.mark.asyncio()
async def test_no_token(holder: WebHolder):
    with pytest.raises(HTTPException) as e:
        await holder.refresh_all()

    assert e.value.status_code == 403


@pytest.mark.asyncio()
async def test_bad_token(holder: WebHolder):
    with pytest.raises(HTTPException) as e:
        await holder.refresh_all("bearer asdf")

    assert e.value.status_code == 400


@pytest.mark.asyncio()
async def test_invalid_token_type(holder: WebHolder, auth_header: str):
    with pytest.raises(HTTPException) as e:
        token = "not_bearer " + auth_header.split()[1]
        await holder.refresh_all(token)

    assert e.value.status_code == 400


@pytest.mark.asyncio()
async def test_token_expired(holder: WebHolder):
    holder.TOKEN_EXP_SECS = 0
    auth_header = f"Bearer {holder._generate_jwt({"username": "asdf"})}"
    with pytest.raises(HTTPException) as e:
        await holder.refresh_all(auth_header)

    assert e.value.status_code == 400


def test_register(holder: WebHolder):
    u = "asdf"
    pw = "1234567890"
    resp = holder.user_register(RegisterRequest(username=u, password=pw, confirm=pw))

    assert resp.username == u
    assert resp.token_type == "Bearer"


def test_register_passwords_dont_match(holder: WebHolder):
    u = "asdf"
    pw = "1234567890"
    with pytest.raises(HTTPException) as e:
        holder.user_register(RegisterRequest(username=u, password=pw, confirm="asdf"))

    error = e.value
    assert error.status_code == 400
    assert "passwords don't match" in error.detail.lower()


def test_register_short_password(holder: WebHolder):
    u = "asdf"
    pw = "0"
    with pytest.raises(HTTPException) as e:
        holder.user_register(RegisterRequest(username=u, password=pw, confirm=pw))
    assert e.value.status_code == 400


def test_double_register(holder: WebHolder):
    u = "asdf"
    pw = "1234567890"
    holder.user_register(RegisterRequest(username=u, password=pw, confirm=pw))

    with pytest.raises(HTTPException) as e:
        holder.user_register(RegisterRequest(username=u, password=pw, confirm=pw))
    assert e.value.status_code == 400


def test_logout(holder: WebHolder):
    u = "asdf"
    pw = "1234567890"
    holder.user_register(RegisterRequest(username=u, password=pw, confirm=pw))

    assert holder.store.active_user.username == "asdf"

    holder.user_logout()

    assert holder.store.active_user is None


def test_login(holder: WebHolder):
    u = "asdf"
    pw = "1234567890"
    holder.user_register(RegisterRequest(username=u, password=pw, confirm=pw))
    holder.user_logout()

    holder.user_login(LoginRequest(username=u, password=pw))


def test_login_wrong_password(holder: WebHolder):
    u = "asdf"
    pw = "1234567890"
    holder.user_register(RegisterRequest(username=u, password=pw, confirm=pw))
    holder.user_logout()

    with pytest.raises(HTTPException) as e:
        holder.user_login(LoginRequest(username=u, password="asdf"))

    assert e.value.status_code == 400
