#include <WiFi.h>
#include <HTTPClient.h>

// Kredensial WiFi khusus simulator Wokwi
const char* ssid = "Wokwi-GUEST"; 
const char* password = "";

// URL Endpoint PythonAnywhere Anda
const char* serverUrl = "http://rifqishandi.pythonanywhere.com/predict_plant_health";

const int ledPin = 13;

void setup() {
  Serial.begin(115200);
  pinMode(ledPin, OUTPUT);
  
  Serial.println("\n--- Sistem IoT Monitoring Tanaman Cerdas ---");
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Terhubung! IP: " + WiFi.localIP().toString());
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");

    // [INTEGRASI AI]: Menghasilkan angka acak 0-3 untuk mensimulasikan kondisi berbeda
    // 0:Healthy, 1:Early Blight, 2:Late Blight, 3:Leaf Spot
    int randomCondition = random(0, 4); 

    // Payload JSON sesuai kriteria tugas
    String jsonPayload = "{\"device_id\": \"ESP32_WOKWI_01\", \"simulated_data\": \"" + String(randomCondition) + "\"}";
    
    Serial.println("[HTTP] Mengirim data simulasi ke server...");
    int httpResponseCode = http.POST(jsonPayload);

    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("Response Code: " + String(httpResponseCode));
      Serial.println("Hasil AI: " + response);
      
      // Indikator visual sukses kirim data
      digitalWrite(ledPin, HIGH); delay(500); digitalWrite(ledPin, LOW);
    } else {
      Serial.println("Error pada pengiriman: " + String(httpResponseCode));
    }
    http.end();
  }
  
  // Interval 10 detik untuk menjaga kontinuitas data dashboard
  delay(5000); 
}
