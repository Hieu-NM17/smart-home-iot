import time

from app.mqtt.client import MQTTClient
from app.mqtt.publisher import MQTTPublisher
from app.mqtt.subscriber import MQTTSubscriber


def test_mqtt_pubsub():
    topic = "home/living_room/light_01/test"
    received_messages = []

    def handle_message(topic, payload):
        received_messages.append(
            {
                "topic": topic,
                "payload": payload
            }
        )

    subscriber_client = MQTTClient()
    subscriber = MQTTSubscriber(subscriber_client)

    subscriber_client.connect()
    subscriber.subscribe(topic, handle_message)
    subscriber_client.start_loop()

    time.sleep(1)

    publisher_client = MQTTClient()
    publisher = MQTTPublisher(publisher_client)

    publisher_client.connect()
    publisher_client.start_loop()

    publisher.publish(
        topic,
        {
            "state": "on"
        }
    )

    time.sleep(1)

    assert len(received_messages) == 1
    assert received_messages[0]["topic"] == topic
    assert received_messages[0]["payload"] == {"state": "on"}

    publisher_client.stop_loop()
    publisher_client.disconnect()

    subscriber_client.stop_loop()
    subscriber_client.disconnect()