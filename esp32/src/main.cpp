#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASSWORD = "";

const char* MQTT_HOST = "host.wokwi.internal";
const int MQTT_PORT = 1883;

const char* MQTT_CLIENT_ID = "esp32_smart_home";

const char* COMMAND_TOPIC =
    "home/living_room/light_01/command";

const char* STATE_TOPIC =
    "home/living_room/light_01/state";

const char* SENSOR_TOPIC =
    "home/living_room/temperature_01/sensor";

const char* HUMIDITY_TOPIC =
    "home/living_room/humidity_01/sensor";

const char* STATUS_TOPIC =
    "home/living_room/esp32_smart_home/status";

const char* STATUS_ONLINE =
    "{\"status\":\"online\",\"devices\":[\"light_01\",\"dht22_01\"]}";

const char* STATUS_OFFLINE =
    "{\"status\":\"offline\",\"devices\":[\"light_01\",\"dht22_01\"]}";

#define DHT_PIN 4
#define DHT_TYPE DHT22

#define LED_PIN 12
#define BUTTON_PIN 13

WiFiClient espClient;
PubSubClient mqttClient(espClient);
DHT dht(DHT_PIN, DHT_TYPE);

unsigned long lastSensorPublish = 0;
const unsigned long SENSOR_INTERVAL = 5000;

bool ledState = false;
bool lastButtonReading = HIGH;
bool stableButtonState = HIGH;
unsigned long lastDebounceTime = 0;
const unsigned long DEBOUNCE_MS = 50;

void connectWiFi() {
    Serial.print("Connecting to WiFi");

    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }

    Serial.println();
    Serial.println("WiFi connected");

    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
}

void publishDeviceState(const char* state) {
    // Retained: a backend that starts (or restarts) later still learns the
    // current LED state as soon as it subscribes.
    bool success = mqttClient.publish(
        STATE_TOPIC,
        state,
        true
    );

    if (success) {
        Serial.print("Published state [");
        Serial.print(STATE_TOPIC);
        Serial.print("]: ");
        Serial.println(state);
    } else {
        Serial.println("Failed to publish device state");
    }
}

void setLight(bool on) {
    ledState = on;
    digitalWrite(LED_PIN, on ? HIGH : LOW);
    publishDeviceState(on ? "on" : "off");
}

void handleButton() {
    bool reading = digitalRead(BUTTON_PIN);

    if (reading != lastButtonReading) {
        lastDebounceTime = millis();
    }

    if (millis() - lastDebounceTime > DEBOUNCE_MS) {
        if (reading != stableButtonState) {
            stableButtonState = reading;

            if (stableButtonState == LOW) {  // nhan xuong
                Serial.println("Button pressed");
                setLight(!ledState);
            }
        }
    }

    lastButtonReading = reading;
}

void publishSensor(
    const char* topic,
    const char* sensorId,
    const char* sensorType,
    float value,
    const char* unit
) {
    char payload[250];

    snprintf(
        payload,
        sizeof(payload),
        "{\"sensor_id\":\"%s\",\"sensor_type\":\"%s\",\"value\":%.2f,\"unit\":\"%s\"}",
        sensorId,
        sensorType,
        value,
        unit
    );

    bool success = mqttClient.publish(
        topic,
        payload
    );

    if (success) {
        Serial.print("Published sensor data [");
        Serial.print(topic);
        Serial.print("]: ");
        Serial.println(payload);
    } else {
        Serial.print("Failed to publish sensor data: ");
        Serial.println(sensorId);
    }
}

void readAndPublishSensor() {
    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();

    if (isnan(temperature) || isnan(humidity)) {
        Serial.println("Failed to read DHT22");
        return;
    }

    Serial.print("Temperature: ");
    Serial.print(temperature);
    Serial.println(" C");

    Serial.print("Humidity: ");
    Serial.print(humidity);
    Serial.println(" %");

    publishSensor(SENSOR_TOPIC, "temperature_01", "temperature", temperature, "celsius");
    publishSensor(HUMIDITY_TOPIC, "humidity_01", "humidity", humidity, "percent");
}

void mqttCallback(
    char* topic,
    byte* payload,
    unsigned int length
) {
    String command = "";

    for (unsigned int i = 0; i < length; i++) {
        command += (char)payload[i];
    }

    Serial.print("Message received [");
    Serial.print(topic);
    Serial.print("]: ");
    Serial.println(command);

    if (String(topic) != COMMAND_TOPIC) {
        return;
    }

    if (command == "on") {
        Serial.println("Light command: ON");
        setLight(true);
    }
    else if (command == "off") {
        Serial.println("Light command: OFF");
        setLight(false);
    }
    else {
        Serial.println("Unknown command");
    }
}

void connectMQTT() {
    while (!mqttClient.connected()) {
        Serial.print("Connecting to MQTT... ");

        if (mqttClient.connect(
                MQTT_CLIENT_ID,
                STATUS_TOPIC,
                1,
                true,
                STATUS_OFFLINE
            )) {
            Serial.println("MQTT connected");

            // Retained, so a backend that starts later still sees it.
            mqttClient.publish(STATUS_TOPIC, STATUS_ONLINE, true);

            bool subscribed = mqttClient.subscribe(
                COMMAND_TOPIC
            );

            if (subscribed) {
                Serial.println("Subscribe successful");
                Serial.print("Subscribed to: ");
                Serial.println(COMMAND_TOPIC);
            } else {
                Serial.println("Subscribe failed");
            }

            // Tell the backend the real LED state after every (re)connect,
            // so its database cannot stay out of sync after a reboot.
            publishDeviceState(ledState ? "on" : "off");

        } else {
            Serial.print("MQTT connection failed, state=");
            Serial.println(mqttClient.state());

            delay(2000);
        }
    }
}

void setup() {
    Serial.begin(115200);

    delay(1000);

    Serial.println();
    Serial.println("================================");
    Serial.println("SMART HOME ESP32");
    Serial.println("================================");

    pinMode(LED_PIN, OUTPUT);
    pinMode(BUTTON_PIN, INPUT_PULLUP);
    digitalWrite(LED_PIN, LOW);

    dht.begin();

    connectWiFi();

    mqttClient.setServer(
        MQTT_HOST,
        MQTT_PORT
    );

    mqttClient.setCallback(
        mqttCallback
    );

    connectMQTT();
}

void loop() {
    if (!mqttClient.connected()) {
        connectMQTT();
    }

    mqttClient.loop();

    handleButton();

    if (millis() - lastSensorPublish >= SENSOR_INTERVAL) {
        lastSensorPublish = millis();

        readAndPublishSensor();
    }

    delay(10);
}
