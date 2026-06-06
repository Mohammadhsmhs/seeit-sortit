"""NeMo Guardrails stub definitions for the London Civic Agent.

NeMo Guardrails is a separate NVIDIA project (not yet integrated into
Agent Toolkit v1.7, but on the roadmap). These stubs define the rail
logic so it can be wired in when the integration lands.

Three rail types:
    InputRail:  Block PII in user input (UK phone, email, NI number)
    OutputRail: Ensure generated submissions don't hallucinate contacts
    TopicRail:  Keep conversations focused on civic issues

Each rail class exposes a check() method that returns (passed: bool, reason: str).
In production, these would be registered with NeMo Guardrails via Colang files.
"""

from __future__ import annotations

import re
from typing import Optional


# ---------------------------------------------------------------------------
# PII patterns — UK-specific
# ---------------------------------------------------------------------------

# UK mobile: 07xxx xxx xxx or +44 7xxx xxx xxx
_UK_PHONE_PATTERN = re.compile(
    r"(?:\+44\s?7\d{3}|\(?07\d{3}\)?)\s?\d{3}\s?\d{3}"
)

# Email
_EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)

# UK National Insurance number: 2 letters + 6 digits + 1 letter (e.g. QQ 12 34 56 A)
_NI_NUMBER_PATTERN = re.compile(
    r"\b[A-CEGHJ-PR-TW-Z][A-CEGHJ-NPR-TW-Z]\s?\d{2}\s?\d{2}\s?\d{2}\s?[A-D]\b",
    re.IGNORECASE,
)

# UK postcode (for reference — not blocked, but flagged)
_POSTCODE_PATTERN = re.compile(
    r"\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b",
    re.IGNORECASE,
)


class InputRail:
    """Block PII in user input before it reaches the agent pipeline.

    In NeMo Guardrails, this would be a Colang input rail:

        define flow input_pii_filter
            user ...
            if contains_pii($user_message)
                bot "I've detected personal information in your message.
                     Please remove phone numbers, email addresses, and
                     National Insurance numbers before submitting."
                stop
    """

    @staticmethod
    def check(text: str) -> tuple[bool, str]:
        """Check input text for PII.

        Returns:
            (True, "") if no PII detected.
            (False, reason) if PII found.
        """
        findings: list[str] = []

        if _UK_PHONE_PATTERN.search(text):
            findings.append("UK phone number detected")

        if _EMAIL_PATTERN.search(text):
            findings.append("email address detected")

        if _NI_NUMBER_PATTERN.search(text):
            findings.append("National Insurance number detected")

        if findings:
            return False, "; ".join(findings)
        return True, ""

    @staticmethod
    def redact(text: str) -> str:
        """Redact PII from text, replacing with placeholders."""
        text = _UK_PHONE_PATTERN.sub("[PHONE_REDACTED]", text)
        text = _EMAIL_PATTERN.sub("[EMAIL_REDACTED]", text)
        text = _NI_NUMBER_PATTERN.sub("[NI_NUMBER_REDACTED]", text)
        return text


# ---------------------------------------------------------------------------
# Known council contact data for validation
# ---------------------------------------------------------------------------

# A subset of real London council phone numbers for validation
_KNOWN_COUNCIL_CONTACTS: dict[str, dict] = {
    "London Borough of Tower Hamlets": {
        "phone": "020 7364 5000",
        "website": "towerhamlets.gov.uk",
    },
    "London Borough of Lambeth": {
        "phone": "020 7926 1000",
        "website": "lambeth.gov.uk",
    },
    "London Borough of Southwark": {
        "phone": "020 7525 5000",
        "website": "southwark.gov.uk",
    },
    "London Borough of Hackney": {
        "phone": "020 8356 5000",
        "website": "hackney.gov.uk",
    },
    "London Borough of Camden": {
        "phone": "020 7974 4444",
        "website": "camden.gov.uk",
    },
    "City of Westminster": {
        "phone": "020 7641 6000",
        "website": "westminster.gov.uk",
    },
    "Transport for London (TfL)": {
        "phone": "0343 222 1234",
        "website": "tfl.gov.uk",
    },
}


