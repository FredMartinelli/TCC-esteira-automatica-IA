import os
import cv2
import numpy as np
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# Caminhos
ORIGINAL_PATH = r"C:\Users\Bruno Fernandes\TCC\dataset_webcam_FINALv2"
AUGMENTED_PATH = r"C:\Users\Bruno Fernandes\TCC\dataset_webcam_FINAL_AUGMENTEDv30"
CLASSES = ['triangulo', 'quadrado', 'circulo']
IMG_SIZE = 64
TEMP_SIZE = 96
TARGET_COUNT = 5000
VISUALIZAR = True  # Ativado para mostrar o primeiro recorte

# Margens separadas
MARGEM_ESQUERDA = 160
MARGEM_DIREITA = 170

# Configurações de aumento
datagen = ImageDataGenerator(
    rotation_range=40,
    width_shift_range=0.05,
    height_shift_range=0.05,
    zoom_range=0.05,
    shear_range=5,
    horizontal_flip=True,
    brightness_range=[0.7, 1.3],
    channel_shift_range=20.0,
    fill_mode='constant',
    cval=0
)

# Cria pastas de destino
for class_name in CLASSES:
    os.makedirs(os.path.join(AUGMENTED_PATH, class_name), exist_ok=True)

# Função para recortar com margens separadas
def recortar_laterais(img):
    h, w = img.shape[:2]
    return img[:, MARGEM_ESQUERDA:w - MARGEM_DIREITA]

# Geração balanceada
total_geradas = 0

for class_name in CLASSES:
    class_path = os.path.join(ORIGINAL_PATH, class_name)
    save_path = os.path.join(AUGMENTED_PATH, class_name)

    if not os.path.exists(class_path):
        print(f"⚠️ Pasta não encontrada: {class_path}")
        continue

    existentes = [f for f in os.listdir(save_path) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    count_existente = len(existentes)
    print(f"\n🔍 {class_name}: {count_existente} imagens já existem")

    if count_existente >= TARGET_COUNT:
        print(f"✅ {class_name} já tem {TARGET_COUNT} ou mais imagens. Pulando...")
        continue

    originais = [f for f in os.listdir(class_path) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    faltam = TARGET_COUNT - count_existente
    por_imagem = max(1, faltam // len(originais)) + 1

    print(f"⚙️ Gerando ~{por_imagem} variações por imagem original...")

    # Exibe o primeiro recorte e pergunta se deve continuar
    if VISUALIZAR and len(originais) > 0:
        img_path = os.path.join(class_path, originais[0])
        img = cv2.imread(img_path)
        if img is not None:
            img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2BGR)

            img_recortada = recortar_laterais(img)
            cv2.imshow("Primeiro Recorte", img_recortada)
            print(f"🖼️ Mostrando o primeiro recorte com margem esquerda = {MARGEM_ESQUERDA} e direita = {MARGEM_DIREITA}")
            print("Pressione qualquer tecla para visualizar...")
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            seguir = input("👉 Deseja continuar com o restante das imagens? (s/n): ")
            if seguir.lower() != 's':
                print("⛔ Execução interrompida pelo usuário.")
                exit()

    # Continua com o restante das imagens
    for img_index, img_name in enumerate(originais):
        img_path = os.path.join(class_path, img_name)
        img = cv2.imread(img_path)
        if img is None:
            print(f"❌ Imagem inválida: {img_path}")
            continue

        # Converte para preto e branco mantendo 3 canais
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2BGR)

        img_recortada = recortar_laterais(img)
        img_resized = cv2.resize(img_recortada, (TEMP_SIZE, TEMP_SIZE))
        bordered = cv2.copyMakeBorder(img_resized, 16, 16, 16, 16, cv2.BORDER_CONSTANT, value=[0, 0, 0])
        bordered = np.expand_dims(bordered, axis=0)

        i = 0
        for batch in datagen.flow(bordered, batch_size=1, save_to_dir=save_path,
                                  save_prefix=f'{class_name}_aug_{img_name.split(".")[0]}',
                                  save_format='jpg'):
            i += 1
            total_geradas += 1
            if i >= por_imagem:
                break

    print(f"✅ {class_name} agora tem pelo menos {TARGET_COUNT} imagens.")

print(f"\n📦 Total de imagens geradas nesta execução: {total_geradas}")
print("🏁 Data Augmentation concluído com sucesso!")