"""
KisanSetu IVR Engine - Main Application
Voice Gateway for farmer phone calls
"""

import sys
import os
# Add backend to path for disease service imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "backend", "api_gateway"))

from fastapi import FastAPI, Form, Query, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime
import uuid
import base64
import io
from PIL import Image
import numpy as np

from voice_gateway import CallManager, TTSEngine, STTEngine
from voice_gateway.tts_engine import IVRPrompts, TTSProvider
from voice_gateway.stt_engine import STTProvider
from services.disease_service import disease_service, DiseaseAdviceGenerator

app = FastAPI(
    title="KisanSetu IVR Engine",
    description="Voice Gateway for KisanSetu - Handles incoming phone calls for disease detection",
    version="1.0.0"
)

# Initialize services
call_manager = CallManager()
# Use local TTS (Twilio's built-in Say) - no credentials needed
tts_engine = TTSEngine(provider=TTSProvider.LOCAL)
stt_engine = STTEngine(provider=STTProvider.GOOGLE_CLOUD)


# ==================== Health & Status ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "IVR Engine",
        "timestamp": datetime.utcnow().isoformat(),
        "active_calls": call_manager.get_active_call_count()
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "KisanSetu IVR Engine",
        "version": "1.0.0",
        "status": "running"
    }


# ==================== Twilio Webhooks ====================

@app.post("/webhooks/call")
async def handle_incoming_call(
    CallSid: str = Form(...),
    From: str = Form(...),
    To: Optional[str] = Form(None)
):
    """
    Handle incoming Twilio/Africa's Talking call
    Start IVR flow with welcome message
    """
    # Create new call session
    session = call_manager.create_call(CallSid, From)

    # Generate welcome TwiML with language selection
    welcome_text = IVRPrompts.get_prompt("welcome", "hi")

    twiml = tts_engine.generate_twiml_with_gather(
        text=welcome_text,
        language="hi",
        num_digits=1,
        callback_url=f"/webhooks/gather"
    )

    return Response(content=twiml, media_type="application/xml")


@app.post("/webhooks/gather")
async def handle_dtmf_input(
    CallSid: str = Form(...),
    Digits: str = Form(...),
    From: str = Form(...)
):
    """Handle DTMF input from user"""
    session = call_manager.get_call(CallSid)

    if not session:
        # Call not found - return error
        return Response(content='<?xml version="1.0"?><Response><Hangup/></Response>')

    # Process based on current state
    current_state = session.state.value

    if current_state == "welcome" or current_state == "language_select":
        # Handle language selection
        if Digits == "1":
            session.language = "hi"
            call_manager.update_state(CallSid, "main_menu")
            response_text = IVRPrompts.get_prompt("language_selected", "hi", lang_name="Hindi")
            response_text += " " + IVRPrompts.get_prompt("main_menu", "hi")
        elif Digits == "2":
            session.language = "en"
            call_manager.update_state(CallSid, "main_menu")
            response_text = IVRPrompts.get_prompt("language_selected", "en", lang_name="English")
            response_text += " " + IVRPrompts.get_prompt("main_menu", "en")
        else:
            response_text = IVRPrompts.get_prompt("invalid_option", session.language)
            response_text += " " + IVRPrompts.get_prompt("welcome", session.language)

        twiml = tts_engine.generate_twiml_with_gather(
            text=response_text,
            language=session.language,
            callback_url="/webhooks/gather"
        )

    elif current_state == "main_menu":
        # Handle main menu options
        if Digits == "1":
            # Disease detection
            call_manager.update_state(CallSid, "disease_scan")
            response_text = IVRPrompts.get_prompt("disease_intro", session.language)

            # Ask for image via MMS
            twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message to="{From}">कृपया अपने फसल की पत्ती की फोटो खींचें और इस नंबर पर MMS के रूप में भेजें।</Message>
    <Say language="{get_twiml_lang(session.language)}">{response_text}</Say>
    <Gather numDigits="1" action="/webhooks/gather" method="POST">
        <Say language="{get_twiml_lang(session.language)}">फोटो भेजने के बाद 1 दबाएं।</Say>
    </Gather>
