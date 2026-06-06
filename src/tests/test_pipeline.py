"""End-to-end pipeline tests using MockProvider with real FixMyStreet descriptions.

Covers:
  - Individual agent tests (intake, severity, routing, submission)
  - Full pipeline integration with all 3 demo scenarios
  - Severity scoring range validation
  - Borough routing validation
  - Edge cases (empty input, very long input, non-London coordinates)
  - Mock mode offline verification
"""

from __future__ import annotations

import socket
import time
import unittest

from src.models.mock import MockProvider
from src.models.base import CivicIssue, IssueCategory
from src.agents.intake import IntakeAgent
from src.agents.severity import SeverityAgent
from src.agents.routing import RoutingAgent
from src.agents.submission import SubmissionAgent
from src.agents.orchestrator import Orchestrator


# ── Valid London boroughs for assertions ─────────────────────────────

LONDON_BOROUGHS = {
    "City of London", "City of London Corporation",
    "Barking and Dagenham", "London Borough of Barking and Dagenham",
    "Barnet", "London Borough of Barnet",
    "Bexley", "London Borough of Bexley",
    "Brent", "London Borough of Brent",
    "Bromley", "London Borough of Bromley",
    "Camden", "London Borough of Camden",
    "Croydon", "London Borough of Croydon",
    "Ealing", "London Borough of Ealing",
    "Enfield", "London Borough of Enfield",
    "Greenwich", "Royal Borough of Greenwich",
    "Hackney", "London Borough of Hackney",
    "Hammersmith and Fulham", "London Borough of Hammersmith and Fulham",
    "Haringey", "London Borough of Haringey",
    "Harrow", "London Borough of Harrow",
    "Havering", "London Borough of Havering",
    "Hillingdon", "London Borough of Hillingdon",
    "Hounslow", "London Borough of Hounslow",
    "Islington", "London Borough of Islington",
    "Kensington and Chelsea", "Royal Borough of Kensington and Chelsea",
    "Kingston upon Thames", "Royal Borough of Kingston upon Thames",
    "Lambeth", "London Borough of Lambeth",
    "Lewisham", "London Borough of Lewisham",
    "Merton", "London Borough of Merton",
    "Newham", "London Borough of Newham",
    "Redbridge", "London Borough of Redbridge",
    "Richmond upon Thames", "London Borough of Richmond upon Thames",
    "Southwark", "London Borough of Southwark",
    "Sutton", "London Borough of Sutton",
    "Tower Hamlets", "London Borough of Tower Hamlets",
    "Waltham Forest", "London Borough of Waltham Forest",
    "Wandsworth", "London Borough of Wandsworth",
    "Westminster", "City of Westminster",
    # TfL is also a valid routing target
    "Transport for London (TfL)",
}


def _is_valid_council(council: str) -> bool:
    """Check if a council string is a known London authority or fallback."""
    for name in LONDON_BOROUGHS:
        if name.lower() in council.lower():
            return True
    return "manual routing" in council.lower()


# ══════════════════════════════════════════════════════════════════════
#  Individual Agent Tests
# ══════════════════════════════════════════════════════════════════════


