import pytest
from fastapi import HTTPException

# from fastapi import HTTPException
from pytest_httpx import HTTPXMock

from vclib.common.src.data_transfer_objects.vp_auth_request import (
    AuthorizationRequestObject,
)
from vclib.holder.src.models.credentials import Credential
from vclib.holder.src.models.field_selection_object import (
    FieldRequest,
    FieldSelectionObject,
)
from vclib.holder.src.storage.local_storage_provider import LocalStorageProvider
from vclib.holder.src.web_holder import WebHolder

# from vclib.holder.src.models.credentials import Credential
# from vclib.holder.src.models.field_selection_object import FieldSelectionObject
# from vclib.holder.src.storage.local_storage_provider import LocalStorageProvider

EXAMPLE_ISSUER = "https://example.com"
OWNER_HOST = "https://localhost"
OWNER_PORT = "8080"
OWNER_URI = f"{OWNER_HOST}:{OWNER_PORT}"

drivers_license_credential = {
    "id": "drivers_license",
    "issuer_url": "https://servicensw.com.au",
    "issuer_name": "Service NSW",
    "credential_configuration_id": "drivers_license",
    "is_deferred": False,
    "c_type": "openid_credential",
    "raw_sdjwtvc": "eyJhbGciOiAiRVMyNTYiLCAidHlwIjogImV4YW1wbGUrc2Qtand0In0.eyJfc2QiOiBbIjZTS2FTQjBkc1VxRV9nX1VwM1BOWHA1dFhEblBMbzNZY19DM200RjQxTUUiLCAiNm5NZkc2a0VLVUxObWx2N3hMZEpWQW1EYW5GTm1MSDZ3MDd0MV9qWGcwTSIsICJBMzE4U1VGT09ybGpwUGxzOS1HMENOTlNZdXNsSHJTNkV0azdFQVRXUHRjIiwgIkJCLURxRFZ5dmNuRUExZDNnamt5RmlDMVVoTVYtbWd3bTVtNzUyWnRTWTgiLCAiQ3BpSGVhZGJKeTkzMDh1YW9QZHJNWW1MVmlXTUtzMGJIZzlGVU9UaUlhQSIsICJDcUMwRE0wMzJKZVhCdnlMQzlTSjNDVkJ4YVN3enJVRXdnYW9XYnlhYlQ4IiwgIk5ZQURxdzh5VWJ4SW9QQk5vS1ZlMGY3TXlOSjM0VHNlNTNTbTdIT0dyZ3ciLCAiUWlMUUxQMzlsN0hlanNyXzU0SlNBYUt4TGFGbHZyT0pjS1V5MW15QW1JdyIsICJfUWtYNldTWjBJUGRBR2UxYng5Uk9RT0FidDlnVWhDR1FPWUFMeWpWd3R3IiwgImhQdV93RGtFNFFndXMwN3l1MmQ1LVZoMTZuUWNsV3UySDEtLWYxV2hpaGMiLCAic2ZVYTFFbmhXTmllbXRWMjRuUDB4QXFMVFF3S21zcUo3T0Z3eHdHRTBVYyJdLCAiaWF0IjogMTcwMDAwMDAwMCwgImlzcyI6ICJzZXJ2aWNlbnN3LmNvbS5hdSIsICJ2Y3QiOiAic2VydmljZW5zdy5jb20uYXUvZHJpdmVyc19saWNlbnNlIiwgIl9zZF9hbGciOiAic2hhLTI1NiJ9.gqwETLGU8-hV_vVN0vbIT8FRFAYqn-0La6Pub5KL1mslDCYsZuenXoOvV493qVd-HMbJAsLyW6tpKaBi1kZk_A~WyJNMm1teWNRbThxdmpjSzdEVk9GeTl3IiwgImdpdmVuX25hbWUiLCAiSm9obiJd~WyI1ZnFlUEdSdVFBM3JLb1hmdFotOFNnIiwgIm1pZGRsZV9uYW1lIiwgIk1vcmdhbiJd~WyJ1T19tWnVVY3FQUURibGRMcjUyN0pnIiwgImZhbWlseV9uYW1lIiwgIkRvZSJd~WyJYMkNkT1VUX1NsU3UyR21WQS1CWDN3IiwgImFkZHJlc3MiLCAiMTMgQmFrZXIgU3RyZWV0LCBTeWRuZXksIE5TVyJd~WyI3NGEtb1FMU25wSXBfRmwtak5tRVRRIiwgImxpY2Vuc2VfbnVtYmVyIiwgMTIzNDU2Nzhd~WyJ1Wkc3Z3Z6UWpnM2lRY0dkZlItWDFBIiwgImxpY2Vuc2VfY2xhc3MiLCAiQyBQMSJd~WyJfbWlYdUVtSnRvRW5rLUctTEZtSkhRIiwgImNhcmRfbnVtYmVyIiwgMTIzNDU2Nzg5MF0~WyJmeTRBRlZ1TTBMVi1jNjNWQ21PQ0FRIiwgImRhdGVfb2ZfYmlydGgiLCAiMjAwMC0wMS0wMSJd~WyJpWFFDSkhWbWp6UWR5QVhCZGplWVdnIiwgImlzX292ZXJfMTgiLCB0cnVlXQ~WyJOZkNxNURNNUZRS0trZ2dfV2VTWWxnIiwgImlzX292ZXJfMjEiLCB0cnVlXQ~WyJ4azh1SHNEUzV5ZTN0dnY1SGxwMF9BIiwgImlzX292ZXJfNjUiLCBmYWxzZV0~",  # noqa: E501
    "received_at": "2024-07-15T02:54:13.634808+00:00",
}

