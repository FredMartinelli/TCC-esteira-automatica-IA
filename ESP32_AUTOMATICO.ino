#include <WiFi.h>
//#include <Arduino.h>
#include <Ultrasonic.h>
#include <ESP32Servo.h>
//#include "driver/mcpwm.h"
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 32
#define OLED_RESET    -1  // Reset não é usado com I2C

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// ======================= CONFIG WIFI =======================
const char* ssid = "MESSIAS";
const char* password = "messias22";
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

// ======================= PWM =======================
// #define MCPWM_UNIT        MCPWM_UNIT_0
// #define MCPWM_TIMER       MCPWM_TIMER_0
// #define MCPWM_GEN_A       MCPWM_OPR_A
// #define PWM_FREQ_HZ       5000      // 5 kHz
// #define PWM_RESOLUTION    100.0     // percent (0–100%)

// ======================= OBJETOS =======================
Ultrasonic ultrasonic(PIN_TRIGGER, PIN_ECHO);
Servo servoCirc, servoQuad, servoTri;

// ======================= VARIÁVEIS =======================
bool esteiraLigada = false;
bool aguardandoRespostaIA = false;
String formaRecebida = "";

// ======================= FUNÇÕES MOTOR =======================
void motorEsteiraLiga(/*int velocidade*/) {
  digitalWrite(PIN_IN1, HIGH);
  digitalWrite(PIN_IN2, LOW);
  // mcpwm_set_duty(MCPWM_UNIT, MCPWM_TIMER, MCPWM_GEN_A, 90.0);
  // mcpwm_set_duty_type(MCPWM_UNIT, MCPWM_TIMER, MCPWM_GEN_A, MCPWM_DUTY_MODE_0);
}

void motorEsteiraDesliga() {
  digitalWrite(PIN_IN1, LOW);
  digitalWrite(PIN_IN2, LOW);
  //mcpwm_set_duty(MCPWM_UNIT, MCPWM_TIMER, MCPWM_GEN_A, 0.0);
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
  display.println("Bom dia!");
  display.display();                  // Atualiza o display

  pinMode(PIN_IN1, OUTPUT);
  pinMode(PIN_IN2, OUTPUT);

  // 1. Inicializa MCPWM
  // mcpwm_gpio_init(MCPWM_UNIT, MCPWM0A, PIN_ENA);
  // mcpwm_config_t pwm_config;
  // pwm_config.frequency = PWM_FREQ_HZ;
  // pwm_config.cmpr_a    = 0;                // duty inicial em %
  // pwm_config.cmpr_b    = 0;
  // pwm_config.counter_mode = MCPWM_UP_COUNTER;
  // pwm_config.duty_mode    = MCPWM_DUTY_MODE_0;
  // mcpwm_init(MCPWM_UNIT, MCPWM_TIMER, &pwm_config);

  servoCirc.attach(PIN_SERVO_CIRC);
  servoQuad.attach(PIN_SERVO_QUAD);
  servoTri.attach(PIN_SERVO_TRI);

  // === Setar posição inicial dos servos ===
  servoCirc.write(95);     // posição inicial
  servoQuad.write(95);     // posição inicial do quadrado
  servoTri.write(100);     // posição inicial do triângulo (ajuste conforme necessário)
  delay(500);             // tempo p/ estabilizar

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
      display.setTextSize(2);
      display.setTextColor(SSD1306_WHITE);
      display.setCursor(0, 10);
      display.println(formaRecebida);
      display.display();

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
      Serial.println("🛑 Peça detectada. Enviando sinal para IA...");

      WiFiClient client;
      if (client.connect("192.168.0.3", 8081)) { // IP do computador com IA
        client.println("avaliar");
        client.stop();
        Serial.println("📤 Sinal 'avaliar' enviado para IA.");
      } else {
        Serial.println("⚠️ Falha ao conectar com IA.");
      }
    }
  }
}

void processarForma() {
  if (formaRecebida == "circulo") {
    servoCirc.write(50);
    motorEsteiraLiga();
    delay(3000);
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