class TestIntakeAgent(unittest.TestCase):
    """Test the IntakeAgent in isolation."""

    def setUp(self) -> None:
        self.llm = MockProvider()
        self.agent = IntakeAgent(self.llm)

    def test_flytipping_classification(self) -> None:
        text = "Someone dumped a mattress and bin bags on the pavement."
        issue = self.agent.process(text, latitude=51.52, longitude=-0.07)
        self.assertEqual(issue.category, "Waste and Fly-Tipping")
        self.assertEqual(issue.subcategory, "Fly-Tipping")

    def test_pothole_classification(self) -> None:
        text = "Deep pothole in the road surface near the junction."
        issue = self.agent.process(text, latitude=51.46, longitude=-0.10)
        self.assertEqual(issue.category, "Roads and Highways")
        self.assertEqual(issue.subcategory, "Pothole")

    def test_streetlight_classification(self) -> None:
        text = "The streetlight outside the hospital is not working."
        issue = self.agent.process(text, latitude=51.50, longitude=-0.12)
        self.assertEqual(issue.category, "Street Lighting and Traffic")
        self.assertEqual(issue.subcategory, "Streetlight Out")

    def test_graffiti_classification(self) -> None:
        text = "Offensive graffiti spray painted on the bus shelter."
        issue = self.agent.process(text)
        self.assertEqual(issue.category, "Street Cleanliness")
        self.assertEqual(issue.subcategory, "Graffiti")

    def test_title_includes_subcategory(self) -> None:
        text = "Deep pothole on Baker Street near the tube station."
        issue = self.agent.process(text)
        self.assertIn("Pothole", issue.title)

    def test_address_extraction_from_road(self) -> None:
        text = "There is a problem on Vallance Road near the school."
        issue = self.agent.process(text)
        self.assertIn("Vallance Road", issue.address)

    def test_status_is_triaged(self) -> None:
        issue = self.agent.process("Pothole on the road")
        self.assertEqual(issue.status, "triaged")

    def test_coordinates_passed_through(self) -> None:
        issue = self.agent.process(
            "A problem", latitude=51.5, longitude=-0.1
        )
        self.assertEqual(issue.latitude, 51.5)
        self.assertEqual(issue.longitude, -0.1)

    def test_photo_description_included(self) -> None:
        issue = self.agent.process(
            "Fly-tipping on the street",
            photo_description="Large pile of rubbish on pavement",
        )
        # Photo description should influence classification
        self.assertEqual(issue.category, "Waste and Fly-Tipping")


class TestSeverityAgent(unittest.TestCase):
    """Test the SeverityAgent in isolation."""

    def setUp(self) -> None:
        self.llm = MockProvider()
        self.agent = SeverityAgent(self.llm)

    def _make_issue(self, **kwargs) -> CivicIssue:
        defaults = {
            "category": "Roads and Highways",
            "subcategory": "Pothole",
            "description": "A pothole on the road.",
        }
        defaults.update(kwargs)
        return CivicIssue(**defaults)

    def test_score_in_range(self) -> None:
        issue = self._make_issue()
        result = self.agent.process(issue)
        self.assertGreaterEqual(result.severity_score, 1)
        self.assertLessEqual(result.severity_score, 10)

    def test_hazard_keywords_boost_score(self) -> None:
        base_issue = self._make_issue(description="A pothole on the road.")
        hazard_issue = self._make_issue(
            description="A dangerous pothole near a school on a busy main road, urgent repair needed."
        )
        base_result = self.agent.process(base_issue)
        hazard_result = self.agent.process(hazard_issue)
        self.assertGreater(hazard_result.severity_score, base_result.severity_score)

    def test_justification_non_empty(self) -> None:
        issue = self._make_issue()
        result = self.agent.process(issue)
        self.assertTrue(len(result.severity_justification) > 0)

    def test_justification_mentions_base_score(self) -> None:
        issue = self._make_issue()
        result = self.agent.process(issue)
        self.assertIn("base", result.severity_justification.lower())

    def test_proximity_boost_near_hospital(self) -> None:
        """Issue near St Thomas' Hospital should get proximity boost."""
        issue = self._make_issue(
            latitude=51.4987,
            longitude=-0.1175,
            description="A pothole near the hospital.",
        )
        result = self.agent.process(issue)
        justification_lower = result.severity_justification.lower()
        # Should have some proximity-related justification
        has_proximity = (
            "hospital" in justification_lower
            or "school" in justification_lower
            or "within" in justification_lower
        )
        self.assertTrue(has_proximity)

    def test_no_coords_still_scores(self) -> None:
        """Even without coordinates, severity should still produce a valid score."""
        issue = self._make_issue(latitude=None, longitude=None)
        result = self.agent.process(issue)
        self.assertGreaterEqual(result.severity_score, 1)
        self.assertLessEqual(result.severity_score, 10)

    def test_score_capped_at_10(self) -> None:
        """Even with many hazard keywords and proximity, score should not exceed 10."""
        issue = self._make_issue(
            description=(
                "Dangerous gas leak with asbestos near a school and hospital "
                "on a busy main road, chemical spill, electrical fire, emergency, "
                "urgent repair needed for elderly and wheelchair users."
            ),
            latitude=51.4987,
            longitude=-0.1175,
        )
        result = self.agent.process(issue)
        self.assertLessEqual(result.severity_score, 10)

    def test_score_minimum_is_1(self) -> None:
        """Even for a trivial issue, score should be at least 1."""
        issue = self._make_issue(
            category="Planning and Building",
            subcategory="",
            description="Minor cosmetic issue.",
        )
        result = self.agent.process(issue)
        self.assertGreaterEqual(result.severity_score, 1)


