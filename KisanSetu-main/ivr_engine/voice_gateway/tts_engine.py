"""
TTS Engine - Text to Speech for IVR responses
Supports Google Cloud TTS, Amazon Polly, gTTS (offline), and local TTS
"""

from typing import Optional, Dict
from enum import Enum
import base64
import hashlib
import json
import io
from gtts import gTTS


class TTSProvider(Enum):
    GOOGLE_CLOUD = "google_cloud"
    AMAZON_POLLY = "amazon_polly"
    AZURE = "azure"
    LOCAL = "local"
    GTTS = "gtts"  # Free offline TTS


class LanguageConfig:
    """Language configuration for TTS voices"""

    GOOGLE_CLOUD_VOICES = {
        "hi": "hi-IN-Standard-A",
        "en": "en-US-Standard-A",
        "mr": "mr-IN-Standard-A",
        "gu": "gu-IN-Standard-A",
        "kn": "kn-IN-Standard-A",
        "ta": "ta-IN-Standard-A",
        "te": "te-IN-Standard-A",
        "bn": "bn-IN-Standard-A",
        "pa": "pa-IN-Standard-A"
    }

    AMAZON_POLLY_VOICES = {
        "hi": "Aditi",
        "en": "Joanna",
        "mr": "Aditi",
        "gu": "Aditi"
    }


class TTSEngine:
    """
    Text to Speech engine for generating IVR prompts
    """

    def __init__(
        self,
        provider: TTSProvider = TTSProvider.GOOGLE_CLOUD,
        api_key: Optional[str] = None,
        cache_enabled: bool = True
    ):
        self.provider = provider
        self.api_key = api_key
        self.cache_enabled = cache_enabled
        self.cache: Dict[str, str] = {}

    def generate_twiml(self, text: str, language: str = "hi") -> str:
        """Generate TwiML with embedded TTS"""
        voice_id = self._get_voice_id(language)
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="{voice_id}" language="{self._get_twiml_lang(language)}">{text}</Say>
</Response>'''

    def generate_twiml_with_gather(
        self,
        text: str,
        language: str = "hi",
        num_digits: int = 1,
        callback_url: str = "/api/v1/ivr/gather-input"
    ) -> str:
        """Generate TwiML with TTS and DTMF gathering"""
        voice_id = self._get_voice_id(language)
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather numDigits="{num_digits}" action="{callback_url}" method="POST">
        <Say voice="{voice_id}" language="{self._get_twiml_lang(language)}">{text}</Say>
    </Gather>
</Response>'''

    def generate_twiml_with_record(
        self,
        text: str,
        language: str = "hi",
        max_duration: int = 30,
        callback_url: str = "/api/v1/ivr/recordings"
    ) -> str:
        """Generate TwiML with TTS and recording"""
        voice_id = self._get_voice_id(language)
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="{voice_id}" language="{self._get_twiml_lang(language)}">{text}</Say>
    <Record action="{callback_url}" method="POST" maxLength="{max_duration}" />
</Response>'''

    def _get_voice_id(self, language: str) -> str:
        """Get voice ID for the language"""
        if self.provider == TTSProvider.GOOGLE_CLOUD:
            return LanguageConfig.GOOGLE_CLOUD_VOICES.get(language, "hi-IN-Standard-A")
        elif self.provider == TTSProvider.AMAZON_POLLY:
            return LanguageConfig.AMAZON_POLLY_VOICES.get(language, "Aditi")
        return "alice"

    def _get_twiml_lang(self, language: str) -> str:
        """Map language code to TwiML language code"""
        lang_map = {
            "hi": "hi-IN",
            "en": "en-US",
            "mr": "mr-IN",
            "gu": "gu-IN",
            "kn": "kn-IN",
            "ta": "ta-IN",
            "te": "te-IN",
            "bn": "bn-IN",
            "pa": "pa-IN"
        }
        return lang_map.get(language, "hi-IN")

    def _get_cache_key(self, text: str, language: str) -> str:
        """Generate cache key for TTS"""
        return hashlib.md5(f"{text}:{language}".encode()).hexdigest()

    def get_cached_audio(self, text: str, language: str) -> Optional[str]:
        """Get cached audio if available"""
        if not self.cache_enabled:
            return None
        cache_key = self._get_cache_key(text, language)
        return self.cache.get(cache_key)

    def cache_audio(self, text: str, language: str, audio_data: str):
        """Cache generated audio"""
        if self.cache_enabled:
            cache_key = self._get_cache_key(text, language)
            self.cache[cache_key] = audio_data

    def generate_audio_gtts(self, text: str, language: str = "hi") -> bytes:
        """Generate audio using gTTS (free, offline)"""
        lang_code = "hi" if language == "hi" else "en"
        tts = gTTS(text=text, lang=lang_code, slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return audio_buffer.getvalue()

    def generate_twiml_with_gtts(
        self,
        text: str,
        language: str = "hi",
        num_digits: int = 1,
        callback_url: str = "/api/v1/ivr/gather-input"
    ) -> str:
        """Generate TwiML with gTTS audio URL and DTMF gathering"""
        # For gTTS, we use TwiML's native <Say> with the text
        # Twilio will handle the TTS natively
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather numDigits="{num_digits}" action="{callback_url}" method="POST">
        <Say language="{self._get_twiml_lang(language)}">{text}</Say>
    </Gather>
</Response>'''

    def generate_twiml_with_audio_url(
        self,
        text: str,
        audio_url: str,
        language: str = "hi",
        num_digits: int = 1,
        callback_url: str = "/api/v1/ivr/gather-input"
    ) -> str:
        """Generate TwiML with pre-generated audio URL and DTMF gathering"""
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather numDigits="{num_digits}" action="{callback_url}" method="POST">
        <Play>{audio_url}</Play>
    </Gather>
