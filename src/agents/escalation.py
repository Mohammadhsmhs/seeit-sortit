"""EscalationAgent — generate phone scripts, formal complaints, and MP/LGO letters.

Handles issues that have been submitted but not resolved within SLA.

Escalation stages:
    Stage 1 (follow_up):        Follow-up phone call script + chase letter to council
    Stage 2 (formal_complaint): Formal complaint letter to the council's complaints dept
    Stage 3 (lgo_mp):           Letter to Local Government Ombudsman + local MP
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from src.models.base import CivicIssue, EscalationStage, LLMProvider
from src.models.mock import MockProvider
from src.prompts import load_prompt

logger = logging.getLogger(__name__)

# Default SLA thresholds (days) — configurable via Orchestrator
DEFAULT_SLA_DAYS = 30
STAGE_2_DAYS = 45
STAGE_3_DAYS = 60

# ---------------------------------------------------------------------------
# London MP data (sample — a real system would use TheyWorkForYou API)
# ---------------------------------------------------------------------------
_BOROUGH_MP: dict[str, dict] = {
    "Tower Hamlets": {
        "mp_name": "Rushanara Ali",
        "constituency": "Bethnal Green and Stepney",
        "address": "House of Commons, London SW1A 0AA",
    },
    "Lambeth": {
        "mp_name": "Florence Eshalomi",
        "constituency": "Vauxhall and Camberwell Green",
        "address": "House of Commons, London SW1A 0AA",
    },
    "Southwark": {
        "mp_name": "Neil Coyle",
        "constituency": "Bermondsey and Old Southwark",
        "address": "House of Commons, London SW1A 0AA",
    },
    "Hackney": {
        "mp_name": "Diane Abbott",
        "constituency": "Hackney North and Stoke Newington",
        "address": "House of Commons, London SW1A 0AA",
    },
    "Camden": {
        "mp_name": "Keir Starmer",
        "constituency": "Holborn and St Pancras",
        "address": "House of Commons, London SW1A 0AA",
    },
    "Westminster": {
        "mp_name": "Nickie Aiken",
        "constituency": "Cities of London and Westminster",
        "address": "House of Commons, London SW1A 0AA",
    },
    "Islington": {
        "mp_name": "Emily Thornberry",
        "constituency": "Islington South and Finsbury",
        "address": "House of Commons, London SW1A 0AA",
    },
}

# LGO contact details
_LGO = {
    "name": "Local Government and Social Care Ombudsman",
    "address": "PO Box 4771, Coventry CV4 0EH",
    "phone": "0300 061 0614",
    "website": "https://www.lgo.org.uk",
}


class EscalationAgent:
    """Generates escalation documents for unresolved civic issues."""

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm
        self._phone_prompt_tpl = load_prompt("escalation_phone")
        self._letter_prompt_tpl = load_prompt("escalation_letter")

    def process(
        self,
        issue: CivicIssue,
        *,
        days_open: int | None = None,
        sla_days: int = DEFAULT_SLA_DAYS,
    ) -> CivicIssue:
        """Determine escalation stage and generate appropriate documents.

        Args:
            issue: A CivicIssue that has already been through submission.
            days_open: Override how many days the issue has been open.
                       If None, uses issue.days_open.
            sla_days: SLA threshold in days for triggering Stage 1.
        """
        if days_open is not None:
            issue.days_open = days_open

        stage = self._determine_stage(issue.days_open, sla_days)
        issue.escalation_stage = stage.value
        if stage != EscalationStage.NONE:
            issue.status = "escalated"

        now = datetime.now().strftime("%d %B %Y")

        if stage == EscalationStage.FOLLOW_UP:
            self._stage_1_followup(issue, now)
        elif stage == EscalationStage.FORMAL_COMPLAINT:
            self._stage_1_followup(issue, now)
            self._stage_2_formal_complaint(issue, now)
        elif stage == EscalationStage.LGO_MP:
            self._stage_1_followup(issue, now)
            self._stage_2_formal_complaint(issue, now)
            self._stage_3_lgo_mp(issue, now)

        return issue

    # -- Stage determination ---------------------------------------------------

    def _determine_stage(self, days_open: int, sla_days: int) -> EscalationStage:
        if days_open >= STAGE_3_DAYS:
            return EscalationStage.LGO_MP
        if days_open >= STAGE_2_DAYS:
            return EscalationStage.FORMAL_COMPLAINT
        if days_open >= sla_days:
            return EscalationStage.FOLLOW_UP
        return EscalationStage.NONE

    # -- Stage 1: Follow-up ---------------------------------------------------

    def _stage_1_followup(self, issue: CivicIssue, date: str) -> None:
        # Skip if already generated
        if any(h.get("stage") == "follow_up" for h in issue.escalation_history):
            return

        phone_script = self._generate_phone_script(issue, date)
        chase_letter = self._generate_chase_letter(issue, date)

        issue.escalation_history.append({
            "stage": "follow_up",
            "date": date,
            "phone_script": phone_script,
            "chase_letter": chase_letter,
        })

    # -- Stage 2: Formal complaint --------------------------------------------

    def _stage_2_formal_complaint(self, issue: CivicIssue, date: str) -> None:
        if any(h.get("stage") == "formal_complaint" for h in issue.escalation_history):
            return

        complaint = self._generate_formal_complaint(issue, date)

        issue.escalation_history.append({
            "stage": "formal_complaint",
            "date": date,
            "formal_complaint": complaint,
        })

    # -- Stage 3: LGO + MP ----------------------------------------------------

    def _stage_3_lgo_mp(self, issue: CivicIssue, date: str) -> None:
        if any(h.get("stage") == "lgo_mp" for h in issue.escalation_history):
            return

        lgo_letter = self._generate_lgo_letter(issue, date)
        mp_letter = self._generate_mp_letter(issue, date)

        issue.escalation_history.append({
            "stage": "lgo_mp",
            "date": date,
            "lgo_letter": lgo_letter,
            "mp_letter": mp_letter,
        })

    # -- Document generation ---------------------------------------------------

    def _generate_phone_script(self, issue: CivicIssue, date: str) -> str:
        """Generate a phone call script for ElevenLabs Conversational AI."""
        if isinstance(self.llm, MockProvider):
            return self._template_phone_script(issue, date)

        prompt = self._phone_prompt_tpl.format(
            council=issue.council,
            title=issue.title,
            category=issue.category,
            reference=issue.id,
            days_open=issue.days_open,
            department=issue.department,
            description=issue.description[:300],
        )
        system = (
            "You are generating a phone call script that will be read by an "
            "AI voice agent (ElevenLabs). Keep sentences short and natural. "
            "Include [PAUSE] markers for natural pauses and [WAIT_FOR_RESPONSE] "
            "markers where the caller should wait for the council's reply."
        )
        raw = self.llm.generate(prompt, system=system)
        logger.debug("Raw phone script response (%d chars): %r", len(raw), raw[:200])
        return raw

    def _generate_chase_letter(self, issue: CivicIssue, date: str) -> str:
        """Generate a follow-up letter to the council."""
        if isinstance(self.llm, MockProvider):
            return self._template_chase_letter(issue, date)

        prompt = self._letter_prompt_tpl.format(
            council=issue.council,
            title=issue.title,
            reference=issue.id,
            category=issue.category,
            department=issue.department,
            days_open=issue.days_open,
            description=issue.description[:300],
        )
        system = (
            "You are writing a formal letter to a London borough council. "
            "Be professional, factual, and reference UK local government procedures."
        )
        raw = self.llm.generate(prompt, system=system)
        logger.debug("Raw chase letter response (%d chars): %r", len(raw), raw[:200])
        return raw

    def _generate_formal_complaint(self, issue: CivicIssue, date: str) -> str:
        """Generate a formal Stage 2 complaint to the council."""
        if isinstance(self.llm, MockProvider):
            return self._template_formal_complaint(issue, date)

        prompt = (
            f"Write a formal Stage 2 complaint to {issue.council} regarding "
            f"civic issue reference {issue.id} which has been unresolved for "
            f"{issue.days_open} days.\n\n"
            f"Issue: {issue.title}\n"
            f"Category: {issue.category}\n"
            f"Description: {issue.description[:300]}\n\n"
            f"Include:\n"
            f"1. Reference to the original report and follow-up\n"
            f"2. A clear statement that this is a formal complaint\n"
            f"3. The impact on the community\n"
            f"4. A request for investigation within 20 working days\n"
            f"5. Mention of the right to escalate to the LGO"
        )
        system = (
            "You are writing a formal complaint under a UK council's complaints "
            "procedure. Reference the Local Government Act 1974 where appropriate."
        )
        return self.llm.generate(prompt, system=system)

    def _generate_lgo_letter(self, issue: CivicIssue, date: str) -> str:
        """Generate a letter to the Local Government Ombudsman."""
        if isinstance(self.llm, MockProvider):
            return self._template_lgo_letter(issue, date)

        prompt = (
            f"Write a letter of complaint to the Local Government and Social Care "
            f"Ombudsman about {issue.council}'s failure to resolve civic issue "
            f"reference {issue.id} after {issue.days_open} days.\n\n"
            f"Issue: {issue.title}\n"
            f"Category: {issue.category}\n"
            f"Description: {issue.description[:300]}\n"
            f"Council: {issue.council}, Department: {issue.department}\n\n"
            f"The letter should explain the council's complaints procedure "
            f"has been exhausted and request an investigation."
        )
        system = (
            "You are writing a formal complaint to the UK Local Government "
            "Ombudsman. Be factual and include a clear timeline of events."
        )
        return self.llm.generate(prompt, system=system)

    def _generate_mp_letter(self, issue: CivicIssue, date: str) -> str:
        """Generate a letter to the local MP."""
        if isinstance(self.llm, MockProvider):
            return self._template_mp_letter(issue, date)

        mp_info = _BOROUGH_MP.get(issue.borough, {})
        mp_name = mp_info.get("mp_name", "[Local MP]")
        constituency = mp_info.get("constituency", issue.borough)

        prompt = (
            f"Write a letter to {mp_name}, MP for {constituency}, requesting "
            f"their intervention regarding an unresolved civic issue in their "
            f"constituency.\n\n"
            f"Issue: {issue.title}\n"
            f"Category: {issue.category}\n"
            f"Council: {issue.council}\n"
            f"Days unresolved: {issue.days_open}\n"
            f"Description: {issue.description[:300]}\n\n"
            f"Ask the MP to raise the matter with the council on the "
            f"constituent's behalf."
        )
        system = (
            "You are writing a formal letter to a Member of Parliament. "
            "Be respectful and factual. Reference the council's failure to act."
        )
        return self.llm.generate(prompt, system=system)

    # -- Template methods (mock mode) ------------------------------------------

    def _template_phone_script(self, issue: CivicIssue, date: str) -> str:
        return f"""PHONE CALL SCRIPT — Follow-up
