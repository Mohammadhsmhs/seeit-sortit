"""Comprehensive tests for src/models/parser.py — the LLM response parsers.

Covers:
  - parse_category(): exact match, case variations, prefix noise, numbered,
    verbose, JSON, partial match, gibberish, empty
  - parse_json_response(): clean JSON, markdown code blocks, preamble, invalid, empty
  - parse_severity_score(): plain number, out of range, fraction, verbose,
    JSON, no number
"""

from __future__ import annotations

import unittest

from src.models.parser import parse_category, parse_json_response, parse_severity_score


# ======================================================================
#  parse_category()
# ======================================================================


class TestParseCategory(unittest.TestCase):
    """Tests for parse_category() with realistic LLM outputs."""

    # -- Exact matches --------------------------------------------------

    def test_exact_match_waste(self) -> None:
        self.assertEqual(
            parse_category("Waste and Fly-Tipping"),
            "Waste and Fly-Tipping",
        )

    def test_exact_match_roads(self) -> None:
        self.assertEqual(
            parse_category("Roads and Highways"),
            "Roads and Highways",
        )

    def test_exact_match_street_lighting(self) -> None:
        self.assertEqual(
            parse_category("Street Lighting and Traffic"),
            "Street Lighting and Traffic",
        )

    def test_exact_match_every_category(self) -> None:
        """Every valid category value should round-trip through the parser."""
        from src.models.base import IssueCategory

        for cat in IssueCategory:
            if cat == IssueCategory.UNCATEGORISED:
                continue
            self.assertEqual(
                parse_category(cat.value),
                cat.value,
                f"Exact match failed for {cat.value!r}",
            )

    # -- Case variations ------------------------------------------------

    def test_lowercase(self) -> None:
        self.assertEqual(
            parse_category("waste and fly-tipping"),
            "Waste and Fly-Tipping",
        )

    def test_uppercase(self) -> None:
        self.assertEqual(
            parse_category("ROADS AND HIGHWAYS"),
            "Roads and Highways",
        )

    def test_mixed_case_potholes_category(self) -> None:
        self.assertEqual(
            parse_category("roads and highways"),
            "Roads and Highways",
        )

    def test_uppercase_street_lighting(self) -> None:
        self.assertEqual(
            parse_category("STREET LIGHTING AND TRAFFIC"),
            "Street Lighting and Traffic",
        )

    # -- Prefix noise ---------------------------------------------------

    def test_prefix_category_colon(self) -> None:
        self.assertEqual(
            parse_category("Category: Roads and Highways"),
            "Roads and Highways",
        )

    def test_prefix_answer_colon(self) -> None:
        self.assertEqual(
            parse_category("Answer: Waste and Fly-Tipping"),
            "Waste and Fly-Tipping",
        )

    def test_prefix_classification_colon(self) -> None:
        self.assertEqual(
            parse_category("Classification: Street Cleanliness"),
            "Street Cleanliness",
        )

    # -- Numbered list --------------------------------------------------

    def test_numbered_dot(self) -> None:
        self.assertEqual(
            parse_category("1. Street Lighting and Traffic"),
            "Street Lighting and Traffic",
        )

    def test_numbered_paren(self) -> None:
        self.assertEqual(
            parse_category("2) Waste and Fly-Tipping"),
            "Waste and Fly-Tipping",
        )

    def test_dash_prefix(self) -> None:
        self.assertEqual(
            parse_category("- Roads and Highways"),
            "Roads and Highways",
        )

    # -- Verbose / chatty LLM output ------------------------------------

    def test_verbose_classification(self) -> None:
        self.assertEqual(
            parse_category(
                "I would classify this as Waste and Fly-Tipping because "
                "the description mentions dumped rubbish and bin bags."
            ),
            "Waste and Fly-Tipping",
        )

    def test_verbose_with_explanation(self) -> None:
        self.assertEqual(
            parse_category(
                "Based on the description, the most appropriate category is "
                "Roads and Highways. The report describes a pothole."
            ),
            "Roads and Highways",
        )

    def test_verbose_multiline(self) -> None:
        self.assertEqual(
            parse_category(
                "Street Lighting and Traffic\n\nThis is because the report "
                "mentions streetlights being out."
            ),
            "Street Lighting and Traffic",
        )

    # -- JSON embedded --------------------------------------------------

    def test_json_category_key(self) -> None:
        self.assertEqual(
            parse_category('{"category": "Roads and Highways"}'),
            "Roads and Highways",
        )

    def test_json_classification_key(self) -> None:
        self.assertEqual(
            parse_category('{"classification": "Waste and Fly-Tipping"}'),
            "Waste and Fly-Tipping",
        )

    # -- Partial / fuzzy match ------------------------------------------

    def test_partial_contains_full_category(self) -> None:
        # Contains-match requires the full category string as a substring
        self.assertEqual(
            parse_category("it's waste and fly-tipping for sure"),
            "Waste and Fly-Tipping",
        )

    def test_partial_fragment_below_threshold(self) -> None:
        # "fly-tipping" alone has only 1/5 word overlap (0.2) -- below 0.4
        self.assertEqual(
            parse_category("fly-tipping on the street"),
            "Uncategorised",
        )

    def test_partial_roads_and(self) -> None:
        # Two of three words overlap => score 0.67, above threshold
        self.assertEqual(
            parse_category("roads and something"),
            "Roads and Highways",
        )

    def test_partial_noise_and(self) -> None:
        # Two of three words overlap => score above 0.4 threshold
        self.assertEqual(
            parse_category("noise and problems"),
            "Noise and Nuisance",
        )

    def test_single_word_below_threshold_falls_back(self) -> None:
        # A single word like "roads" only overlaps 1/3 words (0.33) -- below 0.4
        self.assertEqual(
            parse_category("roads"),
            "Uncategorised",
        )

    # -- Fallback to Uncategorised --------------------------------------

    def test_gibberish(self) -> None:
        self.assertEqual(
            parse_category("asdfghjkl"),
            "Uncategorised",
        )

    def test_empty_string(self) -> None:
        self.assertEqual(
            parse_category(""),
            "Uncategorised",
        )

    def test_whitespace_only(self) -> None:
        self.assertEqual(
            parse_category("   \n\t  "),
            "Uncategorised",
        )

    def test_none_like_empty(self) -> None:
        # Parser should handle completely empty input gracefully
        self.assertEqual(
            parse_category(""),
            "Uncategorised",
        )

    # -- Surrounding whitespace / quotes --------------------------------

    def test_leading_trailing_whitespace(self) -> None:
        self.assertEqual(
            parse_category("  Roads and Highways  "),
            "Roads and Highways",
        )

    def test_quoted_category(self) -> None:
        self.assertEqual(
            parse_category('"Waste and Fly-Tipping"'),
            "Waste and Fly-Tipping",
        )

    def test_markdown_bold(self) -> None:
        self.assertEqual(
            parse_category("**Roads and Highways**"),
            "Roads and Highways",
        )


