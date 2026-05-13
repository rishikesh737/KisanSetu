import tensorflow as tf

print("🔄 Loading the H5 Master Chef...")
model = tf.keras.models.load_model("kisansetu_v38_full.h5")

print("📦 Converting to TensorFlow Lite format...")
converter = tf.lite.TFLiteConverter.from_keras_model(model)

# Optional: Quantize the model to make it even smaller for mobile
converter.optimizations = [tf.lite.Optimize.DEFAULT]

tflite_model = converter.convert()

with open("kisansetu_v38.tflite", "wb") as f:
    f.write(tflite_model)

print("✅ Success! 'kisansetu_v38.tflite' is ready for Flutter deployment.")
