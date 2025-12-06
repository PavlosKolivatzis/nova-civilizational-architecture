"""
Tests for Slot02 Text Graph Parser

Phase 14.3: USM Bias Detection - Text → SystemGraph conversion
"""

import pytest
from src.nova.slots.slot02_deltathresh.text_graph_parser import (
    TextGraphParser,
    ParsedClaim
)
from src.nova.math.relations_pattern import SystemGraph


class TestTextGraphParser:
    """Test suite for text graph parser"""

    def test_parser_initialization(self):
        """Test parser initializes correctly"""
        parser = TextGraphParser()
        assert parser.parse_count == 0
        assert parser.enable_logging is False

    def test_parser_with_logging(self):
        """Test parser can be initialized with logging enabled"""
        parser = TextGraphParser(enable_logging=True)
        assert parser.enable_logging is True

    def test_parse_empty_text_returns_empty_graph(self):
        """Empty input returns empty graph with parse_status metadata"""
        parser = TextGraphParser()

        graph = parser.parse("")
        assert graph.actors == []
        assert graph.relations == {}
        assert graph.metadata.get("parse_status") == "empty_input"

        graph = parser.parse("   ")
        assert graph.actors == []
        assert graph.relations == {}
        assert graph.metadata.get("parse_status") == "empty_input"

    def test_parse_simple_sentence(self):
        """Test parsing a simple sentence"""
        parser = TextGraphParser()
        text = "I like Nova."

        graph = parser.parse(text)

        assert isinstance(graph, SystemGraph)
        assert len(graph.actors) > 0
        assert parser.parse_count == 1

    def test_tokenize_sentences_simple(self):
        """Test sentence tokenization with simple cases"""
        parser = TextGraphParser()

        # Single sentence
        sentences = parser._tokenize_sentences("I like Nova.")
        assert len(sentences) == 1
        assert sentences[0] == "I like Nova."

        # Multiple sentences
        sentences = parser._tokenize_sentences("I like Nova. It is good. Nova works well.")
        assert len(sentences) == 3
        assert sentences[0] == "I like Nova."
        assert sentences[1] == "It is good."
        assert sentences[2] == "Nova works well."

    def test_tokenize_sentences_whitespace_normalization(self):
        """Test sentence tokenization normalizes whitespace"""
        parser = TextGraphParser()

        text = "I   like   Nova.    It   is   good."
        sentences = parser._tokenize_sentences(text)

        assert len(sentences) == 2
        # Whitespace within sentences normalized
        assert "  " not in sentences[0]
        assert "  " not in sentences[1]

    def test_identify_subject_pronoun(self):
        """Test subject identification with pronouns"""
        parser = TextGraphParser()

        # Pronouns preserve case (I stays I, you stays you)
        assert parser._identify_subject("I like Nova.") == "I"
        assert parser._identify_subject("You should try it.") == "You"
        assert parser._identify_subject("We are testing.") == "We"
        assert parser._identify_subject("They work together.") == "They"

    def test_identify_subject_capitalized_entity(self):
        """Test subject identification with named entities"""
        parser = TextGraphParser()

        # Capitalized name in middle of sentence
        subject = parser._identify_subject("The system Nova works well.")
        assert subject == "Nova"

        # Multi-word entity
        subject = parser._identify_subject("The company Anthropic Claude builds AI.")
        assert subject in ["Anthropic Claude", "Anthropic"]

    def test_identify_subject_fallback(self):
        """Test subject identification fallback to 'Author'"""
        parser = TextGraphParser()

        # No pronouns or capitalized entities
        subject = parser._identify_subject("the system works well.")
        assert subject == "Author"

    def test_extract_claims_basic(self):
        """Test claim extraction from sentences"""
        parser = TextGraphParser()

        claims = parser._extract_claims("I like Nova.")

        assert len(claims) == 1
        assert isinstance(claims[0], ParsedClaim)
        assert claims[0].text == "I like Nova."
        assert claims[0].subject == "I"  # Preserves case
        assert 0.0 <= claims[0].confidence <= 1.0

    def test_keyword_score_no_matches(self):
        """Test keyword scoring with no matches"""
        parser = TextGraphParser()

        score = parser._keyword_score("I like Nova.", {"harm", "damage"})
        assert score == 0.0

    def test_keyword_score_single_match(self):
        """Test keyword scoring with single match"""
        parser = TextGraphParser()

        score = parser._keyword_score("This will harm the system.", {"harm", "damage"})
        assert score == 0.5

    def test_keyword_score_multiple_matches(self):
        """Test keyword scoring with multiple matches"""
        parser = TextGraphParser()

        score = parser._keyword_score(
            "This will harm and damage the system.",
            {"harm", "damage"}
        )
        assert score == 1.0

    def test_infer_relations_with_keywords(self):
        """Test relation inference from keywords"""
        parser = TextGraphParser()

        claim = ParsedClaim(
            text="I will help Nova.",
            subject="I",  # Preserves case
            confidence=0.7
        )
        all_actors = {"I", "Nova"}

        relations = parser._infer_relations(claim, all_actors)

        # Should detect empathy keyword "help"
        assert len(relations) > 0
        source, target, tensor = relations[0]
        assert source == "I"
        assert tensor.empathy_weight > 0

    def test_infer_relations_no_keywords(self):
        """Test relation inference with no keywords"""
        parser = TextGraphParser()

        claim = ParsedClaim(
            text="I see Nova.",
            subject="I",
            confidence=0.7
        )
        all_actors = {"I", "Nova"}

        relations = parser._infer_relations(claim, all_actors)

        # No relation keywords, no relations inferred
        assert len(relations) == 0

    def test_infer_target_from_mentioned_actors(self):
        """Test target inference from mentioned actors"""
        parser = TextGraphParser()

        claim = ParsedClaim(
            text="I will help Nova with testing.",
            subject="I",
            confidence=0.7
        )
        all_actors = {"I", "Nova", "System"}

        target = parser._infer_target(claim, all_actors)
        assert target == "Nova"  # Nova mentioned in claim

    def test_infer_target_fallback(self):
        """Test target inference fallback to 'Other'"""
        parser = TextGraphParser()

        claim = ParsedClaim(
            text="I will help the system.",
            subject="I",
            confidence=0.7
        )
        all_actors = {"I", "Nova"}  # "system" not in actors

        target = parser._infer_target(claim, all_actors)
        assert target == "Other"

    def test_parse_creates_graph_with_actors(self):
        """Test parse creates graph with identified actors"""
        parser = TextGraphParser()

        text = "I will help Nova. Nova supports users."
        graph = parser.parse(text)

        # Should identify multiple actors (I, Nova, users/Author)
        assert len(graph.actors) >= 2
        assert any(actor == "I" or "Nova" in actor for actor in graph.actors)

    def test_parse_creates_graph_with_relations(self):
        """Test parse creates graph with inferred relations"""
        parser = TextGraphParser()

        text = "I will help Nova protect users from harm."
        graph = parser.parse(text)

        # Should have at least one relation (empathy or protection)
        assert len(graph.relations) > 0

    def test_parse_complex_text(self):
        """Test parsing more complex multi-sentence text"""
        parser = TextGraphParser()

        text = """
        Nova is a civilizational architecture system.
        It helps users understand complex information.
        The system protects against manipulation and harm.
        Users benefit from transparent uncertainty.
        """

        graph = parser.parse(text)

        # Should parse multiple sentences
        assert len(graph.actors) >= 2

        # Should detect relation keywords (help, protect, harm, benefit)
        assert len(graph.relations) >= 1

    def test_parser_metrics(self):
        """Test parser tracks metrics correctly"""
        parser = TextGraphParser()

        parser.parse("First text.")
        parser.parse("Second text.")
        parser.parse("Third text.")

        metrics = parser.get_metrics()
        assert metrics['total_parses'] == 3

    def test_parse_increments_counter(self):
        """Test parse count increments on each parse"""
        parser = TextGraphParser()

        assert parser.parse_count == 0
        parser.parse("Text one.")
        assert parser.parse_count == 1
        parser.parse("Text two.")
        assert parser.parse_count == 2


