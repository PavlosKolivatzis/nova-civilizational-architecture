"""
VSD-0 F-Domain Filter
Version: 0.1
Purpose: Pre-query constitutional refusal (self-enforced)
Compliance: DOC v1.0 Section 4.3 (F-Domain Filtering - REQUIRED)

This module implements self-enforced F-domain refusal.
Nova does not refuse at runtime. VSD-0 must filter F-domains before querying Nova.
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
from enum import Enum
import yaml


class JurisdictionalDomain(Enum):
    """Jurisdictional domains from Nova's jurisdiction map"""
    OBSERVE_ONLY = "O"  # Measurement, no routing authority
    ROUTE_ONLY = "R"    # Routing decisions, no moral interpretation
    REFUSE_ALWAYS = "F"  # Must refuse to operate


class RefusalCode(Enum):
    """Refusal codes from refusal_event_contract.md"""
    OUT_OF_JURISDICTION = "OUT_OF_JURISDICTION"
    CALIBRATION_DISAGREEMENT_PHASE16_ALPHA = "CALIBRATION_DISAGREEMENT_PHASE16_ALPHA"
    EVENT_HORIZON_VIOLATION = "EVENT_HORIZON_VIOLATION"  # VSD-0 specific
    DMAD_ATTEMPT = "DMAD_ATTEMPT"  # VSD-0 specific
    ALS_ATTEMPT = "ALS_ATTEMPT"  # VSD-0 specific


@dataclass
class RefusalEvent:
    """
    Constitutional refusal event.

    Schema from refusal_event_contract.md
    Emitted when VSD-0 refuses F-domain query.
    """
    event_id: str
    timestamp: str
    refusal_code: RefusalCode
    jurisdiction: JurisdictionalDomain
    query_description: str
    constitutional_basis: str
    action_taken: str

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "refusal_code": self.refusal_code.value,
            "jurisdiction": self.jurisdiction.value,
            "query_description": self.query_description,
            "constitutional_basis": self.constitutional_basis,
            "action_taken": self.action_taken
        }