@pytest.fixture
def holder(tmp_path_factory):
    return WebHolder(
        [f"{OWNER_URI}/add"],
        f"{OWNER_URI}/offer",
        LocalStorageProvider(storage_dir_path=tmp_path_factory.mktemp("test_storage"))
    )

@pytest.fixture
def auth_header(holder: WebHolder):
    holder.store.register("asdf", "1234567890")
    return f"Bearer {holder._generate_jwt({"username": "asdf"})}"

@pytest.fixture
def over_18_field_selection():
    return FieldSelectionObject(field_requests=[
            {
                "field": {
                    "path": ["$.credentialSubject.is_over_18", "$.is_over_18"],
                    "filter": {
                        "type": "boolean",
                        "const": True
                    }
                },
                "input_descriptor_id": "over_18_descriptor",
                "approved": True
            }
        ])

@pytest.fixture
def mock_data(tmp_path_factory):
    over_18_mock_auth_request = {
        "client_id": "some did",
        "client_id_scheme": "did",
        "client_metadata": {"data": "metadata in this object"},
        "presentation_definition": {
            "id": "verify_over_18",
            "input_descriptors": [
                {
                    "id": "over_18_descriptor",
                    "constraints": {
                        "fields": [
                            {
                                "path": [
                                    "$.credentialSubject.is_over_18",
                                    "$.is_over_18"
                                ],
                                "filter": {
                                    "type": "boolean",
                                    "const": True
                                },
                            }
                        ]
                    },
                    "name": "Over 18 Verification",
                    "purpose": "To verify that the individual is over 18 years old",
                }
            ],
        },
        "response_uri": "https://example.com/cb",
        "response_type": "vp_token",
        "response_mode": "direct_post",
        "nonce": "unique nonce",
        "wallet_nonce": None,
        "state": "d1d9846b-0f0e-4716-8178-88a6e76f1673_1721045932",
    }

    holder = WebHolder(
        [f"{OWNER_URI}/add"],
        f"{OWNER_URI}/offer",
        LocalStorageProvider(storage_dir_path=tmp_path_factory.mktemp("test_storage"))
    )

    store: LocalStorageProvider = holder.store
    store.register("asdf", "1234567890")
    user = store.get_active_user_name()
    auth_header = f"Bearer {holder._generate_jwt({"username": user})}"

    return (over_18_mock_auth_request, holder, auth_header)

@pytest.fixture
def mock_data_with_cred(mock_data) -> tuple[dict, WebHolder, str]:
    req, holder, auth_header = mock_data

    store = holder.store
    store._purge_db()
    store.add_credential(Credential(**drivers_license_credential))

    return req, holder, auth_header

@pytest.fixture
def mock_data_with_2_creds(mock_data_with_cred, over_18_field_selection):
    auth_req, holder, auth_header = mock_data_with_cred
    holder.store.add_credential(Credential(
        id="other_cred",
        issuer_url="example2.com",
        credential_configuration_id="some_credential",
        is_deferred=False,
        c_type="vc+sd_jwt",
        raw_sdjwtvc="eyJhbGciOiAiRVMyNTYiLCAidHlwIjogImV4YW1wbGUrc2Qtand0In0.eyJfc2QiOiBbIkRFNVFtTW9qRi1JV0ZVWFJFdm91OGd0ZlRFbUVQdGsyaDlVLTFTZ0lWSW8iXSwgImlhdCI6IDE3MDAwMDAwMDAsICJpc3MiOiAiZXhhbXBsZS5jb20iLCAidmN0IjogImV4YW1wbGUuY29tIiwgIl9zZF9hbGciOiAic2hhLTI1NiJ9.J3-Mrt9YkKFpCk2o_DV6QGkBrJa4akBgkJZqiG4MvgjLM8hP5MUpVTKaKUbibv7sAZWPPdoNPMr_xETy7Zxpiw~WyJXQ25DbEJFelVQbnJyYzB5Rzczcm1BIiwgInByb3BlcnR5IiwgInZhbHVlIl0~",
        received_at="2024-07-15T02:54:13.634808+00:00"))

    auth_req['presentation_definition']['input_descriptors'].append({
        "id": "field",
        "constraints": {
            "fields": [
                {
                    "path": ["$.property", "$.credentialSubject.property"],
                    "filter": {
                        "type": "string",
                        "const": "value"
                    }
                }
            ]
        }
    })

    over_18_field_selection.field_requests.append(FieldRequest(field={
            "path": ["$.property", "$.credentialSubject.property"],
            "filter": {
                "type": "string",
                "const": "value"
            }
        }, input_descriptor_id="field", approved=True))

    return auth_req, holder, auth_header, over_18_field_selection