class TestRoutingAgent(unittest.TestCase):
    """Test the RoutingAgent in isolation."""

    def setUp(self) -> None:
        self.llm = MockProvider()
        self.agent = RoutingAgent(self.llm)

    def _make_issue(self, **kwargs) -> CivicIssue:
        defaults = {
            "category": "Roads and Highways",
            "description": "A pothole on the road.",
        }
        defaults.update(kwargs)
        return CivicIssue(**defaults)

    def test_routes_to_valid_council(self) -> None:
        issue = self._make_issue(latitude=51.52, longitude=-0.07)
        result = self.agent.process(issue)
        self.assertTrue(
            _is_valid_council(result.council),
            f"Council '{result.council}' is not a valid London authority",
        )

    def test_tfl_road_detected(self) -> None:
        """A205 South Circular should route to TfL."""
        issue = self._make_issue(
            description="Pothole on the A205 South Circular road.",
            latitude=51.455, longitude=-0.096,
        )
        result = self.agent.process(issue)
        self.assertEqual(result.council, "Transport for London (TfL)")
        self.assertEqual(result.department, "TfL Highways")

    def test_department_assigned(self) -> None:
        issue = self._make_issue(
            category="Waste and Fly-Tipping",
            latitude=51.52, longitude=-0.07,
        )
        result = self.agent.process(issue)
        self.assertEqual(result.department, "Waste and Environmental Services")

    def test_borough_populated(self) -> None:
        issue = self._make_issue(latitude=51.52, longitude=-0.07)
        result = self.agent.process(issue)
        self.assertTrue(len(result.borough) > 0)

    def test_status_set_to_routed(self) -> None:
        issue = self._make_issue(latitude=51.52, longitude=-0.07)
        result = self.agent.process(issue)
        self.assertEqual(result.status, "routed")

    def test_fallback_without_coordinates(self) -> None:
        """Without coords or recognisable address, should fallback gracefully."""
        issue = self._make_issue(
            latitude=None, longitude=None,
            address="",
            description="A pothole somewhere.",
        )
        result = self.agent.process(issue)
        # Should either find a council or indicate manual routing
        self.assertTrue(len(result.council) > 0)

    def test_multiple_boroughs_consistent(self) -> None:
        """Same coordinates should always route to the same borough."""
        issue1 = self._make_issue(latitude=51.52, longitude=-0.07)
        issue2 = self._make_issue(latitude=51.52, longitude=-0.07)
        r1 = self.agent.process(issue1)
        r2 = self.agent.process(issue2)
        self.assertEqual(r1.borough, r2.borough)
        self.assertEqual(r1.council, r2.council)


