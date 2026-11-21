
import json
import time
import urllib.request
import urllib.error

CATALOGUE_URL = "http://localhost:5001"
COMMANDES_URL = "http://localhost:5002"
NOTIFICATIONS_URL = "http://localhost:5003"


def request_api(url, method="GET", data=None):
    headers = {"Content-Type": "application/json"}

    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers=headers,
        method=method
    )

    with urllib.request.urlopen(req, timeout=5) as response:
        content = response.read().decode("utf-8")
        result = json.loads(content) if content else None
        return response.status, result


def wait_for_services():
    services = [
        CATALOGUE_URL + "/products",
        COMMANDES_URL + "/orders",
        NOTIFICATIONS_URL + "/notifications"
    ]

    print("Attente du démarrage des services...")

    for url in services:
        for attempt in range(30):
            try:
                request_api(url)
                print(f"Service disponible : {url}")
                break
            except Exception:
                if attempt == 29:
                    raise RuntimeError(
                        f"Service indisponible : {url}"
                    )
                time.sleep(2)


def test_catalogue():
    status, products = request_api(
        CATALOGUE_URL + "/products"
    )

    assert status == 200
    assert isinstance(products, list)

    print("TEST CATALOGUE : OK")


def test_commandes():
    status, orders = request_api(
        COMMANDES_URL + "/orders"
    )

    assert status == 200
    assert isinstance(orders, list)

    print("TEST COMMANDES : OK")


def test_notifications():
    status, notifications = request_api(
        NOTIFICATIONS_URL + "/notifications"
    )

    assert status == 200
    assert isinstance(notifications, list)

    print("TEST NOTIFICATIONS : OK")


def test_add_notification():
    data = {
        "order_id": 999,
        "message": "Test automatique GitHub Actions"
    }

    status, result = request_api(
        NOTIFICATIONS_URL + "/notify",
        method="POST",
        data=data
    )

    assert status == 201
    assert "notification" in result

    print("TEST AJOUT NOTIFICATION : OK")


if __name__ == "__main__":
    wait_for_services()

    test_catalogue()
    test_commandes()
    test_notifications()
    test_add_notification()

    print("\nTOUS LES TESTS SONT REUSSIS !")
