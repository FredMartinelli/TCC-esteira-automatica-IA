import os
import numpy as np
import cv2
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.utils import to_categorical
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report
import matplotlib.pyplot as plt
import seaborn as sns

# Caminho do dataset aumentado
DATASET_PATH = r"C:\Users\Bruno Fernandes\TCC\dataset_webcam_FINAL_AUGMENTEDv30"
CLASSES = ['triangulo', 'quadrado', 'circulo']
IMG_SIZE = 64

def load_data():
    data = []
    labels = []
    for idx, class_name in enumerate(CLASSES):
        class_path = os.path.join(DATASET_PATH, class_name)
        for img_name in os.listdir(class_path):
            img_path = os.path.join(class_path, img_name)
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if img is not None:
                img = cv2.resize(img, (128, 128))  # tamanho real após borda
                img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))  # redimensiona para 64x64 após remover borda visualmente
                data.append(img)
                labels.append(idx)
    return np.array(data), np.array(labels)

# Carrega e prepara os dados
X, y = load_data()
X = X.reshape(-1, IMG_SIZE, IMG_SIZE, 1).astype('float32') / 255.0
y = to_categorical(y, num_classes=len(CLASSES))

# Divide em treino e teste
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# CNN inspirada no GitHub
model = Sequential([
    Conv2D(32, (3,3), activation='relu', input_shape=(IMG_SIZE, IMG_SIZE, 1)),
    MaxPooling2D((2,2)),
    Conv2D(64, (3,3), activation='relu'),
    MaxPooling2D((2,2)),
    Flatten(),
    Dense(128, activation='relu'),
    Dropout(0.5),
    Dense(len(CLASSES), activation='softmax')
])

model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
model.summary()

# Treinamento com exibição de acurácia
history = model.fit(
    X_train, y_train,
    epochs=15,
    batch_size=32,
    validation_data=(X_test, y_test),
    verbose=1
)

# Salva o modelo treinado
model.save(r"C:\Users\Bruno Fernandes\TCC\FINAL_V30.h5")

# Avaliação com matriz de confusão
y_pred = model.predict(X_test)
y_pred_classes = np.argmax(y_pred, axis=1)
y_true = np.argmax(y_test, axis=1)

cm = confusion_matrix(y_true, y_pred_classes)
plt.figure(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=CLASSES, yticklabels=CLASSES)
plt.xlabel("Predito")
plt.ylabel("Real")
plt.title("🔍 Matriz de Confusão - IA de Formas")
plt.tight_layout()
plt.show()

print("\n📊 Relatório de Classificação:")
print(classification_report(y_true, y_pred_classes, target_names=CLASSES))