from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
import numpy as np
from PIL import Image
import io
import tensorflow.lite as tflite
import os

router = APIRouter()

# 1. Load the TFLite Model
MODEL_PATH = "assets/models/kisansetu_v38.tflite"

try:
    interpreter = tflite.Interpreter(model_path=MODEL_PATH)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    print("✅ TFLite Model Loaded Successfully")
except Exception as e:
    print(f"⚠️ Failed to load model: {e}")


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
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File provided is not an image.")

    try:
        # Read and preprocess the image
        contents = await file.read()
        input_data = process_image(contents)

        # Run Inference
        interpreter.set_tensor(input_details[0]["index"], input_data)
        interpreter.invoke()
        output_data = interpreter.get_tensor(output_details[0]["index"])[0]

        # Get highest confidence prediction
        class_id = int(np.argmax(output_data))
        confidence = float(output_data[class_id])

        return DiseaseResponse(
            class_id=class_id,
            confidence=confidence,
            message="Inference completed successfully.",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
