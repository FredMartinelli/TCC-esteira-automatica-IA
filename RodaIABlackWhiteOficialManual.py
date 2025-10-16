
# --- CONFIGURAÇÕES ---------------------------------------------------------
#MODEL_PATH   = "FINAL_V20.h5"
#IMG_SIZE     = 64
#CATEGORIES = ["triangulo", "quadrado", "circulo"]

ESP32_IP     = "192.168.153.160"
ESP32_PORT   = 8080

import socket
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

# Inicia webcam
cap = cv2.VideoCapture(1)

print("🧠 IA pronta para avaliar!")
print("Aperte Q para a IA avaliar ou S para sair")

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Erro ao acessar a webcam.")
        break

    # Desenha tracejados nas margens ignoradas
    desenhar_tracejado(frame, MARGEM_ESQUERDA)
    desenhar_tracejado(frame, frame.shape[1] - MARGEM_DIREITA)

    # Mostra instruções na tela
    cv2.putText(frame, "Aperte Q para a IA avaliar ou S para sair", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.imshow("Webcam - Avaliacao de Formas", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        # Aplica o mesmo pré-processamento do dataset
        img_recortada = recortar_laterais(frame)
        img_resized = cv2.resize(img_recortada, (TEMP_SIZE, TEMP_SIZE))
        bordered = cv2.copyMakeBorder(img_resized, 16, 16, 16, 16, cv2.BORDER_CONSTANT, value=[0, 0, 0])
        final_img = cv2.resize(bordered, (IMG_SIZE, IMG_SIZE))
        gray = cv2.cvtColor(final_img, cv2.COLOR_BGR2GRAY)
        normalized = gray.astype('float32') / 255.0
        input_data = normalized.reshape(1, IMG_SIZE, IMG_SIZE, 1)

        # Faz a previsão
        prediction = model.predict(input_data)
        class_index = np.argmax(prediction)
        confidence = prediction[0][class_index]

        texto = f"{CLASSES[class_index]} ({confidence:.2f})"
        cv2.putText(frame, texto, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
        cv2.imshow("Webcam - Avaliacao de Formas", frame)
        print(f"🔍 Forma detectada: {CLASSES[class_index]} (confiança: {confidence:.2f})")

    # Envia a forma detectada para o ESP32 via socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((ESP32_IP, ESP32_PORT))
                forma_detectada = CLASSES[class_index]
                s.sendall(forma_detectada.encode())
                print(f"📤 Forma '{forma_detectada}' enviada ao ESP32 com sucesso.")
        except Exception as e:
            print(f"⚠️ Erro ao enviar para ESP32: {e}")

    elif key == ord('s'):
        print("👋 Saindo da avaliação...")
        break

# Libera recursos
cap.release()
cv2.destroyAllWindows()