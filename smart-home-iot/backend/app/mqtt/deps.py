from app.mqtt.publisher import MQTTPublisher

_publisher: MQTTPublisher | None = None


def set_publisher(publisher: MQTTPublisher | None) -> None:
    global _publisher
    _publisher = publisher


def get_publisher() -> MQTTPublisher | None:
    # Does not raise: the route checks the connection after validating
    # the request, so bad input still gets 422 / 404 instead of 503.
    return _publisher
