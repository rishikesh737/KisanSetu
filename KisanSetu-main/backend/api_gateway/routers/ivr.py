from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Form, File, UploadFile
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime
import uuid
import json
import os

router = APIRouter()

# IVR Call States
IVR_STATES = {
    "WELCOME": "welcome",
    "LANGUAGE_SELECT": "language_select",
    "MAIN_MENU": "main_menu",
    "DISEASE_SCAN": "disease_scan",
    "AWAITING_IMAGE": "awaiting_image",
    "MARKET_PRICES": "market_prices",
    "WEATHER_INFO": "weather_info",
    "RESULTS": "results",
    "GOODBYE": "goodbye"
}

LANGUAGES = {
    "1": {"code": "hi", "name": "Hindi", "tts_voice": "hi-IN-Standard-A"},
    "2": {"code": "en", "name": "English", "tts_voice": "en-US-Standard-A"}
}

MENU_OPTIONS = {
    "hi": {
        "welcome": "नमस्ते! किसान सेतु IVR सेवा में आपका स्वागत है। राष्ट्रीय भाषा के लिए 1 दबाएं, अंग्रेजी के लिए 2 दबाएं।",
        "language_selected": "आपने {lang} चुना है।",
        "main_menu": "मुख्य मेन्यू में आपका स्वागत है। रोग पहचान के लिए 1 दबाएं। मंडी भाव जानने के लिए 2 दबाएं। मौसम जानने के लिए 3 दबाएं। बाहर निकलने के लिए 9 दबाएं।",
        "disease_scan_intro": "रोग पहचान सेवा में आपका स्वागत है। कृपया अपने फसल की पत्ती की फोटो खींचें और भेजें। फोटो भेजने के बाद हम आपको रोग की जानकारी देंगे।",
        "receiving_image": "हम आपकी छवि प्राप्त कर रहे हैं। कृपया प्रतीक्षा करें।",
        "processing": "हम रोग का विश्लेषण कर रहे हैं। कृपया प्रतीक्षा करें।",
        "disease_result": "आपके पौधे में {disease} पाया गया। इसकी पुष्टि {confidence} प्रतिशत है। उपचार के लिए सलाह: {advice}",
        "no_disease": "बहुत बढ़िया! आपका पौधा स्वस्थ है। कोई रोग नहीं पाया गया।",
        "market_menu": "मंडी भाव जानने के लिए अपने जिले का नाम बोलें।",
        "weather_menu": "मौसम जानने के लिए अपने जिले का नाम बोलें।",
        "goodbye": "धन्यवाद! किसान सेतु सेवा का उपयोग करने के लिए धन्यवाद। जल्द मिलते हैं।",
        "invalid_option": "अमान्य विकल्प। कृपया सही बटन दबाएं।",
        "error": "कुछ त्रुटि हो गई। कृपया पुनः प्रयास करें।"
    },
    "en": {
        "welcome": "Namaste! Welcome to KisanSetu IVR service. Press 1 for Hindi, 2 for English.",
        "language_selected": "You have selected {lang}.",
        "main_menu": "Welcome to main menu. Press 1 for disease detection. Press 2 for market prices. Press 3 for weather information. Press 9 to exit.",
        "disease_scan_intro": "Welcome to disease detection service. Please take a photo of your crop leaf and send it. After sending the photo, we will provide disease information.",
        "receiving_image": "We are receiving your image. Please wait.",
        "processing": "We are analyzing the disease. Please wait.",
        "disease_result": "Your plant has {disease}. Confidence is {confidence} percent. Treatment advice: {advice}",
        "no_disease": "Great! Your plant is healthy. No disease detected.",
        "market_menu": "Speak your district name to know market prices.",
        "weather_menu": "Speak your district name to know weather information.",
        "goodbye": "Thank you! Thanks for using KisanSetu service. Goodbye.",
        "invalid_option": "Invalid option. Please press the correct button.",
        "error": "Some error occurred. Please try again."
    }
}

