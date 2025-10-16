import os
import cv2

# === CONFIGURAÇÕES ===
# Nome da figura geométrica (vai ser o nome da pasta)
figura = input("Digite o nome da figura geométrica: ").strip().lower()

# Pasta onde os datasets ficarão salvos
dataset_folder = "dataset_webcam_FINALv2"
save_folder = os.path.join(dataset_folder, figura)
os.makedirs(save_folder, exist_ok=True)

# Abrir webcam USB (trocar o número se necessário: 0 = câmera interna, 1 = webcam USB)
webcam = cv2.VideoCapture(1)  # teste 0 ou 1, dependendo do seu setup

if not webcam.isOpened():
    print("❌ Não foi possível acessar a webcam.")
    exit()

print("\n📸 Pressione 'S' para capturar imagem")
print("❌ Pressione 'Q' para sair\n")

contador = len(os.listdir(save_folder))  # continua numeração se já existir imagens

while True:
    ret, frame = webcam.read()
    if not ret:
        print("❌ Falha ao capturar frame.")
        break

    cv2.imshow("Webcam - Pressione S para salvar", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('s'):  # salva imagem
        contador += 1
        filename = f"{figura}_{contador:03d}.jpg"
        filepath = os.path.join(save_folder, filename)
        cv2.imwrite(filepath, frame)
        print(f"✅ Imagem salva: {filepath}")

    elif key == ord('q'):  # sai do loop
        break

webcam.release()
cv2.destroyAllWindows()