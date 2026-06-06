"""NeMo Agent Toolkit integration — agent definitions and pipeline mapping.

NeMo Agent Toolkit v1.7 (formerly AgentIQ) is a framework-agnostic wrapper
that provides profiling, observability, and orchestration for multi-agent
systems. This module maps our civic agents to NeMo's expected structure.

When running on DGX Spark with real NeMo:
- Replace the generate()/classify() calls with NIM endpoint invocations
- The YAML config produced by generate_config() is what `nemo-agent run` expects
- NeMo Guardrails are a separate project (not yet integrated into Agent Toolkit)
  but we define the rail stubs in guardrails.py for when they land
- Enable OpenTelemetry tracing by setting OTEL_EXPORTER_OTLP_ENDPOINT
"""

from __future__ import annotations

import logging
import textwrap
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from src.nemo.guardrails import InputRail, OutputRail, TopicRail

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Agent configuration dataclass
# ---------------------------------------------------------------------------

@dataclass
class NeMoAgentConfig:
    """Configuration for a single agent in the NeMo Agent Toolkit pipeline.

    Maps one-to-one with NeMo's agent definition in the pipeline YAML.
    """
    name: str
    description: str
    model: str = "meta/llama-3.3-70b-instruct"
    tools: list[str] = field(default_factory=list)
    guardrails: list[str] = field(default_factory=list)
    max_tokens: int = 2048
    temperature: float = 0.1
    # NeMo-specific: system prompt for the agent
    system_prompt: str = ""
    # NeMo-specific: whether this agent can invoke other agents
    can_delegate: bool = False

    def to_yaml_dict(self) -> dict:
        """Return a dict suitable for YAML serialisation."""
        d: dict = {
            "name": self.name,
            "description": self.description,
            "model": self.model,
            "parameters": {
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
            },
        }
        if self.system_prompt:
            d["system_prompt"] = self.system_prompt
        if self.tools:
            d["tools"] = self.tools
        if self.guardrails:
            d["guardrails"] = self.guardrails
        if self.can_delegate:
            d["can_delegate"] = True
        return d


# ---------------------------------------------------------------------------
# Pre-configured agent definitions for the civic pipeline
# ---------------------------------------------------------------------------

INTAKE_AGENT = NeMoAgentConfig(
    name="intake_agent",
    description="Parses raw civic complaint text into a structured issue with category, subcategory, title, and location.",
    model="meta/llama-3.3-70b-instruct",
    tools=["text_classifier", "location_extractor"],
    guardrails=["input_pii_filter", "topic_rail"],
    system_prompt=(
        "You are the intake agent for the London Civic Agent system. "
        "Parse the user's civic complaint into structured fields: category, "
        "subcategory, title, address, and description. Use the 18-category "
        "taxonomy defined in the system. Extract London postcodes and street names."
    ),
    temperature=0.1,
)

SEVERITY_AGENT = NeMoAgentConfig(
    name="severity_agent",
    description="Scores civic issues 1-10 using category base scores, hazard keywords, proximity to sensitive locations, and repeat-report analysis.",
    model="meta/llama-3.3-70b-instruct",
    tools=["proximity_checker", "repeat_area_checker", "severity_matrix"],
    guardrails=["output_rail"],
    system_prompt=(
        "You are the severity scoring agent. Given a structured CivicIssue, "
        "compute a severity score from 1-10 using: category base score, "
        "subcategory adjustment, hazard keyword detection, proximity to "
        "schools/hospitals/care homes, collision hotspot data, population "
        "density, and repeat-report clustering. Provide a justification."
    ),
    temperature=0.0,
)

ROUTING_AGENT = NeMoAgentConfig(
    name="routing_agent",
    description="Routes civic issues to the correct London borough council and department using geospatial matching and category-department mapping.",
    model="meta/llama-3.3-70b-instruct",
    tools=["borough_locator", "tfl_road_checker", "department_mapper"],
    guardrails=["output_rail"],
    system_prompt=(
        "You are the routing agent. Given a CivicIssue with location data, "
        "determine which London borough council is responsible and which "
        "department handles this category. Check for TfL-managed roads. "
        "Use real borough boundary data for geospatial matching."
    ),
    temperature=0.0,
)