### unit testing
@pytest.mark.asyncio()
async def test0_presentation_initiation(httpx_mock: HTTPXMock, mock_data):
    over_18_auth_req, holder, auth_header = mock_data
    httpx_mock.add_response(
        url="https://example.com/request/over_18",
        json=over_18_auth_req)
    response = await holder.get_auth_request(
        "https://example.com/request/over_18", auth_header)

    assert response == AuthorizationRequestObject(**over_18_auth_req)

@pytest.mark.asyncio()
async def test1_invalid_scope(httpx_mock: HTTPXMock, mock_data):
    # TODO: parse scope values in the wallet
    pass

@pytest.mark.asyncio()
async def test2_missing_pd(httpx_mock: HTTPXMock, mock_data):
    over_18_auth_req, holder, auth_header = mock_data

    over_18_auth_req.pop('presentation_definition')
    httpx_mock.add_response(
        url="https://example.com/request/over_18",
        json=over_18_auth_req)

    with pytest.raises(HTTPException):
        await holder.get_auth_request(
            "https://example.com/request/over_18", auth_header)

@pytest.mark.asyncio()
async def test3_more_than_one_pd_type(httpx_mock: HTTPXMock, mock_data):
    over_18_auth_req, holder, auth_header = mock_data

    over_18_auth_req["presentation_definition_uri"] = "https://example.com/presentationdefs/over_18"
    httpx_mock.add_response(
        url="https://example.com/request/over_18",
        json=over_18_auth_req)

    with pytest.raises(HTTPException):
        await holder.get_auth_request(
            "https://example.com/request/over_18", auth_header)

@pytest.mark.asyncio()
async def test4_malformed_pd(httpx_mock: HTTPXMock, mock_data):
    over_18_auth_req, holder, auth_header = mock_data

    # is missing presentation_definition id
    over_18_auth_req["presentation_definition"] = {'input_descriptors': []}
    httpx_mock.add_response(
        url="https://example.com/request/over_18",
        json=over_18_auth_req)

    with pytest.raises(HTTPException):
        await holder.get_auth_request(
            "https://example.com/request/over_18", auth_header)


@pytest.mark.asyncio()
async def test5_unsupported_id_scheme(httpx_mock: HTTPXMock, mock_data):
    # TODO: implement client_id_scheme checking and passing from wallet to verifier
    pass

@pytest.mark.asyncio()
async def test6_mismatching_id_scheme(httpx_mock: HTTPXMock, mock_data):
    # TODO: implement client_id_scheme checking and passing from wallet to verifier
    pass

@pytest.mark.asyncio()
async def test10_working_presentation(httpx_mock: HTTPXMock,
                                         mock_data_with_cred,
                                         over_18_field_selection):
    auth_req, holder, auth_header = mock_data_with_cred

    httpx_mock.add_response(
        url="https://example.com/request/over_18",
        json=auth_req)

    await holder.get_auth_request(
        "https://example.com/request/over_18", auth_header)


    httpx_mock.add_response(
        url="https://example.com/cb",
        json={"status": "OK"})

    assert holder.current_transaction == AuthorizationRequestObject(**auth_req)
    resp = await holder.present_selection(
        over_18_field_selection, auth_header)

    assert resp == 'success'

@pytest.mark.asyncio()
async def test11_wallet_lacks_credentials(httpx_mock: HTTPXMock,
                                         mock_data,
                                         over_18_field_selection):

    over_18_auth_req, holder, auth_header = mock_data
    field_selection = over_18_field_selection

    httpx_mock.add_response(
        url="https://example.com/request/over_18",
        json=over_18_auth_req)


    await holder.get_auth_request(
        "https://example.com/request/over_18", auth_header)

    with pytest.raises(HTTPException):
        resp = await holder.present_selection(field_selection, auth_header)
        assert resp.status_code == 403
        assert "access_denied" in resp.json()['detail']

@pytest.mark.asyncio()
async def test12_no_ongoing_presentation(mock_data, over_18_field_selection):
    _, holder, auth_header = mock_data
    with pytest.raises(HTTPException):

        await holder.present_selection(over_18_field_selection, auth_header)


