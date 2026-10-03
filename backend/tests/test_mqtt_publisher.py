from app.mqtt.publisher import MQTTPublisher


class FakeResult:
    def wait_for_publish(self, timeout=None):
        pass


class FakePahoClient:
    def __init__(self):
        self.sent = []

    def publish(self, topic, message):
        self.sent.append((topic, message))
        return FakeResult()


class FakeMQTTClient:
    def __init__(self):
        self.client = FakePahoClient()


def test_publish_string_is_sent_raw():
    fake = FakeMQTTClient()

    MQTTPublisher(fake).publish("home/a/b/command", "on")

    assert fake.client.sent == [("home/a/b/command", "on")]


def test_publish_dict_is_sent_as_json():
    fake = FakeMQTTClient()

    MQTTPublisher(fake).publish("home/a/b/state", {"state": "on"})

    assert fake.client.sent == [("home/a/b/state", '{"state": "on"}')]
