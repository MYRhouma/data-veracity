from pathlib import Path

from fastapi.testclient import TestClient

from dva_acapy_controller.config import ADMIN_LABEL
from dva_acapy_controller.controller import app
from dva_acapy_controller.controller import presentation_queue
from dva_acapy_controller.controller import webhook_logs


client = TestClient(app)


def test_get_root():
    resp = client.get("/")

    assert resp.status_code == 200
    assert resp.headers["Content-Type"].startswith("text/html")
    assert resp.content == Path("static/index.html").read_bytes()


def test_post_webhook():
    topic = "testtopic"
    data = {
        "foo": "bar",
        "baz": [1, 2, 3],
    }
    data_with_source = {**data, "source": ADMIN_LABEL}

    resp = client.post(f"/webhooks/topic/{topic}", json=data)

    assert resp.status_code == 200
    assert resp.headers["Content-Type"] == "application/json"
    assert resp.json() == {"status": "received"}
    assert webhook_logs[-1] == {
        "topic": topic,
        "data": data_with_source,
    }
    assert presentation_queue.get_nowait() == data_with_source


# Further tests would need refactoring and the ACA-Py agent