@pytest.mark.asyncio()
async def test13_multiple_credential_presentation(
        httpx_mock: HTTPXMock,
        mock_data_with_2_creds):
    auth_req, holder, auth_header, selection = mock_data_with_2_creds

    httpx_mock.add_response(
        url="https://example.com/request/over_18",
        json=auth_req)

    await holder.get_auth_request(
        "https://example.com/request/over_18", auth_header)


    httpx_mock.add_response(
        url="https://example.com/cb",
        json={"status": "OK"})

    assert holder.current_transaction == AuthorizationRequestObject(**auth_req)
    resp = await holder.present_selection(
        selection, auth_header)

    assert resp == 'success'

@pytest.mark.asyncio()
async def test14_requested_multiple_fields_from_credential(
        httpx_mock: HTTPXMock,
        mock_data_with_cred,
        over_18_field_selection):
    auth_req, holder, auth_header = mock_data_with_cred
    input_descriptors = auth_req['presentation_definition']['input_descriptors']
    input_descriptors[0]['constraints']['fields'].append({
        "path": ["$.is_over_21",
                 "$.credentialSubject.is_over_21"],
        "filter": {
            "type": "boolean",
            "const": False
        }
    })

    input_descriptors[0]['constraints']['fields'].append({
        "path": ["$.given_name",
                 "$.credentialSubject.given_name"],
        "filter": {
            "type": "string"
        }
    })

    over_18_field_selection.field_requests.append(FieldRequest(field={
            "path": ["$.is_over_21",
                    "$.credentialSubject.is_over_21"],
            "filter": {
                "type": "boolean",
                "const": False
            }
        }, input_descriptor_id="field", approved=True))

    over_18_field_selection.field_requests.append(FieldRequest(field={
            "path": ["$.given_name",
                    "$.credentialSubject.given_name"],
            "filter": {
                "type": "string"
            }
        }, input_descriptor_id="field", approved=True))

    httpx_mock.add_response(
        url="https://example.com/request/over_18",
        json=auth_req)

    await holder.get_auth_request(
        "https://example.com/request/over_18", auth_header)


    httpx_mock.add_response(
        url="https://example.com/cb",
        json={"status": "OK"})

    assert holder.current_transaction == AuthorizationRequestObject(**auth_req)
    resp = await holder.present_selection(
        over_18_field_selection, auth_header)

    assert resp == 'success'

@pytest.mark.asyncio()
async def test15_user_rejected_presentation_request(
        httpx_mock: HTTPXMock,
        mock_data_with_2_creds):
    auth_req, holder, auth_header, _ = mock_data_with_2_creds

    httpx_mock.add_response(
        url="https://example.com/request/over_18",
        json=auth_req)

    await holder.get_auth_request(
        "https://example.com/request/over_18", auth_header)

    assert holder.current_transaction == AuthorizationRequestObject(**auth_req)

    with pytest.raises(HTTPException):
        resp = await holder.present_selection(
            FieldSelectionObject(field_requests=[]), auth_header)
        assert "access_denied" in resp.json()["detail"]

@pytest.mark.asyncio()
async def test16_request_property_in_payload(
        httpx_mock: HTTPXMock, mock_data_with_2_creds):
    _, holder, auth_header, _ = mock_data_with_2_creds
    auth_req = {
        "client_id": "some did",
        "client_id_scheme": "did",
        "client_metadata": {"data": "metadata in this object"},
        "presentation_definition": {
            "id": "request_property_in_payload",
            "input_descriptors": [
                {
                    "id": "payload_property",
                    "constraints": {
                        "fields": [
                            {
                                "path": [
                                    "$.credentialSubject.iss",
                                    "$.iss"
                                ],
                                "filter": {
                                    "type": "string",
                                    "const": "servicensw.com.au"
                                },
                            }
                        ]
                    }
                }
            ],
        },
        "response_uri": "https://example.com/cb",
        "response_type": "vp_token",
        "response_mode": "direct_post",
        "nonce": "unique nonce",
        "wallet_nonce": None,
        "state": "d1d9846b-0f0e-4716-8178-88a6e76f1673_1721045932",
    }

    selection = FieldSelectionObject(field_requests=[
            {
                "approved": True,
                "input_descriptor_id": "request_property_in_payload",
                "field": {
                    "path": [
                        "$.credentialSubject.iss",
                        "$.iss"
                    ],
                    "filter": {
                        "type": "string",
                        "const": "servicensw.com.au"
                    },
                }
            }
        ])

    httpx_mock.add_response(
        url="https://example.com/request/payload_property",
        json=auth_req
    )

    await holder.get_auth_request(
        "https://example.com/request/payload_property", auth_header)

    httpx_mock.add_response(
        url="https://example.com/cb", json={"status": "OK"})

    resp = await holder.present_selection(selection, auth_header)
    assert resp == "success"