# Disease advice in Hindi and English
DISEASE_ADVICE = {
    "Apple___Apple_scab": {"hi": "फलों को हटाएं और नियंत्रित करें। कवकनाशी का उपयोग करें।", "en": "Remove infected fruits and control. Use fungicide."},
    "Apple___Black_rot": {"hi": "संक्रमित शाखाओं को काटें। कवकनाशी स्प्रे करें।", "en": "Prune infected branches. Apply fungicide spray."},
    "Apple___Cedar_apple_rust": {"hi": "प्रभावित पत्तियों को हटाएं। कवकनाशी का उपयोग करें।", "en": "Remove affected leaves. Use fungicide."},
    "Apple___healthy": {"hi": "पेड़ स्वस्थ है। नियमित रखरखाव जारी रखें।", "en": "Tree is healthy. Continue regular maintenance."},
    "Tomato___Late_blight": {"hi": "फफूंदनाशी का उपयोग करें। प्रभावित पौधों को हटाएं।", "en": "Use fungicide. Remove affected plants."},
    "Tomato___Early_blight": {"hi": "पत्तियों को हटाएं और कवकनाशी लगाएं।", "en": "Remove leaves and apply fungicide."},
    "Potato___Late_blight": {"hi": "फफूंदनाशी स्प्रे करें। नियंत्रण उपाय करें।", "en": "Apply fungicide spray. Take control measures."},
    "Potato___Early_blight": {"hi": "कवकनाशी का उपयोग करें। सिंचाई नियंत्रित करें।", "en": "Use fungicide. Control irrigation."},
    "default": {"hi": "कृपया स्थानीय कृषि विशेषज्ञ से संपर्क करें।", "en": "Please contact local agricultural expert."}
}

# In-memory call state storage (use Redis in production)
active_calls: Dict[str, dict] = {}


class IVRRequest(BaseModel):
    call_sid: str
    from_number: str
    digits: Optional[str] = None
    audio_url: Optional[str] = None


class IVRResponse(BaseModel):
    response_xml: str
    call_sid: str


class DiseaseScanRequest(BaseModel):
    call_sid: str
    image_data: str  # Base64 encoded


@router.get("/health")
async def ivr_health():
    """Health check for IVR service"""
    return {"status": "healthy", "service": "IVR Engine"}


@router.post("/callback")
async def ivr_callback(
    CallSid: str = Query(...),
    From: str = Query(...),
    Digits: Optional[str] = Query(None),
    AudioUrl: Optional[str] = Query(None)
):
    """
    Main IVR callback endpoint - handles incoming calls and user inputs
    """
    call_sid = CallSid
    user_input = Digits
    audio_url = AudioUrl

    # Initialize or retrieve call state
    if call_sid not in active_calls:
        active_calls[call_sid] = {
            "call_sid": call_sid,
            "from_number": From,
            "language": "hi",
            "state": IVR_STATES["WELCOME"],
            "session_data": {},
            "created_at": datetime.utcnow()
        }

    call_state = active_calls[call_sid]
    language = call_state["language"]

    # Route based on current state
    response = handle_ivr_flow(call_state, user_input, audio_url, language)

    return response


