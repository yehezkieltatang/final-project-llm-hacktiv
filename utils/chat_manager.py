"""Chat session management for SIEMGuard."""

import json
from datetime import datetime
from typing import List, Dict, Optional

class ChatManager:
    """Manages chat sessions, conversation history, and state."""

    def __init__(self):
        self.messages: List[Dict[str, str]] = []
        self.session_id: str = datetime.now().strftime("%Y%m%d_%H%M%S")

    def add_message(self, role: str, content: str):
        """Add a message to the conversation history."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

    def get_conversation_context(self, max_messages: int = 10) -> List[Dict[str, str]]:
        """
        Get the last N messages for LLM context.
        Returns messages in the format expected by Groq API.
        """
        context = []
        for msg in self.messages[-max_messages:]:
            context.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        return context

    def clear_history(self):
        """Clear all conversation history."""
        self.messages = []

    def export_chat(self, format: str = "txt") -> str:
        """
        Export chat history to a string format.

        Args:
            format: 'txt' or 'json'

        Returns:
            Formatted chat history string
        """
        if format == "json":
            return json.dumps(self.messages, indent=2, default=str)
        
        # Plain text format
        lines = []
        lines.append("=" * 60)
        lines.append(f"SIEMGuard Chat Export - {self.session_id}")
        lines.append(f"Total Messages: {len(self.messages)}")
        lines.append("=" * 60)
        lines.append("")

        for msg in self.messages:
            role_label = "👤 You" if msg["role"] == "user" else "🤖 SIEMGuard"
            timestamp = msg.get("timestamp", "")
            lines.append(f"[{timestamp}] {role_label}:")
            lines.append(msg["content"])
            lines.append("-" * 40)
            lines.append("")

        return "\n".join(lines)


def parse_event_json(text: str) -> Optional[str]:
    """
    Try to extract and validate JSON from user input.
    Returns formatted JSON string if valid, None otherwise.
    """
    # Try to find JSON in the text (between triple backticks or raw)
    text = text.strip()
    
    # Remove markdown code block if present
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last line (```json and ```)
        if len(lines) > 2:
            text = "\n".join(lines[1:-1])
    
    try:
        parsed = json.loads(text)
        return json.dumps(parsed, indent=2)
    except json.JSONDecodeError:
        return None


def get_event_summary(event: dict) -> Dict[str, str]:
    """
    Extract key fields from a security event for quick display.
    """
    summary = {}
    
    # Alert info
    alert = event.get("alert_json", "{}")
    if isinstance(alert, str):
        try:
            alert = json.loads(alert)
        except:
            alert = {}
    
    summary["signature"] = event.get("alert_signature", alert.get("signature", "N/A"))
    summary["category"] = event.get("alert_category", alert.get("category", "N/A"))
    summary["severity"] = str(event.get("alert_severity", alert.get("severity", "N/A")))
    summary["action"] = event.get("alert_action", alert.get("action", "N/A"))
    
    # Flow info
    summary["src_ip"] = event.get("src_ip", event.get("flow_src_ip", "N/A"))
    summary["dest_ip"] = event.get("dest_ip", event.get("flow_dest_ip", "N/A"))
    summary["src_port"] = str(event.get("src_port", "N/A"))
    summary["dest_port"] = str(event.get("dest_port", "N/A"))
    summary["proto"] = event.get("proto", "N/A")
    
    # GeoIP
    summary["src_geo"] = f"{event.get('src_geoip_city_name', '?')}, {event.get('src_geoip_country_iso_code', '?')}"
    summary["dest_geo"] = f"{event.get('dest_geoip_city_name', '?')}, {event.get('dest_geoip_country_iso_code', '?')}"
    
    # MITRE
    mitre = event.get("mitre", "{}")
    if isinstance(mitre, str):
        try:
            mitre = json.loads(mitre)
        except:
            mitre = {}
    
    summary["mitre_tactic"] = mitre.get("tactic_name", "N/A")
    summary["mitre_technique"] = mitre.get("technique_name", "N/A")
    summary["kill_chain"] = event.get("cyber_kill_chain", "N/A")
    
    return summary