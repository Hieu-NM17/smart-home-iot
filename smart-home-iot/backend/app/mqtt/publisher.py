import json

from app.mqtt.client import MQTTClient


class MQTTPublisher:
    def __init__(self, mqtt_client: MQTTClient):
        self.mqtt_client = mqtt_client

    def is_connected(self) -> bool:
        return self.mqtt_client.is_connected()

    def publish(self, topic: str, payload: dict | str, timeout: float = 2.0):
        # dict -> JSON (sensor/test messages); str -> sent as-is
        # (device commands such as "on" / "off").
        message = payload if isinstance(payload, str) else json.dumps(payload)

        result = self.mqtt_client.client.publish(
            topic,
            message
        )

        result.wait_for_publish(timeout=timeout)

        return result