def handle_ivr_flow(call_state: dict, digits: Optional[str], audio_url: Optional[str], language: str) -> dict:
    """Main IVR flow handler"""
    current_state = call_state["state"]

    # Handle different states
    if current_state == IVR_STATES["WELCOME"]:
        return generate_tts_response(
            MENU_OPTIONS[language]["welcome"],
            next_state=IVR_STATES["LANGUAGE_SELECT"],
            call_state=call_state
        )

    elif current_state == IVR_STATES["LANGUAGE_SELECT"]:
        if digits and digits in LANGUAGES:
            call_state["language"] = LANGUAGES[digits]["code"]
            lang_name = LANGUAGES[digits]["name"]
            return generate_tts_response(
                MENU_OPTIONS[call_state["language"]]["language_selected"].format(lang=lang_name),
                next_state=IVR_STATES["MAIN_MENU"],
                call_state=call_state
            )
        else:
            return generate_tts_response(
                MENU_OPTIONS[language]["invalid_option"],
                next_state=IVR_STATES["WELCOME"],
                call_state=call_state
            )

    elif current_state == IVR_STATES["MAIN_MENU"]:
        if digits == "1":
            return generate_tts_response(
                MENU_OPTIONS[language]["disease_scan_intro"],
                next_state=IVR_STATES["AWAITING_IMAGE"],
                call_state=call_state,
                record=True
            )
        elif digits == "2":
            return generate_tts_response(
                MENU_OPTIONS[language]["market_menu"],
                next_state=IVR_STATES["MARKET_PRICES"],
                call_state=call_state
            )
        elif digits == "3":
            return generate_tts_response(
                MENU_OPTIONS[language]["weather_menu"],
                next_state=IVR_STATES["WEATHER_INFO"],
                call_state=call_state
            )
        elif digits == "9":
            return generate_tts_response(
                MENU_OPTIONS[language]["goodbye"],
                next_state=IVR_STATES["GOODBYE"],
                call_state=call_state,
                end_call=True
            )
        else:
            return generate_tts_response(
                MENU_OPTIONS[language]["invalid_option"],
                next_state=IVR_STATES["MAIN_MENU"],
                call_state=call_state
            )

    elif current_state == IVR_STATES["AWAITING_IMAGE"]:
        # When user sends image via MMS
        if audio_url or digits == "#":
            return generate_tts_response(
                MENU_OPTIONS[language]["processing"],
                next_state=IVR_STATES["RESULTS"],
                call_state=call_state
            )

    elif current_state == IVR_STATES["RESULTS"]:
        # Disease detection results would be played here
        return generate_tts_response(
            MENU_OPTIONS[language]["main_menu"],
            next_state=IVR_STATES["MAIN_MENU"],
            call_state=call_state
        )

    return generate_tts_response(
        MENU_OPTIONS[language]["error"],
        next_state=IVR_STATES["WELCOME"],
        call_state=call_state
    )


def generate_tts_response(
    message: str,
    next_state: str,
    call_state: dict,
    record: bool = False,
    end_call: bool = False
) -> dict:
    """Generate TwiML response with TTS"""

    twiml_elements = []

    # Add TTS
    twiml_elements.append(f'<Say language="{call_state["language"]}">{message}</Say>')

    # Record if needed
    if record:
        twiml_elements.append('<Record action="/api/v1/ivr/recordings" method="POST" maxLength="30" />')

    # If not ending call, gather next input
    if not end_call:
        twiml_elements.append(f'<Gather numDigits="1" action="/api/v1/ivr/callback" method="POST">')
        twiml_elements.append(f'<Say language="{call_state["language"]}">{message}</Say>')
        twiml_elements.append('</Gather>')
    else:
        twiml_elements.append('<Hangup />')

    # Update state
    call_state["state"] = next_state
    active_calls[call_state["call_sid"]] = call_state

    return {
        "response_xml": f'<?xml version="1.0" encoding="UTF-8"?><Response>{"".join(twiml_elements)}</Response>',
        "call_sid": call_state["call_sid"],
        "message": message
    }


@router.post("/incoming-call")
async def handle_incoming_call(
    CallSid: str = Form(...),
    From: str = Form(...)
):
    """Initial webhook for incoming Twilio calls"""
    call_sid = CallSid

    # Initialize new call
    active_calls[call_sid] = {
        "call_sid": call_sid,
        "from_number": From,
        "language": "hi",
        "state": IVR_STATES["WELCOME"],
        "session_data": {},
        "created_at": datetime.utcnow()
    }

    # Return TwiML with welcome message
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="hi-IN">नमस्ते! किसान सेतु IVR सेवा में आपका स्वागत है। राष्ट्रीय भाषा के लिए 1 दबाएं, अंग्रेजी के लिए 2 दबाएं।</Say>
    <Gather numDigits="1" action="/api/v1/ivr/callback" method="POST">
        <Say language="hi-IN">नमस्ते! किसान सेतु IVR सेवा में आपका स्वागत है। राष्ट्रीय भाषा के लिए 1 दबाएं, अंग्रेजी के लिए 2 दबाएं।</Say>
    </Gather>
