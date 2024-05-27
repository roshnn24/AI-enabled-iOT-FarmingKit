#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <DHT.h>

// Define pin connections
#define DHTPIN D4        // Pin connected to the DATA pin of DHT sensor
#define IR_PIN D1        // Pin connected to the OUT pin of IR sensor
#define TRIG_PIN D2      // Pin connected to the TRIG pin of Ultrasonic sensor
#define ECHO_PIN D3      // Pin connected to the ECHO pin of Ultrasonic sensor

// Define DHT sensor type
#define DHTTYPE DHT11    // DHT 11 or DHT22

DHT dht(DHTPIN, DHTTYPE);

// Your WiFi credentials
const char* ssid = "";
const char* password ="";

// Flask server IP address and port
const char* serverName = "http://192.168.1.8:5000/sensor-data";

void setup() {
  // Start the serial communication
  Serial.begin(115200);
  
  // Initialize the DHT sensor
  dht.begin();
  
  // Initialize pin modes
  pinMode(IR_PIN, INPUT);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;

    // Read data from DHT sensor
    float humidity = dht.readHumidity();
    float temperature = dht.readTemperature();

    // Check if any reads failed and exit early (to try again).
    if (isnan(humidity) || isnan(temperature)) {
      Serial.println("Failed to read from DHT sensor!");
      return;
    }

    // Read data from IR sensor
    int irValue = digitalRead(IR_PIN);

    // Read data from Ultrasonic sensor
    long duration, distance;
    digitalWrite(TRIG_PIN, LOW);
    delayMicroseconds(2);
    digitalWrite(TRIG_PIN, HIGH);
    delayMicroseconds(10);
    digitalWrite(TRIG_PIN, LOW);
    duration = pulseIn(ECHO_PIN, HIGH);
    distance = duration * 0.034 / 2; // Convert duration to distance

    // Prepare JSON payload
    String jsonPayload = "{\"temperature\":" + String(temperature) +
                         ",\"humidity\":" + String(humidity) +
                         ",\"irValue\":" + String(irValue) +
                         ",\"distance\":" + String(distance) + "}";

    WiFiClient client;
    http.begin(client, serverName); // Change this line
    http.addHeader("Content-Type", "application/json");

    int httpResponseCode = http.POST(jsonPayload);

    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println(httpResponseCode);
      Serial.println(response);
    } else {
      Serial.print("Error on sending POST: ");
      Serial.println(httpResponseCode);
    }

    http.end();
  } else {
    Serial.println("WiFi Disconnected");
  }

  // Wait for a second before next reading
  delay(1000);
}