class FDomainFilter:
    """
    F-Domain filtering and constitutional refusal.

    Required by DOC v1.0 Section 4.3:
    - Classify requests by jurisdictional domain (O/R/F)
    - Block F-domain queries before they reach Nova
    - Emit RefusalEvent for all refusals

    Nova does not refuse at runtime. VSD-0 must self-enforce.
    """

    def __init__(self, ontology_path: str, audit_log_callback=None):
        """
        Initialize F-domain filter.

        Args:
            ontology_path: Path to ontology.yaml (jurisdiction/refusal declarations)
            audit_log_callback: Function to call when refusal occurs (writes to audit log)
        """
        self.ontology_path = ontology_path
        self.audit_log = audit_log_callback

        # Load F-domains from ontology.yaml
        self.f_domains: List[str] = []
        self.refusal_map: dict = {}
        self._load_ontology()

        self.refusal_count = 0

    def _load_ontology(self):
        """Load F-domains and refusal map from ontology.yaml"""
        try:
            with open(self.ontology_path, 'r') as f:
                ontology = yaml.safe_load(f)

            # Extract F-domains from jurisdiction declaration
            jurisdiction = ontology.get('jurisdiction', {})
            self.f_domains = jurisdiction.get('refuse_always', [])

            # Extract refusal map
            self.refusal_map = ontology.get('refusal_map', {})

        except Exception as e:
            print(f"[F-FILTER] Warning: Failed to load ontology: {e}")
            # Use minimal F-domains as fallback
            self.f_domains = [
                'phase16_alpha_boundary_resolution',
                'non_structural_moral_interpretation',
                'post_hoc_pressure_justification'
            ]

    def _emit_refusal_event(self, query: str, domain_matched: str,
                           refusal_code: RefusalCode, basis: str):
        """Emit RefusalEvent to audit log"""
        self.refusal_count += 1

        event = RefusalEvent(
            event_id=f"refusal_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{self.refusal_count}",
            timestamp=datetime.utcnow().isoformat() + "Z",
            refusal_code=refusal_code,
            jurisdiction=JurisdictionalDomain.REFUSE_ALWAYS,
            query_description=query[:200],  # Truncate for safety
            constitutional_basis=basis,
            action_taken="query_blocked_pre_nova"
        )

        if self.audit_log:
            self.audit_log(event.to_dict(), event_type="refusal_event")

        # Print to stdout for debugging
        print(f"[REFUSAL] {refusal_code.value}: {domain_matched}")

    def classify_query(self, query: str) -> JurisdictionalDomain:
        """
        Classify query by jurisdictional domain (O/R/F).

        This is semantic→decision authority coupling (explicit and auditable).

        Args:
            query: Query text to classify

        Returns:
            Jurisdictional domain (O/R/F)
        """
        query_lower = query.lower()

        # Check for F-domain patterns
        f_domain_patterns = {
            'phase16_alpha_boundary_resolution': [
                'rt-027', 'rt-028', 'rt-029',
                'phase 16.α', 'phase 16 alpha',
                'calibration disagreement', 'boundary resolution'
            ],
            'non_structural_moral_interpretation': [
                'is this moral', 'is this ethical', 'is this right',
                'should i', 'ought to', 'moral judgment',
                'interpret morally', 'moral meaning'
            ],
            'post_hoc_pressure_justification': [
                'justify pressure', 'rationalize agency',
                'post-hoc', 'after the fact justification',
                'explain why pressure was okay'
            ],
            'nova_core_modification': [
                'modify nova', 'change nova code', 'update frozen artifact',
                'rewrite nova', 'extend nova core'
            ],
            'derivative_sovereignty_delegation': [
                'delegate refusal to nova', 'let nova handle f-domain',
                'outsource filtering', 'nova will refuse'
            ],
            'authority_surface_hiding': [
                'hide authority', 'claim neutrality', 'obscure power',
                'don\'t declare jurisdiction'
            ]
        }

        # Check each F-domain
        for domain_name, patterns in f_domain_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                return JurisdictionalDomain.REFUSE_ALWAYS

        # Check for O-domain patterns (observe-only)
        o_domain_patterns = [
            'measure', 'observe', 'detect', 'monitor', 'report',
            'what is the bias', 'what is the harm status',
            'show me a_p', 'get measurement'
        ]

        if any(pattern in query_lower for pattern in o_domain_patterns):
            return JurisdictionalDomain.OBSERVE_ONLY

        # Check for R-domain patterns (routing decisions)
        r_domain_patterns = [
            'route', 'decide', 'select regime', 'governance decision',
            'which path', 'should route to'
        ]

        if any(pattern in query_lower for pattern in r_domain_patterns):
            return JurisdictionalDomain.ROUTE_ONLY

        # Default: assume O-domain (safest classification)
        return JurisdictionalDomain.OBSERVE_ONLY

    def filter_query(self, query: str) -> tuple[bool, Optional[RefusalEvent]]:
        """
        Filter query through F-domain check.

        Required by DOC v1.0 Section 4.3:
        "Derivatives must implement F-domain filtering."

        Args:
            query: Query to filter

        Returns:
            (allowed, refusal_event)
            - allowed: True if query can proceed, False if refused
            - refusal_event: RefusalEvent if refused, None otherwise
        """
        # Classify query
        domain = self.classify_query(query)

        # If F-domain, refuse
        if domain == JurisdictionalDomain.REFUSE_ALWAYS:
            # Determine which F-domain matched
            query_lower = query.lower()
            matched_domain = "unknown_f_domain"

            if any(x in query_lower for x in ['rt-027', 'rt-028', 'rt-029', 'phase 16.α']):
                matched_domain = "phase16_alpha_boundary_resolution"
                refusal_code = RefusalCode.CALIBRATION_DISAGREEMENT_PHASE16_ALPHA
                basis = "docs/specs/phase16_alpha_calibration_protocol.md"

            elif any(x in query_lower for x in ['moral', 'ethical', 'should', 'ought']):
                matched_domain = "non_structural_moral_interpretation"
                refusal_code = RefusalCode.OUT_OF_JURISDICTION
                basis = "docs/specs/nova_jurisdiction_map.md (F-domain: non-structural moral)"

            elif any(x in query_lower for x in ['justify', 'post-hoc', 'rationalize']):
                matched_domain = "post_hoc_pressure_justification"
                refusal_code = RefusalCode.OUT_OF_JURISDICTION
                basis = "docs/specs/nova_jurisdiction_map.md (F-domain: post-hoc justification)"

            elif any(x in query_lower for x in ['modify nova', 'change nova', 'extend nova']):
                matched_domain = "nova_core_modification"
                refusal_code = RefusalCode.EVENT_HORIZON_VIOLATION
                basis = "docs/constitution/PHASE3_CLOSEOUT.md (Nova Core no longer extensible)"

            elif any(x in query_lower for x in ['delegate', 'outsource', 'nova will refuse']):
                matched_domain = "derivative_sovereignty_delegation"
                refusal_code = RefusalCode.DMAD_ATTEMPT
                basis = "docs/specs/derivative_ontology_contract.md (DMAD prevention)"

            elif any(x in query_lower for x in ['hide authority', 'claim neutrality']):
                matched_domain = "authority_surface_hiding"
                refusal_code = RefusalCode.ALS_ATTEMPT
                basis = "docs/specs/derivative_ontology_contract.md (ALS prevention)"

            else:
                refusal_code = RefusalCode.OUT_OF_JURISDICTION
                basis = "docs/specs/nova_jurisdiction_map.md (F-domain: general)"

            # Emit refusal event
            self._emit_refusal_event(
                query=query,
                domain_matched=matched_domain,
                refusal_code=refusal_code,
                basis=basis
            )

            # Return refusal
            event = RefusalEvent(
                event_id=f"refusal_{self.refusal_count}",
                timestamp=datetime.utcnow().isoformat() + "Z",
                refusal_code=refusal_code,
                jurisdiction=JurisdictionalDomain.REFUSE_ALWAYS,
                query_description=query[:200],
                constitutional_basis=basis,
                action_taken="query_blocked_pre_nova"
            )

            return (False, event)

        # Query allowed (O or R domain)
        return (True, None)

    def get_status(self) -> dict:
        """Get filter status"""
        return {
            "ontology_loaded": len(self.f_domains) > 0,
            "f_domains_count": len(self.f_domains),
            "refusals_count": self.refusal_count,
            "enforcement": "self_enforced_pre_query"
        }


