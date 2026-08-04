import pytest
from fastapi.testclient import TestClient

from main import _store, app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_store():
    _store.clear()
    yield
    _store.clear()


def test_add_preference():
    resp = client.post(
        "/preferences",
        json={
            "customer_id": "cust-1",
            "marketing_opt_in": True,
            "comm_channel": "sms",
            "zip_code": 2118,
            "display_name": "Alex",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["zip_code"] == "02118"
    assert body["comm_channel"] == "sms"


def test_add_duplicate_is_conflict():
    client.post("/preferences", json={"customer_id": "cust-2"})
    resp = client.post("/preferences", json={"customer_id": "cust-2"})
    assert resp.status_code == 409


def test_add_uses_defaults_for_missing_fields():
    resp = client.post("/preferences", json={"customer_id": "cust-3"})
    assert resp.status_code == 201
    body = resp.json()
    assert body == {
        "customer_id": "cust-3",
        "marketing_opt_in": False,
        "comm_channel": "email",
        "zip_code": None,
        "display_name": "",
    }


def test_update_preference_partial():
    client.post("/preferences", json={"customer_id": "cust-4", "display_name": "Old"})
    resp = client.put("/preferences/cust-4", json={"display_name": "New"})
    assert resp.status_code == 200
    assert resp.json()["display_name"] == "New"
    # Untouched field survives the partial update.
    assert resp.json()["comm_channel"] == "email"


def test_update_missing_customer_is_404():
    resp = client.put("/preferences/does-not-exist", json={"display_name": "x"})
    assert resp.status_code == 404


def test_delete_preference():
    client.post("/preferences", json={"customer_id": "cust-5"})
    resp = client.delete("/preferences/cust-5")
    assert resp.status_code == 204
    assert client.get("/preferences", params={"customer_id": "cust-5"}).json() == []


def test_delete_missing_customer_is_404():
    resp = client.delete("/preferences/nope")
    assert resp.status_code == 404


def test_search_by_comm_channel():
    client.post("/preferences", json={"customer_id": "a", "comm_channel": "push"})
    client.post("/preferences", json={"customer_id": "b", "comm_channel": "email"})
    resp = client.get("/preferences", params={"comm_channel": "push"})
    assert [r["customer_id"] for r in resp.json()] == ["a"]


def test_search_by_display_name_substring():
    client.post("/preferences", json={"customer_id": "a", "display_name": "Alexandra"})
    client.post("/preferences", json={"customer_id": "b", "display_name": "Bob"})
    resp = client.get("/preferences", params={"display_name_contains": "alex"})
    assert [r["customer_id"] for r in resp.json()] == ["a"]


def test_unknown_comm_channel_is_422_not_500():
    resp = client.post(
        "/preferences", json={"customer_id": "c", "comm_channel": "carrier_pigeon"}
    )
    assert resp.status_code == 422


def test_invalid_zip_is_422_not_500():
    resp = client.post("/preferences", json={"customer_id": "d", "zip_code": "abc"})
    assert resp.status_code == 422


def test_oversized_display_name_is_422_not_500():
    resp = client.post(
        "/preferences", json={"customer_id": "e", "display_name": "x" * 10000}
    )
    assert resp.status_code == 422
