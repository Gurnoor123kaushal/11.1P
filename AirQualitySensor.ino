#include <Wire.h>
#include <BH1750FVI.h>  // Library for the BH1750 light sensor
#include <DHT.h>        // Library for the DHT sensor
#include <WiFiNINA.h>   // Library for WiFi connection
#include <PubSubClient.h> // Library for MQTT

// Constants for WiFi and MQTT
char ssid[] = "iPhone";                     // WiFi SSID
char pass[] = "12345678";                // WiFi password
const char* broker = "broker.hivemq.com"; // MQTT broker address
const char* topic = "Home/SensorData";    // MQTT topic for sending sensor data

// Initialize WiFi and MQTT clients
WiFiClient wifiClient;
PubSubClient client(wifiClient);

// Light sensor setup (BH1750)
BH1750FVI LightSensor(BH1750FVI::k_DevModeContHighRes); // High-res mode for better accuracy

// DHT22 sensor setup
#define DHTPIN 2             // DHT sensor pin
#define DHTTYPE DHT22        // DHT22 sensor type
DHT dht(DHTPIN, DHTTYPE);

// Soil moisture sensor setup
const int soilMoisturePin = A1;
int soilMoistureValue = 0;

// MQ-135 CO₂ sensor setup
const int mq135Pin = A0;
const float RZERO = 76.63;       // Reference resistance at 1000 ppm CO2 (calibrated)
const float SCALE_FACTOR = 110.47;  // Scale factor for CO₂ estimation in ppm

// MQ-2 Smoke sensor setup
#define MQ2PIN A0            // Analog pin connected to the MQ2 sensor

// Function to connect to WiFi
void connectWiFi() {
  WiFi.begin(ssid, pass);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");
}

// Function to connect to MQTT broker
void connectMQTT() {
  client.setServer(broker, 1883);
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("ArduinoNano")) {
      Serial.println("Connected to MQTT broker");
    } else {
      Serial.print("Failed, rc=");
      Serial.print(client.state());
      delay(2000);
    }
  }
}

void setup() {
  Serial.begin(115200);   // Initialize serial communication
  LightSensor.begin();    // Start BH1750 light sensor
  dht.begin();            // Start DHT sensor
  connectWiFi();          // Connect to WiFi
  connectMQTT();          // Connect to MQTT broker
  delay(1000);            // Wait a moment for setup
}

void loop() {
  client.loop(); // Keep MQTT connection alive

  // Read light intensity from BH1750
  uint16_t lux = LightSensor.GetLightIntensity();
  Serial.print("Light Intensity: ");
  Serial.print(lux);
  Serial.println(" lx");

  // Read temperature and humidity from DHT22
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();

  // Check if readings from DHT22 are valid
  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("Failed to read from DHT sensor!");
  } else {
    Serial.print("Humidity: ");
    Serial.print(humidity);
    Serial.print(" %\t");
    Serial.print("Temperature: ");
    Serial.print(temperature);
    Serial.println(" °C");
  }

  // Read soil moisture level
  soilMoistureValue = analogRead(soilMoisturePin);
  int moisturePercentage = map(soilMoistureValue, 200, 500, 100, 0);  // Calibrated values

  Serial.print("Soil Moisture Value: ");
  Serial.print(soilMoistureValue);
  Serial.print(" (");
  Serial.print(moisturePercentage);
  Serial.println("%)");

  // Check soil moisture level
  if (moisturePercentage < 30) {
    Serial.println("Warning: Soil is dry!");
  } else if (moisturePercentage > 60) {
    Serial.println("Soil is wet.");
  } else {
    Serial.println("Soil moisture is optimal.");
  }

  // Read CO₂ concentration from MQ-135
  int sensorValue = analogRead(mq135Pin);  // Read analog value
  float voltage = (sensorValue / 1024.0) * 5.0;  // Convert to voltage
  float ppm = SCALE_FACTOR * (voltage / RZERO);  // Estimate CO₂ in ppm

  Serial.print("CO₂ Concentration: ");
  Serial.print(ppm);
  Serial.println(" ppm");

  // Read the MQ2 sensor value for smoke level
  int mq2Value = analogRead(MQ2PIN);
  float smokeLevel = map(mq2Value, 100, 900, 0, 100); // Adjusted for clean and smoky air

  Serial.print("Smoke Level: ");
  Serial.print(smokeLevel);
  Serial.println(" %");

  // Prepare the data string for MQTT with temperature, humidity, light, soil moisture, CO₂, and smoke level
  String dataMessage = "Temperature: " + String(temperature) +
                       ", Humidity: " + String(humidity) +
                       ", Light: " + String(lux) + " lx" +
                       ", Soil Moisture: " + String(moisturePercentage) + "%" +
                       ", CO₂: " + String(ppm) + " ppm" +
                       ", Smoke Level: " + String(smokeLevel) + "%";

  // Publish the sensor data to MQTT
  if (client.publish(topic, dataMessage.c_str())) {
    Serial.println("Sensor data sent successfully!");
    Serial.println(dataMessage);
  } else {
    Serial.println("Failed to send sensor data");
  }

  delay(5000);  // Delay before the next reading for more stable data
}
