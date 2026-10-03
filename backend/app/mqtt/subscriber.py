import json

from app.mqtt.client import MQTTClient


class MQTTSubscriber:
    def __init__(self, mqtt_client: MQTTClient):
        self.mqtt_client = mqtt_client

    def subscribe(self, topic: str, callback):
        self.mqtt_client.client.subscribe(topic)

        def on_message(client, userdata, message):
            try:
                payload = json.loads(message.payload.decode())
            except json.JSONDecodeError:
                payload = message.payload.decode()

            callback(message.topic, payload)

        self.mqtt_client.client.on_message = on_message