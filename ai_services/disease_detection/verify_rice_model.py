"""
KisanSetu: Rice Expert TFLite Model Verifier
=============================================
Standalone post-training verification script.

Performs:
  1. Loads the exported .tflite file
  2. Prints input/output tensor shapes and dtypes
  3. Runs inference on a random test image from the dataset
  4. Confirms softmax probabilities sum to ~1.0
  5. Prints the predicted class and confidence

Usage:
  python verify_rice_model.py
  python verify_rice_model.py --model path/to/model.tflite
  python verify_rice_model.py --image path/to/test_image.jpg
"""

import argparse
import os
import random
import sys

import numpy as np

# Suppress TF info logs for cleaner output
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
import tensorflow as tf
from PIL import Image


# ─── Configuration ──────────────────────────────────────────────────────────
DEFAULT_MODEL = "rice_expert_v1.tflite"
DEFAULT_LABELS = "rice_labels.txt"
DATA_DIR = "data/rice"
IMG_SIZE = (224, 224)


def load_labels(labels_path):
    """Load class labels from the labels file."""
    if not os.path.isfile(labels_path):
        print(f"❌ Labels file not found: {labels_path}")
        sys.exit(1)

    with open(labels_path, "r") as f:
        labels = [line.strip() for line in f.readlines() if line.strip()]

    print(f"🏷️  Loaded {len(labels)} class labels: {labels}")
    return labels


def load_random_test_image():
    """Pick a random image from the dataset for testing."""
    if not os.path.isdir(DATA_DIR):
        return None, None

    class_dirs = [
        d for d in sorted(os.listdir(DATA_DIR))
        if os.path.isdir(os.path.join(DATA_DIR, d)) and not d.startswith(".")
    ]

    if not class_dirs:
        return None, None

    # Pick a random class, then a random image from it
    random_class = random.choice(class_dirs)
    class_path = os.path.join(DATA_DIR, random_class)

    images = [
        f for f in os.listdir(class_path)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]

    if not images:
        return None, None

    random_image = random.choice(images)
    image_path = os.path.join(class_path, random_image)

    return image_path, random_class


def preprocess_image(image_path):
    """
    Load and preprocess an image for inference.

    Returns raw [0, 255] float32 values since normalization
    is baked into the TFLite model's Rescaling layer.
    """
    image = Image.open(image_path).convert("RGB")
    image = image.resize(IMG_SIZE)
    img_array = np.array(image, dtype=np.float32)
    # Add batch dimension: (224, 224, 3) → (1, 224, 224, 3)
    img_array = np.expand_dims(img_array, axis=0)
    return img_array


