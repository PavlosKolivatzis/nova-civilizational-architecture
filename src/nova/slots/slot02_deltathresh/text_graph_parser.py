"""
Slot02 Text Graph Parser - Convert Text to SystemGraph

Phase 14.3: USM Bias Detection for Input Analysis
Transforms plain text → SystemGraph for USM structural analysis.

Scope:
- NO external NLP dependencies (SpaCy removed)
- Simple heuristics for sentence/claim extraction
- Syntactic pattern matching for relation inference
- Feature flag: NOVA_ENABLE_BIAS_DETECTION=0 (default off)

Invariant Compliance:
- #5 Reversibility: Feature flag gated
- #6 Transparent uncertainty: Returns confidence scores
- #7 Observability: Logs parsing metrics
"""

import re
import logging
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass

from src.nova.math.relations_pattern import SystemGraph, RelationTensor

logger = logging.getLogger(__name__)


@dataclass
class ParsedClaim:
    """A claim extracted from text"""
    text: str
    subject: str  # Actor who makes/holds the claim
    confidence: float  # 0.0-1.0 confidence in extraction


class TextGraphParser:
    """
    Convert plain text to SystemGraph for USM analysis.

    Strategy:
    1. Sentence tokenization (regex-based)
    2. Claim extraction (heuristic patterns)
    3. Actor identification (named entities via simple patterns)
    4. Relation inference (syntactic patterns)

    Limitations (Phase 2C):
    - No coreference resolution
    - Simple pronoun handling (I, you, we, they)
    - Basic sentiment → RelationTensor mapping
    - No cross-sentence relation inference

    Future (Phase 2D+):
    - Lightweight NER (no external deps)
    - Improved relation extraction
    - Multi-sentence coherence analysis
    """

    # Sentence boundary detection patterns
    SENTENCE_DELIMITERS = re.compile(r'(?<=[.!?])\s+(?=[A-Z])')

    # Actor patterns (simple NER approximation)
    PRONOUN_ACTORS = {'I', 'you', 'we', 'they', 'he', 'she', 'it'}
    CAPITALIZED_ENTITY = re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b')

    # Relation keyword patterns
    PROFIT_KEYWORDS = {'profit', 'gain', 'benefit', 'advantage', 'value', 'extract'}
    HARM_KEYWORDS = {'harm', 'damage', 'hurt', 'exploit', 'manipulate', 'deceive'}
    INFO_KEYWORDS = {'inform', 'tell', 'share', 'communicate', 'reveal', 'disclose'}
    EMPATHY_KEYWORDS = {'empathy', 'care', 'protect', 'support', 'help', 'understand'}

    def __init__(self, enable_logging: bool = False):
        """
        Initialize text graph parser.

        Args:
            enable_logging: If True, log parsing details
        """
        self.enable_logging = enable_logging
        self.parse_count = 0

    def parse(self, text: str) -> SystemGraph:
        """
        Parse text into SystemGraph.

        Args:
            text: Input text to parse

        Returns:
            SystemGraph with actors and relations

        Raises:
            ValueError: If text is empty or invalid
        """
        if not text or not text.strip():
            raise ValueError("Cannot parse empty text")

        self.parse_count += 1

        # Step 1: Sentence tokenization
        sentences = self._tokenize_sentences(text)

        if self.enable_logging:
            logger.info(f"Parsed {len(sentences)} sentences from {len(text)} chars")

        # Step 2: Extract claims and actors
        claims = []
        actors = set()

        for sentence in sentences:
            sentence_claims = self._extract_claims(sentence)
            claims.extend(sentence_claims)
            actors.update(claim.subject for claim in sentence_claims)

        # Step 3: Build SystemGraph
        # SystemGraph requires actors list and relations dict at init
        relations_dict = {}

        # Step 4: Infer relations from claims
        for claim in claims:
            relations = self._infer_relations(claim, actors)
            for (source, target, tensor) in relations:
                relations_dict[(source, target)] = tensor
                # Ensure both source and target are in actors set
                actors.add(source)
                actors.add(target)

        actor_list = list(actors)
        G = SystemGraph(actors=actor_list, relations=relations_dict)

        if self.enable_logging:
            logger.info(
                f"Graph: {len(G.actors)} actors, {len(G.relations)} relations"
            )

        return G

    def _tokenize_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using simple heuristics.

        Args:
            text: Input text

        Returns:
            List of sentence strings
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Split on sentence delimiters
        sentences = self.SENTENCE_DELIMITERS.split(text)

        # Filter empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    def _extract_claims(self, sentence: str) -> List[ParsedClaim]:
        """
        Extract claims from a sentence.

        Heuristic: Each sentence is treated as a claim.
        Subject identification:
        - First pronoun or capitalized entity
        - Fallback: "Author"

        Args:
            sentence: Sentence text

        Returns:
            List of ParsedClaim objects
        """
        # Identify subject (simple first-pass heuristic)
        subject = self._identify_subject(sentence)

        claim = ParsedClaim(
            text=sentence,
            subject=subject,
            confidence=0.7  # Heuristic extraction confidence
        )

        return [claim]

    def _identify_subject(self, sentence: str) -> str:
        """
        Identify the subject actor of a sentence.

        Strategy:
        1. Look for pronouns (I, you, we, they, etc.)
        2. Look for capitalized entities (Name, Organization)
        3. Fallback to "Author"

        Args:
            sentence: Sentence text

        Returns:
            Subject actor name (preserves capitalization)
        """
        words = sentence.split()

        # Check for pronouns (case-insensitive check, but preserve original case)
        for word in words:
            if word.lower() in {p.lower() for p in self.PRONOUN_ACTORS}:
                return word  # Return as-is (preserves "I" vs "i")

        # Check for capitalized entities (excluding first word if start of sentence)
        matches = self.CAPITALIZED_ENTITY.findall(sentence)
        if matches:
            # Skip first match if it's the first word (likely capitalized for sentence start)
            first_word = sentence.split()[0] if sentence else ""
            candidates = [m for m in matches if m != first_word or len(matches) == 1]
            if candidates:
                return candidates[0]

        # Fallback
        return "Author"

    def _infer_relations(
        self,
        claim: ParsedClaim,
        all_actors: set
    ) -> List[Tuple[str, str, RelationTensor]]:
        """
        Infer relations from a claim using keyword patterns.

        Strategy:
        - Scan claim text for relation keywords
        - Map keywords → RelationTensor weights
        - Generate (source, target, tensor) tuples

        Limitations:
        - No sophisticated NLP (dependency parsing, semantic role labeling)
        - Binary relations only (no n-ary)
        - Sentiment approximation

        Args:
            claim: Parsed claim
            all_actors: Set of all identified actors

        Returns:
            List of (source, target, RelationTensor) tuples
        """
        relations = []
        text_lower = claim.text.lower()

        # Determine relation weights from keywords
        profit_weight = self._keyword_score(text_lower, self.PROFIT_KEYWORDS)
        harm_weight = self._keyword_score(text_lower, self.HARM_KEYWORDS)
        info_weight = self._keyword_score(text_lower, self.INFO_KEYWORDS)
        empathy_weight = self._keyword_score(text_lower, self.EMPATHY_KEYWORDS)

        # If any relation keywords found, create relation
        if profit_weight + harm_weight + info_weight + empathy_weight > 0:
            tensor = RelationTensor(
                profit_weight=profit_weight,
                harm_weight=harm_weight,
                info_weight=info_weight,
                empathy_weight=empathy_weight
            )

            # Infer target from other actors mentioned in claim
            target = self._infer_target(claim, all_actors)

            relations.append((claim.subject, target, tensor))

        return relations

    def _keyword_score(self, text: str, keywords: set) -> float:
        """
        Compute keyword match score (0.0-1.0).

        Args:
            text: Lowercased text
            keywords: Set of keywords to match

        Returns:
            Score based on keyword presence
        """
        matches = sum(1 for kw in keywords if kw in text)
        if matches == 0:
            return 0.0
        # Normalize: 1 match = 0.5, 2+ matches = 1.0
        return min(matches * 0.5, 1.0)

    def _infer_target(self, claim: ParsedClaim, all_actors: set) -> str:
        """
        Infer relation target from claim text.

        Strategy:
        - Look for other actors mentioned in claim
        - Fallback to "Other"

        Args:
            claim: Parsed claim
            all_actors: Set of all identified actors

        Returns:
            Target actor name
        """
        # Find actors mentioned in claim text (excluding subject)
        mentioned = [
            actor for actor in all_actors
            if actor != claim.subject and actor.lower() in claim.text.lower()
        ]

        if mentioned:
            return mentioned[0]

        # Fallback: generic "Other"
        return "Other"

    def get_metrics(self) -> Dict[str, int]:
        """
        Get parser performance metrics.

        Returns:
            Dict with parsing statistics
        """
        return {
            'total_parses': self.parse_count
        }
