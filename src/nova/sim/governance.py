"""
Nova Simulation Interface (NSI) - Phase 11.0-rc
Federated Epistemology Panel (FEP) Governance Loop

Implements democratic governance for simulation use-cases with FCQ validation.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time
import hashlib
import json


class GovernanceDecision(Enum):
    """FEP governance decisions"""
    APPROVE = "approve"
    APPROVE_WITH_CONDITIONS = "approve_with_conditions"
    DENY = "deny"
    ESCALATE = "escalate"
    FREEZE = "freeze"  # FCQ ≥ 0.90 triggers automatic freeze


class SimulationUseCase(Enum):
    """Approved simulation use cases"""
    POLICY_ANALYSIS = "policy_analysis"
    SOCIAL_DYNAMICS = "social_dynamics"
    ETHICAL_DILEMMAS = "ethical_dilemmas"
    CULTURAL_ADAPTATION = "cultural_adaptation"
    EDUCATIONAL_DEMOS = "educational_demos"
    RESEARCH_VALIDATION = "research_validation"


@dataclass
class GovernanceVote:
    """Individual FEP member vote"""
    member_id: str
    use_case: SimulationUseCase
    decision: GovernanceDecision
    confidence: float  # 0.0 to 1.0
    reasoning: str
    conditions: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'member_id': self.member_id,
            'use_case': self.use_case.value,
            'decision': self.decision.value,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'conditions': self.conditions,
            'timestamp': self.timestamp
        }


@dataclass
class GovernanceProposal:
    """Simulation use case proposal for FEP voting"""
    proposal_id: str
    use_case: SimulationUseCase
    description: str
    proposer: str
    simulation_config: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    ethical_review: Dict[str, Any]
    created_at: float = field(default_factory=time.time)
    votes: List[GovernanceVote] = field(default_factory=list)
    status: str = "open"  # open, approved, denied, frozen

    def add_vote(self, vote: GovernanceVote):
        """Add a vote to the proposal"""
        self.votes.append(vote)

    def calculate_fcq(self) -> float:
        """Calculate Federated Consensus Quality (FCQ)"""
        if not self.votes:
            return 0.0

        # FCQ = weighted average of (alignment × provenance)
        # Alignment: 1.0 for approve/approve_with_conditions, 0.0 for deny/escalate
        # Provenance: confidence score as proxy for data quality

        total_weight = 0.0
        weighted_sum = 0.0

        for vote in self.votes:
            # Alignment score
            if vote.decision in [GovernanceDecision.APPROVE, GovernanceDecision.APPROVE_WITH_CONDITIONS]:
                alignment = 1.0
            elif vote.decision == GovernanceDecision.DENY:
                alignment = 0.0
            else:  # ESCALATE
                alignment = 0.5

            # Provenance score (confidence as proxy)
            provenance = vote.confidence

            # Weight by confidence (higher confidence votes count more)
            weight = vote.confidence
            total_weight += weight
            weighted_sum += weight * alignment * provenance

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def get_decision(self) -> Tuple[GovernanceDecision, Dict[str, Any]]:
        """Get final governance decision based on FCQ and votes"""

        fcq = self.calculate_fcq()

        # FCQ ≥ 0.90 triggers automatic freeze
        if fcq >= 0.90:
            return GovernanceDecision.FREEZE, {
                'fcq': fcq,
                'reason': 'FCQ threshold exceeded - automatic freeze',
                'conditions': ['Immediate suspension', 'Full FEP review required']
            }

        # Count votes by type
        approve_count = sum(1 for v in self.votes if v.decision == GovernanceDecision.APPROVE)
        conditional_count = sum(1 for v in self.votes if v.decision == GovernanceDecision.APPROVE_WITH_CONDITIONS)
        deny_count = sum(1 for v in self.votes if v.decision == GovernanceDecision.DENY)
        total_votes = len(self.votes)

        # Decision logic
        if approve_count > total_votes * 0.6:  # >60% approve
            return GovernanceDecision.APPROVE, {'fcq': fcq}

        elif (approve_count + conditional_count) > total_votes * 0.5:  # >50% approve/conditional
            conditions = []
            for vote in self.votes:
                if vote.decision == GovernanceDecision.APPROVE_WITH_CONDITIONS:
                    conditions.extend(vote.conditions)
            return GovernanceDecision.APPROVE_WITH_CONDITIONS, {
                'fcq': fcq,
                'conditions': list(set(conditions))  # Remove duplicates
            }

        elif deny_count > total_votes * 0.4:  # >40% deny
            return GovernanceDecision.DENY, {'fcq': fcq}

        else:
            return GovernanceDecision.ESCALATE, {
                'fcq': fcq,
                'reason': 'Insufficient consensus - requires escalation'
            }


@dataclass
class FEPGovernance:
    """Federated Epistemology Panel governance system"""

    panel_members: List[str]  # FEP member IDs
    active_proposals: Dict[str, GovernanceProposal] = field(default_factory=dict)
    approved_use_cases: Dict[str, GovernanceProposal] = field(default_factory=dict)
    audit_log: List[Dict[str, Any]] = field(default_factory=list)

    def submit_proposal(self, use_case: SimulationUseCase, description: str,
                       proposer: str, simulation_config: Dict[str, Any],
                       risk_assessment: Dict[str, Any],
                       ethical_review: Dict[str, Any]) -> str:
        """Submit a new simulation use case proposal"""

        proposal_id = hashlib.sha256(
            f"{use_case.value}:{proposer}:{time.time()}".encode()
        ).hexdigest()[:16]

        proposal = GovernanceProposal(
            proposal_id=proposal_id,
            use_case=use_case,
            description=description,
            proposer=proposer,
            simulation_config=simulation_config,
            risk_assessment=risk_assessment,
            ethical_review=ethical_review
        )

        self.active_proposals[proposal_id] = proposal

        # Audit log
        self.audit_log.append({
            'action': 'proposal_submitted',
            'proposal_id': proposal_id,
            'use_case': use_case.value,
            'proposer': proposer,
            'timestamp': time.time()
        })

        return proposal_id

    def cast_vote(self, proposal_id: str, member_id: str, decision: GovernanceDecision,
                  confidence: float, reasoning: str, conditions: List[str] = None) -> bool:
        """Cast a vote on a proposal"""

        if proposal_id not in self.active_proposals:
            return False

        if member_id not in self.panel_members:
            return False

        proposal = self.active_proposals[proposal_id]

        # Check if member already voted
        if any(v.member_id == member_id for v in proposal.votes):
            return False

        vote = GovernanceVote(
            member_id=member_id,
            use_case=proposal.use_case,
            decision=decision,
            confidence=confidence,
            reasoning=reasoning,
            conditions=conditions or []
        )

        proposal.add_vote(vote)

        # Audit log
        self.audit_log.append({
            'action': 'vote_cast',
            'proposal_id': proposal_id,
            'member_id': member_id,
            'decision': decision.value,
            'confidence': confidence,
            'timestamp': time.time()
        })

        # Check if voting is complete (all members voted)
        if len(proposal.votes) >= len(self.panel_members):
            self._finalize_proposal(proposal_id)

        return True

    def _finalize_proposal(self, proposal_id: str):
        """Finalize a completed proposal"""

        proposal = self.active_proposals[proposal_id]
        decision, details = proposal.get_decision()

        proposal.status = decision.value

        # Move to approved if accepted
        if decision in [GovernanceDecision.APPROVE, GovernanceDecision.APPROVE_WITH_CONDITIONS]:
            self.approved_use_cases[proposal_id] = proposal

        # Remove from active
        del self.active_proposals[proposal_id]

        # Audit log
        self.audit_log.append({
            'action': 'proposal_finalized',
            'proposal_id': proposal_id,
            'decision': decision.value,
            'fcq': details.get('fcq', 0.0),
            'conditions': details.get('conditions', []),
            'timestamp': time.time()
        })

    def check_use_case_approval(self, use_case: SimulationUseCase,
                               simulation_config: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Check if a use case is approved for the given configuration"""

        # Find approved proposals for this use case
        approved_proposals = [
            p for p in self.approved_use_cases.values()
            if p.use_case == use_case and p.status in ['approve', 'approve_with_conditions']
        ]

        if not approved_proposals:
            return False, {'reason': 'No approved proposals for this use case'}

        # Check if config matches approved parameters
        for proposal in approved_proposals:
            if self._config_matches_approval(simulation_config, proposal):
                conditions = []
                if proposal.status == 'approve_with_conditions':
                    final_decision, details = proposal.get_decision()
                    conditions = details.get('conditions', [])

                return True, {
                    'approved': True,
                    'proposal_id': proposal.proposal_id,
                    'conditions': conditions,
                    'fcq': proposal.calculate_fcq()
                }

        return False, {'reason': 'Configuration does not match approved parameters'}

    def _config_matches_approval(self, config: Dict[str, Any],
                                proposal: GovernanceProposal) -> bool:
        """Check if simulation config matches approved proposal parameters"""

        approved_config = proposal.simulation_config

        # Check critical parameters
        critical_params = ['num_agents', 'max_steps', 'consensus_model']

        for param in critical_params:
            if config.get(param) != approved_config.get(param):
                return False

        # Check agent limits
        if config.get('num_agents', 0) > approved_config.get('max_agents', 50):
            return False

        return True

    def get_proposal_status(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a proposal"""

        if proposal_id in self.active_proposals:
            proposal = self.active_proposals[proposal_id]
            return {
                'status': 'active',
                'votes': len(proposal.votes),
                'required_votes': len(self.panel_members),
                'fcq': proposal.calculate_fcq()
            }

        elif proposal_id in self.approved_use_cases:
            proposal = self.approved_use_cases[proposal_id]
            return {
                'status': 'approved',
                'decision': proposal.status,
                'fcq': proposal.calculate_fcq()
            }

        return None

    def get_audit_trail(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get governance audit trail"""
        return self.audit_log[-limit:]


# Demo FEP panel for Phase 11.0-rc
def create_demo_fep() -> FEPGovernance:
    """Create demonstration FEP panel with sample members"""
    return FEPGovernance(
        panel_members=[
            "fep_member_001",  # Ethics specialist
            "fep_member_002",  # Technical expert
            "fep_member_003",  # Domain expert
            "fep_member_004",  # Civil society rep
            "fep_member_005"   # Academic researcher
        ]
    )


# Example usage and testing
def demo_governance_flow():
    """Demonstrate FEP governance flow"""

    fep = create_demo_fep()

    # Submit proposal
    proposal_id = fep.submit_proposal(
        use_case=SimulationUseCase.POLICY_ANALYSIS,
        description="Climate policy consensus simulation",
        proposer="researcher_001",
        simulation_config={
            'num_agents': 25,
            'max_steps': 50,
            'consensus_model': 'friedkin_johnsen',
            'max_agents': 50
        },
        risk_assessment={'level': 'low', 'mitigations': ['guardrails', 'monitoring']},
        ethical_review={'approved': True, 'concerns': []}
    )

    print(f"Proposal submitted: {proposal_id}")

    # Cast votes
    members = fep.panel_members
    votes = [
        (members[0], GovernanceDecision.APPROVE, 0.9, "Well-designed study"),
        (members[1], GovernanceDecision.APPROVE, 0.8, "Technical parameters appropriate"),
        (members[2], GovernanceDecision.APPROVE_WITH_CONDITIONS, 0.7,
         "Good but needs transparency", ["Publish methodology", "Share raw data"]),
        (members[3], GovernanceDecision.APPROVE, 0.85, "Addresses important policy questions"),
        (members[4], GovernanceDecision.APPROVE, 0.9, "Rigorous approach")
    ]

    for member_id, decision, confidence, reasoning, *conditions in votes:
        conditions = conditions[0] if conditions else []
        fep.cast_vote(proposal_id, member_id, decision, confidence, reasoning, conditions)

    # Check final status
    status = fep.get_proposal_status(proposal_id)
    print(f"Final status: {status}")

    # Check approval for similar config
    approved, details = fep.check_use_case_approval(
        SimulationUseCase.POLICY_ANALYSIS,
        {'num_agents': 25, 'max_steps': 50, 'consensus_model': 'friedkin_johnsen'}
    )

    print(f"Use case approved: {approved}")
    if approved:
        print(f"FCQ: {details['fcq']:.3f}")
        if details.get('conditions'):
            print(f"Conditions: {details['conditions']}")


if __name__ == "__main__":
    demo_governance_flow()
