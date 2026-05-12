"""
KisanSetu Phase 1: Rice Expert Model Training
==============================================
Architecture: MobileNetV2 (transfer learning) → TFLite export
Input:  224x224 RGB, raw [0, 255] pixels (Rescaling layer baked in)
Output: 5-class softmax

Classes (alphabetical — matches tf.keras folder order):
  0: Rice_Bacterial_Blight
  1: Rice_Blast
  2: Rice_Brown_Spot
  3: Rice_Healthy
  4: Rice_Tungro

Usage:
  python train_rice_expert.py

Prerequisites:
  pip install tensorflow numpy
  Download dataset into data/rice/ (see data/README.md)
"""

import tensorflow as tf
from tensorflow.keras import layers, models, callbacks
import numpy as np
import os

# ─── Configuration ──────────────────────────────────────────────────────────
DATA_DIR = "data/rice"
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS_HEAD = 20       # Epochs for classifier head training (frozen backbone)
EPOCHS_FINETUNE = 10   # Epochs for fine-tuning top backbone layers
LEARNING_RATE = 1e-4
FINE_TUNE_AT_LAYER = 100  # Unfreeze MobileNetV2 layers from this index onward

OUTPUT_H5 = "rice_expert_v1.h5"
OUTPUT_TFLITE = "rice_expert_v1.tflite"
OUTPUT_LABELS = "rice_labels.txt"

# Expected classes in alphabetical order (how TF reads folder names)
RICE_CLASSES = [
    "Rice_Bacterial_Blight",
    "Rice_Blast",
    "Rice_Brown_Spot",
    "Rice_Healthy",
    "Rice_Tungro",
]


def build_datasets():
    """
    Load and split the rice disease dataset.

    Uses tf.keras.utils.image_dataset_from_directory which:
    - Reads class names from subfolder names (alphabetical order)
    - Returns raw [0, 255] uint8 pixel values (normalization is in the model)
    - Splits 80/20 train/val using seed=42 for reproducibility
    """
    if not os.path.isdir(DATA_DIR):
        raise FileNotFoundError(
            f"Dataset directory not found: {DATA_DIR}\n"
            f"Please download the rice dataset first. See data/README.md"
        )

    train_ds = tf.keras.utils.image_dataset_from_directory(
        DATA_DIR,
        validation_split=0.2,
        subset="training",
        seed=42,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        label_mode="int",
    )

    val_ds = tf.keras.utils.image_dataset_from_directory(
        DATA_DIR,
        validation_split=0.2,
        subset="validation",
        seed=42,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        label_mode="int",
    )

    # Verify detected classes match our expectations
    detected = train_ds.class_names
    print(f"📋 Detected classes: {detected}")
    if detected != RICE_CLASSES:
        print(f"⚠️  WARNING: Detected classes don't match expected order!")
        print(f"   Expected: {RICE_CLASSES}")
        print(f"   Got:      {detected}")
        print(f"   The labels file will use the DETECTED order.")

    # Performance optimizations: cache, shuffle, prefetch
    AUTOTUNE = tf.data.AUTOTUNE
    train_ds = train_ds.cache().shuffle(1000).prefetch(buffer_size=AUTOTUNE)
    val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)

    return train_ds, val_ds, detected


def build_model(num_classes: int):
    """
    Build MobileNetV2 with normalization BAKED INTO the graph.

    This is the single most critical design decision:
    - Input pixels: [0, 255] float32
    - Rescaling layer normalizes to [0, 1] inside the graph
    - Flutter can feed raw pixel values with zero preprocessing
    - Eliminates train/serve skew bugs entirely

    Returns:
        model: The compiled Keras model
        base_model: The MobileNetV2 backbone (for fine-tuning control)
    """
    # Data augmentation block (only active during training)
    data_augmentation = tf.keras.Sequential([
        layers.RandomFlip("horizontal"),
        layers.RandomRotation(0.15),
        layers.RandomZoom(0.1),
        layers.RandomContrast(0.1),
    ], name="data_augmentation")

    # Load MobileNetV2 pretrained on ImageNet (without classifier head)
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=(224, 224, 3),
        include_top=False,
        weights="imagenet",
    )
    base_model.trainable = False  # Freeze for initial head training

    # Build the full model with normalization baked in
    inputs = tf.keras.Input(shape=(224, 224, 3), name="input_image")

    # CRITICAL: Bake [0,255] → [0,1] normalization into the graph
    x = layers.Rescaling(1.0 / 255.0, name="normalization")(inputs)
    x = data_augmentation(x)
    x = base_model(x, training=False)
    x = layers.GlobalAveragePooling2D(name="global_avg_pool")(x)
    x = layers.Dropout(0.3, name="dropout")(x)
    outputs = layers.Dense(
        num_classes, activation="softmax", name="predictions"
    )(x)

    model = models.Model(inputs, outputs, name="rice_expert_v1")
    return model, base_model


