///
///
///
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <SPIFFS.h>
#include <Preferences.h>

Preferences prefs;

char* ssid;
char* pwd;
char* mqtt_server = "localhost";
int mqtt_port = 1883;

struct WifiConfig {
  String ssid;
  String password;
};




// const char* mqtt_server = "test.mosquitto.org";
const char* pub_topic = "test/device001/status";
const char* sub_topic = "test/device001/cmd";





// ====== GLOBALS ======
WiFiClient espClient;
PubSubClient client(espClient);

unsigned long lastMsg = 0;
int msgCount = 0;
int ledPin = 2; // built-in LED pin for ESP32


// ====== FUNCTIONS ======
void setup_wifi(const char* ssid, const char* pwd) {
  delay(100);
  Serial.println("Connecting to WiFi...");

  WiFi.begin(ssid, pwd);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    digitalWrite(ledPin, HIGH);
    delay(200); // wait for a second
    digitalWrite(ledPin, LOW);
    delay(200); // wait for a second
  }

  Serial.println("\nWiFi connected");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message received [");
  Serial.print(topic);
  Serial.print("]: ");

  for (int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
  }
  Serial.println();
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Connecting to MQTT...");

    String clientId = "ESP32Client-";
    clientId += String(random(0xffff), HEX);

    if (client.connect(clientId.c_str())) {
      Serial.println("connected");
      client.subscribe(sub_topic);
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" retrying in 5s");
      delay(5000);
    }
  }
}

// int myFunction(int, int);
int myFunction(int x, int y) {
  return x + y;
}

// ====== SETUP ======
void setup() {
  pinMode(ledPin, OUTPUT);

  Serial.begin(115200);
  delay(3000);
  //
  prefs.begin("wifi", false); // namespace
  String ssid = prefs.getString("ssid", "");
  String pass = prefs.getString("pass", "");

  Serial.println("SSID: ");
  Serial.println(ssid);
  // Serial.println(pass);

  prefs.end();
//
  setup_wifi(ssid.c_str(), pass.c_str());
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

// ====== LOOP ======
void loop() {

  if (!client.connected()) {
    reconnect();
    digitalWrite(ledPin, HIGH);
    delay(200); // wait for a second
    digitalWrite(ledPin, LOW);
    delay(200); // wait for a second
    Serial.print("notCon: ");
  }

  client.loop();

  unsigned long now = millis();
  if (now - lastMsg > 10000) {
    lastMsg = now;

    digitalWrite(ledPin, HIGH);
    delay(500); // wait for a second
    digitalWrite(ledPin, LOW);
    delay(500); // wait for a second

    // String payload = "{\"msg\":\"hello\",\"count\":";
    // payload += msgCount++;
    // payload += "}";

    String payload = "{";
    payload += "\"ID\":\"KD_001\",";
    payload += "\"temp_c\":12.3,";
    payload += "\"RH\":100.0,";
    payload += "\"status\":\"ok\"";
    payload += "}";

    Serial.print("Publishing: ");
    Serial.println(payload);

    client.publish(pub_topic, payload.c_str());
  }
}