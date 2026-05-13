"""
Disease Detection Service - Handles disease analysis requests from IVR
"""

from typing import Dict, Optional
import base64
import io
from PIL import Image
import numpy as np


class DiseaseDetectionService:
    """
    Service to handle disease detection requests
    Can work with local TFLite model or external API
    """

    def __init__(self, model_path: str = "assets/models/kisansetu_v38.tflite"):
        self.model_path = model_path
        self.model_loaded = False
        self.interpreter = None

    def load_model(self):
        """Load the TFLite model"""
        try:
            import tensorflow.lite as tflite
            self.interpreter = tflite.Interpreter(model_path=self.model_path)
            self.interpreter.allocate_tensors()
            self.model_loaded = True
            return True
        except Exception as e:
            print(f"Failed to load model: {e}")
            return False

    def analyze_image(
        self,
        image_data: bytes
    ) -> Dict:
        """
        Analyze image for disease detection

        Args:
            image_data: Raw image bytes

        Returns:
            Dict with disease detection results
        """
        if not self.model_loaded:
            self.load_model()

        try:
            # Preprocess image
            image = Image.open(io.BytesIO(image_data)).convert("RGB")
            image = image.resize((224, 224))
            img_array = np.array(image, dtype=np.float32)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = (img_array / 127.5) - 1.0

            # Run inference
            if self.interpreter:
                input_details = self.interpreter.get_input_details()
                output_details = self.interpreter.get_output_details()

                self.interpreter.set_tensor(input_details[0]["index"], img_array)
                self.interpreter.invoke()
                output_data = self.interpreter.get_tensor(output_details[0]["index"])[0]

                # Get prediction
                class_id = int(np.argmax(output_data))
                confidence = float(output_data[class_id])

                disease_name = self._get_disease_name(class_id)

                return {
                    "success": True,
                    "class_id": class_id,
                    "disease_name": disease_name,
                    "confidence": confidence,
                    "is_healthy": "healthy" in disease_name.lower()
                }

            return {"success": False, "error": "Model not loaded"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def analyze_base64_image(
        self,
        base64_image: str
    ) -> Dict:
        """Analyze base64 encoded image"""
        try:
            image_bytes = base64.b64decode(base64_image)
            return self.analyze_image(image_bytes)
        except Exception as e:
            return {"success": False, "error": f"Failed to decode image: {str(e)}"}

    def _get_disease_name(self, class_id: int) -> str:
        """Get disease name from class ID"""
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

        if 0 <= class_id < len(CLASS_NAMES):
            return CLASS_NAMES[class_id]
        return "Unknown"


class DiseaseAdviceGenerator:
    """Generate treatment advice for detected diseases"""

    ADVICE = {
        "Apple___Apple_scab": {
            "hi": "फलों को हटाएं और कवकनाशी का उपयोग करें। प्रूडिंग से नियंत्रण करें।",
            "en": "Remove infected fruits and use fungicide. Control through pruning."
        },
        "Apple___Black_rot": {
            "hi": "संक्रमित शाखाओं को काटें और कवकनाशी स्प्रे करें।",
            "en": "Prune infected branches and apply fungicide spray."
        },
        "Apple___Cedar_apple_rust": {
            "hi": "प्रभावित पत्तियों को हटाएं। पास के देवदार को हटाएं। कवकनाशी का उपयोग करें।",
            "en": "Remove affected leaves. Remove nearby cedar trees. Use fungicide."
        },
        "Tomato___Late_blight": {
            "hi": "तुरंत कवकनाशी का उपयोग करें। प्रभावित पौधों को हटाएं। सिंचाई कम करें।",
            "en": "Use fungicide immediately. Remove affected plants. Reduce irrigation."
        },
        "Tomato___Early_blight": {
            "hi": "पत्तियों को हटाएं और कवकनाशी लगाएं। पानी का छिड़काव नीचे से करें।",
            "en": "Remove leaves and apply fungicide. Water from below."
        },
        "Potato___Late_blight": {
            "hi": "फफूंदनाशी स्प्रे करें। कंदों को तुरंत निकालें।",
            "en": "Apply fungicide spray. Remove tubers immediately."
        },
        "Potato___Early_blight": {
            "hi": "कवकनाशी का उपयोग करें। पत्तियों को हटाएं। सिंचाई नियंत्रित करें।",
            "en": "Use fungicide. Remove leaves. Control irrigation."
        },
        "default": {
            "hi": "कृपया स्थानीय कृषि विशेषज्ञ से संपर्क करें।",
            "en": "Please contact local agricultural expert."
        }
    }

    @classmethod
    def get_advice(cls, disease_name: str, language: str = "hi") -> str:
        """Get treatment advice for disease"""
        advice_dict = cls.ADVICE.get(disease_name, cls.ADVICE["default"])
        return advice_dict.get(language, advice_dict["en"])

    @classmethod
    def generate_result_message(cls, result: Dict, language: str = "hi") -> str:
        """Generate full result message with advice"""
        if not result.get("success"):
            return "Error analyzing image" if language == "en" else "छवि विश्लेषण में त्रुटि"

        disease_name = result.get("disease_name", "")
        confidence = int(result.get("confidence", 0) * 100)

        if result.get("is_healthy"):
            if language == "hi":
                return "बहुत बढ़िया! आपका पौधा स्वस्थ है। कोई रोग नहीं पाया गया।"
            return "Great! Your plant is healthy. No disease detected."

        disease_display = disease_name.split("___")[-1].replace("_", " ")
        advice = cls.get_advice(disease_name, language)

        if language == "hi":
            return f"आपके पौधे में {disease_display} पाया गया। इसकी पुष्टि {confidence} प्रतिशत है। उपचार: {advice}"
        return f"Your plant has {disease_display}. Confidence: {confidence}%. Advice: {advice}"


# Global service instance
disease_service = DiseaseDetectionService()