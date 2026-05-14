"""
Call Manager - Handles IVR call flow and state management
"""

from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class CallState(Enum):
    INITIATED = "initiated"
    RINGING = "ringing"
    CONNECTED = "connected"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    FAILED = "failed"
    BUSY = "busy"
    NO_ANSWER = "no_answer"


class IVRState(Enum):
    WELCOME = "welcome"
    LANGUAGE_SELECT = "language_select"
    MAIN_MENU = "main_menu"
    DISEASE_SCAN = "disease_scan"
    AWAITING_IMAGE = "awaiting_image"
    MARKET_PRICES = "market_prices"
    WEATHER_INFO = "weather_info"
    RESULTS = "results"
    GOODBYE = "goodbye"


@dataclass
class CallSession:
    call_sid: str
    phone_number: str
    language: str = "hi"
    state: IVRState = IVRState.WELCOME
    call_state: CallState = CallState.INITIATED
    session_data: Dict = field(default_factory=dict)
    ivr_history: List[Dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_to_history(self, action: str, data: Dict = None):
        self.ivr_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "data": data or {}
        })
        self.updated_at = datetime.utcnow()


class CallManager:
    """
    Manages IVR call sessions and state transitions
    Integrates with Twilio/Africa's Talking
    """

    def __init__(self):
        self.active_calls: Dict[str, CallSession] = {}
        self.completed_calls: Dict[str, CallSession] = {}

    def create_call(self, call_sid: str, phone_number: str) -> CallSession:
        """Create a new IVR call session"""
        session = CallSession(
            call_sid=call_sid,
            phone_number=phone_number
        )
        self.active_calls[call_sid] = session
        session.add_to_history("call_initiated", {"phone": phone_number})
        return session

    def get_call(self, call_sid: str) -> Optional[CallSession]:
        """Retrieve an active call session"""
        return self.active_calls.get(call_sid)

    def update_state(self, call_sid: str, new_state: IVRState) -> bool:
        """Update the IVR state for a call"""
        session = self.get_call(call_sid)
        if not session:
            return False

        old_state = session.state
        session.state = new_state
        session.add_to_history("state_change", {
            "from": old_state.value,
            "to": new_state.value
        })
        return True

    def set_language(self, call_sid: str, language: str) -> bool:
        """Set the preferred language for a call"""
        session = self.get_call(call_sid)
        if not session:
            return False

        session.language = language
        session.add_to_history("language_set", {"language": language})
        return True

    def store_session_data(self, call_sid: str, key: str, value) -> bool:
        """Store data in the call session"""
        session = self.get_call(call_sid)
        if not session:
            return False

        session.session_data[key] = value
        session.add_to_history("data_store", {key: str(value)})
        return True

    def get_session_data(self, call_sid: str, key: str, default=None):
        """Retrieve data from the call session"""
        session = self.get_call(call_sid)
        if not session:
            return default
        return session.session_data.get(key, default)

    def complete_call(self, call_sid: str, status: CallState = CallState.COMPLETED):
        """Mark a call as completed"""
        session = self.get_call(call_sid)
        if session:
            session.call_state = status
            session.state = IVRState.GOODBYE
            session.add_to_history("call_completed", {"status": status.value})
            self.completed_calls[call_sid] = session
            if call_sid in self.active_calls:
                del self.active_calls[call_sid]

    def fail_call(self, call_sid: str, reason: str):
        """Mark a call as failed"""
        session = self.get_call(call_sid)
        if session:
            session.call_state = CallState.FAILED
            session.add_to_history("call_failed", {"reason": reason})
            self.completed_calls[call_sid] = session
            if call_sid in self.active_calls:
                del self.active_calls[call_sid]

    def get_call_history(self, call_sid: str) -> Optional[List[Dict]]:
        """Get the IVR history for a call"""
        session = self.get_call(call_sid)
        if not session:
            session = self.completed_calls.get(call_sid)
        if session:
            return session.ivr_history
        return None

    def get_active_call_count(self) -> int:
        """Get count of active calls"""
        return len(self.active_calls)

    def get_all_active_calls(self) -> List[CallSession]:
        """Get all active call sessions"""
        return list(self.active_calls.values())


# Global call manager instance
call_manager = CallManager()