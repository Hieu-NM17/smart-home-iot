from app.mqtt.client import MQTTClient


mqtt = MQTTClient()

mqtt.connect()
mqtt.start_loop()

input("Press Enter to disconnect...")

mqtt.stop_loop()
mqtt.disconnect()