def run_verification(model_path, labels_path, image_path=None):
    """Run the full verification pipeline."""
    print("=" * 60)
    print("🧪 KisanSetu Rice Expert — TFLite Verification")
    print("=" * 60)

    # ─── Step 1: Load Labels ────────────────────────────────────────────
    labels = load_labels(labels_path)

    # ─── Step 2: Load TFLite Model ──────────────────────────────────────
    if not os.path.isfile(model_path):
        print(f"❌ Model file not found: {model_path}")
        print("   Run train_rice_expert.py first to generate the model.")
        sys.exit(1)

    model_size_mb = os.path.getsize(model_path) / 1024 / 1024
    print(f"\n📦 Loading model: {model_path} ({model_size_mb:.1f} MB)")

    interpreter = tf.lite.Interpreter(model_path=model_path)
    interpreter.allocate_tensors()

    inp_details = interpreter.get_input_details()[0]
    out_details = interpreter.get_output_details()[0]

    print(f"   Input tensor:  shape={inp_details['shape']}, dtype={inp_details['dtype']}")
    print(f"   Output tensor: shape={out_details['shape']}, dtype={out_details['dtype']}")

    # Validate expected shapes
    expected_input = [1, 224, 224, 3]
    expected_output = [1, len(labels)]
    if list(inp_details["shape"]) != expected_input:
        print(f"   ⚠️  Input shape mismatch! Expected {expected_input}")
    if list(out_details["shape"]) != expected_output:
        print(f"   ⚠️  Output shape mismatch! Expected {expected_output}")

    # ─── Step 3: Dummy Input Sanity Check ───────────────────────────────
    print("\n🔢 Running dummy input sanity check...")
    dummy_input = np.random.randint(0, 255, (1, 224, 224, 3)).astype(np.float32)
    interpreter.set_tensor(inp_details["index"], dummy_input)
    interpreter.invoke()
    dummy_probs = interpreter.get_tensor(out_details["index"])[0]

    dummy_sum = float(np.sum(dummy_probs))
    print(f"   Dummy probabilities: {[f'{p:.4f}' for p in dummy_probs]}")
    print(f"   Sum: {dummy_sum:.4f} (expected: ~1.0)")

    if abs(dummy_sum - 1.0) > 0.05:
        print("   ❌ FAIL: Probability sum is too far from 1.0!")
        return False
    else:
        print("   ✅ PASS: Softmax output is valid")

    # ─── Step 4: Real Image Inference ───────────────────────────────────
    actual_label = None

    if image_path is None:
        # Try to find a random image from the dataset
        image_path, actual_label = load_random_test_image()

    if image_path and os.path.isfile(image_path):
        print(f"\n📸 Running inference on real image: {image_path}")
        if actual_label:
            print(f"   Actual label: {actual_label}")

        img_input = preprocess_image(image_path)
        interpreter.set_tensor(inp_details["index"], img_input)
        interpreter.invoke()
        probs = interpreter.get_tensor(out_details["index"])[0]

        # Display all predictions sorted by confidence
        print("\n   ┌─────────────────────────────────────────────┐")
        print("   │  CLASS                        CONFIDENCE    │")
        print("   ├─────────────────────────────────────────────┤")

        indexed_probs = list(enumerate(probs))
        indexed_probs.sort(key=lambda x: x[1], reverse=True)

        for idx, prob in indexed_probs:
            label = labels[idx] if idx < len(labels) else f"Unknown_{idx}"
            bar = "█" * int(prob * 30)
            marker = " ◀ TOP" if idx == indexed_probs[0][0] else ""
            print(f"   │  {label:<28} {prob*100:5.1f}% {bar}{marker}")

        print("   └─────────────────────────────────────────────┘")

        top_idx, top_prob = indexed_probs[0]
        predicted_label = labels[top_idx] if top_idx < len(labels) else f"Unknown_{top_idx}"

        print(f"\n   🤖 Prediction: {predicted_label}")
        print(f"   📊 Confidence: {top_prob * 100:.1f}%")

        if top_prob >= 0.85:
            print("   ✅ Above 85% guardrail threshold")
        else:
            print("   ⚠️  Below 85% guardrail — would show 'Scan Unclear' in app")

        if actual_label:
            if predicted_label == actual_label:
                print("   ✅ CORRECT: Prediction matches actual label!")
            else:
                print(f"   ❌ MISMATCH: Predicted '{predicted_label}' but actual is '{actual_label}'")
    else:
        print("\n📸 Skipping real image test (no dataset images found)")
        print("   To test with a real image, run:")
        print(f"   python verify_rice_model.py --image path/to/leaf.jpg")

    # ─── Summary ────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("✅ VERIFICATION COMPLETE")
    print("=" * 60)
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Verify the KisanSetu Rice Expert TFLite model"
    )
    parser.add_argument(
        "--model", type=str, default=DEFAULT_MODEL,
        help=f"Path to the .tflite model file (default: {DEFAULT_MODEL})"
    )
    parser.add_argument(
        "--labels", type=str, default=DEFAULT_LABELS,
        help=f"Path to the labels file (default: {DEFAULT_LABELS})"
    )
    parser.add_argument(
        "--image", type=str, default=None,
        help="Path to a specific image to test (optional)"
    )

    args = parser.parse_args()
    success = run_verification(args.model, args.labels, args.image)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