</Response>'''

    return {"content": twiml, "content_type": "text/xml"}


@router.post("/gather-input")
async def gather_input(
    CallSid: str = Form(...),
    Digits: str = Form(...),
    From: str = Form(...)
):
    """Handle DTMF input from Twilio Gather"""

    if CallSid not in active_calls:
        # New call, redirect to welcome
        return {"content": get_goodbye_twiml(), "content_type": "text/xml"}

    call_state = active_calls[CallSid]
    language = call_state["language"]
    digits = Digits
    current_state = call_state["state"]

    # Process input based on current state
    if current_state == IVR_STATES["LANGUAGE_SELECT"]:
        if digits in LANGUAGES:
            call_state["language"] = LANGUAGES[digits]["code"]
            lang_name = LANGUAGES[digits]["name"]
            call_state["state"] = IVR_STATES["MAIN_MENU"]

            response_text = MENU_OPTIONS[call_state["language"]]["language_selected"].format(lang=lang_name) + " " + MENU_OPTIONS[call_state["language"]]["main_menu"]

            twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather numDigits="1" action="/api/v1/ivr/gather-input" method="POST">
        <Say language="{get_twiml_lang(call_state['language'])}">{response_text}</Say>
    </Gather>
</Response>'''
            return {"content": twiml, "content_type": "text/xml"}

    elif current_state == IVR_STATES["MAIN_MENU"]:
        if digits == "1":
            call_state["state"] = IVR_STATES["DISEASE_SCAN"]
            response_text = MENU_OPTIONS[language]["disease_scan_intro"]
        elif digits == "2":
            call_state["state"] = IVR_STATES["MARKET_PRICES"]
            response_text = MENU_OPTIONS[language]["market_menu"]
        elif digits == "3":
            call_state["state"] = IVR_STATES["WEATHER_INFO"]
            response_text = MENU_OPTIONS[language]["weather_menu"]
        elif digits == "9":
            return {"content": get_goodbye_twiml(language), "content_type": "text/xml"}
        else:
            response_text = MENU_OPTIONS[language]["invalid_option"] + " " + MENU_OPTIONS[language]["main_menu"]

        twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather numDigits="1" action="/api/v1/ivr/gather-input" method="POST">
        <Say language="{get_twiml_lang(language)}">{response_text}</Say>
    </Gather>
</Response>'''
        return {"content": twiml, "content_type": "text/xml"}

    elif current_state in [IVR_STATES["MARKET_PRICES"], IVR_STATES["WEATHER_INFO"]]:
        # Store the district name from DTMF
        call_state["session_data"]["district"] = digits
        call_state["state"] = IVR_STATES["MAIN_MENU"]
        response_text = MENU_OPTIONS[language]["main_menu"]

        twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather numDigits="1" action="/api/v1/ivr/gather-input" method="POST">
        <Say language="{get_twiml_lang(language)}">{response_text}</Say>
    </Gather>
</Response>'''
        return {"content": twiml, "content_type": "text/xml"}

    return {"content": get_goodbye_twiml(language), "content_type": "text/xml"}


def get_twiml_lang(language: str) -> str:
    """Map internal language code to TwiML language"""
    return "hi-IN" if language == "hi" else "en-US"


def get_goodbye_twiml(language: str = "hi") -> str:
    """Generate goodbye TwiML"""
    goodbye_msg = MENU_OPTIONS[language]["goodbye"]
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="{get_twiml_lang(language)}">{goodbye_msg}</Say>
    <Hangup />
</Response>'''


@router.post("/mms-receive")
async def receive_mms_image(
    CallSid: str = Form(...),
    From: str = Form(...),
    MediaUrl: str = Form(...)
):
    """Handle incoming MMS with images for disease detection"""

    if CallSid not in active_calls:
        raise HTTPException(status_code=400, detail="No active call found")

    call_state = active_calls[CallSid]
    language = call_state["language"]

    # Store the image URL for processing
    call_state["session_data"]["image_url"] = MediaUrl
    call_state["state"] = IVR_STATES["RESULTS"]

    # In production, trigger async disease detection here
    # For now, return processing message

    response_text = MENU_OPTIONS[language]["processing"]

    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="{get_twiml_lang(language)}">{response_text}</Say>
    <Gather numDigits="1" action="/api/v1/ivr/gather-input" method="POST">
        <Say language="{get_twiml_lang(language)}">{MENU_OPTIONS[language]['main_menu']}</Say>
    </Gather>
</Response>'''

    return {"content": twiml, "content_type": "text/xml"}