</Response>'''
            return Response(content=twiml)

        elif Digits == "2":
            # Market prices
            call_manager.update_state(CallSid, "market_prices")
            response_text = IVRPrompts.get_prompt("market_menu", session.language)

            twiml = tts_engine.generate_twiml_with_gather(
                text=response_text,
                language=session.language,
                callback_url="/webhooks/gather"
            )

        elif Digits == "3":
            # Weather
            call_manager.update_state(CallSid, "weather_info")
            response_text = IVRPrompts.get_prompt("weather_menu", session.language)

            twiml = tts_engine.generate_twiml_with_gather(
                text=response_text,
                language=session.language,
                callback_url="/webhooks/gather"
            )

        elif Digits == "9":
            # Exit
            response_text = IVRPrompts.get_prompt("goodbye", session.language)
            twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="{get_twiml_lang(session.language)}">{response_text}</Say>
    <Hangup/>
</Response>'''
            call_manager.complete_call(CallSid)
            return Response(content=twiml)

        else:
            response_text = IVRPrompts.get_prompt("invalid_option", session.language)
            response_text += " " + IVRPrompts.get_prompt("main_menu", session.language)

            twiml = tts_engine.generate_twiml_with_gather(
                text=response_text,
                language=session.language,
                callback_url="/webhooks/gather"
            )

    else:
        # Default - go back to main menu
        response_text = IVRPrompts.get_prompt("main_menu", session.language)
        twiml = tts_engine.generate_twiml_with_gather(
            text=response_text,
            language=session.language,
            callback_url="/webhooks/gather"
        )

    return Response(content=twiml, media_type="application/xml")


@app.post("/webhooks/mms")
async def handle_mms_image(
    CallSid: str = Form(...),
    From: str = Form(...),
    MediaUrl: str = Form(...)
):
    """Handle incoming MMS with image for disease detection"""
    session = call_manager.get_call(CallSid)

    if not session:
        raise HTTPException(status_code=404, detail="Call session not found")

    # Store image URL for processing
    call_manager.store_session_data(CallSid, "image_url", MediaUrl)

    # Send processing message
    response_text = IVRPrompts.get_prompt("processing", session.language)

    # In production, trigger async disease detection here
    # For demo, return with result message
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="{get_twiml_lang(session.language)}">{response_text}</Say>
    <Say language="{get_twiml_lang(session.language)}">{IVRPrompts.get_prompt("healthy_result", session.language)}</Say>
    <Gather numDigits="1" action="/webhooks/gather" method="POST">
        <Say language="{get_twiml_lang(session.language)}">{IVRPrompts.get_prompt("main_menu", session.language)}</Say>
    </Gather>
</Response>'''

    call_manager.update_state(CallSid, "results")
    return Response(content=twiml, media_type="application/xml")


@app.post("/webhooks/status")
async def handle_call_status(
    CallSid: str = Form(...),
    CallStatus: str = Form(...)
):
    """Handle call status callbacks"""
    if CallStatus in ["completed", "busy", "no-answer", "failed"]:
        call_manager.complete_call(CallSid)

    return {"status": "recorded"}


# ==================== IVR API Endpoints ====================

class AnalyzeRequest(BaseModel):
    call_sid: str
    image_base64: str


@app.post("/api/analyze")
async def analyze_iv_image(request: AnalyzeRequest):
    """
    Analyze image from IVR flow
    Returns disease detection result
    In production, this would call the API Gateway's disease detection service
    """
    # For now, return a placeholder response
    # In production, make HTTP call to API Gateway
    # import httpx
    # async with httpx.AsyncClient() as client:
    #     response = await client.post(
    #         "http://api_gateway:8000/api/v1/disease/predict",
    #         files={"file": request.image_base64}
    #     )

    # Decode base64 image
    try:
        image_bytes = base64.b64decode(request.image_base64)
        result = disease_service.analyze_image(image_bytes)

        if result.get("success"):
            message = DiseaseAdviceGenerator.generate_result_message(result, "hi")
            return {
                "success": True,
                "result": result,
                "message": message
            }
        else:
            return {
                "success": False,
                "error": result.get("error")
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/calls/{call_sid}")
async def get_call_info(call_sid: str):
    """Get information about a specific call"""
    session = call_manager.get_call(call_sid)

    if not session:
        raise HTTPException(status_code=404, detail="Call not found")

    return {
        "call_sid": session.call_sid,
        "phone_number": session.phone_number,
        "language": session.language,
        "state": session.state.value,
        "call_state": session.call_state.value,
        "session_data": session.session_data,
        "created_at": session.created_at.isoformat()
    }


@app.get("/api/active-calls")
async def get_active_calls():
    """Get all active calls"""
    calls = call_manager.get_all_active_calls()
    return {
        "count": len(calls),
        "calls": [
            {
                "call_sid": c.call_sid,
                "phone_number": c.phone_number,
                "language": c.language,
                "state": c.state.value,
                "created_at": c.created_at.isoformat()
            }
            for c in calls
        ]
    }


def get_twiml_lang(language: str) -> str:
    """Map language code to TwiML format"""
    return "hi-IN" if language == "hi" else "en-US"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)