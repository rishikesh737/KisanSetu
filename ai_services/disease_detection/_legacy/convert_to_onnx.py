import tensorflow as tf
import tf2onnx

print("Loading .h5 model...")
# Load the model
model = tf.keras.models.load_model("kisansetu_v38_full.h5")

print("Tracing the raw TF graph to bypass Keras 3 bugs...")


# Trace the model into a raw TensorFlow graph
@tf.function(
    input_signature=[tf.TensorSpec(shape=[None, 224, 224, 3], dtype=tf.float32)]
)
def model_predict(inputs):
    return model(inputs)


print("Converting to ONNX format (this may take a minute)...")
output_path = "kisansetu_v38.onnx"

# Convert from the raw function instead of the Keras object
model_proto, _ = tf2onnx.convert.from_function(
    model_predict,
    input_signature=[tf.TensorSpec(shape=[None, 224, 224, 3], dtype=tf.float32)],
    opset=13,
    output_path=output_path,
)

print(f"✅ Success! Model saved as {output_path}")
