"""NeMo Agent Toolkit integration layer.

Structures our civic agents for compatibility with NVIDIA NeMo Agent Toolkit v1.7.
This is a preparation layer — it defines the configuration and pipeline mapping
that NeMo expects, without requiring NeMo to be installed locally.

When running on DGX Spark with real NeMo:
1. Install nemo-agent-toolkit: pip install nemo-agent-toolkit
2. Replace MockProvider with a NIM-backed LLM
3. Use NeMoPipeline.generate_config() to produce the YAML
4. Launch with: nemo-agent run --config civic_agents.yaml
"""

from src.nemo.toolkit import NeMoAgentConfig, NeMoAgentToolkit, NeMoPipeline
from src.nemo.guardrails import InputRail, OutputRail, TopicRail

__all__ = [
    "NeMoAgentConfig",
    "NeMoAgentToolkit",
    "NeMoPipeline",
    "InputRail",
    "OutputRail",
    "TopicRail",
]
