"""Abstract LLM provider and CivicIssue data model."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Issue taxonomy — mirrors docs/issue-taxonomy/Index.md
# ---------------------------------------------------------------------------

class IssueCategory(str, Enum):
    ROADS_AND_HIGHWAYS = "Roads and Highways"
    WASTE_AND_FLY_TIPPING = "Waste and Fly-Tipping"
    STREET_CLEANLINESS = "Street Cleanliness"
    STREET_LIGHTING_AND_TRAFFIC = "Street Lighting and Traffic"
    PAVEMENTS_AND_FOOTWAYS = "Pavements and Footways"
    VEHICLES = "Vehicles"
    TREES_AND_VEGETATION = "Trees and Vegetation"
    PARKS_AND_PUBLIC_SPACES = "Parks and Public Spaces"
    NOISE_AND_NUISANCE = "Noise and Nuisance"
    POLLUTION = "Pollution"
    ANTISOCIAL_BEHAVIOUR = "Antisocial Behaviour"
    HOUSING = "Housing"
    PLANNING_AND_BUILDING = "Planning and Building"
    PEST_CONTROL = "Pest Control"
    FOOD_AND_BUSINESS = "Food and Business"
    DEAD_ANIMALS = "Dead Animals"
    UTILITIES = "Utilities"
    FRAUD_AND_MISUSE = "Fraud and Misuse"
    UNCATEGORISED = "Uncategorised"


class IssueStatus(str, Enum):
    NEW = "new"
    TRIAGED = "triaged"
    ROUTED = "routed"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    ESCALATED = "escalated"
    FIXED = "fixed"


class EscalationStage(str, Enum):
    NONE = "none"
    FOLLOW_UP = "follow_up"           # Stage 1: follow-up call/letter to council
    FORMAL_COMPLAINT = "formal_complaint"  # Stage 2: formal complaint to council
    LGO_MP = "lgo_mp"                 # Stage 3: Local Government Ombudsman / MP


class CivicIssue(BaseModel):
    """A single civic complaint flowing through the pipeline."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    title: str = ""
    category: str = IssueCategory.UNCATEGORISED.value
    subcategory: str = ""
    description: str = ""

    # Location
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: str = ""
    borough: str = ""

    # Severity
    severity_score: int = 0
    severity_justification: str = ""

    # Media
    photos: list[str] = Field(default_factory=list)

    # Metadata
    reported_at: datetime = Field(default_factory=datetime.now)
    status: str = IssueStatus.NEW.value

    # Routing
    council: str = ""
    department: str = ""

    # Output
    submission_text: str = ""

    # Escalation
    escalation_stage: str = EscalationStage.NONE.value
    escalation_history: list[dict] = Field(default_factory=list)
    days_open: int = 0


# ---------------------------------------------------------------------------
# Abstract LLM provider
# ---------------------------------------------------------------------------

class LLMProvider(ABC):
    """Interface every model backend must implement."""

    @abstractmethod
    def generate(self, prompt: str, *, system: str | None = None) -> str:
        """Free-form text generation."""

    @abstractmethod
    def classify(self, text: str, categories: list[str]) -> str:
        """Return the single best-matching category from *categories*."""

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Return a dense embedding vector for *text*."""
