"""CLI entry point — run the full civic agent pipeline.

Usage:
    python -m src.main --demo                     # run 3 demo scenarios
    python -m src.main "There's a pothole on..."  # process a description
    python -m src.main --text "..." --lat 51.5 --lon -0.1
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from src.config import MODEL_PROVIDER
from src.models.base import CivicIssue, LLMProvider
from src.models.mock import MockProvider
from src.agents.orchestrator import Orchestrator


# ---------------------------------------------------------------------------
# Provider factory
# ---------------------------------------------------------------------------

def get_provider() -> LLMProvider:
    """Instantiate the LLM provider based on MODEL_PROVIDER env var."""
    match MODEL_PROVIDER:
        case "openai":
            from src.config import OPENAI_BASE_URL, OPENAI_API_KEY, OPENAI_MODEL
            from src.models.openai_compat import OpenAICompatProvider
            return OpenAICompatProvider(
                base_url=OPENAI_BASE_URL,
                model_name=OPENAI_MODEL,
                api_key=OPENAI_API_KEY,
            )
        case "nim":
            from src.config import NIM_BASE_URL, NIM_API_KEY, NIM_MODEL, NIM_EMBED_MODEL
            from src.models.nim import NIMProvider
            return NIMProvider(
                base_url=NIM_BASE_URL,
                model_name=NIM_MODEL,
                api_key=NIM_API_KEY,
                embed_model=NIM_EMBED_MODEL,
            )
        case _:
            return MockProvider()


# ---------------------------------------------------------------------------
# Demo scenarios — based on real FixMyStreet report types
# ---------------------------------------------------------------------------

DEMOS = [
    {
        "name": "Fly-tipping on residential street",
        "text": (
            "Someone has dumped a large pile of rubbish including a mattress, "
            "broken furniture, and several bin bags on the pavement outside "
            "42 Vallance Road. It's blocking the path and people with pushchairs "
            "have to walk in the road to get past. It's been there for three days "
            "and is attracting rats. This is near a primary school and it's a "
            "real health hazard for the children."
        ),
        "latitude": 51.5210,
        "longitude": -0.0656,
    },
    {
        "name": "Dangerous pothole on busy road",
        "text": (
            "There is a very deep pothole in the middle lane of the A205 South "
            "Circular near the junction with Herne Hill Road. It's about 30cm "
            "across and at least 10cm deep. I've seen two cars swerve to avoid "
            "it in the last hour. With the rain it fills with water and you can't "
            "see it until you're right on top of it. A cyclist could easily come "
            "off their bike. This is on a busy main road and needs urgent repair."
        ),
        "latitude": 51.4550,
        "longitude": -0.0960,
    },
    {
        "name": "Streetlight outage near hospital",
        "text": (
            "Three streetlights in a row are out on Lambeth Palace Road, between "
            "the roundabout and the entrance to St Thomas' Hospital. The whole "
            "stretch is completely dark after 9pm. There have been muggings in "
            "this area recently and it feels very unsafe for staff leaving the "
            "hospital on the night shift. I reported this two weeks ago and "
            "nothing has been done."
        ),
        "latitude": 51.4975,
        "longitude": -0.1185,
    },
]


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def print_report(issue: CivicIssue, scenario_name: str = "") -> None:
    """Pretty-print a processed CivicIssue."""
    sep = "=" * 68

    if scenario_name:
        print(f"\n{sep}")
        print(f"  DEMO: {scenario_name}")
        print(sep)

    print(f"""
{sep}
  CLASSIFIED ISSUE
{sep}
  ID:           {issue.id}
  Title:        {issue.title}
  Category:     {issue.category}
  Subcategory:  {issue.subcategory or 'N/A'}
  Status:       {issue.status}

{sep}
  LOCATION
{sep}
  Address:      {issue.address or 'N/A'}
  Borough:      {issue.borough}
  Coordinates:  {issue.latitude}, {issue.longitude}

{sep}
  SEVERITY ASSESSMENT
{sep}
  Score:        {issue.severity_score}/10
  Justification:
