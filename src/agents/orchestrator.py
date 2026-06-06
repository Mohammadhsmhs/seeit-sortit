"""Orchestrator — chains intake -> severity -> routing -> submission (-> escalation)."""

from __future__ import annotations

import logging
import os

from src.agents.intake import IntakeAgent
from src.agents.severity import SeverityAgent
from src.agents.routing import RoutingAgent
from src.agents.submission import SubmissionAgent
from src.agents.escalation import EscalationAgent, DEFAULT_SLA_DAYS
from src.agents.followup_call import FollowUpCallAgent
from src.models.base import CivicIssue, LLMProvider

# Guardrails are optional — skip gracefully if unavailable
try:
    from src.nemo.guardrails import InputRail, OutputRail, TopicRail
    _GUARDRAILS_AVAILABLE = True
except ImportError:
    _GUARDRAILS_AVAILABLE = False

logger = logging.getLogger(__name__)


class Orchestrator:
    """Runs the full pipeline: raw text in, completed CivicIssue out."""

    def __init__(
        self,
        llm: LLMProvider,
        *,
        sla_days: int = DEFAULT_SLA_DAYS,
        guardrails: bool = True,
        auto_save: bool = True,
        enable_calls: bool = False,
    ) -> None:
        self.llm = llm
        self.sla_days = sla_days
        self.auto_save = auto_save
        self.enable_calls = enable_calls
        self.guardrails_enabled = guardrails and _GUARDRAILS_AVAILABLE
        if guardrails and not _GUARDRAILS_AVAILABLE:
            logger.warning("Guardrails requested but import failed — running without guardrails")
        self.intake = IntakeAgent(llm)
        self.severity = SeverityAgent(llm)
        self.routing = RoutingAgent(llm)
        self.submission = SubmissionAgent(llm)
        self.escalation = EscalationAgent(llm)
        self.followup_call = FollowUpCallAgent()

    def process(
        self,
        text: str,
        *,
        photo_description: str | None = None,
        photos: list[str] | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        days_open: int | None = None,
    ) -> CivicIssue:
        """Run the full agent pipeline and return a completed CivicIssue.

        Args:
            days_open: If provided and >= sla_days, triggers escalation
                       after submission. Used for demo/testing.
        """
        # Pre-pipeline guardrails
        if self.guardrails_enabled:
            # Topic rail — reject off-topic requests
            topic_ok, topic_reason = TopicRail.check(text)
            if not topic_ok:
                logger.info("TopicRail rejected input: %s", topic_reason)
                issue = CivicIssue(description=text)
                issue.submission_text = (
                    f"Request rejected: {topic_reason}. "
                    "I can only help with civic issues such as road defects, "
                    "fly-tipping, streetlight outages, and similar problems."
                )
                issue.status = "rejected"
                return issue

            # Input rail — redact PII if detected
            pii_ok, pii_reason = InputRail.check(text)
            if not pii_ok:
                logger.warning("InputRail detected PII: %s — redacting", pii_reason)
                text = InputRail.redact(text)

        # Step 1: Intake — parse and classify
        issue = self.intake.process(
            text,
            photo_description=photo_description,
            photos=photos,
            latitude=latitude,
            longitude=longitude,
        )

        # Step 2: Severity scoring
        issue = self.severity.process(issue)

        # Step 3: Route to council / department
        issue = self.routing.process(issue)

        # Step 4: Generate formal submission
        issue = self.submission.process(issue)

        # Post-pipeline guardrails — check submission for hallucinated contacts
        if self.guardrails_enabled:
            output_ok, output_reason = OutputRail.check(
                issue.submission_text, council_name=issue.council
            )
            if not output_ok:
                logger.warning(
                    "OutputRail flagged submission: %s", output_reason
                )

        # Step 5 (optional): Escalation — triggered when issue exceeds SLA
        if days_open is not None and days_open >= self.sla_days:
            issue = self.escalation.process(
                issue, days_open=days_open, sla_days=self.sla_days
            )

            # Step 6 (optional): Place follow-up call to council
            if self.enable_calls:
                issue = self.followup_call.process(issue)

        # Persist to the processed-issues store
        if self.auto_save:
            try:
                from src.data.processed_issues import save_issue
                save_issue(issue)
            except Exception:
                logger.exception("Failed to auto-save processed issue %s", issue.id)

        return issue
