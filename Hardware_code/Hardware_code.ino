

#include <Arduino.h>

#include <ESP8266WiFi.h>
#include <ESP8266WiFiMulti.h>

#include <ESP8266HTTPClient.h>

#include <WiFiClientSecureBearSSL.h>
#define wifiStatusLed D3
#define onStatusLed D4


ESP8266WiFiMulti WiFiMulti;

// Fingerprint for demo URL, expires on June 2, 2024, needs to be updated well before this date
const char* fingerprint = "C5 0E AC 4E B6 D2 9E C6 D4 11 6A 3F C0 F4 DD 46 96 56 CA 3C";
#define DEVICE_ID "53d1d1e4-9e97-45a4-823d-17e5248166a9"
      //Copy this code to your device sketch.
//#define DEVICE_ID  "5f71e954-3ecf-43cd-9261-0cb1dd00e49c"
      //Copy this code to your device sketch. 



void setup() {

  Serial.begin(9600);
  // Serial.setDebugOutput(true);

  Serial.println();
  Serial.println();
  Serial.println();
  pinMode(wifiStatusLed, OUTPUT);
pinMode(onStatusLed, OUTPUT);
digitalWrite(onStatusLed, HIGH);


  for (uint8_t t = 4; t > 0; t--) {
    Serial.printf("[SETUP] WAIT %d...\n", t);
    Serial.flush();
    delay(1000);
  }

 
  WiFi.mode(WIFI_STA);
  WiFiMulti.addAP("Novatech", "Nova@Tech");
  WiFiMulti.addAP( "growfertile","grow@fertile");
  if (WiFiMulti.run() != WL_CONNECTED) {
    
    Serial.println(" Wifi Connected  ");
    digitalWrite(wifiStatusLed, HIGH);
    Serial.println(" Wifi not Connected  ");
    delay(500);
    digitalWrite(wifiStatusLed, LOW);
    delay(500);
    
  }
  else {
    digitalWrite(wifiStatusLed, HIGH);
    Serial.println(" Wifi  Connected  ");
    delay(1000);
    
  }


  

}
String serverName = "https://growfertile.science/soil-data";
void send_readings(int N, int P, int K) {
  std::unique_ptr<BearSSL::WiFiClientSecure>client(new BearSSL::WiFiClientSecure);

//  client->setFingerprint(fingerprint);
  // Or, if you happy to ignore the SSL certificate, then use the following line instead:
   client->setInsecure();

  HTTPClient https;
  ///soil-data?device=080a3eaf-945c-4b14-8787-4f48cef3ed81&N=20&P=30&K=40
  
  String serverPath = serverName + "?device=" + String(DEVICE_ID) + "&N="+N+"&P="+P+"&K="+K;


  Serial.print("[HTTPS] begin...\n");
  if (https.begin(*client, serverPath)) {  // HTTPS

    Serial.print("[HTTPS] GET...\n");
    // start connection and send HTTP header
    int httpCode = https.GET();

    // httpCode will be negative on error
    if (httpCode > 0) {
      // HTTP header has been send and Server response header has been handled
      Serial.printf("[HTTPS] GET... code: %d\n", httpCode);

      // file found at server
      if (httpCode == HTTP_CODE_OK || httpCode == HTTP_CODE_MOVED_PERMANENTLY) {
        String payload = https.getString();
       
        
        
        
        delay(1000);
        Serial.println(payload);
      }
    } else {
      Serial.printf("[HTTPS] GET... failed, error: %s\n", https.errorToString(httpCode).c_str());
     
    }

    https.end();
  } else {
    Serial.printf("[HTTPS] Unable to connect\n");
  }
}



void loop() {

  //Serial.println("Starting the reading process");
  int N=random(0.1, 5);
  int P=random(0.05, 0.5);
  int K=random(0.1, 5);
  if (WiFi.status()==WL_CONNECTED){
    send_readings(N, P, K);
    digitalWrite(wifiStatusLed, HIGH);
  delay(2000);
    
  }
  else{
    if (WiFiMulti.run() != WL_CONNECTED) {
    digitalWrite(wifiStatusLed, HIGH);
    Serial.println(" Wifi not Connected  ");
    delay(500);
    digitalWrite(wifiStatusLed, LOW);
    delay(500);
  }

  }
  
}
