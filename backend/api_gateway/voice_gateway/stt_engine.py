"""
STT Engine - Speech to Text for IVR voice input
Supports Google Cloud Speech, Amazon Transcribe, and Whisper
"""

from typing import Optional, Dict, List
from enum import Enum
import base64
import json


class STTProvider(Enum):
    GOOGLE_CLOUD = "google_cloud"
    AMAZON_TRANSCRIBE = "amazon_transcribe"
    WHISPER = "whisper"
    DEEPSPEEK = "deepseek"


class LanguageCode:
    """Supported language codes for STT"""

    LANGUAGE_CODES = {
        "hi": "hi-IN",      # Hindi - India
        "en": "en-US",     # English - US
        "mr": "mr-IN",     # Marathi
        "gu": "gu-IN",     # Gujarati
        "kn": "kn-IN",     # Kannada
        "ta": "ta-IN",     # Tamil
        "te": "te-IN",     # Telugu
        "bn": "bn-IN",     # Bengali
        "pa": "pa-IN",     # Punjabi
        "ml": "ml-IN",     # Malayalam
        "as": "as-IN",     # Assamese
        "or": "or-IN",     # Odia
    }


class STTEngine:
    """
    Speech to Text engine for processing voice input
    """

    def __init__(
        self,
        provider: STTProvider = STTProvider.GOOGLE_CLOUD,
        api_key: Optional[str] = None,
        model: str = "default"
    ):
        self.provider = provider
        self.api_key = api_key
        self.model = model

    def transcribe_audio(
        self,
        audio_data: bytes,
        language: str = "hi"
    ) -> Dict:
        """
        Transcribe audio data to text

        Args:
            audio_data: Raw audio bytes
            language: Language code for transcription

        Returns:
            Dict with transcription text and confidence
        """
        lang_code = LanguageCode.LANGUAGE_CODES.get(language, "hi-IN")

        # In production, this would call the actual STT API
        # For now, return mock structure
        return {
            "success": True,
            "text": "",
            "language": lang_code,
            "confidence": 0.0,
            "words": []
        }

    def transcribe_from_url(
        self,
        audio_url: str,
        language: str = "hi"
    ) -> Dict:
        """
        Transcribe audio from URL

        Args:
            audio_url: URL to audio file
            language: Language code for transcription

        Returns:
            Dict with transcription text and confidence
        """
        lang_code = LanguageCode.LANGUAGE_CODES.get(language, "hi-IN")

        return {
            "success": True,
            "text": "",
            "language": lang_code,
            "confidence": 0.0,
            "audio_url": audio_url
        }

    def transcribe_base64(
        self,
        base64_audio: str,
        language: str = "hi"
    ) -> Dict:
        """
        Transcribe base64 encoded audio

        Args:
            base64_audio: Base64 encoded audio string
            language: Language code for transcription

        Returns:
            Dict with transcription text and confidence
        """
        try:
            audio_bytes = base64.b64decode(base64_audio)
            return self.transcribe_audio(audio_bytes, language)
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "text": ""
            }

    def process_dtmf(self, digits: str) -> Optional[str]:
        """Process DTMF tone input"""
        if not digits:
            return None

        # Map DTMF to actions or text
        dtmf_map = {
            "1": "one",
            "2": "two",
            "3": "three",
            "4": "four",
            "5": "five",
            "6": "six",
            "7": "seven",
            "8": "eight",
            "9": "nine",
            "0": "zero",
            "*": "star",
            "#": "hash"
        }

        return "".join([dtmf_map.get(d, "") for d in digits])


class SpeechRecognitionResult:
    """Structured speech recognition result"""

    def __init__(
        self,
        text: str,
        confidence: float,
        language: str,
        alternatives: List[str] = None
    ):
        self.text = text
        self.confidence = confidence
        self.language = language
        self.alternatives = alternatives or []

    def to_dict(self) -> Dict:
        return {
            "text": self.text,
            "confidence": self.confidence,
            "language": self.language,
            "alternatives": self.alternatives
        }

    def is_command(self) -> bool:
        """Check if recognized speech is a command"""
        command_keywords = ["menu", "help", "repeat", "back", "exit", "stop"]
        return any(kw in self.text.lower() for kw in command_keywords)

    def extract_intent(self) -> Optional[str]:
        """Extract intent from recognized speech"""
        text_lower = self.text.lower()

        if any(word in text_lower for word in ["रोग", "disease", "बीमारी"]):
            return "disease_detection"
        elif any(word in text_lower for word in ["भाव", "price", "दाम", "mandi"]):
            return "market_prices"
        elif any(word in text_lower for word in ["मौसम", "weather"]):
            return "weather"
        elif any(word in text_lower for word in ["मदद", "help", "सहायता"]):
            return "help"

        return None


class VoiceInputHandler:
    """Handler for processing voice input in IVR"""

    def __init__(self, stt_engine: STTEngine):
        self.stt_engine = stt_engine

    def process_voice_input(
        self,
        audio_data: bytes,
        language: str = "hi"
    ) -> SpeechRecognitionResult:
        """Process voice input and return structured result"""
        result = self.stt_engine.transcribe_audio(audio_data, language)

        return SpeechRecognitionResult(
            text=result.get("text", ""),
            confidence=result.get("confidence", 0.0),
            language=result.get("language", language)
        )

    def process_dtmf_input(self, digits: str) -> Dict:
        """Process DTMF input"""
        processed = self.stt_engine.process_dtmf(digits)

        return {
            "input_type": "dtmf",
            "digits": digits,
            "processed": processed
        }

    def determine_input_method(
        self,
        audio_data: Optional[bytes] = None,
        digits: Optional[str] = None
    ) -> str:
        """Determine whether input is voice or DTMF"""
        if digits:
            return "dtmf"
        elif audio_data:
            return "voice"
        return "unknown"