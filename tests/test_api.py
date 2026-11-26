import asyncio
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.errors import integrity_error_handler
from app.models import INT32_MAX, Customer, Order, OrderLine, Product


def make_product(client: TestClient, code="CAKE-01", price="24.50", **extra) -> dict:
    resp = client.post(
        "/products", json={"code": code, "name": f"Product {code}", "price": price, **extra}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def make_customer(client: TestClient, email="ada@example.com") -> dict:
    resp = client.post(
        "/customers", json={"first_name": "Ada", "last_name": "Baker", "email": email}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_health(client: TestClient):
    assert client.get("/health").json() == {"status": "ok"}


def test_product_crud(client: TestClient):
    product = make_product(client)
    assert product["price"] == "24.50"

    resp = client.patch(f"/products/{product['id']}", json={"price": "26.00"})
    assert resp.json()["price"] == "26.00"
    assert resp.json()["name"] == product["name"]  # untouched fields are kept

    assert [p["code"] for p in client.get("/products").json()] == ["CAKE-01"]
    assert client.delete(f"/products/{product['id']}").status_code == 204
    assert client.get(f"/products/{product['id']}").status_code == 404


def test_product_validation_and_duplicates(client: TestClient):
    assert client.post("/products", json={"code": "X", "name": "X", "price": "-1"}).status_code == 422
    make_product(client, code="DUP")
    assert client.post("/products", json={"code": "DUP", "name": "Again", "price": "1"}).status_code == 409


def test_customer_rejects_bad_and_duplicate_email(client: TestClient):
    bad = client.post("/customers", json={"first_name": "A", "last_name": "B", "email": "nope"})
    assert bad.status_code == 422
    make_customer(client)
    dup = client.post(
        "/customers", json={"first_name": "C", "last_name": "D", "email": "ada@example.com"}
    )
    assert dup.status_code == 409


def test_order_totals_use_price_at_order_time(client: TestClient):
    customer = make_customer(client)
    cake = make_product(client, code="CAKE", price="20.00")
    bread = make_product(client, code="BREAD", price="4.25")

    resp = client.post(
        "/orders",
        json={
            "customer_id": customer["id"],
            "lines": [
                {"product_id": cake["id"], "quantity": 2},
                {"product_id": bread["id"], "quantity": 3},
            ],
        },
    )
    assert resp.status_code == 201, resp.text
    order = resp.json()
    assert order["status"] == "created"
    assert order["total"] == "52.75"

    # Repricing a product must not change existing orders.
    client.patch(f"/products/{cake['id']}", json={"price": "99.00"})
    assert client.get(f"/orders/{order['id']}").json()["total"] == "52.75"

    # A product that is on an order can't be deleted.
    assert client.delete(f"/products/{cake['id']}").status_code == 409


def test_order_rejects_unknown_or_inactive_products(client: TestClient):
    customer = make_customer(client)
    retired = make_product(client, code="OLD", is_active=False)

    unknown = client.post(
        "/orders", json={"customer_id": customer["id"], "lines": [{"product_id": 999, "quantity": 1}]}
    )
    assert unknown.status_code == 422

    inactive = client.post(
        "/orders",
        json={"customer_id": customer["id"], "lines": [{"product_id": retired["id"], "quantity": 1}]},
    )
    assert inactive.status_code == 422

    no_customer = client.post("/orders", json={"customer_id": 999, "lines": [{"product_id": 1, "quantity": 1}]})
    assert no_customer.status_code == 422


def test_order_status_flow(client: TestClient):
    customer = make_customer(client)
    product = make_product(client)
    order = client.post(
        "/orders", json={"customer_id": customer["id"], "lines": [{"product_id": product["id"], "quantity": 1}]}
    ).json()

    resp = client.patch(f"/orders/{order['id']}/status", json={"status": "completed"})
    assert resp.json()["status"] == "completed"
    assert client.get("/orders", params={"status": "completed"}).json()[0]["id"] == order["id"]

    # Finished orders are locked.
    again = client.patch(f"/orders/{order['id']}/status", json={"status": "paid"})
    assert again.status_code == 409


def test_patch_rejects_null_but_allows_omitting_fields(client: TestClient):
    product = make_product(client, description="Chocolate")
    customer = make_customer(client)

    for field in ("name", "description", "price", "is_active"):
        resp = client.patch(f"/products/{product['id']}", json={field: None})
        assert resp.status_code == 422, field
    for field in ("first_name", "last_name", "email", "phone", "address"):
        resp = client.patch(f"/customers/{customer['id']}", json={field: None})
        assert resp.status_code == 422, field

    resp = client.patch(f"/products/{product['id']}", json={"name": "Renamed"})
    assert resp.status_code == 200
    assert resp.json()["description"] == "Chocolate"  # omitted fields are untouched


def test_customer_email_may_be_blank(client: TestClient):
    def create(**email):
        return client.post("/customers", json={"first_name": "A", "last_name": "B", **email})

    # Omitted or "" both mean no email, and several customers can have none.
    assert create().json()["email"] == ""
    assert create(email="").status_code == 201

    # Non-empty values must still be valid and unique.
    assert create(email="not-an-email").status_code == 422
    with_email = create(email="ada@example.com").json()
    assert create(email="ada@example.com").status_code == 409

    # PATCH can clear an email or set a valid one, but not set an invalid one.
    url = f"/customers/{with_email['id']}"
    assert client.patch(url, json={"email": "nope"}).status_code == 422
    assert client.patch(url, json={"email": ""}).json()["email"] == ""
    assert client.patch(url, json={"email": "ada@example.com"}).json()["email"] == "ada@example.com"


def test_ids_above_postgres_int_max_are_rejected(client: TestClient):
    customer = make_customer(client)
    product = make_product(client)
    too_big = INT32_MAX + 1

    def order(customer_id, product_id):
        return client.post(
            "/orders",
            json={"customer_id": customer_id, "lines": [{"product_id": product_id, "quantity": 1}]},
        )

    assert order(too_big, product["id"]).status_code == 422
    assert order(customer["id"], too_big).status_code == 422
    for path in ("/products", "/customers", "/orders"):
        assert client.get(f"{path}/{too_big}").status_code == 422, path
        assert client.get(f"{path}/{INT32_MAX}").status_code == 404, path
    assert client.get(f"/orders?customer_id={too_big}").status_code == 422


def violate(session: Session, row) -> IntegrityError:
    session.add(row)
    with pytest.raises(IntegrityError) as info:
        session.commit()
    session.rollback()
    return info.value


def handle(exc: IntegrityError):
    return asyncio.run(integrity_error_handler(None, exc))


def test_check_constraints_return_422_with_message(session: Session):
    # Write straight to the database, bypassing the API's own validation.
    product = Product(code="P", name="P", price=Decimal("-0.01"))
    resp = handle(violate(session, product))
    assert resp.status_code == 422
    assert resp.body == b'{"detail":"Price must be zero or greater"}'

    customer = Customer(first_name="A", last_name="B")
    session.add_all([customer, Product(code="FREE", name="Free", price=Decimal("0"))])
    session.commit()

    def line(**overrides):
        fields = {"product_id": 1, "quantity": 1, "unit_price": Decimal("1")} | overrides
        return Order(customer_id=customer.id, lines=[OrderLine(**fields)])

    resp = handle(violate(session, line(quantity=0)))
    assert resp.status_code == 422
    assert resp.body == b'{"detail":"Quantity must be greater than zero"}'

    resp = handle(violate(session, line(unit_price=Decimal("-1"))))
    assert resp.body == b'{"detail":"Unit price must be zero or greater"}'

    # Zero prices are allowed.
    session.add(line(unit_price=Decimal("0")))
    session.commit()


def test_other_integrity_errors_are_not_turned_into_422(session: Session):
    session.add(Product(code="DUP", name="A", price=Decimal("1")))
    session.commit()
    exc = violate(session, Product(code="DUP", name="B", price=Decimal("1")))
    with pytest.raises(IntegrityError):
        handle(exc)


def test_free_product_is_allowed(client: TestClient):
    assert make_product(client, code="FREE", price="0")["price"] == "0.00"


def test_customer_phone_and_address_may_be_blank(client: TestClient):
    created = client.post("/customers", json={"first_name": "A", "last_name": "B"}).json()
    assert created["phone"] == "" and created["address"] == ""

    url = f"/customers/{created['id']}"
    filled = client.patch(url, json={"phone": "555-0100", "address": "1 Bun Lane"}).json()
    assert filled["phone"] == "555-0100" and filled["address"] == "1 Bun Lane"

    cleared = client.patch(url, json={"phone": "", "address": ""})
    assert cleared.status_code == 200
    assert cleared.json()["phone"] == "" and cleared.json()["address"] == ""