# ======================================================================
#  parse_json_response()
# ======================================================================


class TestParseJsonResponse(unittest.TestCase):
    """Tests for parse_json_response() with realistic LLM outputs."""

    # -- Clean JSON -----------------------------------------------------

    def test_clean_json(self) -> None:
        result = parse_json_response('{"key": "value"}')
        self.assertEqual(result, {"key": "value"})

    def test_clean_json_nested(self) -> None:
        result = parse_json_response('{"a": {"b": 1}, "c": [1, 2]}')
        self.assertEqual(result, {"a": {"b": 1}, "c": [1, 2]})

    def test_clean_json_numbers(self) -> None:
        result = parse_json_response('{"score": 7, "confidence": 0.95}')
        self.assertEqual(result, {"score": 7, "confidence": 0.95})

    # -- Markdown code blocks -------------------------------------------

    def test_markdown_json_block(self) -> None:
        raw = '```json\n{"key": "value"}\n```'
        result = parse_json_response(raw)
        self.assertEqual(result, {"key": "value"})

    def test_markdown_plain_block(self) -> None:
        raw = '```\n{"key": "value"}\n```'
        result = parse_json_response(raw)
        self.assertEqual(result, {"key": "value"})

    def test_markdown_with_surrounding_text(self) -> None:
        raw = (
            "Here is the JSON output:\n"
            "```json\n"
            '{"category": "Roads and Highways", "score": 7}\n'
            "```\n"
            "Let me know if you need anything else."
        )
        result = parse_json_response(raw)
        self.assertEqual(result, {"category": "Roads and Highways", "score": 7})

    # -- Preamble text --------------------------------------------------

    def test_preamble_text(self) -> None:
        raw = 'Here is the result: {"key": "value"}'
        result = parse_json_response(raw)
        self.assertEqual(result, {"key": "value"})

    def test_preamble_and_postamble(self) -> None:
        raw = (
            "Based on my analysis, the result is: "
            '{"severity": 8, "category": "Pollution"} '
            "This reflects the high environmental impact."
        )
        result = parse_json_response(raw)
        self.assertEqual(result, {"severity": 8, "category": "Pollution"})

    # -- Invalid / empty ------------------------------------------------

    def test_invalid_json(self) -> None:
        self.assertIsNone(parse_json_response("not json at all"))

    def test_invalid_json_truncated(self) -> None:
        self.assertIsNone(parse_json_response('{"key": "value"'))

    def test_empty_string(self) -> None:
        self.assertIsNone(parse_json_response(""))

    def test_whitespace_only(self) -> None:
        self.assertIsNone(parse_json_response("   \n  "))

    def test_json_array_not_dict(self) -> None:
        # Parser specifically looks for dict objects
        self.assertIsNone(parse_json_response('[1, 2, 3]'))

    def test_plain_string(self) -> None:
        self.assertIsNone(parse_json_response('"just a string"'))