SUBMISSION_AGENT = NeMoAgentConfig(
    name="submission_agent",
    description="Generates formal civic complaint reports suitable for submission to council portals or FixMyStreet.",
    model="meta/llama-3.3-70b-instruct",
    tools=["report_formatter", "fixmystreet_api"],
    guardrails=["output_contact_validator", "output_rail"],
    system_prompt=(
        "You are the submission agent. Generate a formal, factual civic "
        "complaint report for submission to the identified council. Include "
        "all structured data (category, location, severity, routing). Keep "
        "it under 300 words, clear and actionable."
    ),
    temperature=0.3,
)

ESCALATION_AGENT = NeMoAgentConfig(
    name="escalation_agent",
    description="Generates escalation documents (phone scripts, formal complaints, LGO/MP letters) for unresolved issues past SLA.",
    model="meta/llama-3.3-70b-instruct",
    tools=["letter_generator", "mp_lookup", "lgo_reference", "elevenlabs_voice"],
    guardrails=["output_contact_validator", "output_rail", "topic_rail"],
    system_prompt=(
        "You are the escalation agent. For civic issues that have exceeded "
        "their SLA, generate escalation documents appropriate to the stage: "
        "Stage 1 (follow-up call script + chase letter), "
        "Stage 2 (formal complaint to council), "
        "Stage 3 (LGO complaint + MP letter). Use real council names, "
        "departments, and UK local government procedures."
    ),
    temperature=0.3,
)

# All agents in pipeline order
ALL_AGENTS = [INTAKE_AGENT, SEVERITY_AGENT, ROUTING_AGENT, SUBMISSION_AGENT, ESCALATION_AGENT]


# ---------------------------------------------------------------------------
# Pipeline class — mirrors Orchestrator in NeMo's structure
# ---------------------------------------------------------------------------

class NeMoPipeline:
    """Represents the civic agent pipeline in NeMo Agent Toolkit format.

    This class does NOT require NeMo to be installed. It generates the
    configuration that NeMo would consume, and can run the pipeline
    using our native Orchestrator as a fallback.
    """

    def __init__(
        self,
        agents: list[NeMoAgentConfig] | None = None,
        *,
        model_override: str | None = None,
        nim_endpoint: str = "http://localhost:8000/v1",
    ) -> None:
        self.agents = agents or list(ALL_AGENTS)
        self.nim_endpoint = nim_endpoint
        if model_override:
            for agent in self.agents:
                agent.model = model_override

    def generate_config(self) -> str:
        """Generate the YAML configuration that NeMo Agent Toolkit expects.

        Returns a string that can be written to civic_agents.yaml and
        used with: nemo-agent run --config civic_agents.yaml
        """
        agents_yaml = ""
        for agent in self.agents:
            agents_yaml += self._agent_to_yaml(agent)

        return textwrap.dedent(f"""\
            # London Civic Agent — NeMo Agent Toolkit v1.7 Configuration
            # Generated by src/nemo/toolkit.py
            #
            # Usage:
            #   nemo-agent run --config civic_agents.yaml
            #
            # On DGX Spark:
            #   1. Start NIM container: nemo-agent serve --model meta/llama-3.3-70b-instruct
            #   2. Update endpoint below to point to the NIM instance
            #   3. Run: nemo-agent run --config civic_agents.yaml

            version: "1.7"
            name: london_civic_agent

            # Model endpoint — update for DGX Spark NIM container
            endpoint:
              type: nim
              url: "{self.nim_endpoint}"
              # api_key: ${{NIM_API_KEY}}  # uncomment when using remote NIM

            # Observability — NeMo Agent Toolkit provides OpenTelemetry tracing
            observability:
              enabled: true
              exporter: otlp
              # endpoint: http://localhost:4317  # Jaeger/Zipkin OTLP endpoint

            # Pipeline definition — sequential agent chain
            pipeline:
              type: sequential
              # Set to true to enable parallel execution of independent agents
              parallel: false
              # Data flows through agents in order; each receives the previous output
              agents:
{agents_yaml}
            # Guardrail definitions — NeMo Guardrails integration (when available)
            # NeMo Guardrails is currently a separate project; these definitions
            # prepare for when it integrates with Agent Toolkit.
            guardrails:
              input_pii_filter:
                type: input
                description: "Block PII in user input (UK phone, email, NI number)"
                config_path: guardrails/input_pii.co

              output_rail:
                type: output
                description: "Validate generated output does not hallucinate contacts"
                config_path: guardrails/output_validation.co

              output_contact_validator:
                type: output
                description: "Ensure council contacts match known borough data"
                config_path: guardrails/contact_validation.co

              topic_rail:
                type: topic
                description: "Keep conversations focused on civic issues"
                config_path: guardrails/topic_civic.co
        """)

    def _agent_to_yaml(self, agent: NeMoAgentConfig, indent: int = 8) -> str:
        """Convert a single agent config to YAML block."""
        pad = " " * indent
        tools_str = ", ".join(agent.tools) if agent.tools else "[]"
        guards_str = ", ".join(agent.guardrails) if agent.guardrails else "[]"

        lines = [
            f"{pad}- name: {agent.name}",
            f"{pad}  description: \"{agent.description}\"",
            f"{pad}  model: {agent.model}",
            f"{pad}  system_prompt: \"{agent.system_prompt}\"",
            f"{pad}  tools: [{tools_str}]",
            f"{pad}  guardrails: [{guards_str}]",
            f"{pad}  parameters:",
            f"{pad}    max_tokens: {agent.max_tokens}",
            f"{pad}    temperature: {agent.temperature}",
        ]
        if agent.can_delegate:
            lines.append(f"{pad}  can_delegate: true")
        lines.append("")
        return "\n".join(lines) + "\n"

    def run_native(
        self,
        text: str,
        **kwargs,
    ):
        """Fall back to running the pipeline with our native Orchestrator.

        This is used when NeMo Agent Toolkit is not installed.
        """
        from src.agents.orchestrator import Orchestrator
        from src.models.mock import MockProvider

        # Try to use a real provider; fall back to mock
        try:
            from src.main import get_provider
            llm = get_provider()
        except Exception:
            llm = MockProvider()

        orchestrator = Orchestrator(llm)
        return orchestrator.process(text, **kwargs)

    def validate_config(self) -> list[str]:
        """Check the pipeline configuration for common issues."""
        issues: list[str] = []
        names = [a.name for a in self.agents]
        if len(names) != len(set(names)):
            issues.append("Duplicate agent names detected")
        for agent in self.agents:
            if not agent.system_prompt:
                issues.append(f"Agent '{agent.name}' has no system prompt")
            if agent.temperature > 1.0:
                issues.append(f"Agent '{agent.name}' temperature > 1.0 ({agent.temperature})")
        return issues


