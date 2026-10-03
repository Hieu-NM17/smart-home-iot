import json

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

from app.config import settings


class MQTTClient:
    def __init__(self):
        self.client = mqtt.Client(
            callback_api_version=CallbackAPIVersion.VERSION2
        )

        # Topics are (re)subscribed in _on_connect so they survive a broker
        # restart / reconnect. message_handler(topic, payload) receives every
        # incoming message; payload is parsed JSON when possible, else str.
        self.subscriptions: list[str] = []
        self.message_handler = None

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

    def add_subscription(self, topic: str):
        if topic not in self.subscriptions:
            self.subscriptions.append(topic)

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            print("MQTT connected")

            for topic in self.subscriptions:
                client.subscribe(topic)
                print(f"MQTT subscribed: {topic}")
        else:
            print(f"MQTT connection failed: {reason_code}")

    def _on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        print(f"MQTT disconnected: {reason_code}")

    def _on_message(self, client, userdata, message):
        if self.message_handler is None:
            return

        text = message.payload.decode(errors="replace")

        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = text

        try:
            self.message_handler(message.topic, payload)
        except Exception as exc:
            # Never let one bad message kill the paho network thread.
            print(f"MQTT handler error on {message.topic}: {exc}")

    def connect(self):
        args = (
            settings.mqtt_broker_host,
            settings.mqtt_broker_port,
            settings.mqtt_keepalive,
        )

        try:
            self.client.connect(*args)
        except OSError as exc:
            # Broker not up yet: do not crash the API. loop_start() will keep
            # retrying in the background, and commands answer 503 meanwhile.
            print(f"MQTT broker unavailable ({exc}); retrying in background")
            self.client.connect_async(*args)

    def disconnect(self):
        self.client.disconnect()

    def is_connected(self) -> bool:
        return self.client.is_connected()

    def start_loop(self):
        self.client.loop_start()

    def stop_loop(self):
        self.client.loop_stop()