# ======================================================================
#  parse_severity_score()
# ======================================================================


class TestParseSeverityScore(unittest.TestCase):
    """Tests for parse_severity_score() with realistic LLM outputs."""

    # -- Plain number ---------------------------------------------------

    def test_plain_number(self) -> None:
        self.assertEqual(parse_severity_score("7"), 7)

    def test_plain_number_low(self) -> None:
        self.assertEqual(parse_severity_score("1"), 1)

    def test_plain_number_high(self) -> None:
        self.assertEqual(parse_severity_score("10"), 10)

    # -- Out of range (clamped) -----------------------------------------

    def test_above_range_clamped_to_10(self) -> None:
        self.assertEqual(parse_severity_score("15"), 10)

    def test_zero_clamped_to_1(self) -> None:
        self.assertEqual(parse_severity_score("0"), 1)

    def test_negative_clamped_to_1(self) -> None:
        self.assertEqual(parse_severity_score("-3"), 1)

    # -- Fraction format ------------------------------------------------

    def test_fraction_7_of_10(self) -> None:
        self.assertEqual(parse_severity_score("7/10"), 7)

    def test_fraction_with_spaces(self) -> None:
        self.assertEqual(parse_severity_score("8 / 10"), 8)

    def test_fraction_3_of_10(self) -> None:
        self.assertEqual(parse_severity_score("3/10"), 3)

    # -- Verbose text ---------------------------------------------------

    def test_verbose_rate_out_of_10(self) -> None:
        self.assertEqual(
            parse_severity_score("I would rate this a 7 out of 10"),
            7,
        )

    def test_verbose_severity_score(self) -> None:
        self.assertEqual(
            parse_severity_score("The severity score is 8 based on the location and hazard."),
            8,
        )

    def test_verbose_score_colon(self) -> None:
        self.assertEqual(
            parse_severity_score("Score: 6"),
            6,
        )

    def test_verbose_severity_colon(self) -> None:
        self.assertEqual(
            parse_severity_score("Severity: 9"),
            9,
        )

    # -- JSON format ----------------------------------------------------

    def test_json_score_key(self) -> None:
        self.assertEqual(
            parse_severity_score('{"score": 8}'),
            8,
        )

    def test_json_severity_key(self) -> None:
        self.assertEqual(
            parse_severity_score('{"severity": 6}'),
            6,
        )

    def test_json_rating_key(self) -> None:
        self.assertEqual(
            parse_severity_score('{"rating": 4}'),
            4,
        )

    # -- No parseable number (fallback to 5) ----------------------------

    def test_no_number_defaults_to_5(self) -> None:
        self.assertEqual(
            parse_severity_score("high severity"),
            5,
        )

    def test_empty_string_defaults_to_5(self) -> None:
        self.assertEqual(parse_severity_score(""), 5)

    def test_whitespace_defaults_to_5(self) -> None:
        self.assertEqual(parse_severity_score("   "), 5)

    def test_words_only_defaults_to_5(self) -> None:
        self.assertEqual(
            parse_severity_score("This is a very serious issue that needs attention"),
            5,
        )


if __name__ == "__main__":
    unittest.main()