Date: {date}
Council: {issue.council}
Department: {issue.department}
Reference: {issue.id}

[INTRODUCTION]
Hello, my name is [CALLER_NAME] and I am calling about a civic issue
I reported {issue.days_open} days ago. My reference number is {issue.id}.

[PAUSE]

[ISSUE SUMMARY]
I reported a {issue.category.lower()} issue — specifically,
{issue.title.lower()}. The issue was reported to your
{issue.department} department.

[PAUSE]

[REQUEST]
It has now been {issue.days_open} days since I made the report and I have
not received any update or seen any action taken. Could you please
provide me with:
1. The current status of my report
2. A timeline for when this will be resolved
3. A case reference number if one has not been assigned

[WAIT_FOR_RESPONSE]

[ESCALATION WARNING]
If this matter is not resolved within 14 days, I will be submitting
a formal complaint through your council's complaints procedure.

[WAIT_FOR_RESPONSE]

[CLOSE]
Thank you for your time. Could I have your name and direct contact
details for my records?

[WAIT_FOR_RESPONSE]

Thank you. I will follow up in writing. Goodbye.
"""

    def _template_chase_letter(self, issue: CivicIssue, date: str) -> str:
        return f"""FOLLOW-UP LETTER — Stage 1 Escalation

{date}

{issue.council}
{issue.department}

