import tensorflow as tf
from tensorflow.keras import layers, models
import os

# 1. Configuration
# Path verified by your previous 'ls'
DATA_DIR = "research/dataset/plantvillage dataset/color"
IMG_SIZE = (224, 224)
BATCH_SIZE = 32

print("🌿 Loading 38-class dataset...")

# 2. Optimized Data Pipeline
train_ds = tf.keras.utils.image_dataset_from_directory(
    DATA_DIR,
    validation_split=0.2,
    subset="training",
    seed=123,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
)

val_ds = tf.keras.utils.image_dataset_from_directory(
    DATA_DIR,
    validation_split=0.2,
    subset="validation",
    seed=123,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
)

# 3. Model Architecture (MobileNetV2 for mobile efficiency)
base_model = tf.keras.applications.MobileNetV2(
    input_shape=(224, 224, 3), include_top=False, weights="imagenet"
)
base_model.trainable = False  # Freeze pre-trained weights

model = models.Sequential(
    [
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.Dropout(0.2),  # Regularization to prevent overfitting
        layers.Dense(38, activation="softmax"),  # Match your 38 folders
    ]
)

model.compile(
    optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"]
)

# 4. Training
print("🚀 Starting GPU-accelerated training...")
model.fit(train_ds, validation_data=val_ds, epochs=5)

# 5. Save for Phase 2
model.save("kisansetu_v38_full.h5")
print("✅ Training complete. Model saved as 'kisansetu_v38_full.h5'")
