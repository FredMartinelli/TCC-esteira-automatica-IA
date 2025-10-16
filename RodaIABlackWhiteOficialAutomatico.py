# --- CONFIGURAÇÕES ---------------------------------------------------------
#MODEL_PATH   = "modelo_formas_v14.2.h5"
#IMG_SIZE     = 64
#CATEGORIES = ["triangulo", "quadrado", "circulo"]

ESP32_IP     = "192.168.153.160"
ESP32_PORT   = 8080
LISTEN_PORT  = 8081  # Porta onde ESP32 envia "avaliar"

import socket
import threading
import cv2
import numpy as np
from tensorflow.keras.models import load_model

# Caminho do modelo treinado
MODEL_PATH = r"C:\Users\Bruno Fernandes\TCC\FINAL_V20.h5"
CLASSES = ['triangulo', 'quadrado', 'circulo']
IMG_SIZE = 64
TEMP_SIZE = 96
MARGEM_ESQUERDA = 160
MARGEM_DIREITA = 170

# Carrega o modelo
model = load_model(MODEL_PATH)

# Função para recortar as laterais
def recortar_laterais(img):
    h, w = img.shape[:2]
    return img[:, MARGEM_ESQUERDA:w - MARGEM_DIREITA]

# Função para desenhar tracejado vertical
def desenhar_tracejado(frame, x, cor=(0, 0, 255), espessura=1, intervalo=10):
    h = frame.shape[0]
    for y in range(0, h, intervalo * 2):
        cv2.line(frame, (x, y), (x, y + intervalo), cor, espessura)

# Função principal de avaliação
def avaliar_forma():
    ret, frame = cap.read()
    if not ret:
        print("❌ Erro ao acessar a webcam.")
        return

    img_recortada = recortar_laterais(frame)
    img_resized = cv2.resize(img_recortada, (TEMP_SIZE, TEMP_SIZE))
    bordered = cv2.copyMakeBorder(img_resized, 16, 16, 16, 16, cv2.BORDER_CONSTANT, value=[0, 0, 0])
    final_img = cv2.resize(bordered, (IMG_SIZE, IMG_SIZE))
    gray = cv2.cvtColor(final_img, cv2.COLOR_BGR2GRAY)
    normalized = gray.astype('float32') / 255.0
    input_data = normalized.reshape(1, IMG_SIZE, IMG_SIZE, 1)

    prediction = model.predict(input_data)
    class_index = np.argmax(prediction)
    confidence = prediction[0][class_index]
    forma_detectada = CLASSES[class_index]

    texto = f"{forma_detectada} ({confidence:.2f})"
    cv2.putText(frame, texto, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
    cv2.imshow("Webcam - Avaliacao de Formas", frame)
    print(f"🔍 Forma detectada: {forma_detectada} (confiança: {confidence:.2f})")

    # Envia a forma detectada para o ESP32 via socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ESP32_IP, ESP32_PORT))
            s.sendall(forma_detectada.encode())
            print(f"📤 Forma '{forma_detectada}' enviada ao ESP32 com sucesso.")
    except Exception as e:
        print(f"⚠️ Erro ao enviar para ESP32: {e}")

# Thread que escuta o ESP32
def escutar_esp32():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.bind(("0.0.0.0", LISTEN_PORT))
        servidor.listen()
        print(f"🟢 Aguardando sinal do ESP32 na porta {LISTEN_PORT}...")
        while True:
            conn, addr = servidor.accept()
            with conn:
                msg = conn.recv(1024).decode().strip()
                if msg == "avaliar":
                    print("📩 Sinal recebido do ESP32: avaliar")
                    avaliar_forma()

# Inicia webcam
cap = cv2.VideoCapture(1)

# Inicia thread de escuta
threading.Thread(target=escutar_esp32, daemon=True).start()

print("🧠 IA pronta para avaliar automaticamente!")
print("Pressione S para sair")

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Erro ao acessar a webcam.")
        break

    desenhar_tracejado(frame, MARGEM_ESQUERDA)
    desenhar_tracejado(frame, frame.shape[1] - MARGEM_DIREITA)

    cv2.putText(frame, "Aguardando sinal do ESP32... Pressione S para sair", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.imshow("Webcam - Avaliacao de Formas", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('s'):
        print("👋 Saindo da avaliação...")
        break

# Libera recursos
cap.release()
cv2.destroyAllWindows()