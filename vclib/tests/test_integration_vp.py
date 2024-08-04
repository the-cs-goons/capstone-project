import os
import time

import httpx
import pytest
import uvicorn
from fastapi.testclient import TestClient
from multiprocess import Process

from vclib.common.src.data_transfer_objects.vp_auth_request import Field
from vclib.holder.examples.demo_agent import credential_holder
from vclib.holder.src.models.field_selection_object import FieldSelectionObject, FieldRequest
from vclib.verifier.examples.bar_demo_agent import verifier as bar_verifier
from vclib.verifier.examples.car_rental_demo_agent import (
    verifier as car_rental_verifier,
)

clients = {
    "holder": {
        "app": TestClient(credential_holder.get_server()).app,
        "port": int(os.getenv("CS3900_HOLDER_AGENT_PORT")),
    },
    "bar_verifier": {
        "app": TestClient(bar_verifier.get_server()).app,
        "port": int(os.getenv("CS3900_BAR_VERIFIER_DEMO_AGENT_PORT")),
    },
    "car_rental_verifier": {
        "app": TestClient(car_rental_verifier.get_server()).app,
        "port": int(os.getenv("CS3900_CAR_RENTAL_VERIFIER_DEMO_AGENT_PORT")),
    },
}

bar_verifier.base_url = f"http://localhost:{clients['bar_verifier']['port']}"
car_rental_verifier.base_url = f"http://localhost:{clients['car_rental_verifier']['port']}"


@pytest.fixture(scope="session", autouse=True)
def setup():
    procs = []
    for client in clients.values():
        proc = Process(
            target=uvicorn.run,
            args=(client["app"],),
            kwargs={"host": "0.0.0.0", "port": client["port"]},
            daemon=True,
        )
        proc.start()
        procs.append(proc)
    time.sleep(1)
    yield
    for proc in procs:
        proc.terminate()


def get(
    client_name: str, path: str, *args, token: str | None = None, headers: dict | None = None, **kwargs
) -> httpx.Response:
    if token is not None:
        if headers is None:
            headers = {}
        headers["Authorization"] = f"Bearer {token}"
    return httpx.get(
        f"http://localhost:{clients[client_name]['port']}{path}", *args, headers=headers, **kwargs
    )


def post(
    client_name: str, path: str, *args, token: str | None = None, headers: dict | None = None, **kwargs
) -> httpx.Response:
    if token is not None:
        if headers is None:
            headers = {}
        headers["Authorization"] = f"Bearer {token}"
    return httpx.post(
        f"http://localhost:{clients[client_name]['port']}{path}", *args, headers=headers, **kwargs
    )


@pytest.fixture
def token() -> str:
    # login to get bearer token
    res = post(
        "holder",
        "/login",
        json={
            "username": "asdf",
            "password": "1234567890",
        },
    )
    res.raise_for_status()
    token = res.json()["access_token"]

    # check mock credential is there to verify token is working
    res = get("holder", "/credentials", token=token)
    res.raise_for_status()
    assert len(res.json()) == 1
    assert res.json()[0]["id"] == "mock_photocard"

    return token


def test_bar_presentation_flow(token):
    # initiate presentation flow
    res = get(
        "holder",
        "/presentation/init",
        token=token,
        params={
            "request_uri": f"http://localhost:{clients['bar_verifier']['port']}/request/verify_over_18"
        },
    )
    res.raise_for_status()
    assert res.json()["presentation_definition"]["id"] == "verify_over_18"

    # make presentation
    res = post(
        "holder",
        "/presentation/",
        token=token,
        json=FieldSelectionObject(field_requests=[
            FieldRequest(
                field=Field(
                    path=["$.credentialSubject.is_over_18", "$.is_over_18"],
                    filter={"type": "boolean", "const": True},
                    optional=False,
                ),
                input_descriptor_id="over_18_descriptor",
                approved=True
            ),
            FieldRequest(
                field=Field(
                    path=["$.credentialSubject.birthdate", "$.birthdate"],
                    filter={"type": "number"},
                    optional=True,
                ),
                input_descriptor_id="dob_descriptor",
                approved=True
            )
        ]).model_dump(),
    )
    res.raise_for_status()

# def test_car_rental_presentation_flow(token):
#     # initiate presentation flow
#     res = get(
#         "holder",
#         "/presentation/init",
#         token=token,
#         params={
#             "request_uri": f"http://localhost:{clients['car_rental_verifier']['port']}/request/rental_eligibility"
#         },
#     )
#     res.raise_for_status()
#     assert res.json()["presentation_definition"]["id"] == "rental_eligibility"

#     # make presentation
#     res = post(
#         "holder",
#         "/presentation/",
#         token=token,
#         json=FieldSelectionObject(field_requests=[
#             FieldRequest(
#                 field=Field(
#                     path=["$.credentialSubject.is_over_18", "$.is_over_18"],
#                     filter={"type": "boolean", "const": True},
#                     optional=False,
#                 ),
#                 input_descriptor_id="over_18_descriptor",
#                 approved=True
#             ),
#             FieldRequest(
#                 field=Field(
#                     path=["$.credentialSubject.birthdate", "$.birthdate"],
#                     filter={"type": "number"},
#                     optional=True,
#                 ),
#                 input_descriptor_id="dob_descriptor",
#                 approved=True
#             )
#         ]).model_dump(),
#     )
#     res.raise_for_status()
