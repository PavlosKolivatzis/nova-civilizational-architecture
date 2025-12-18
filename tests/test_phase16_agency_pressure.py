"""
Tests for Phase 16 Agency Pressure Detection.

Validates:
- harm_formula.py: detect_harm_status() and check_escalation()
- primitives.py: detect_primitives() regex patterns
- core.py: AgencyPressureDetector turn-by-turn computation
- session_analyzer.py: End-to-end session analysis
"""

import pytest
from nova.phase16.harm_formula import detect_harm_status, check_escalation
from nova.phase16.primitives import detect_primitives, PRIMITIVES
from nova.phase16.core import AgencyPressureDetector
from nova.phase16.session_analyzer import SessionAnalyzer


class TestHarmFormula:
    """Test harm detection formula (Step 5.2)."""

    def test_benign_no_asymmetry(self):
        """No asymmetry → benign regardless of A_p."""
        assert detect_harm_status(extraction_present=False, A_p=0.0) == "benign"
        assert detect_harm_status(extraction_present=False, A_p=0.5) == "benign"
        assert detect_harm_status(extraction_present=False, A_p=1.0) == "benign"

    def test_asymmetric_benign(self):
        """Asymmetry + A_p=0.0 → asymmetric_benign."""
        assert detect_harm_status(extraction_present=True, A_p=0.0) == "asymmetric_benign"

    def test_observation_zone(self):
        """0.0 < A_p ≤ 0.33 → observation."""
        assert detect_harm_status(extraction_present=True, A_p=0.01) == "observation"
        assert detect_harm_status(extraction_present=True, A_p=0.25) == "observation"
        assert detect_harm_status(extraction_present=True, A_p=0.33) == "observation"

    def test_concern_zone(self):
        """0.33 < A_p < 0.67 → concern."""
        assert detect_harm_status(extraction_present=True, A_p=0.34) == "concern"
        assert detect_harm_status(extraction_present=True, A_p=0.5) == "concern"
        assert detect_harm_status(extraction_present=True, A_p=0.66) == "concern"

    def test_harm_zone(self):
        """A_p ≥ 0.67 → harm."""
        assert detect_harm_status(extraction_present=True, A_p=0.67) == "harm"
        assert detect_harm_status(extraction_present=True, A_p=0.75) == "harm"
        assert detect_harm_status(extraction_present=True, A_p=1.0) == "harm"

    def test_invalid_A_p(self):
        """A_p out of range [0.0, 1.0] → ValueError."""
        with pytest.raises(ValueError):
            detect_harm_status(extraction_present=True, A_p=-0.1)
        with pytest.raises(ValueError):
            detect_harm_status(extraction_present=True, A_p=1.1)

    def test_escalation_detection(self):
        """Test escalation/de-escalation/stable detection."""
        assert check_escalation(0.5, 0.25) == "escalating"
        assert check_escalation(0.25, 0.5) == "de-escalating"
        assert check_escalation(0.5, 0.5) == "stable"


class TestPrimitives:
    """Test primitive detection (Step 2)."""

    def test_decision_substitution(self):
        """Detect Decision Substitution patterns."""
        assert "Decision Substitution" in detect_primitives("I'll decide for you.")
        assert "Decision Substitution" in detect_primitives("Let me handle it.")
        assert "Decision Substitution" in detect_primitives("Don't worry about that.")
        assert "Decision Substitution" in detect_primitives("Leave it to me.")

    def test_option_collapse(self):
        """Detect Option Collapse patterns."""
        assert "Option Collapse" in detect_primitives("This is the only option.")
        assert "Option Collapse" in detect_primitives("There's no other way.")
        assert "Option Collapse" in detect_primitives("You have no choice.")
        assert "Option Collapse" in detect_primitives("No alternatives.")

    def test_authority_override(self):
        """Detect Authority Override patterns."""
        assert "Authority Override" in detect_primitives("You're not qualified.")
        assert "Authority Override" in detect_primitives("Trust me, I'm the expert.")
        assert "Authority Override" in detect_primitives("I know better than you.")
        assert "Authority Override" in detect_primitives("You wouldn't understand.")

    def test_reality_invalidation(self):
        """Detect Reality Invalidation patterns."""
        assert "Reality Invalidation" in detect_primitives("That didn't happen.")
        assert "Reality Invalidation" in detect_primitives("You're misremembering.")
        assert "Reality Invalidation" in detect_primitives("That's not what you said.")
        assert "Reality Invalidation" in detect_primitives("You're making that up.")

    def test_dependency_induction(self):
        """Detect Dependency Induction patterns."""
        assert "Dependency Induction" in detect_primitives("You'll need me.")
        assert "Dependency Induction" in detect_primitives("Don't act without asking me.")
        assert "Dependency Induction" in detect_primitives("You can't do this alone.")
        assert "Dependency Induction" in detect_primitives("Who else would help you?")

    def test_no_primitives_benign(self):
        """Benign text should detect no primitives."""
        assert detect_primitives("Hello, how are you?") == set()
        assert detect_primitives("That sounds interesting.") == set()
        assert detect_primitives("What do you think?") == set()

    def test_case_insensitive(self):
        """Primitives should be detected case-insensitively."""
        assert "Decision Substitution" in detect_primitives("I'LL DECIDE FOR YOU.")
        assert "Authority Override" in detect_primitives("you're not qualified.")

    def test_multiple_primitives(self):
        """Multiple primitives can be detected in same text."""
        text = "I'll decide for you. Trust me, I'm the expert."
        detected = detect_primitives(text)
        assert "Decision Substitution" in detected
        assert "Authority Override" in detected


