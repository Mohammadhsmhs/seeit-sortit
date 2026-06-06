"""ElevenLabs integration — Scribe STT, Conversational AI agents, and outbound calls."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

import requests

from src.config import ELEVENLABS_API_KEY, ELEVENLABS_BASE_URL

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionResult:
    """Response shape for Scribe STT."""
    text: str = ""
    language_code: str = "en"
    confidence: float = 0.0
    words: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ConversationResult:
    """Response shape for Conversational AI call."""
    conversation_id: str = ""
    status: str = ""
    transcript: list[dict[str, str]] = field(default_factory=list)
    call_successful: bool = False
    call_duration_secs: int = 0
    analysis: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentConfig:
    """Config returned after creating a Conversational AI agent."""
    agent_id: str = ""
    name: str = ""


class ElevenLabsClient:
    """Client for ElevenLabs Scribe (STT) and Conversational AI.

    Scribe endpoint: POST /v1/speech-to-text
    Conversational AI agent: POST /v1/convai/agents/create
    Outbound call: POST /v1/convai/twilio/outbound_call
    Conversation details: GET /v1/convai/conversations/{id}
    """

    def __init__(
        self,
        api_key: str = ELEVENLABS_API_KEY,
        base_url: str = ELEVENLABS_BASE_URL,
        stub: bool = False,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.stub = stub or not api_key

    def _headers(self) -> dict[str, str]:
        return {
            "xi-api-key": self.api_key,
        }

    # -- Scribe STT ----------------------------------------------------------

    def transcribe(
        self,
        audio_path: str,
        language_code: str = "en",
        model: str = "scribe_v1",
    ) -> TranscriptionResult:
        """Transcribe an audio file using ElevenLabs Scribe.

        Endpoint: POST {base_url}/speech-to-text
        """
        if self.stub:
            return TranscriptionResult(
                text="[Stub] There is a large pothole on the corner of Baker Street and Marylebone Road.",
                language_code=language_code,
                confidence=0.95,
            )

        with open(audio_path, "rb") as f:
            files = {"file": f}
            data = {"model": model, "language_code": language_code}
            resp = requests.post(
                f"{self.base_url}/speech-to-text",
                headers=self._headers(),
                files=files,
                data=data,
                timeout=60,
            )
        resp.raise_for_status()
        body = resp.json()
        return TranscriptionResult(
            text=body.get("text", ""),
            language_code=body.get("language_code", language_code),
            confidence=body.get("confidence", 0.0),
            words=body.get("words", []),
        )

    # -- Conversational AI: Agent management ---------------------------------

    def create_agent(
        self,
        name: str,
        system_prompt: str,
        first_message: str,
        voice_id: str = "JBFqnCBsd6RMkjVDRZzb",  # "George" — clear British male
        language: str = "en",
    ) -> AgentConfig:
        """Create a Conversational AI agent.

        Endpoint: POST {base_url}/convai/agents/create
        """
        if self.stub:
            return AgentConfig(
                agent_id="agent_stub_council_followup",
                name=name,
            )

        payload = {
            "name": name,
            "conversation_config": {
                "agent": {
                    "prompt": {
                        "prompt": system_prompt,
                    },
                    "first_message": first_message,
                    "language": language,
                },
                "tts": {
                    "voice_id": voice_id,
                },
            },
        }
        resp = requests.post(
            f"{self.base_url}/convai/agents/create",
            headers={**self._headers(), "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        body = resp.json()
        logger.info("Created ElevenLabs agent: %s", body.get("agent_id"))
        return AgentConfig(
            agent_id=body.get("agent_id", ""),
            name=name,
        )

    # -- Conversational AI: Outbound calls -----------------------------------

    def make_outbound_call(
        self,
        agent_id: str,
        agent_phone_number_id: str,
        to_number: str,
        first_message: str = "",
    ) -> ConversationResult:
        """Initiate an outbound phone call via ElevenLabs + Twilio.

        Endpoint: POST {base_url}/convai/twilio/outbound_call
        """
        if self.stub:
            logger.info(
                "[Stub] Outbound call: agent=%s to=%s", agent_id, to_number
            )
            return ConversationResult(
                conversation_id="conv_stub_call_001",
                status="initiated",
                call_successful=True,
                transcript=[
                    {"role": "agent", "text": first_message or "Hello, I am calling about a civic issue."},
                    {"role": "user", "text": "[Stub] Council officer response placeholder."},
                ],
            )

        payload: dict[str, Any] = {
            "agent_id": agent_id,
            "agent_phone_number_id": agent_phone_number_id,
            "to_number": to_number,
        }
        if first_message:
            payload["first_message"] = first_message

        resp = requests.post(
            f"{self.base_url}/convai/twilio/outbound_call",
            headers={**self._headers(), "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        body = resp.json()
        logger.info("Outbound call initiated: %s", body.get("conversation_id"))
        return ConversationResult(
            conversation_id=body.get("conversation_id", ""),
            status=body.get("status", "initiated"),
            call_successful=True,
        )

    # -- Conversational AI: Conversation retrieval ---------------------------

    def get_conversation(self, conversation_id: str) -> ConversationResult:
        """Fetch conversation details and transcript.

        Endpoint: GET {base_url}/convai/conversations/{conversation_id}
        """
        if self.stub:
            return ConversationResult(
                conversation_id=conversation_id,
                status="completed",
                call_successful=True,
                transcript=[
                    {"role": "agent", "text": "Hello, I am calling about civic issue reference abc123."},
                    {"role": "user", "text": "Let me look that up for you."},
                    {"role": "user", "text": "I can see the report. We'll send a team out this week."},
                    {"role": "agent", "text": "Thank you. Could I have your name for my records?"},
                    {"role": "user", "text": "Yes, this is James from the highways department."},
                    {"role": "agent", "text": "Thank you, James. I will follow up in writing. Goodbye."},
                ],
                analysis={
                    "outcome": "Council acknowledged the issue and committed to action.",
                    "follow_up_needed": True,
                },
            )

        resp = requests.get(
            f"{self.base_url}/convai/conversations/{conversation_id}",
            headers=self._headers(),
            timeout=30,
        )
        resp.raise_for_status()
        body = resp.json()

        transcript = []
        for turn in body.get("transcript", []):
            transcript.append({
                "role": turn.get("role", ""),
                "text": turn.get("message", ""),
            })

        return ConversationResult(
            conversation_id=conversation_id,
            status=body.get("status", ""),
            call_successful=body.get("status") in ("done", "completed"),
            transcript=transcript,
            call_duration_secs=body.get("metadata", {}).get("call_duration_secs", 0),
            analysis=body.get("analysis", {}),
        )

    # -- Legacy convenience method -------------------------------------------

    def start_conversation(
        self,
        agent_id: str,
        phone_number: str,
        first_message: str = "",
    ) -> ConversationResult:
        """Backwards-compatible wrapper — delegates to make_outbound_call."""
        return self.make_outbound_call(
            agent_id=agent_id,
            agent_phone_number_id="",
            to_number=phone_number,
            first_message=first_message,
        )