def export_to_tflite(model, class_names):
    """
    Export Keras model to TFLite with Float16 quantization.

    Float16 quantization provides:
    - ~2x model size reduction vs float32
    - Negligible accuracy loss (<0.5%)
    - Compatible with all mobile devices (CPU fallback automatic)
    """
    print("\n📦 Converting to TFLite with Float16 quantization...")
    converter = tf.lite.TFLiteConverter.from_keras_model(model)

    # Float16 quantization: good balance of size vs accuracy
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_types = [tf.float16]

    tflite_model = converter.convert()

    with open(OUTPUT_TFLITE, "wb") as f:
        f.write(tflite_model)

    size_mb = len(tflite_model) / 1024 / 1024
    print(f"✅ TFLite model saved: {OUTPUT_TFLITE} ({size_mb:.1f} MB)")

    # Save labels file for Flutter (one class per line)
    with open(OUTPUT_LABELS, "w") as f:
        for cls in class_names:
            f.write(f"{cls}\n")
    print(f"🏷️  Labels saved: {OUTPUT_LABELS}")

    return tflite_model


def verify_tflite(tflite_path):
    """
    Verify the exported TFLite model:
    1. Check input/output tensor shapes and dtypes
    2. Run inference on dummy data
    3. Confirm softmax output sums to ~1.0
    """
    print(f"\n🧪 Verifying TFLite model: {tflite_path}")

    interpreter = tf.lite.Interpreter(model_path=tflite_path)
    interpreter.allocate_tensors()

    inp_details = interpreter.get_input_details()[0]
    out_details = interpreter.get_output_details()[0]

    print(f"   Input:  shape={inp_details['shape']}, dtype={inp_details['dtype']}")
    print(f"   Output: shape={out_details['shape']}, dtype={out_details['dtype']}")

    # Run inference with dummy [0, 255] pixel data
    dummy_input = np.random.randint(0, 255, (1, 224, 224, 3)).astype(np.float32)
    interpreter.set_tensor(inp_details["index"], dummy_input)
    interpreter.invoke()
    probs = interpreter.get_tensor(out_details["index"])[0]

    prob_sum = float(np.sum(probs))
    print(f"   Probabilities: {[f'{p:.4f}' for p in probs]}")
    print(f"   Sum of probs:  {prob_sum:.4f} (should be ~1.0)")

    if abs(prob_sum - 1.0) > 0.01:
        print("   ⚠️  WARNING: Probability sum deviates from 1.0!")
    else:
        print("   ✅ TFLite verification passed!")


def train():
    """Main training pipeline."""
    print("=" * 60)
    print("🌾 KisanSetu Rice Expert — Phase 1 Training Pipeline")
    print("=" * 60)

    # ─── Step 1: Load Data ──────────────────────────────────────────────
    train_ds, val_ds, detected_classes = build_datasets()
    num_classes = len(detected_classes)
    print(f"\n📊 Training {num_classes}-class rice disease classifier\n")

    # ─── Step 2: Build Model ────────────────────────────────────────────
    model, base_model = build_model(num_classes)
    model.summary()

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    # ─── Step 3: Phase A — Train classifier head (backbone frozen) ──────
    print(f"\n🔒 Phase A: Training classifier head ({EPOCHS_HEAD} epochs, backbone frozen)...")
    early_stop = callbacks.EarlyStopping(
        monitor="val_accuracy",
        patience=5,
        restore_best_weights=True,
        verbose=1,
    )

    history_a = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS_HEAD,
        callbacks=[early_stop],
    )

    best_val_acc_a = max(history_a.history["val_accuracy"])
    print(f"📈 Phase A best val_accuracy: {best_val_acc_a:.4f}")

    # ─── Step 4: Phase B — Fine-tune top backbone layers ────────────────
    print(f"\n🔓 Phase B: Fine-tuning top backbone layers ({EPOCHS_FINETUNE} epochs)...")
    print(f"   Unfreezing layers {FINE_TUNE_AT_LAYER}+ of {len(base_model.layers)} total")

    base_model.trainable = True
    for layer in base_model.layers[:FINE_TUNE_AT_LAYER]:
        layer.trainable = False

    # Use a lower learning rate for fine-tuning (1/10th)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE / 10),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    history_b = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS_FINETUNE,
        callbacks=[early_stop],
    )

    best_val_acc_b = max(history_b.history["val_accuracy"])
    print(f"📈 Phase B best val_accuracy: {best_val_acc_b:.4f}")

    # ─── Step 5: Save Keras model ───────────────────────────────────────
    model.save(OUTPUT_H5)
    print(f"\n💾 Keras model saved: {OUTPUT_H5}")

    # ─── Step 6: Export to TFLite ───────────────────────────────────────
    export_to_tflite(model, detected_classes)

    # ─── Step 7: Verify TFLite ──────────────────────────────────────────
    verify_tflite(OUTPUT_TFLITE)

    # ─── Summary ────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("🎯 TRAINING COMPLETE — SUMMARY")
    print("=" * 60)
    print(f"   Classes:          {detected_classes}")
    print(f"   Phase A accuracy: {best_val_acc_a:.4f}")
    print(f"   Phase B accuracy: {best_val_acc_b:.4f}")
    print(f"   Keras model:      {OUTPUT_H5}")
    print(f"   TFLite model:     {OUTPUT_TFLITE}")
    print(f"   Labels file:      {OUTPUT_LABELS}")
    print(f"\n   Next step: Copy {OUTPUT_TFLITE} and {OUTPUT_LABELS}")
    print(f"   to app/assets/models/ and app/assets/labels/")
    print("=" * 60)


if __name__ == "__main__":
    train()
