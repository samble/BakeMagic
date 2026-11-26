from itertools import count

from fastapi.testclient import TestClient

from tests.test_api import make_customer, make_product

_codes = count(1)


def make_standing_order(client: TestClient, **overrides) -> dict:
    """Create a standing order for a new customer and product (both unique per call)."""
    body = {
        "customer_id": make_customer(client, email="")["id"],
        "days": ["mon", "fri"],
        "lines": [{"product_id": make_product(client, code=f"SO-{next(_codes)}")["id"], "quantity": 2}],
    } | overrides
    resp = client.post("/standing-orders", json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_create_and_read(client: TestClient):
    created = make_standing_order(client, days=["fri", "mon", "fri"], notes="Back door")
    assert created["days"] == ["mon", "fri"]  # de-duplicated, Sunday-first order
    assert created["notes"] == "Back door"
    assert created["is_active"] is True
    assert [line["quantity"] for line in created["lines"]] == [2]

    assert client.get(f"/standing-orders/{created['id']}").json() == created


def test_create_validation(client: TestClient):
    customer = make_customer(client)
    product = make_product(client)
    line = [{"product_id": product["id"], "quantity": 1}]

    def post(**body):
        return client.post(
            "/standing-orders", json={"customer_id": customer["id"], "days": ["mon"], "lines": line} | body
        )

    assert post(days=[]).status_code == 422
    assert post(days=["funday"]).status_code == 422
    assert post(lines=[]).status_code == 422
    assert post(lines=[{"product_id": product["id"], "quantity": 0}]).status_code == 422
    assert post(customer_id=999).json()["detail"] == "Customer does not exist"
    assert post(lines=[{"product_id": 999, "quantity": 1}]).json()["detail"] == "Unknown product ids: [999]"

    client.patch(f"/products/{product['id']}", json={"is_active": False})
    assert post().json()["detail"] == f"Inactive product ids: [{product['id']}]"


def test_list_filters(client: TestClient):
    mon = make_standing_order(client, days=["mon"])
    sat = make_standing_order(client, days=["sat"], is_active=False)

    def ids(query=""):
        return [s["id"] for s in client.get(f"/standing-orders{query}").json()]

    assert ids() == [mon["id"], sat["id"]]
    assert ids("?day=mon") == [mon["id"]]
    assert ids("?day=sat&active_only=true") == []
    assert ids(f"?customer_id={sat['customer_id']}") == [sat["id"]]
    assert client.get("/standing-orders?day=funday").status_code == 422


def test_update(client: TestClient):
    standing = make_standing_order(client)
    url = f"/standing-orders/{standing['id']}"
    bread = make_product(client, code="BREAD")

    resp = client.patch(url, json={"days": ["sun", "wed"], "is_active": False})
    assert resp.json()["days"] == ["sun", "wed"]
    assert resp.json()["is_active"] is False
    assert resp.json()["lines"] == standing["lines"]  # untouched

    resp = client.patch(url, json={"lines": [{"product_id": bread["id"], "quantity": 5}]})
    assert [(line["product_id"], line["quantity"]) for line in resp.json()["lines"]] == [(bread["id"], 5)]

    assert client.patch(url, json={"days": []}).status_code == 422
    assert client.patch(url, json={"lines": []}).status_code == 422
    assert client.patch(url, json={"days": None}).status_code == 422
    assert client.patch("/standing-orders/999", json={"is_active": True}).status_code == 404


def test_delete(client: TestClient):
    standing = make_standing_order(client)
    product_id = standing["lines"][0]["product_id"]

    # A product on a standing order can't be deleted.
    assert client.delete(f"/products/{product_id}").status_code == 409

    assert client.delete(f"/standing-orders/{standing['id']}").status_code == 204
    assert client.get(f"/standing-orders/{standing['id']}").status_code == 404
    assert client.delete(f"/products/{product_id}").status_code == 204