Dear Sir/Madam,

Re: Unresolved civic issue — Reference {issue.id}

I am writing to follow up on a report I submitted regarding a
{issue.category.lower()} issue at {issue.address or 'the location specified in my original report'}.

Issue: {issue.title}
Date reported: {issue.reported_at.strftime('%d %B %Y')}
Days elapsed: {issue.days_open}
Severity: {issue.severity_score}/10

Despite reporting this issue {issue.days_open} days ago, I have received
no confirmation that action has been taken. The original report detailed
the following:

{issue.description}

I request that you:
1. Acknowledge receipt of this follow-up within 5 working days
2. Provide a clear timeline for resolution
3. Assign a named officer to this case

If I do not receive a satisfactory response within 14 days, I will
escalate this matter through your formal complaints procedure.

Yours faithfully,
[RESIDENT_NAME]
"""

    def _template_formal_complaint(self, issue: CivicIssue, date: str) -> str:
        return f"""FORMAL COMPLAINT — Stage 2

{date}

Complaints Department
{issue.council}

Dear Complaints Officer,

FORMAL COMPLAINT — Reference {issue.id}

I wish to make a formal complaint regarding the failure of
{issue.council} to address a {issue.category.lower()} issue
that I reported {issue.days_open} days ago.

Issue: {issue.title}
Location: {issue.address or 'As specified in original report'}
Department: {issue.department}
Original report date: {issue.reported_at.strftime('%d %B %Y')}
Severity assessment: {issue.severity_score}/10

