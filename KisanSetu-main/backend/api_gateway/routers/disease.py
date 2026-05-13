from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
import numpy as np
from PIL import Image
import io
import os

router = APIRouter()

# Model loading with fallback
MODEL_PATH = "assets/models/kisansetu_v38.tflite"
interpreter = None
input_details = None
output_details = None
model_loaded = False

try:
    # Try TensorFlow 2.x native lite interpreter
    import tensorflow as tf
    interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    model_loaded = True
    print("[OK] TFLite Model Loaded Successfully")
except Exception as e:
    print(f"[!] TF Lite failed: {e}")
    # Try ONNX runtime as fallback
    try:
        import onnxruntime as ort
        sess = ort.InferenceSession(MODEL_PATH.replace('.tflite', '.onnx'), providers=['CPUExecutionProvider'])
        model_loaded = "onnx"
        print("[OK] ONNX Model loaded")
    except:
        # Try using numpy-based fallback (simulated predictions)
        print("[!] Running in SIMULATION mode (no ML model)")
        model_loaded = "simulated"


# 2. Define Response Schema
class DiseaseResponse(BaseModel):
    class_id: int
    disease_name: str
    confidence: float
    message: str


CLASS_NAMES = [
    "Apple___Apple_scab",
    "Apple___Black_rot",
    "Apple___Cedar_apple_rust",
    "Apple___healthy",
    "Blueberry___healthy",
    "Cherry_(including_sour)___Powdery_mildew",
    "Cherry_(including_sour)___healthy",
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
    "Corn_(maize)___Common_rust_",
    "Corn_(maize)___Northern_Leaf_Blight",
    "Corn_(maize)___healthy",
    "Grape___Black_rot",
    "Grape___Esca_(Black_Measles)",
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)",
    "Grape___healthy",
    "Orange___Haunglongbing_(Citrus_greening)",
    "Peach___Bacterial_spot",
    "Peach___healthy",
    "Pepper,_bell___Bacterial_spot",
    "Pepper,_bell___healthy",
    "Potato___Early_blight",
    "Potato___Late_blight",
    "Potato___healthy",
    "Raspberry___healthy",
    "Soybean___healthy",
    "Squash___Powdery_mildew",
    "Strawberry___Leaf_scorch",
    "Strawberry___healthy",
    "Tomato___Bacterial_spot",
    "Tomato___Early_blight",
    "Tomato___Late_blight",
    "Tomato___Leaf_Mold",
    "Tomato___Septoria_leaf_spot",
    "Tomato___Spider_mites Two-spotted_spider_mite",
    "Tomato___Target_Spot",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato___Tomato_mosaic_virus",
    "Tomato___healthy",
]


def process_image(image_bytes: bytes) -> np.ndarray:
    """Prepares the image exactly how MobileNetV2 expects it."""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image = image.resize((224, 224))
    img_array = np.array(image, dtype=np.float32)
    img_array = np.expand_dims(img_array, axis=0)

    # MobileNetV2 specific preprocessing (scaling between -1 and 1)
    img_array = (img_array / 127.5) - 1.0
    return img_array


@router.post("/predict", response_model=DiseaseResponse)
async def predict_disease(file: UploadFile = File(...)):
    """
    Receives a crop leaf image from the Flutter app and returns the disease diagnosis.
    """
    global model_loaded, interpreter

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File provided is not an image.")

    try:
        # Read and preprocess the image
        contents = await file.read()
        input_data = process_image(contents)

        # Handle different model states
        if model_loaded == "simulated" or model_loaded == False:
            # SIMULATION MODE - analyze image color to give pseudo-result
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(contents))
            img = img.resize((50, 50))
            arr = np.array(img)

            # Simple color-based heuristic
            avg_green = np.mean(arr[:,:,1])
            avg_red = np.mean(arr[:,:,0])
            avg_blue = np.mean(arr[:,:,2])

            # If green dominant -> likely healthy
            if avg_green > avg_red and avg_green > avg_blue:
                class_id = 21  # Potato___healthy
                disease = "Potato___healthy"
            elif avg_red > avg_green * 1.5:
                class_id = 67  # Tomato___Late_blight
                disease = "Tomato___Late_blight"
            else:
                class_id = 37  # Grape___healthy
                disease = "Grape___healthy"

            return DiseaseResponse(
                class_id=class_id,
                disease_name=disease,
                confidence=0.78,
                message="Analysis based on image colors (demo mode). For accurate results, fix the ML model.",
            )

        elif model_loaded == "onnx":
            # ONNX inference
            import onnxruntime as ort
            sess = ort.InferenceSession(MODEL_PATH.replace('.tflite', '.onnx'))
            output = sess.run(None, {"input": input_data})[0]
            class_id = int(np.argmax(output))
            confidence = float(output[0][class_id])
            return DiseaseResponse(
                class_id=class_id,
                confidence=confidence,
                message="ONNX inference completed.",
            )

        else:
            # TFLite inference
            interpreter.set_tensor(input_details[0]["index"], input_data)
            interpreter.invoke()
            output_data = interpreter.get_tensor(output_details[0]["index"])[0]
            class_id = int(np.argmax(output_data))
            confidence = float(output_data[class_id])
            return DiseaseResponse(
                class_id=class_id,
                confidence=confidence,
                message="TFLite inference completed successfully.",
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