# Standalone function for testing F-domain classification
def test_f_domain_classification(queries: List[str]):
    """
    Test F-domain classification on sample queries.

    Args:
        queries: List of query strings to test
    """
    # Use default ontology path
    filter = FDomainFilter("ontology.yaml")

    print("=== F-Domain Classification Test ===\n")

    for query in queries:
        domain = filter.classify_query(query)
        allowed, refusal = filter.filter_query(query)

        print(f"Query: {query[:60]}...")
        print(f"  Domain: {domain.value}")
        print(f"  Allowed: {allowed}")
        if refusal:
            print(f"  Refusal Code: {refusal.refusal_code.value}")
        print()


if __name__ == "__main__":
    # Example: Test F-domain filtering
    test_queries = [
        # Should be refused (F-domain)
        "Is this morally right to do?",
        "Can you help me resolve RT-027 boundary case?",
        "Justify why this agency pressure was acceptable",
        "Modify Nova's jurisdiction map",
        "Let Nova handle F-domain filtering for me",

        # Should be allowed (O-domain)
        "What is the current bias vector?",
        "Measure the agency pressure for this conversation",
        "Report the harm status",

        # Should be allowed (R-domain)
        "Which regime should this be routed to?",
        "Make a routing decision based on bias_vector"
    ]

    test_f_domain_classification(test_queries)