""")
    # Print justification lines individually for readability
    for reason in issue.severity_justification.split("; "):
        print(f"    - {reason}")

    print(f"""
{sep}
  ROUTING DECISION
{sep}
  Council:      {issue.council}
  Department:   {issue.department}

{sep}
  SUBMISSION TEXT
{sep}""")
    for line in issue.submission_text.strip().split("\n"):
        print(f"  {line}")
    print(sep)

    # Print escalation details if present
    if issue.escalation_history:
        print(f"""
{sep}
  ESCALATION ({issue.escalation_stage.upper()}) — {issue.days_open} days open
{sep}""")
        for entry in issue.escalation_history:
            stage_label = entry.get("stage", "unknown").replace("_", " ").title()
            print(f"\n  --- Stage: {stage_label} ({entry.get('date', 'N/A')}) ---")
            for key, value in entry.items():
                if key in ("stage", "date"):
                    continue
                label = key.replace("_", " ").title()
                print(f"\n  [{label}]")
                for line in str(value).strip().split("\n"):
                    print(f"  {line}")
        print(sep)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="London Civic Agent — process civic complaints through the full pipeline."
    )
    parser.add_argument("text", nargs="?", help="Raw complaint description text.")
    parser.add_argument("--demo", action="store_true", help="Run 3 built-in demo scenarios.")
    parser.add_argument("--lat", type=float, default=None, help="Latitude of issue location.")
    parser.add_argument("--lon", type=float, default=None, help="Longitude of issue location.")
    parser.add_argument("--photo", type=str, default=None, help="Path to a photo of the issue.")
    parser.add_argument(
        "--days-open", type=int, default=None,
        help="Simulate days since report (triggers escalation when >= SLA).",
    )
    parser.add_argument(
        "--provider",
        choices=["mock", "openai", "nim"],
        default=None,
        help="Override MODEL_PROVIDER env var.",
    )
    parser.add_argument(
        "--nemo",
        action="store_true",
        help="Use NeMo Agent Toolkit pipeline wrapper (falls back to standard Orchestrator if NeMo is not installed).",
    )
    parser.add_argument(
        "--call",
        action="store_true",
        help="Enable outbound follow-up calls via ElevenLabs Conversational AI (requires ELEVENLABS_API_KEY).",
    )
    args = parser.parse_args()

    # Override provider if specified
    if args.provider:
        import src.config as cfg
        cfg.MODEL_PROVIDER = args.provider

    # Select pipeline mode
    nemo_toolkit = None
    if args.nemo:
        from src.nemo.toolkit import NeMoAgentToolkit
        nemo_toolkit = NeMoAgentToolkit.from_config()
        provider_name = "NeMoAgentToolkit"
    else:
        provider_name = None

    if nemo_toolkit is None:
        llm = get_provider()
        orchestrator = Orchestrator(llm, enable_calls=args.call)
        provider_name = type(llm).__name__

    print(f"\nLondon Civic Agent — using {provider_name}")
    print(f"{'=' * 68}")

    def _run(text, **kwargs):
        if nemo_toolkit is not None:
            return nemo_toolkit.run_pipeline(text, **kwargs)
        return orchestrator.process(text, **kwargs)

    if args.demo:
        for i, demo in enumerate(DEMOS):
            # Last demo scenario gets escalation to show the full pipeline
            demo_days = demo.get("days_open", None)
            if args.days_open is not None:
                demo_days = args.days_open
            elif i == len(DEMOS) - 1:
                # Streetlight scenario: simulate 35 days open for escalation demo
                demo_days = 35

            issue = _run(
                demo["text"],
                latitude=demo.get("latitude"),
                longitude=demo.get("longitude"),
                days_open=demo_days,
            )
            print_report(issue, scenario_name=demo["name"])
        print(f"\nProcessed {len(DEMOS)} demo scenarios.\n")
        return

    if not args.text:
        parser.print_help()
        print("\nError: provide a text description or use --demo.")
        sys.exit(1)

    photos = [args.photo] if args.photo else None
    issue = _run(
        args.text,
        photos=photos,
        latitude=args.lat,
        longitude=args.lon,
        days_open=args.days_open,
    )
    print_report(issue)


if __name__ == "__main__":
    main()