class TestSubmissionAgent(unittest.TestCase):
    """Test the SubmissionAgent in isolation."""

    def setUp(self) -> None:
        self.llm = MockProvider()
        self.agent = SubmissionAgent(self.llm)

    def _make_issue(self, **kwargs) -> CivicIssue:
        defaults = {
            "title": "Test Issue",
            "category": "Roads and Highways",
            "subcategory": "Pothole",
            "description": "A pothole on the road.",
            "borough": "Test Borough",
            "council": "Test Council",
            "department": "Highways",
            "severity_score": 7,
            "severity_justification": "Base score: 6; hazard keyword: +1",
            "latitude": 51.5,
            "longitude": -0.1,
        }
        defaults.update(kwargs)
        return CivicIssue(**defaults)

    def test_submission_text_generated(self) -> None:
        issue = self._make_issue()
        result = self.agent.process(issue)
        self.assertTrue(len(result.submission_text) > 100)

    def test_submission_contains_civic_issue_report(self) -> None:
        issue = self._make_issue()
        result = self.agent.process(issue)
        self.assertIn("CIVIC ISSUE REPORT", result.submission_text)

    def test_submission_contains_category(self) -> None:
        issue = self._make_issue()
        result = self.agent.process(issue)
        self.assertIn("Roads and Highways", result.submission_text)

    def test_submission_contains_description(self) -> None:
        issue = self._make_issue()
        result = self.agent.process(issue)
        self.assertIn("A pothole on the road.", result.submission_text)

    def test_submission_contains_severity(self) -> None:
        issue = self._make_issue()
        result = self.agent.process(issue)
        self.assertIn("7/10", result.submission_text)

    def test_submission_contains_council(self) -> None:
        issue = self._make_issue()
        result = self.agent.process(issue)
        self.assertIn("Test Council", result.submission_text)

    def test_submission_contains_coordinates(self) -> None:
        issue = self._make_issue()
        result = self.agent.process(issue)
        self.assertIn("51.500000", result.submission_text)
        self.assertIn("-0.100000", result.submission_text)

    def test_status_set_to_submitted(self) -> None:
        issue = self._make_issue()
        result = self.agent.process(issue)
        self.assertEqual(result.status, "submitted")

    def test_no_coordinates_omits_map_reference(self) -> None:
        issue = self._make_issue(latitude=None, longitude=None)
        result = self.agent.process(issue)
        self.assertNotIn("Map reference:", result.submission_text)


# ══════════════════════════════════════════════════════════════════════
#  Full Pipeline Integration Tests
# ══════════════════════════════════════════════════════════════════════


class TestFullPipeline(unittest.TestCase):
    """Run real-world FixMyStreet report texts through the full pipeline."""

    def setUp(self) -> None:
        self.llm = MockProvider()
        self.orchestrator = Orchestrator(self.llm)

    # -- Demo scenario 1: Fly-tipping ----------------------------------------

    def test_demo_scenario_flytipping(self) -> None:
        """Real FixMyStreet-style fly-tipping report near a school."""
        text = (
            "Someone has dumped a large pile of rubbish including a mattress, "
            "broken furniture, and several bin bags on the pavement outside "
            "42 Vallance Road. It's blocking the path and people with pushchairs "
            "have to walk in the road to get past. It's been there for three days "
            "and is attracting rats. This is near a primary school and it's a "
            "real health hazard for the children."
        )
        issue = self.orchestrator.process(
            text, latitude=51.5210, longitude=-0.0656
        )

        self.assertEqual(issue.category, "Waste and Fly-Tipping")
        self.assertEqual(issue.subcategory, "Fly-Tipping")
        self.assertGreaterEqual(issue.severity_score, 1)
        self.assertLessEqual(issue.severity_score, 10)
        self.assertTrue(len(issue.severity_justification) > 0)
        self.assertTrue(_is_valid_council(issue.council))
        self.assertEqual(issue.department, "Waste and Environmental Services")
        self.assertTrue(len(issue.submission_text) > 0)
        self.assertEqual(issue.status, "submitted")

    # -- Demo scenario 2: Pothole on TfL road --------------------------------

    def test_demo_scenario_pothole_tfl(self) -> None:
        """Pothole on A205 South Circular — should route to TfL."""
        text = (
            "There is a very deep pothole in the middle lane of the A205 South "
            "Circular near the junction with Herne Hill Road. It's about 30cm "
            "across and at least 10cm deep. I've seen two cars swerve to avoid "
            "it in the last hour. With the rain it fills with water and you can't "
            "see it until you're right on top of it. A cyclist could easily come "
            "off their bike. This is on a busy main road and needs urgent repair."
        )
        issue = self.orchestrator.process(
            text, latitude=51.4550, longitude=-0.0960
        )

        self.assertEqual(issue.category, "Roads and Highways")
        self.assertEqual(issue.subcategory, "Pothole")
        self.assertGreaterEqual(issue.severity_score, 6)
        self.assertLessEqual(issue.severity_score, 8)
        self.assertEqual(issue.council, "Transport for London (TfL)")
        self.assertEqual(issue.department, "TfL Highways")
        self.assertIn("CIVIC ISSUE REPORT", issue.submission_text)

    # -- Demo scenario 3: Streetlight near hospital ---------------------------

    def test_demo_scenario_streetlight(self) -> None:
        """Streetlight outage near St Thomas' Hospital."""
        text = (
            "Three streetlights in a row are out on Lambeth Palace Road, between "
            "the roundabout and the entrance to St Thomas' Hospital. The whole "
            "stretch is completely dark after 9pm. There have been muggings in "
            "this area recently and it feels very unsafe for staff leaving the "
            "hospital on the night shift. I reported this two weeks ago and "
            "nothing has been done."
        )
        issue = self.orchestrator.process(
            text, latitude=51.4975, longitude=-0.1185
        )

        self.assertEqual(issue.category, "Street Lighting and Traffic")
        self.assertGreaterEqual(issue.severity_score, 4)
        self.assertLessEqual(issue.severity_score, 7)
        self.assertTrue(_is_valid_council(issue.council))
        self.assertEqual(issue.department, "Highways and Transport")
        self.assertEqual(issue.status, "submitted")


