#include <DHT.h>

#define DHT_PIN 15      
#define PIR_PIN 13     
#define DHT_TYPE DHT22


#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

#define WIFI_SSID ""
#define WIFI_PASSWORD ""
#define SERVER_URL ""



DHT dht(DHT_PIN, DHT_TYPE);

void setup() {
    Serial.begin(115200);
    WiFi.mode(WIFI_STA);
    delay(100);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    Serial.print("Connecting to WiFi");
    int attempts=0;
    while (WiFi.status()!= WL_CONNECTED && attempts<20) {
        delay(500);
        Serial.print(".");
        attempts++;
    }
    Serial.println(WiFi.status());
    Serial.println("Connected");
    Serial.println(WiFi.localIP());
    
    pinMode(PIR_PIN, INPUT);
    dht.begin();
    pinMode(DHT_PIN, INPUT_PULLUP);

    delay(300);}

void loop() {
    float temperature=dht.readTemperature();
    float humidity= dht.readHumidity();
    int motion= digitalRead(PIR_PIN);
    
    Serial.print("Temp: "); Serial.println(temperature);
    Serial.print("Humidity: "); Serial.println(humidity);
    Serial.print("Motion: "); Serial.println(motion);
    long timestamp= millis();
    if (isnan(temperature) || isnan(humidity)) {
    Serial.println("DHT read failed, skipping");
    delay(2000);
    return;}
    JsonDocument doc;
    doc["device_id"] ="room_1";
    doc["temperature"]= temperature;
    doc["humidity"] =humidity;
    doc["motion"] =motion;
    doc["timestamp"] =timestamp;
    
    String jsonString;
    serializeJson(doc, jsonString);

    //send to server
    HTTPClient http;
    http.begin(SERVER_URL);
    http.addHeader("Content-Type", "application/json");
    int responseCode =http.POST(jsonString);
    
    Serial.print("Response: ");
    Serial.println(responseCode);
    
    http.end();
    delay(30000);
}
   