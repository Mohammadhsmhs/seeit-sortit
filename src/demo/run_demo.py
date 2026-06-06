"""Polished demo runner for the NVIDIA Hack for Impact presentation.

Usage:
    python -m src.demo.run_demo              # all 3 scenarios
    python -m src.demo.run_demo --scenario 1 # single scenario
    python -m src.demo.run_demo --fast       # skip delays (for testing)
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Optional

from src.agents.orchestrator import Orchestrator
from src.models.base import CivicIssue

# ---------------------------------------------------------------------------
# ANSI colour codes
# ---------------------------------------------------------------------------
_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"

_RED = "\033[91m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_BLUE = "\033[94m"
_MAGENTA = "\033[95m"
_CYAN = "\033[96m"
_WHITE = "\033[97m"

_BG_BLUE = "\033[44m"
_BG_GREEN = "\033[42m"
_BG_RED = "\033[41m"
_BG_YELLOW = "\033[43m"

DEMO_DIR = Path(__file__).parent

SCENARIO_FILES = [
    "scenario_1_flytipping.json",
    "scenario_2_pothole.json",
    "scenario_3_streetlight.json",
]

# Delay between visual steps (seconds). Set to 0 with --fast.
_STEP_DELAY = 0.6
_AGENT_DELAY = 1.2


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def _width() -> int:
    """Terminal width, capped at 80."""
    try:
        import shutil
        return min(shutil.get_terminal_size().columns, 80)
    except Exception:
        return 80


def _bar(char: str = "=", colour: str = _CYAN) -> str:
    return f"{colour}{char * _width()}{_RESET}"


def _header(text: str, colour: str = _CYAN) -> None:
    w = _width()
    pad = max(0, (w - len(text) - 4) // 2)
    print(f"\n{colour}{_BOLD}{'=' * pad}  {text}  {'=' * pad}{_RESET}")


def _subheader(text: str) -> None:
    print(f"\n  {_BOLD}{_WHITE}{text}{_RESET}")
    print(f"  {_DIM}{'-' * (len(text) + 2)}{_RESET}")


def _kv(key: str, value: str, indent: int = 4) -> None:
    pad = " " * indent
    print(f"{pad}{_DIM}{key}:{_RESET} {_WHITE}{value}{_RESET}")


def _progress(label: str, steps: list[str], delay: float) -> None:
    """Animated progress indicator for agent processing."""
    spinner = ["|", "/", "-", "\\"]
    for i, step in enumerate(steps):
        icon = spinner[i % len(spinner)]
        status = f"{_YELLOW}{icon}{_RESET} {_DIM}{label}:{_RESET} {step}"
        print(f"  {status}", end="", flush=True)
        if delay > 0:
            time.sleep(delay)
        print(f"\r  {_GREEN}*{_RESET} {_DIM}{label}:{_RESET} {step}")


def _severity_bar(score: int) -> str:
    """Visual severity bar: filled/empty blocks with colour."""
    if score >= 8:
        colour = _RED
    elif score >= 5:
        colour = _YELLOW
    else:
        colour = _GREEN
    filled = "#" * score
    empty = "-" * (10 - score)
    return f"{colour}{_BOLD}{filled}{_RESET}{_DIM}{empty}{_RESET} {colour}{score}/10{_RESET}"


# ---------------------------------------------------------------------------
# Scenario loading
# ---------------------------------------------------------------------------

def load_scenario(filename: str) -> dict:
    path = DEMO_DIR / filename
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Run a single scenario through the pipeline with visual output
# ---------------------------------------------------------------------------

def run_scenario(
    scenario: dict,
    orchestrator: Orchestrator,
    index: int,
    delay: float,
) -> CivicIssue:
    """Process one scenario and display results with formatting."""

    name = scenario["name"]
    _header(f"SCENARIO {index}: {name}", _CYAN)

    # Show input
    _subheader("INPUT")
    desc = scenario["description"]
    # Word-wrap at ~70 chars
    words = desc.split()
    line = "    "
    for w in words:
        if len(line) + len(w) + 1 > 74:
            print(f"{_DIM}{line}{_RESET}")
            line = "    "
        line += w + " "
    if line.strip():
        print(f"{_DIM}{line}{_RESET}")

    if scenario.get("photo_description"):
        print()
        _kv("Photo", scenario["photo_description"][:80] + "...")

    loc = scenario.get("location", {})
    if loc:
        print()
        _kv("Location", f"{loc.get('address', 'N/A')}")
        _kv("Coordinates", f"{loc.get('latitude', 'N/A')}, {loc.get('longitude', 'N/A')}")

    print()

    # Agent pipeline with progress indicators
    _subheader("AGENT PIPELINE")

    _progress("Intake Agent", [
        "Parsing description...",
        "Classifying issue category...",
        "Extracting subcategory...",
        "Generating title...",
    ], delay * 0.3)

    # Run intake
    issue = orchestrator.intake.process(
        scenario["description"],
        photo_description=scenario.get("photo_description"),
        latitude=loc.get("latitude"),
        longitude=loc.get("longitude"),
    )

    print()
    _kv("Category", f"{_BOLD}{issue.category}{_RESET}")
    _kv("Subcategory", issue.subcategory or "N/A")
    _kv("Title", issue.title)

    if delay > 0:
        time.sleep(delay)

    print()
    _progress("Severity Agent", [
        "Category base score...",
        "Scanning hazard keywords...",
        "Proximity check (schools, hospitals)...",
        "Checking repeat reports...",
    ], delay * 0.3)

    # Run severity
    issue = orchestrator.severity.process(issue)

    print()
    _kv("Severity", _severity_bar(issue.severity_score))
    print()
    for reason in issue.severity_justification.split("; "):
        if reason.strip():
            print(f"      {_DIM}> {reason}{_RESET}")

    if delay > 0:
        time.sleep(delay)

    print()
    _progress("Routing Agent", [
        "Checking TfL road network...",
        "Locating borough from coordinates...",
        "Mapping category to department...",
    ], delay * 0.3)

    # Run routing
    issue = orchestrator.routing.process(issue)

    print()
    _kv("Council", f"{_BOLD}{issue.council}{_RESET}")
    _kv("Department", issue.department)
    _kv("Borough", issue.borough)

    if delay > 0:
        time.sleep(delay)

    print()
    _progress("Submission Agent", [
        "Generating formal report...",
        "Attaching evidence and severity...",
    ], delay * 0.3)

    # Run submission
    issue = orchestrator.submission.process(issue)

    print()
    _subheader("GENERATED SUBMISSION")
    for line in issue.submission_text.strip().split("\n"):
        print(f"    {_DIM}{line}{_RESET}")

    # Show escalation path for scenario 3
    meta = scenario.get("metadata", {})
    escalation = meta.get("escalation_path")
    if escalation:
        print()
        _subheader("ESCALATION PATH")
        for step in escalation:
            print(f"    {_YELLOW}>{_RESET} {step}")

    print()
    print(_bar())

    return issue


# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------

def print_summary(results: list[tuple[dict, CivicIssue]]) -> None:
    _header("SUMMARY -- ALL SCENARIOS", _GREEN)
    print()

    # Table header
    h_scenario = "Scenario"
    h_category = "Category"
    h_severity = "Severity"
    h_council = "Routed To"
    h_status = "Status"

    print(f"  {_BOLD}{h_scenario:<36} {h_category:<28} {h_severity:<12} {h_council:<32} {h_status}{_RESET}")
    print(f"  {'-' * 36} {'-' * 28} {'-' * 12} {'-' * 32} {'-' * 10}")

    for scenario, issue in results:
        name = scenario["name"][:35]
        cat = issue.category[:27]

        score = issue.severity_score
        if score >= 8:
            sev_colour = _RED
        elif score >= 5:
            sev_colour = _YELLOW
        else:
            sev_colour = _GREEN
        sev = f"{sev_colour}{score}/10{_RESET}"
        # Pad to account for ANSI codes in severity string
        sev_padded = f"{sev}{'':>{12 - 4}}"

        council = issue.council[:31]
        status = f"{_GREEN}{issue.status}{_RESET}"

        print(f"  {name:<36} {cat:<28} {sev_padded} {council:<32} {status}")

    print()

    # Stats line
    total_severity = sum(issue.severity_score for _, issue in results)
    avg_severity = total_severity / len(results) if results else 0
    tfl_count = sum(1 for _, issue in results if "TfL" in issue.council)

    print(f"  {_DIM}Average severity: {avg_severity:.1f}/10 | TfL-routed: {tfl_count}/{len(results)} | All processed on-device{_RESET}")
    print()
    print(_bar("=", _GREEN))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="London Civic Agent -- Demo Runner")
    parser.add_argument(
        "--scenario", type=int, choices=[1, 2, 3], default=None,
        help="Run a single scenario (1, 2, or 3).",
    )
    parser.add_argument(
        "--fast", action="store_true",
        help="Skip animation delays.",
    )
    parser.add_argument(
        "--provider", choices=["mock", "openai", "nim"], default=None,
        help="Override MODEL_PROVIDER env var.",
    )
    args = parser.parse_args()

    if args.fast:
        global _STEP_DELAY, _AGENT_DELAY
        _STEP_DELAY = 0
        _AGENT_DELAY = 0

    delay = 0 if args.fast else _AGENT_DELAY

    # Override provider if specified
    if args.provider:
        import src.config as cfg
        cfg.MODEL_PROVIDER = args.provider

    # Instantiate provider and orchestrator
    from src.main import get_provider
    llm = get_provider()
    orchestrator = Orchestrator(llm)

    provider_name = type(llm).__name__

    # Banner
    print()
    print(_bar("=", _BLUE))
    print()
    print(f"  {_BOLD}{_BLUE}LONDON CIVIC AGENT{_RESET}")
    print(f"  {_DIM}NVIDIA Hack for Impact London 2026{_RESET}")
    print(f"  {_DIM}Model provider: {provider_name}{_RESET}")
    print()
    print(_bar("=", _BLUE))

    if delay > 0:
        time.sleep(0.5)

    # Select scenarios
    if args.scenario:
        indices = [args.scenario - 1]
    else:
        indices = list(range(len(SCENARIO_FILES)))

    results: list[tuple[dict, CivicIssue]] = []

    for i in indices:
        scenario = load_scenario(SCENARIO_FILES[i])
        issue = run_scenario(scenario, orchestrator, i + 1, delay)
        results.append((scenario, issue))

    # Persist all processed issues so the dashboard can display them
    from src.data.processed_issues import save_issue
    for _, issue in results:
        save_issue(issue)
    print(f"\n  {_DIM}Saved {len(results)} issue(s) to processed_issues.json{_RESET}")

    # Summary table
    if len(results) > 1:
        print_summary(results)
    elif len(results) == 1:
        print(f"\n  {_GREEN}Scenario complete.{_RESET}\n")

    # Final line
    print(f"  {_DIM}Run with --fast to skip delays, --scenario N for a single scenario.{_RESET}")
    print()


if __name__ == "__main__":
    main()