# ══════════════════════════════════════════════════════════════════════
#  Severity Scoring Range Validation
# ══════════════════════════════════════════════════════════════════════


class TestSeverityRange(unittest.TestCase):
    """Verify severity scores always land in 1-10 for every category."""

    def setUp(self) -> None:
        self.llm = MockProvider()
        self.orchestrator = Orchestrator(self.llm)

    def test_all_categories_produce_valid_severity(self) -> None:
        """Every IssueCategory should produce a score in [1, 10]."""
        for cat in IssueCategory:
            issue = CivicIssue(
                category=cat.value,
                description=f"A problem related to {cat.value}.",
            )
            agent = SeverityAgent(self.llm)
            result = agent.process(issue)
            self.assertGreaterEqual(
                result.severity_score, 1,
                f"Category {cat.value} scored below 1: {result.severity_score}",
            )
            self.assertLessEqual(
                result.severity_score, 10,
                f"Category {cat.value} scored above 10: {result.severity_score}",
            )

    def test_extreme_hazard_keywords_capped(self) -> None:
        """Hazard keyword bonus should be capped at +1."""
        issue = CivicIssue(
            category="Pollution",
            description=(
                "gas leak asbestos chemical electrical sinkhole collapse "
                "flood fire needle syringe dangerous urgent emergency "
                "child elderly wheelchair blind school hospital busy road main road"
            ),
            latitude=51.4987,
            longitude=-0.1175,
        )
        agent = SeverityAgent(self.llm)
        result = agent.process(issue)
        self.assertLessEqual(result.severity_score, 10)


# ══════════════════════════════════════════════════════════════════════
#  Routing Borough Validation
# ══════════════════════════════════════════════════════════════════════