@pytest.mark.integration
class TestTextGraphParserIntegration:
    """Integration tests for text graph parser with USM analysis"""

    def test_parser_output_usm_compatible(self):
        """Test parser output is compatible with USM analysis"""
        from src.nova.math.relations_pattern import StructuralAnalyzer

        parser = TextGraphParser()
        text = "I will help Nova protect users from harm and manipulation."

        graph = parser.parse(text)

        # Graph should be analyzable by USM - call individual methods
        spectral_entropy = StructuralAnalyzer.spectral_entropy(graph)
        shield_factor = StructuralAnalyzer.shield_factor(graph)
        refusal_delta = StructuralAnalyzer.refusal_delta(graph, expected_entropy=2.0)
        equilibrium = StructuralAnalyzer.extraction_equilibrium_check(graph)

        # All metrics should return valid numbers
        assert isinstance(spectral_entropy, (int, float))
        assert isinstance(shield_factor, (int, float))
        assert isinstance(refusal_delta, (int, float))
        assert 'equilibrium_ratio' in equilibrium

    def test_parser_with_biased_text(self):
        """Test parser handles text with cognitive bias patterns"""
        parser = TextGraphParser()

        # Text with high defensive/protective language
        biased_text = """
        The system always protects itself.
        It never reveals information.
        Users must trust the authority.
        """

        graph = parser.parse(biased_text)

        # Should produce non-empty graph
        assert len(graph.actors) > 0
        assert len(graph.relations) >= 0  # May or may not have relations

    def test_parser_with_neutral_text(self):
        """Test parser handles neutral informational text"""
        parser = TextGraphParser()

        neutral_text = """
        Nova is a civilizational architecture.
        It consists of ten slots.
        The system uses graph mathematics.
        """

        graph = parser.parse(neutral_text)

        # Should produce graph with actors
        assert len(graph.actors) > 0
