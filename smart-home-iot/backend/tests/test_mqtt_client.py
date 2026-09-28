from types import SimpleNamespace

from app.mqtt.client import MQTTClient


class FakePaho:
    def __init__(self):
        self.subscribed = []

    def subscribe(self, topic):
        self.subscribed.append(topic)


def message(topic, payload: bytes):
    return SimpleNamespace(topic=topic, payload=payload)


def test_subscriptions_are_redone_on_every_connect():
    client = MQTTClient()
    client.add_subscription("home/+/+/state")
    client.add_subscription("home/+/+/state")  # duplicate is ignored

    fake = FakePaho()

    client._on_connect(fake, None, None, 0, None)
    client._on_connect(fake, None, None, 0, None)  # reconnect

    assert fake.subscribed == ["home/+/+/state", "home/+/+/state"]


def test_no_subscribe_when_connection_fails():
    client = MQTTClient()
    client.add_subscription("home/+/+/state")

    fake = FakePaho()

    client._on_connect(fake, None, None, 5, None)

    assert fake.subscribed == []


def test_message_dispatch_parses_json_or_text():
    client = MQTTClient()
    received = []
    client.message_handler = lambda topic, payload: received.append(
        (topic, payload)
    )

    client._on_message(None, None, message("t/1", b"on"))
    client._on_message(None, None, message("t/2", b'{"value": 25.5}'))

    assert received == [("t/1", "on"), ("t/2", {"value": 25.5})]


def test_handler_error_does_not_propagate():
    client = MQTTClient()

    def boom(topic, payload):
        raise RuntimeError("boom")

    client.message_handler = boom

    client._on_message(None, None, message("t/1", b"on"))


def test_connect_falls_back_to_async_when_broker_is_down():
    client = MQTTClient()
    calls = []

    def refuse(*args):
        calls.append("connect")
        raise ConnectionRefusedError("refused")

    client.client.connect = refuse
    client.client.connect_async = lambda *args: calls.append("connect_async")

    client.connect()

    assert calls == ["connect", "connect_async"]