class TestRoutingBoroughs(unittest.TestCase):
    """Verify routing returns valid London boroughs or fallback."""

    def setUp(self) -> None:
        self.llm = MockProvider()

    def test_central_london_routes_to_valid_borough(self) -> None:
        coords = [
            (51.5074, -0.1278),  # Central London
            (51.5210, -0.0656),  # Vallance Road area
            (51.4550, -0.0960),  # Herne Hill area
            (51.4975, -0.1185),  # Lambeth Palace Road area
            (51.5900, -0.1000),  # North London
            (51.4000, -0.1000),  # South London
        ]
        agent = RoutingAgent(self.llm)
        for lat, lon in coords:
            issue = CivicIssue(
                category="Roads and Highways",
                description="A pothole.",
                latitude=lat, longitude=lon,
            )
            result = agent.process(issue)
            self.assertTrue(
                _is_valid_council(result.council),
                f"Coords ({lat}, {lon}) routed to invalid council: {result.council}",
            )

    def test_tfl_keyword_detection(self) -> None:
        """Various TfL road references should trigger TfL routing."""
        tfl_descriptions = [
            "Pothole on the A205 South Circular.",
            "Issue on the A1 near Holloway.",
            "Problem on the North Circular road.",
            "Defect on a red route near Victoria.",
        ]
        agent = RoutingAgent(self.llm)
        for desc in tfl_descriptions:
            issue = CivicIssue(
                category="Roads and Highways",
                description=desc,
                latitude=51.5, longitude=-0.1,
            )
            result = agent.process(issue)
            self.assertEqual(
                result.council, "Transport for London (TfL)",
                f"Description '{desc[:40]}...' should route to TfL",
            )


# ══════════════════════════════════════════════════════════════════════
#  Edge Cases
# ══════════════════════════════════════════════════════════════════════


class TestEdgeCases(unittest.TestCase):
    """Edge cases: empty input, very long input, non-London coords."""

    def setUp(self) -> None:
        self.llm = MockProvider()
        self.orchestrator = Orchestrator(self.llm)

    def test_empty_description(self) -> None:
        """Empty string should still produce a valid (if generic) issue."""
        issue = self.orchestrator.process("")
        self.assertTrue(len(issue.category) > 0)
        self.assertGreaterEqual(issue.severity_score, 1)
        self.assertLessEqual(issue.severity_score, 10)
        self.assertEqual(issue.status, "submitted")

    def test_very_long_description(self) -> None:
        """A description with 2000+ words should not crash the pipeline."""
        long_text = (
            "There is a pothole on the road. " * 500
        )
        issue = self.orchestrator.process(
            long_text, latitude=51.5, longitude=-0.1
        )
        self.assertTrue(len(issue.category) > 0)
        self.assertGreaterEqual(issue.severity_score, 1)
        self.assertLessEqual(issue.severity_score, 10)
        self.assertEqual(issue.status, "submitted")

    def test_non_london_coordinates(self) -> None:
        """Coordinates outside London should still route (to nearest borough)."""
        # Edinburgh coordinates
        issue = self.orchestrator.process(
            "A pothole on the road.",
            latitude=55.9533,
            longitude=-3.1883,
        )
        # Should still produce a result, even if routing is imprecise
        self.assertTrue(len(issue.council) > 0)
        self.assertEqual(issue.status, "submitted")

    def test_null_coordinates(self) -> None:
        """No coordinates should still complete the pipeline."""
        issue = self.orchestrator.process(
            "A pothole on Baker Street near the tube station."
        )
        self.assertTrue(len(issue.category) > 0)
        self.assertEqual(issue.status, "submitted")

    def test_special_characters_in_description(self) -> None:
        """Unicode and special characters should not crash the pipeline."""
        text = (
            "There's a pothole — about 30cm × 20cm — on the A205. "
            "It’s very dangerous! Coordinates: 51°N, 0°W. "
            "£100 damage to my car. Réf: #12345."
        )
        issue = self.orchestrator.process(text, latitude=51.5, longitude=-0.1)
        self.assertEqual(issue.status, "submitted")

    def test_numbers_only_description(self) -> None:
        """All-numeric input should not crash."""
        issue = self.orchestrator.process("12345 67890 111")
        self.assertEqual(issue.status, "submitted")


# ══════════════════════════════════════════════════════════════════════
#  Mock Mode Offline Verification
# ══════════════════════════════════════════════════════════════════════