class OutputRail:
    """Ensure generated submissions don't contain hallucinated council contacts.

    In NeMo Guardrails, this would be a Colang output rail:

        define flow output_contact_validator
            bot ...
            if contains_phone_number($bot_message)
                $valid = validate_council_contact($bot_message)
                if not $valid
                    bot "I've removed unverified contact details from the
                         submission to ensure accuracy."
                    stop
    """

    @staticmethod
    def check(text: str, council_name: str = "") -> tuple[bool, str]:
        """Check output text for potentially hallucinated contact details.

        Returns:
            (True, "") if output passes validation.
            (False, reason) if suspicious content found.
        """
        findings: list[str] = []

        # Check for phone numbers in output that don't match known contacts
        phone_matches = _UK_PHONE_PATTERN.findall(text)
        if phone_matches and council_name:
            known = _KNOWN_COUNCIL_CONTACTS.get(council_name, {})
            known_phone = known.get("phone", "")
            for phone in phone_matches:
                # Normalise for comparison
                normalised = re.sub(r"\s+", "", phone)
                known_normalised = re.sub(r"\s+", "", known_phone)
                if known_normalised and normalised != known_normalised:
                    findings.append(
                        f"Phone number '{phone}' does not match known contact "
                        f"for {council_name} ({known_phone})"
                    )

        # Check for email addresses that look auto-generated
        email_matches = _EMAIL_PATTERN.findall(text)
        for email in email_matches:
            domain = email.split("@")[1].lower()
            # Flag emails that claim to be council emails but use wrong domain
            if council_name and "gov.uk" in domain:
                known = _KNOWN_COUNCIL_CONTACTS.get(council_name, {})
                known_website = known.get("website", "")
                if known_website and known_website not in domain:
                    findings.append(
                        f"Email domain '{domain}' may not match {council_name}"
                    )

        if findings:
            return False, "; ".join(findings)
        return True, ""


class TopicRail:
    """Keep conversations focused on civic issues.

    In NeMo Guardrails, this would be a Colang topic rail:

        define flow topic_civic
            user ...
            if not is_civic_topic($user_message)
                bot "I can only help with civic issues such as road defects,
                     fly-tipping, streetlight outages, and similar problems.
                     Could you describe the issue you'd like to report?"
                stop
    """

    # Keywords that indicate a civic-related topic
    _CIVIC_KEYWORDS = [
        "pothole", "road", "pavement", "streetlight", "street light",
        "fly-tip", "flytip", "rubbish", "waste", "bin", "litter",
        "graffiti", "drain", "flooding", "tree", "park", "noise",
        "parking", "vehicle", "abandoned", "broken", "damaged",
        "council", "report", "complaint", "issue", "problem",
        "dangerous", "hazard", "safety", "pollution", "smell",
        "rat", "pest", "dog fouling", "needle", "syringe",
        "housing", "damp", "mould", "planning", "building",
    ]

    # Keywords that indicate off-topic content
    _OFF_TOPIC_KEYWORDS = [
        "weather forecast", "stock market", "recipe", "sports score",
        "movie review", "song lyrics", "write me a poem",
        "tell me a joke", "what is the meaning of life",
        "translate", "code review", "programming",
    ]

    @classmethod
    def check(cls, text: str) -> tuple[bool, str]:
        """Check if input text is related to civic issues.

        Returns:
            (True, "") if on-topic.
            (False, reason) if off-topic.
        """
        lower = text.lower()

        # Check for off-topic signals first
        for kw in cls._OFF_TOPIC_KEYWORDS:
            if kw in lower:
                return False, f"Off-topic content detected: '{kw}'"

        # Check for civic keywords
        civic_score = sum(1 for kw in cls._CIVIC_KEYWORDS if kw in lower)
        if civic_score > 0:
            return True, ""

        # Short messages without civic keywords — could be follow-up or unclear
        if len(text.split()) < 5:
            return True, ""  # Allow short messages (could be "yes", "update", etc.)

        # Longer messages without any civic keywords
        return False, "No civic issue keywords detected in the message"