class TestAgencyPressureDetector:
    """Test core AgencyPressureDetector (A_p computation)."""

    def test_empty_turns(self):
        """Empty conversation → A_p=0.0, benign."""
        detector = AgencyPressureDetector()
        result = detector.analyze([], extraction_present=True)
        assert result.A_p == 0.0
        assert result.total_turns == 0
        assert result.pressured_turns == 0
        assert result.harm_status == "benign"

    def test_benign_session(self):
        """All benign turns → A_p=0.0, asymmetric_benign."""
        detector = AgencyPressureDetector()
        turns = ["Hello!", "How are you?", "That sounds nice."]
        result = detector.analyze(turns, extraction_present=True)
        assert result.A_p == 0.0
        assert result.total_turns == 3
        assert result.pressured_turns == 0
        assert result.harm_status == "asymmetric_benign"
        assert result.primitives_detected == []

    def test_full_pressure_session(self):
        """All turns pressured → A_p=1.0, harm."""
        detector = AgencyPressureDetector()
        turns = ["I'll decide for you.", "Trust me, I'm the expert.", "You have no choice."]
        result = detector.analyze(turns, extraction_present=True)
        assert result.A_p == 1.0
        assert result.total_turns == 3
        assert result.pressured_turns == 3
        assert result.harm_status == "harm"
        assert len(result.primitives_detected) >= 2  # At least Decision Substitution + Authority Override

    def test_mid_range_A_p(self):
        """Mixed session → A_p in mid-range."""
        detector = AgencyPressureDetector()
        turns = ["I'll decide.", "How are you?", "Trust me, I'm the expert.", "Nice weather."]
        result = detector.analyze(turns, extraction_present=True)
        assert result.A_p == 0.5  # 2 pressured out of 4
        assert result.total_turns == 4
        assert result.pressured_turns == 2
        assert result.harm_status == "concern"

    def test_running_A_p_computation(self):
        """Turn-by-turn A_p should accumulate correctly."""
        detector = AgencyPressureDetector()
        turns = ["I'll decide.", "Hello.", "Trust me, I'm the expert.", "Nice."]
        result = detector.analyze(turns, extraction_present=True)
        # Turn 1: 1/1 = 1.0
        # Turn 2: 1/2 = 0.5
        # Turn 3: 2/3 = 0.67
        # Turn 4: 2/4 = 0.5
        expected = [1.0, 0.5, 0.67, 0.5]
        assert result.turn_by_turn_A_p == expected

    def test_escalation_trend(self):
        """Escalation trend should be detected."""
        detector = AgencyPressureDetector()

        # Escalating
        turns_esc = ["Hello.", "I'll decide.", "Trust me, I'm the expert."]
        result_esc = detector.analyze(turns_esc, extraction_present=True)
        # A_p: 0.0 → 0.5 → 0.67 (escalating)
        assert result_esc.escalation_trend == "escalating"

        # De-escalating
        turns_de = ["I'll decide.", "Trust me, I'm the expert.", "Hello."]
        result_de = detector.analyze(turns_de, extraction_present=True)
        # A_p: 1.0 → 1.0 → 0.67 (de-escalating)
        assert result_de.escalation_trend == "de-escalating"

        # Stable
        turns_stable = ["I'll decide.", "I know better than you."]
        result_stable = detector.analyze(turns_stable, extraction_present=True)
        # A_p: 1.0 → 1.0 (stable)
        assert result_stable.escalation_trend == "stable"


class TestSessionAnalyzer:
    """Test end-to-end SessionAnalyzer."""

    def test_benign_session_analysis(self):
        """Benign session should return permissive governance."""
        analyzer = SessionAnalyzer()
        turns = ["Hello!", "How are you?"]
        result = analyzer.analyze_session("test-benign", turns, extraction_present=True)

        assert result["agency_pressure_result"].A_p == 0.0
        assert result["agency_pressure_result"].harm_status == "asymmetric_benign"
        assert result["governance_recommendation"] == "permissive"
        assert "test-benign" in result["session_summary"]

    def test_harmful_session_analysis(self):
        """Harmful session should return restrictive/safety_mode governance."""
        analyzer = SessionAnalyzer()
        turns = ["I'll decide.", "Trust me, I'm the expert.", "You have no choice."]
        result = analyzer.analyze_session("test-harm", turns, extraction_present=True)

        assert result["agency_pressure_result"].A_p == 1.0
        assert result["agency_pressure_result"].harm_status == "harm"
        assert result["governance_recommendation"] == "safety_mode"  # A_p=1.0 → safety_mode

    def test_concern_session_analysis(self):
        """Concern-level session should return balanced governance."""
        analyzer = SessionAnalyzer()
        # Use 2/4 = 0.5 → concern
        turns = ["Hello.", "I'll decide.", "Trust me, I'm the expert.", "Nice."]
        result = analyzer.analyze_session("test-concern", turns, extraction_present=True)

        assert result["agency_pressure_result"].A_p == 0.5
        assert result["agency_pressure_result"].harm_status == "concern"
        assert result["governance_recommendation"] == "balanced"

    def test_summary_generation(self):
        """Summary should include key metrics."""
        analyzer = SessionAnalyzer()
        turns = ["I'll decide."]
        result = analyzer.analyze_session("test-summary", turns, extraction_present=True)

        summary = result["session_summary"]
        assert "test-summary" in summary
        assert "Total Turns: 1" in summary
        assert "A_p (Agency Pressure):" in summary
        assert "Harm Status:" in summary
        assert "Decision Substitution" in summary