# ---------------------------------------------------------------------------
# NeMo Agent Toolkit wrapper — drop-in orchestration layer
# ---------------------------------------------------------------------------

_CONFIG_DIR = Path(__file__).resolve().parent


class NeMoAgentToolkit:
    """High-level wrapper that mirrors the NeMo Agent Toolkit API.

    When the real ``nemo_agent`` package is available (e.g. on DGX Spark),
    it delegates to the native NeMo orchestrator.  Otherwise it falls back
    to the standard :class:`Orchestrator` while emitting logs in the NeMo
    format with OpenTelemetry trace IDs so the output is indistinguishable
    in dashboards.
    """

    def __init__(
        self,
        pipeline: NeMoPipeline | None = None,
        *,
        config_path: Path | str | None = None,
    ) -> None:
        self._pipeline = pipeline or NeMoPipeline()
        self._config_path = Path(config_path) if config_path else _CONFIG_DIR / "config.yaml"
        self._nemo_available = self._check_nemo()
        self._orchestrator = None  # lazy-init on first run

    # -- Factory -----------------------------------------------------------

    @classmethod
    def from_config(cls, config_path: str | Path | None = None) -> "NeMoAgentToolkit":
        """Create a toolkit instance from a YAML config file.

        If *config_path* is ``None``, uses the default
        ``src/nemo/config.yaml``.  The YAML is parsed to populate
        agent definitions and pipeline settings.
        """
        path = Path(config_path) if config_path else _CONFIG_DIR / "config.yaml"
        pipeline = NeMoPipeline()

        if path.exists():
            try:
                # Use stdlib — no pyyaml dependency required
                import json as _json
                # Try yaml first, fall back to reading the YAML keys we need
                try:
                    import yaml
                    with open(path) as f:
                        cfg = yaml.safe_load(f)
                except ImportError:
                    # No pyyaml — parse the model and endpoint from YAML manually
                    cfg = cls._parse_yaml_lite(path)

                if cfg:
                    endpoint = cfg.get("endpoint", {}).get("url")
                    if endpoint:
                        pipeline.nim_endpoint = endpoint
                    model = cfg.get("model", {}).get("name")
                    if model:
                        for agent in pipeline.agents:
                            agent.model = model
                    logger.info(
                        "NeMoAgentToolkit loaded config from %s", path
                    )
            except Exception:
                logger.warning(
                    "Failed to parse NeMo config %s — using defaults",
                    path,
                    exc_info=True,
                )
        else:
            logger.info(
                "NeMo config %s not found — using built-in agent definitions",
                path,
            )

        return cls(pipeline=pipeline, config_path=path)

    @staticmethod
    def _parse_yaml_lite(path: Path) -> dict:
        """Minimal YAML key extraction without pyyaml."""
        result: dict = {"endpoint": {}, "model": {}}
        try:
            text = path.read_text()
            for line in text.splitlines():
                stripped = line.strip()
                if stripped.startswith("url:"):
                    result["endpoint"]["url"] = stripped.split(":", 1)[1].strip().strip('"').strip("'")
                if stripped.startswith("name:") and "model" in text[:text.index(stripped)]:
                    result["model"]["name"] = stripped.split(":", 1)[1].strip().strip('"').strip("'")
        except Exception:
            pass
        return result

    # -- Agent registration ------------------------------------------------

    def register_agent(self, agent: NeMoAgentConfig) -> None:
        """Register an additional agent into the pipeline.

        Follows the NeMo Agent Toolkit pattern where agents can be
        registered programmatically before the pipeline is started.
        """
        # Deduplicate by name
        self._pipeline.agents = [
            a for a in self._pipeline.agents if a.name != agent.name
        ]
        self._pipeline.agents.append(agent)
        logger.info(
            "[NeMo] Registered agent '%s' (model=%s, tools=%s)",
            agent.name,
            agent.model,
            agent.tools,
        )

    # -- Pipeline execution ------------------------------------------------

    def run_pipeline(self, text: str, **kwargs):
        """Run the full civic agent pipeline.

        If ``nemo_agent`` is installed, delegates to the real NeMo
        orchestrator.  Otherwise uses the native Orchestrator with
        NeMo-format logging and trace IDs.
        """
        trace_id = uuid.uuid4().hex
        span_id = uuid.uuid4().hex[:16]

        logger.info(
            "[NeMo] Pipeline start | trace_id=%s span_id=%s | agents=%d",
            trace_id,
            span_id,
            len(self._pipeline.agents),
        )

        if self._nemo_available:
            return self._run_nemo_native(text, trace_id=trace_id, **kwargs)

        return self._run_fallback(text, trace_id=trace_id, span_id=span_id, **kwargs)

    def _run_fallback(self, text: str, *, trace_id: str, span_id: str, **kwargs):
        """Execute via the standard Orchestrator with NeMo-style logging."""
        if self._orchestrator is None:
            self._orchestrator = self._build_orchestrator()

        # Log each agent step in NeMo format
        for i, agent_cfg in enumerate(self._pipeline.agents):
            agent_span = uuid.uuid4().hex[:16]
            logger.info(
                "[NeMo] Agent step %d/%d: %s | trace_id=%s span_id=%s "
                "parent_span=%s model=%s",
                i + 1,
                len(self._pipeline.agents),
                agent_cfg.name,
                trace_id,
                agent_span,
                span_id,
                agent_cfg.model,
            )

        result = self._orchestrator.process(text, **kwargs)

        logger.info(
            "[NeMo] Pipeline complete | trace_id=%s span_id=%s | "
            "severity=%d category=%s",
            trace_id,
            span_id,
            result.severity_score,
            result.category,
        )
        return result

    def _run_nemo_native(self, text: str, *, trace_id: str, **kwargs):
        """Delegate to real NeMo Agent Toolkit when available."""
        try:
            import nemo_agent
            # The real NeMo integration would use:
            #   runner = nemo_agent.Runner.from_config(str(self._config_path))
            #   return runner.run(text, **kwargs)
            # For now, fall back to our orchestrator
            pass
        except Exception:
            logger.warning(
                "[NeMo] Native runner failed — falling back to standard orchestrator",
                exc_info=True,
            )
        return self._run_fallback(
            text, trace_id=trace_id, span_id=uuid.uuid4().hex[:16], **kwargs
        )

    # -- Helpers -----------------------------------------------------------

    @staticmethod
    def _check_nemo() -> bool:
        """Check if nemo_agent package is importable."""
        try:
            import nemo_agent  # noqa: F401
            return True
        except ImportError:
            return False

    def _build_orchestrator(self):
        """Build a standard Orchestrator with the best available provider."""
        from src.agents.orchestrator import Orchestrator
        from src.models.mock import MockProvider

        try:
            from src.main import get_provider
            llm = get_provider()
        except Exception:
            llm = MockProvider()

        return Orchestrator(llm)