Timeline of events:
- {issue.reported_at.strftime('%d %B %Y')}: Original report submitted
- Follow-up letter sent (Stage 1 escalation)
- No substantive response received to date

The continued failure to address this issue has had the following
impact on the local community:
- {issue.severity_justification}

Under your council's complaints procedure, I request:
1. A full investigation into why this report has not been actioned
2. A written response within 20 working days
3. Details of the remedial action to be taken
4. Confirmation of the expected resolution date

I am aware of my right to refer this matter to the Local Government
and Social Care Ombudsman if I am not satisfied with the outcome
of this complaint, in accordance with the Local Government Act 1974.

Yours faithfully,
[RESIDENT_NAME]
"""

    def _template_lgo_letter(self, issue: CivicIssue, date: str) -> str:
        return f"""LETTER TO THE LOCAL GOVERNMENT OMBUDSMAN — Stage 3

{date}

{_LGO['name']}
{_LGO['address']}

Dear Ombudsman,

COMPLAINT AGAINST {issue.council.upper()}
Reference: {issue.id}

I wish to refer a complaint to the Ombudsman regarding the failure
of {issue.council} to address a civic issue in the borough of
{issue.borough}.

Summary of complaint:
I reported a {issue.category.lower()} issue ({issue.title})
on {issue.reported_at.strftime('%d %B %Y')}. Despite {issue.days_open} days
having elapsed, and having exhausted the council's complaints
procedure, the issue remains unresolved.

Timeline:
- {issue.reported_at.strftime('%d %B %Y')}: Original report to {issue.department}
- Stage 1: Follow-up letter sent to {issue.council}
- Stage 2: Formal complaint submitted to Complaints Department
- No resolution achieved through the council's procedures

The issue:
{issue.description}

Severity: {issue.severity_score}/10
Factors: {issue.severity_justification}

I believe {issue.council} has failed in its duty to:
1. Respond to civic reports within a reasonable timeframe
2. Maintain public infrastructure and safety standards
3. Follow its own complaints procedure

I request that the Ombudsman investigate this matter.

I confirm that I have completed the council's complaints procedure
before bringing this complaint to you.

Yours faithfully,
[RESIDENT_NAME]

Contact: [RESIDENT_EMAIL]
"""

    def _template_mp_letter(self, issue: CivicIssue, date: str) -> str:
        mp_info = _BOROUGH_MP.get(issue.borough, {})
        mp_name = mp_info.get("mp_name", "[Local MP]")
        constituency = mp_info.get("constituency", issue.borough)
        mp_address = mp_info.get("address", "House of Commons, London SW1A 0AA")

        return f"""LETTER TO MEMBER OF PARLIAMENT — Stage 3

{date}

{mp_name} MP
{mp_address}

Dear {mp_name},

Re: Unresolved civic issue in {constituency}

I am writing to you as my Member of Parliament to request your
assistance with a civic issue that {issue.council} has failed
to resolve despite repeated reports and a formal complaint.

Issue: {issue.title}
Category: {issue.category}
Location: {issue.address or issue.borough}
Reference: {issue.id}
Days unresolved: {issue.days_open}

The issue was first reported on {issue.reported_at.strftime('%d %B %Y')}.
I have followed the council's complaints procedure through to
completion without resolution:

1. Original report submitted to {issue.department}
2. Follow-up letter sent to {issue.council}
3. Formal complaint submitted to the Complaints Department
4. Complaint referred to the Local Government Ombudsman

The severity of this issue has been assessed at {issue.severity_score}/10,
based on the following factors:
{issue.severity_justification}

I would be grateful if you could:
1. Raise this matter with {issue.council} on my behalf
2. Request an explanation for the delay in resolution
3. Seek a commitment to a specific resolution timeline

I am happy to provide any further details or meet to discuss
this matter at your constituency surgery.

Yours sincerely,
[RESIDENT_NAME]
[RESIDENT_ADDRESS]
"""
