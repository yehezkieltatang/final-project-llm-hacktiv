import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class GroqClient:
    """Wrapper for Groq API to interact with LLM models."""

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY not found. Please set it in your .env file.\n"
                "Copy .env.example to .env and add your API key."
            )
        self.client = Groq(api_key=api_key)
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    def get_response(
        self,
        messages: list,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        """
        Send a chat completion request to Groq API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Controls randomness (0.0 - 1.0)
            max_tokens: Maximum tokens in response

        Returns:
            Response text from the model
        """
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=0.95,
                stream=False,
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Error communicating with Groq API: {str(e)}"

    def analyze_event(self, event_json: str, language: str = "en") -> str:
        """
        Analyze a security event and return explanation.

        Args:
            event_json: JSON string of the security event
            language: 'en' for English, 'id' for Indonesian

        Returns:
            Analysis text
        """
        system_prompt = (
            "You are a SOC (Security Operations Center) analyst assistant. "
            "Analyze the following security event/alert and provide a clear analysis.\n\n"
            "Include in your analysis:\n"
            "1. Event Summary: What happened in simple terms\n"
            "2. Severity Assessment: Explain the severity level and risk\n"
            "3. MITRE ATT&CK: If MITRE data is available, explain the tactic and technique\n"
            "4. Cyber Kill Chain: Which phase this event falls into\n"
            "5. Key Indicators: Source IP, Destination IP, ports, protocol\n"
            "6. GeoIP Context: Where is the traffic coming from/going to\n"
            "7. Recommendation: What action should be taken (if any)\n\n"
            "Be concise but thorough. Use security best practices."
            if language == "en"
            else (
                "Anda adalah asisten analis SOC (Security Operations Center). "
                "Analisis event/alert keamanan berikut dan berikan analisis yang jelas.\n\n"
                "Sertakan dalam analisis Anda:\n"
                "1. Ringkasan Event: Apa yang terjadi dalam bahasa sederhana\n"
                "2. Penilaian Severity: Jelaskan tingkat keparahan dan risiko\n"
                "3. MITRE ATT&CK: Jika data MITRE tersedia, jelaskan taktik dan teknik\n"
                "4. Cyber Kill Chain: Fase mana dari serangan ini\n"
                "5. Indikator Kunci: IP Sumber, IP Tujuan, port, protokol\n"
                "6. Konteks GeoIP: Dari mana/ke mana lalu lintas ini\n"
                "7. Rekomendasi: Tindakan apa yang harus diambil (jika ada)\n\n"
                "Jadilah ringkas namun menyeluruh. Gunakan praktik terbaik keamanan."
            )
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze this security event:\n```json\n{event_json}\n```"}
        ]

        return self.get_response(messages, temperature=0.2, max_tokens=2048)