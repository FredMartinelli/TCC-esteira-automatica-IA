#include <WiFi.h>
#include <Ultrasonic.h>
#include <ESP32Servo.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 32
#define OLED_RESET    -1  // Reset não é usado com I2C

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);


// ======================= CONFIG WIFI =======================
const char* ssid = "A54 de Fred";
const char* password = "fred1234";
WiFiServer server(8080); // Porta para receber dados do Python

// ======================= PINOS =======================
#define PIN_TRIGGER       12
#define PIN_ECHO          13
#define PIN_ENA           25
#define PIN_IN1           33
#define PIN_IN2           4
#define PIN_SERVO_CIRC    18
#define PIN_SERVO_QUAD    5
#define PIN_SERVO_TRI     19

// ======================= OBJETOS =======================
Ultrasonic ultrasonic(PIN_TRIGGER, PIN_ECHO);
Servo servoCirc, servoQuad, servoTri;

// ======================= VARIÁVEIS =======================
bool esteiraLigada = false;
bool aguardandoRespostaIA = false;
String formaRecebida = "";

// ======================= FUNÇÕES MOTOR =======================
void motorEsteiraLiga() {
  digitalWrite(PIN_IN1, HIGH);
  digitalWrite(PIN_IN2, LOW);
}

void motorEsteiraDesliga() {
  digitalWrite(PIN_IN1, LOW);
  digitalWrite(PIN_IN2, LOW);
}

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22); // SDA = GPIO 21, SCL = GPIO 22

  // Inicializa o display
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("❌ Falha ao inicializar o display OLED");
    while (true); // trava se falhar
  }

  display.clearDisplay();
  display.setTextSize(2);             // Tamanho do texto
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 10);           // Posição do texto
  display.println("Bom dia!");       // Palavra a ser exibida
  display.display();                  // Atualiza o display

  pinMode(PIN_IN1, OUTPUT);
  pinMode(PIN_IN2, OUTPUT);

  servoCirc.attach(PIN_SERVO_CIRC);
  servoQuad.attach(PIN_SERVO_QUAD);
  servoTri.attach(PIN_SERVO_TRI);

  // === Setar posição inicial dos servos ===
  servoCirc.write(95);
  servoQuad.write(95);
  servoTri.write(100);
  delay(500);

  motorEsteiraDesliga();

  WiFi.begin(ssid, password);
  Serial.print("Conectando-se ao Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ Wi-Fi conectado.");
  Serial.print("📡 IP do ESP32: ");
  Serial.println(WiFi.localIP());

  server.begin();
  Serial.println("🟢 Servidor iniciado na porta 8080");
}

void loop() {
  // Controle via Serial Monitor
  if (Serial.available()) {
    char comando = Serial.read();
    if (comando == '1') {
      esteiraLigada = true;
      motorEsteiraLiga();
      Serial.println("🟢 Esteira LIGADA via Serial");
    } else if (comando == '0') {
      esteiraLigada = false;
      motorEsteiraDesliga();
      Serial.println("🔴 Esteira DESLIGADA via Serial");
    }
  }

  // Verifica se recebeu conexão do Python
  WiFiClient client = server.available();
  if (client) {
    String msg = client.readStringUntil('\n');
    msg.trim();
    if (msg.length() > 0) {
      formaRecebida = msg;
      Serial.println("📨 Forma recebida via Python: " + formaRecebida);
        display.clearDisplay();
        display.setTextSize(2);             // Tamanho do texto
        display.setTextColor(SSD1306_WHITE);
        display.setCursor(0, 10);           // Posição do texto
        display.println(formaRecebida);       // Palavra a ser exibida
        display.display();                  // Atualiza o display

      processarForma();
    }
    client.stop();
  }

  // Verifica se há peça na esteira
  if (esteiraLigada && !aguardandoRespostaIA) {
    float distancia = ultrasonic.read();
    if (distancia < 8.0 && distancia > 0) {
      motorEsteiraDesliga();
      aguardandoRespostaIA = true;
      Serial.println("🛑 Peça detectada. Aguardando comando da IA...");
    }
  }
}

void processarForma() {
  if (formaRecebida == "circulo") {
    servoCirc.write(50);
    motorEsteiraLiga();
    delay(2000);
    servoCirc.write(95);
  } else if (formaRecebida == "quadrado") {
    servoQuad.write(50);
    motorEsteiraLiga();
    delay(2000);
    servoQuad.write(95);
  } else if (formaRecebida == "triangulo") {
    servoTri.write(145);
    motorEsteiraLiga();
    delay(2000);
    servoTri.write(100);
  } else {
    Serial.println("⚠️ Forma desconhecida recebida: " + formaRecebida);
  }

  motorEsteiraLiga(); // volta à velocidade padrão
  formaRecebida = "";
  aguardandoRespostaIA = false;
  esteiraLigada = true; // reativa a esteira após o processo
}