@router.post("/scan-image")
async def scan_image_for_disease(
    call_sid: str = Form(...),
    image_url: str = Form(...)
):
    """
    Endpoint to trigger disease scan using the image URL
    Integrates with the disease detection service
    """
    if call_sid not in active_calls:
        raise HTTPException(status_code=400, detail="No active call found")

    call_state = active_calls[call_sid]
    language = call_state["language"]

    # Download image from URL and run disease detection
    # In production, this would call the disease detection service
    # For now, return the structure

    # This would typically call: POST /api/v1/disease/predict with the image
    return {
        "status": "processing",
        "call_sid": call_sid,
        "message": "Disease detection initiated"
    }


@router.get("/call-status/{call_sid}")
async def get_call_status(call_sid: str):
    """Get the current status of an IVR call"""
    if call_sid not in active_calls:
        raise HTTPException(status_code=404, detail="Call not found")

    return active_calls[call_sid]


@router.post("/call-end")
async def call_ended(
    CallSid: str = Form(...),
    CallStatus: str = Form(...)
):
    """Handle call termination"""
    if CallSid in active_calls:
        call_state = active_calls[CallSid]
        call_state["status"] = CallStatus
        call_state["ended_at"] = datetime.utcnow()
        # Keep for records, don't delete immediately

    return {"status": "recorded"}


@router.post("/test-tts")
async def test_tts(
    message: str = Form(...),
    language: str = Form("hi")
):
    """Test TTS endpoint"""
    return {
        "twiml": f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="{get_twiml_lang(language)}">{message}</Say>
</Response>''',
        "language": language
    }


# ==================== DISEASE DETECTION INTEGRATION ====================

@router.post("/disease/analyze")
async def analyze_disease_from_ivr(
    call_sid: str = Form(...),
    image_data: str = Form(...)  # Base64 encoded image
):
    """
    Analyze image for disease from IVR flow
    Returns both JSON result and generates TTS response
    """
    import base64
    import requests

    if call_sid not in active_calls:
        raise HTTPException(status_code=400, detail="No active call found")

    call_state = active_calls[call_sid]
    language = call_state["language"]

    try:
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)

        # Call disease detection API
        # In production, this would be the actual endpoint
        files = {"file": ("image.jpg", image_bytes, "image/jpeg")}

        # This is a placeholder - actual call would be:
        # response = requests.post("http://disease-service:8001/api/v1/disease/predict", files=files)

        # For now, return mock result structure
        mock_result = {
            "class_id": 0,
            "disease_name": "Tomato___healthy",
            "confidence": 0.95,
            "message": "Analysis complete"
        }

        # Generate TTS response based on result
        tts_response = generate_disease_result_tts(mock_result, language)

        return {
            "disease_result": mock_result,
            "tts_response": tts_response,
            "call_sid": call_sid
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Disease analysis failed: {str(e)}")


def generate_disease_result_tts(result: dict, language: str) -> str:
    """Generate TTS message for disease result"""

    disease_name = result.get("disease_name", "")
    confidence = int(result.get("confidence", 0) * 100)

    # Check if healthy
    if "healthy" in disease_name.lower():
        return MENU_OPTIONS[language]["no_disease"]

    # Get disease name without the prefix
    disease_display = disease_name.split("___")[-1].replace("_", " ")

    # Get advice
    advice = DISEASE_ADVICE.get(disease_name, DISEASE_ADVICE["default"])[language]

    return MENU_OPTIONS[language]["disease_result"].format(
        disease=disease_display,
        confidence=confidence,
        advice=advice
    )