class TestMockModeOffline(unittest.TestCase):
    """Verify that mock mode makes zero network calls."""

    def test_no_network_calls_in_mock_mode(self) -> None:
        """Block socket.connect and verify the full pipeline completes."""
        original_connect = socket.socket.connect
        calls_detected = []

        def _blocking_connect(self_sock, addr):
            calls_detected.append(addr)
            raise RuntimeError(f"Unexpected network call to {addr}")

        socket.socket.connect = _blocking_connect
        try:
            llm = MockProvider()
            orch = Orchestrator(llm)
            issue = orch.process(
                "A pothole on the road near a school.",
                latitude=51.52, longitude=-0.07,
            )
            self.assertEqual(len(calls_detected), 0, f"Network calls detected: {calls_detected}")
            self.assertEqual(issue.status, "submitted")
        finally:
            socket.socket.connect = original_connect


# ══════════════════════════════════════════════════════════════════════
#  MockProvider Unit Tests
# ══════════════════════════════════════════════════════════════════════


class TestMockProvider(unittest.TestCase):
    """Unit-test the MockProvider's classify, generate, and embed methods."""

    def setUp(self) -> None:
        self.llm = MockProvider()

    def test_classify_keywords(self) -> None:
        categories = [
            "Roads and Highways",
            "Waste and Fly-Tipping",
            "Street Lighting and Traffic",
        ]
        self.assertEqual(
            self.llm.classify("deep pothole on the road", categories),
            "Roads and Highways",
        )
        self.assertEqual(
            self.llm.classify("someone dumped a mattress and rubbish", categories),
            "Waste and Fly-Tipping",
        )
        self.assertEqual(
            self.llm.classify("the streetlight is not working", categories),
            "Street Lighting and Traffic",
        )

    def test_classify_fallback_to_first(self) -> None:
        """When no keywords match, should return the first category."""
        result = self.llm.classify("xyzzy qwerty", ["Alpha", "Beta"])
        self.assertEqual(result, "Alpha")

    def test_embed_deterministic(self) -> None:
        v1 = self.llm.embed("test input")
        v2 = self.llm.embed("test input")
        self.assertEqual(v1, v2)
        self.assertEqual(len(v1), 384)

    def test_embed_different_inputs_differ(self) -> None:
        v1 = self.llm.embed("test input")
        v2 = self.llm.embed("different input")
        self.assertNotEqual(v1, v2)

    def test_embed_normalized(self) -> None:
        """Embeddings should be approximately L2-normalised."""
        import math
        vec = self.llm.embed("test input")
        norm = math.sqrt(sum(v * v for v in vec))
        self.assertAlmostEqual(norm, 1.0, places=5)

    def test_generate_returns_string(self) -> None:
        result = self.llm.generate("Hello, generate something")
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)


# ══════════════════════════════════════════════════════════════════════
#  Performance Sanity Check
# ══════════════════════════════════════════════════════════════════════


class TestPerformance(unittest.TestCase):
    """Ensure the mock pipeline completes within reasonable time."""

    def test_single_scenario_under_5_seconds(self) -> None:
        llm = MockProvider()
        orch = Orchestrator(llm)
        start = time.perf_counter()
        orch.process(
            "A deep pothole on the road near a school.",
            latitude=51.52, longitude=-0.07,
        )
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 5.0, f"Pipeline took {elapsed:.2f}s (>5s)")

    def test_three_scenarios_under_10_seconds(self) -> None:
        llm = MockProvider()
        orch = Orchestrator(llm)
        demos = [
            ("Fly-tipping", 51.5210, -0.0656),
            ("A pothole on the A205 South Circular", 51.4550, -0.0960),
            ("Streetlights out near hospital", 51.4975, -0.1185),
        ]
        start = time.perf_counter()
        for text, lat, lon in demos:
            orch.process(text, latitude=lat, longitude=lon)
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 10.0, f"3 scenarios took {elapsed:.2f}s (>10s)")


if __name__ == "__main__":
    unittest.main()