</Response>'''


class IVRPrompts:
    """Pre-defined IVR prompt templates"""

    HINDI_PROMPTS = {
        "welcome": "नमस्ते! किसान सेतु IVR सेवा में आपका स्वागत है। राष्ट्रीय भाषा के लिए 1 दबाएं, अंग्रेजी के लिए 2 दबाएं।",
        "language_selected": "आपने {lang_name} चुना है।",
        "main_menu": "मुख्य मेन्यू में आपका स्वागत है। रोग पहचान के लिए 1 दबाएं। मंडी भाव जानने के लिए 2 दबाएं। मौसम जानने के लिए 3 दबाएं। बाहर निकलने के लिए 9 दबाएं।",
        "disease_intro": "रोग पहचान सेवा में आपका स्वागत है। कृपया अपने फसल की पत्ती की फोटो खींचें और MMS के जरिए भेजें। फोटो भेजने के बाद हम आपको रोग की जानकारी देंगे।",
        "receiving_image": "हम आपकी छवि प्राप्त कर रहे हैं। कृपया प्रतीक्षा करें।",
        "processing": "हम रोग का विश्लेषण कर रहे हैं। कृपया प्रतीक्षा करें।",
        "disease_result": "आपके पौधे में {disease} पाया गया। इसकी पुष्टि {confidence} प्रतिशत है। उपचार के लिए सलाह: {advice}",
        "healthy_result": "बहुत बढ़िया! आपका पौधा स्वस्थ है। कोई रोग नहीं पाया गया।",
        "market_menu": "मंडी भाव जानने के लिए अपने जिले का नाम बोलें।",
        "weather_menu": "मौसम जानने के लिए अपने जिले का नाम बोलें।",
        "goodbye": "धन्यवाद! किसान सेतु सेवा का उपयोग करने के लिए धन्यवाद। जल्द मिलते हैं।",
        "invalid_option": "अमान्य विकल्प। कृपया सही बटन दबाएं।",
        "error": "कुछ त्रुटि हो गई। कृपया पुनः प्रयास करें।",
        "transferring": "कृपया प्रतीक्षा करें, हम आपको ऑपरेटर से जोड़ रहे हैं।",
        "callback": "आपका अनुरोध दर्ज किया गया। हम जल्द ही आपसे संपर्क करेंगे।"
    }

    ENGLISH_PROMPTS = {
        "welcome": "Namaste! Welcome to KisanSetu IVR service. Press 1 for Hindi, 2 for English.",
        "language_selected": "You have selected {lang_name}.",
        "main_menu": "Welcome to main menu. Press 1 for disease detection. Press 2 for market prices. Press 3 for weather. Press 9 to exit.",
        "disease_intro": "Welcome to disease detection. Please take a photo of your crop leaf and send via MMS. We will provide disease information after receiving the photo.",
        "receiving_image": "We are receiving your image. Please wait.",
        "processing": "We are analyzing the disease. Please wait.",
        "disease_result": "Your plant has {disease}. Confidence is {confidence} percent. Treatment advice: {advice}",
        "healthy_result": "Great! Your plant is healthy. No disease detected.",
        "market_menu": "Speak your district name to know market prices.",
        "weather_menu": "Speak your district name to know weather information.",
        "goodbye": "Thank you for using KisanSetu service. Goodbye.",
        "invalid_option": "Invalid option. Please press the correct button.",
        "error": "Some error occurred. Please try again.",
        "transferring": "Please wait, we are connecting you to an operator.",
        "callback": "Your request has been recorded. We will contact you soon."
    }

    @classmethod
    def get_prompt(cls, key: str, language: str = "hi", **kwargs) -> str:
        """Get formatted prompt for the language"""
        prompts = cls.HINDI_PROMPTS if language == "hi" else cls.ENGLISH_PROMPTS
        template = prompts.get(key, prompts["error"])
        return template.format(**kwargs)