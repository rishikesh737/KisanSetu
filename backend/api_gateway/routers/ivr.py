"""
KisanSetu IVR Engine - Main Application
Voice Gateway for farmer phone calls (Exotel Passthru backend)
"""

import os

from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime
import uuid
import base64

from voice_gateway.call_manager import CallManager
from voice_gateway.tts_engine import TTSEngine, TTSProvider, IVRPrompts
from voice_gateway.stt_engine import STTEngine, STTProvider

router = APIRouter()

# ---------------------------------------------------------------------------
# Runtime config — set TUNNEL_BASE_URL in backend/api_gateway/.env
# This must be an absolute public URL so that Exotel's servers can reach the
# callbackUrl embedded inside every "gather" response payload.
# ---------------------------------------------------------------------------
TUNNEL_BASE_URL = os.getenv("TUNNEL_BASE_URL", "https://your-tunnel.ngrok.io").rstrip("/")

# Initialize services
call_manager = CallManager()
# Provider switched to EXOTEL — responses are JSON dicts, not TwiML XML
tts_engine = TTSEngine(provider=TTSProvider.EXOTEL)
stt_engine = STTEngine(provider=STTProvider.GOOGLE_CLOUD)


# ==================== Health & Status ====================

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "IVR Engine",
        "timestamp": datetime.utcnow().isoformat(),
        "active_calls": call_manager.get_active_call_count()
    }


@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "KisanSetu IVR Engine",
        "version": "2.0.0",
        "provider": "Exotel",
        "status": "running"
    }


# ==================== Exotel Webhooks ====================

@router.post("/webhooks/call")
async def handle_incoming_call(
    CallSid: str = Form(...),
    From: str = Form(...),
    To: Optional[str] = Form(None)
):
    """
    Handle incoming Exotel call (Passthru applet entry point).
    Returns a JSON payload instructing Exotel to play the welcome message
    and gather 1 DTMF digit for language selection.
    """
    # Create new call session — CallManager is provider-agnostic
    session = call_manager.create_call(CallSid, From)

    welcome_text = IVRPrompts.get_prompt("welcome", "hi")

    payload = tts_engine.generate_exotel_gather(
        text=welcome_text,
        language="hi",
        max_digits=1,
        callback_url=f"{TUNNEL_BASE_URL}/api/v1/ivr/webhooks/gather"
    )
    return JSONResponse(content=payload)


@router.post("/webhooks/gather")
async def handle_dtmf_input(
    CallSid: str = Form(...),
    Digits: str = Form(...),
    From: str = Form(...)
):
    """
    Handle DTMF digit(s) collected by Exotel.
    Exotel POSTs Digits here after the 'gather' action completes.
    Returns the next Exotel Passthru JSON action.
    """
    session = call_manager.get_call(CallSid)

    if not session:
        # Unknown session — disconnect cleanly
        return JSONResponse(content=tts_engine.generate_exotel_hangup())

    gather_url = f"{TUNNEL_BASE_URL}/api/v1/ivr/webhooks/gather"
    current_state = session.state.value

    if current_state in ("welcome", "language_select"):
        # ── Language selection ──────────────────────────────────────────────
        if Digits == "1":
            session.language = "hi"
            call_manager.update_state(CallSid, "main_menu")
            text = (IVRPrompts.get_prompt("language_selected", "hi", lang_name="Hindi") +
                    " " + IVRPrompts.get_prompt("main_menu", "hi"))
        elif Digits == "2":
            session.language = "en"
            call_manager.update_state(CallSid, "main_menu")
            text = (IVRPrompts.get_prompt("language_selected", "en", lang_name="English") +
                    " " + IVRPrompts.get_prompt("main_menu", "en"))
        else:
            text = (IVRPrompts.get_prompt("invalid_option", session.language) +
                    " " + IVRPrompts.get_prompt("welcome", session.language))

        payload = tts_engine.generate_exotel_gather(
            text=text,
            language=session.language,
            max_digits=1,
            callback_url=gather_url
        )
        return JSONResponse(content=payload)

    elif current_state == "main_menu":
        # ── Main menu ───────────────────────────────────────────────────────
        if Digits == "1":
            # Disease detection
            # NOTE: Exotel does not support MMS. Farmers are directed to the
            # KisanSetu Android app for image-based disease detection.
            call_manager.update_state(CallSid, "disease_scan")
            text = IVRPrompts.get_prompt("disease_intro", session.language)
            payload = tts_engine.generate_exotel_gather(
                text=text,
                language=session.language,
                max_digits=1,
                callback_url=gather_url
            )
            return JSONResponse(content=payload)

        elif Digits == "2":
            # Market prices
            call_manager.update_state(CallSid, "market_prices")
            text = IVRPrompts.get_prompt("market_menu", session.language)

        elif Digits == "3":
            # Weather info
            call_manager.update_state(CallSid, "weather_info")
            text = IVRPrompts.get_prompt("weather_menu", session.language)

        elif Digits == "9":
            # Exit
            farewell = IVRPrompts.get_prompt("goodbye", session.language)
            call_manager.complete_call(CallSid)
            payload = tts_engine.generate_exotel_hangup(farewell, session.language)
            return JSONResponse(content=payload)

        else:
            text = (IVRPrompts.get_prompt("invalid_option", session.language) +
                    " " + IVRPrompts.get_prompt("main_menu", session.language))

        payload = tts_engine.generate_exotel_gather(
            text=text,
            language=session.language,
            max_digits=1,
            callback_url=gather_url
        )
        return JSONResponse(content=payload)

    else:
        # Fallback — return to main menu from any unhandled state
        text = IVRPrompts.get_prompt("main_menu", session.language)
        payload = tts_engine.generate_exotel_gather(
            text=text,
            language=session.language,
            max_digits=1,
            callback_url=gather_url
        )
        return JSONResponse(content=payload)


@router.post("/webhooks/mms")
async def handle_mms_image(
    CallSid: str = Form(None),
    From: str = Form(None),
    MediaUrl: str = Form(None)
):
    """
    DEPRECATED — Exotel does not support MMS.

    Image-based disease detection has moved to the KisanSetu Android app,
    which performs on-device TFLite inference. This endpoint returns HTTP 410
    so that any legacy integrations fail loudly rather than silently.
    """
    return JSONResponse(
        status_code=410,
        content={
            "detail": (
                "MMS is not supported on Exotel. "
                "Use the KisanSetu Android app for offline image-based disease detection."
            )
        }
    )


@router.post("/webhooks/status")
async def handle_call_status(
    CallSid: str = Form(...),
    Status: str = Form(...)  # Exotel sends "Status"; Twilio used "CallStatus"
):
    """
    Handle Exotel call-status callbacks.
    Exotel posts this when the call transitions to a terminal state.
    """
    terminal_states = {"completed", "busy", "no-answer", "failed"}
    if Status.lower() in terminal_states:
        call_manager.complete_call(CallSid)
    return {"status": "recorded"}


# ==================== IVR API Endpoints (provider-agnostic) ====================

class AnalyzeRequest(BaseModel):
    call_sid: str
    image_base64: str


@router.post("/api/analyze")
async def analyze_ivr_image(request: AnalyzeRequest):
    """
    Analyze image from IVR flow.
    Cloud inference is deprecated — on-device TFLite via Android app is the
    primary detection path.
    """
    try:
        base64.b64decode(request.image_base64)  # validate encoding
        return {
            "success": False,
            "error": (
                "Cloud inference is deprecated. "
                "Please use the KisanSetu Android App for offline detection."
            )
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/api/calls/{call_sid}")
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


@router.get("/api/active-calls")
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
