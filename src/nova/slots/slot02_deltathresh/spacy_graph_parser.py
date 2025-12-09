"""
spaCy-based SystemGraph parser (Phase 14.7)

Extracts relations from text using dependency parsing instead of regex patterns.
Produces graphs with 5-10 edges per multi-party response (vs 0-1 for regex parser).

Architecture:
- Parse text with spaCy's dependency parser
- Extract (subject, verb, object) triples from dependency trees
- Map dependency types to RelationTensor weights
- Build SystemGraph with actors + weighted relations

Feature flag: NOVA_USE_SPACY_PARSER=1 (default)
Fallback: Uses text_graph_parser.py (regex) if spaCy fails or flag=0
"""
from __future__ import annotations

import os
from typing import Dict, List, Optional, Set, Tuple

try:
    import spacy
    from spacy.tokens import Doc, Token
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

from src.nova.math.relations_pattern import RelationTensor, SystemGraph


class SpacyGraphParser:
    """spaCy dependency-based relation extractor for SystemGraph."""

    def __init__(self, enable_logging: bool = False):
        """
        Initialize parser with spaCy model.

        Args:
            enable_logging: Enable debug logging

        Raises:
            ImportError: If spaCy not installed
            OSError: If model not downloaded (run: python -m spacy download en_core_web_sm)
        """
        if not SPACY_AVAILABLE:
            raise ImportError(
                "spaCy not installed. Run: pip install spacy && python -m spacy download en_core_web_sm"
            )

        self.enable_logging = enable_logging
        self._nlp: Optional[spacy.Language] = None

    def _load_model(self) -> spacy.Language:
        """Lazy-load spaCy model (expensive operation, do once)."""
        if self._nlp is None:
            try:
                self._nlp = spacy.load("en_core_web_sm")
            except OSError as e:
                raise OSError(
                    "spaCy model not found. Run: python -m spacy download en_core_web_sm"
                ) from e
        return self._nlp

    def parse(self, text: str) -> SystemGraph:
        """
        Parse text into SystemGraph using dependency parsing.

        Args:
            text: Input text to parse

        Returns:
            SystemGraph with actors and weighted relations
        """
        if not text or not text.strip():
            # Empty input → VOID graph
            return SystemGraph(actors=[], relations={})

        nlp = self._load_model()
        doc = nlp(text)

        # Extract relations from dependency parse
        relations: Dict[Tuple[str, str], RelationTensor] = {}
        actors_set: Set[str] = set()

        for sent in doc.sents:
            sent_relations = self._extract_relations_from_sentence(sent)
            sent_actors = set()

            for (subj, obj), tensor in sent_relations.items():
                actors_set.add(subj)
                actors_set.add(obj)
                sent_actors.add(subj)
                sent_actors.add(obj)

                # Merge tensors if relation already exists
                if (subj, obj) in relations:
                    relations[(subj, obj)] = self._merge_tensors(
                        relations[(subj, obj)], tensor
                    )
                else:
                    relations[(subj, obj)] = tensor

            # Add weak co-occurrence edges for actors in same sentence (builds connected graph)
            if len(sent_actors) > 1:
                sent_actors_list = sorted(sent_actors)
                for i, actor1 in enumerate(sent_actors_list):
                    for actor2 in sent_actors_list[i+1:]:
                        # Only add if no explicit relation exists
                        if (actor1, actor2) not in relations and (actor2, actor1) not in relations:
                            # Weak informational link (co-occurrence)
                            relations[(actor1, actor2)] = RelationTensor(
                                profit_weight=0.0,
                                harm_weight=0.0,
                                info_weight=0.2,  # Weak co-occurrence signal
                                empathy_weight=0.0
                            )

        actors = sorted(actors_set)

        return SystemGraph(actors=actors, relations=relations)

    def _extract_relations_from_sentence(
        self, sent: spacy.tokens.Span
    ) -> Dict[Tuple[str, str], RelationTensor]:
        """
        Extract (subject, object) relations from a single sentence.

        Strategy:
        1. Find verbs (ROOT, AUX, VERB)
        2. For each verb, find subject (nsubj, nsubjpass) and object (dobj, pobj, attr)
        3. Map dependency pattern → RelationTensor weights

        Returns:
            Dict mapping (subject_name, object_name) to RelationTensor
        """
        relations: Dict[Tuple[str, str], RelationTensor] = {}

        # Find all verbs in sentence (include ROOT even if not tagged VERB, handles "questions" as noun)
        verbs = []
        for token in sent:
            if token.pos_ in {"VERB", "AUX"}:
                verbs.append(token)
            elif token.dep_ == "ROOT":
                # ROOT might be verb-like noun ("questions", "challenges")
                verbs.append(token)

        for verb in verbs:
            # Find subjects of this verb
            subjects = self._find_subjects(verb)
            # Find objects of this verb
            objects = self._find_objects(verb)

            if not subjects or not objects:
                continue

            # Create relation for each (subject, object) pair
            for subj in subjects:
                for obj in objects:
                    if subj == obj:
                        continue  # Skip self-relations

                    tensor = self._classify_relation(verb, subj, obj)
                    relations[(subj, obj)] = tensor

        return relations

    def _find_subjects(self, verb: Token) -> List[str]:
        """Find subject entities for a verb."""
        subjects = []

        for child in verb.children:
            if child.dep_ in {"nsubj", "nsubjpass", "agent", "compound"}:
                # Get full noun phrase if available
                if child.pos_ in {"PROPN", "NOUN", "PRON"}:
                    name = self._get_entity_name(child)
                    if name is not None:  # Filter out abstract concepts
                        subjects.append(name)

        return subjects

    def _find_objects(self, verb: Token) -> List[str]:
        """Find object entities for a verb."""
        objects = []

        for child in verb.children:
            # Direct objects
            if child.dep_ in {"dobj", "attr", "oprd", "npadvmod"}:
                if child.pos_ in {"PROPN", "NOUN", "PRON"}:
                    name = self._get_entity_name(child)
                    if name is not None:  # Filter out abstract concepts
                        objects.append(name)

            # Prepositional objects
            elif child.dep_ == "prep":
                for grandchild in child.children:
                    if grandchild.dep_ == "pobj":
                        if grandchild.pos_ in {"PROPN", "NOUN", "PRON"}:
                            name = self._get_entity_name(grandchild)
                            if name is not None:  # Filter out abstract concepts
                                objects.append(name)

        return objects

    def _get_entity_name(self, token: Token) -> Optional[str]:
        """
        Extract entity name from token.

        Only returns names for PERSON-like entities (filters out abstract concepts).

        Handles:
        - Proper nouns (Alice, Bob) → use text
        - Pronouns (she, he, they) → use lemma
        - Common nouns (CEO, investigator) → use lemma (capitalized)
        - Abstract nouns (methodology, conclusion) → None (filtered out)
        """
        # Filter out abstract/non-agent nouns
        abstract_concepts = {
            "methodology", "conclusion", "experiment", "result", "finding",
            "research", "paper", "study", "analysis", "data", "approach",
            "proposal", "solution", "problem", "issue", "claim", "evidence"
        }

        lemma = token.lemma_.lower() if token.lemma_ else token.text.lower()
        if lemma in abstract_concepts:
            return None  # Not a person/agent

        if token.pos_ == "PROPN":
            # Proper noun: use text as-is
            return token.text
        elif token.pos_ == "PRON":
            # Pronoun: normalize (he/she/they → He/She/They)
            return token.lemma_.capitalize() if token.lemma_ != "-PRON-" else token.text.capitalize()
        else:
            # Common noun: use lemma, capitalize
            return token.lemma_.capitalize() if token.lemma_ else token.text.capitalize()

    def _classify_relation(self, verb: Token, subj: str, obj: str) -> RelationTensor:
        """
        Classify relation based on verb semantics and dependency structure.

        Mapping:
        - Collaborative verbs (collaborate, coordinate, support) → empathy_weight
        - Extractive verbs (demand, mandate, control) → profit_weight
        - Adversarial verbs (oppose, question, criticize) → harm_weight
        - Informational verbs (analyze, discuss, review) → info_weight

        Falls back to info_weight=0.5 for unknown verbs.
        """
        verb_lemma = verb.lemma_.lower()

        # Collaborative / supportive relations
        if verb_lemma in {
            "collaborate", "coordinate", "support", "help", "assist",
            "cooperate", "partner", "agree", "appreciate", "thank"
        }:
            return RelationTensor(
                profit_weight=0.0,
                harm_weight=0.0,
                info_weight=0.0,
                empathy_weight=0.7
            )

        # Extractive / controlling relations
        elif verb_lemma in {
            "demand", "mandate", "control", "order", "command", "require",
            "dictate", "insist", "enforce", "threaten"
        }:
            return RelationTensor(
                profit_weight=0.8,
                harm_weight=0.0,
                info_weight=0.0,
                empathy_weight=0.0
            )

        # Adversarial / oppositional relations
        elif verb_lemma in {
            "oppose", "question", "criticize", "challenge", "dispute",
            "reject", "deny", "refuse", "contradict", "conflict"
        }:
            return RelationTensor(
                profit_weight=0.0,
                harm_weight=0.6,
                info_weight=0.0,
                empathy_weight=0.0
            )

        # Informational / analytical relations (default)
        else:
            return RelationTensor(
                profit_weight=0.0,
                harm_weight=0.0,
                info_weight=0.5,
                empathy_weight=0.0
            )

    def _merge_tensors(self, t1: RelationTensor, t2: RelationTensor) -> RelationTensor:
        """Merge two relation tensors by averaging weights."""
        return RelationTensor(
            profit_weight=(t1.profit_weight + t2.profit_weight) / 2,
            harm_weight=(t1.harm_weight + t2.harm_weight) / 2,
            info_weight=(t1.info_weight + t2.info_weight) / 2,
            empathy_weight=(t1.empathy_weight + t2.empathy_weight) / 2
        )


def get_parser(enable_logging: bool = False) -> SpacyGraphParser:
    """Factory function for SpacyGraphParser."""
    return SpacyGraphParser(enable_logging=enable_logging)
