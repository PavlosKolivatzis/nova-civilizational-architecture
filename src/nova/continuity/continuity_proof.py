"""Continuity Proofs - Phase 13

Mathematical proofs that regime transitions preserve system continuity.
Validates ledger continuity, temporal continuity, amplitude continuity,
and regime continuity (hysteresis + min-duration).

Design: ADR-13-Init.md
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from src.nova.continuity.avl_ledger import AVLEntry

# Default amplitude continuity threshold
DEFAULT_AMPLITUDE_DELTA = 0.5


@dataclass
class ProofResult:
    """Result of a continuity proof."""
    proof_name: str
    passed: bool
    violations: List[str]
    entries_checked: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "proof_name": self.proof_name,
            "passed": self.passed,
            "violations": self.violations,
            "entries_checked": self.entries_checked,
        }


class ContinuityProof:
    """Continuity proof validators.
    
    Provides mathematical proofs that regime transitions preserve
    system continuity invariants.
    """
    
    def __init__(self, amplitude_delta: float = DEFAULT_AMPLITUDE_DELTA):
        """Initialize continuity proof validator.
        
        Args:
            amplitude_delta: Maximum allowed amplitude change between entries
        """
        self._amplitude_delta = amplitude_delta
    
    def prove_ledger_continuity(self, ledger: List[AVLEntry]) -> ProofResult:
        """Prove from_regime[N] == to_regime[N-1] for all transitions.
        
        Ledger continuity ensures that when a transition occurs,
        the transition_from field matches the previous entry's regime.
        
        Args:
            ledger: List of AVL entries to validate
        
        Returns:
            ProofResult with pass/fail and any violations
        """
        violations = []
        
        if len(ledger) < 2:
            return ProofResult(
                proof_name="ledger_continuity",
                passed=True,
                violations=[],
                entries_checked=len(ledger),
            )
        
        for i in range(1, len(ledger)):
            current = ledger[i]
            previous = ledger[i - 1]
            
            # If there's a transition, verify continuity
            if current.transition_from is not None:
                if current.transition_from != previous.orp_regime:
                    violations.append(
                        f"Entry {i}: transition_from={current.transition_from} "
                        f"but previous regime={previous.orp_regime}"
                    )
        
        return ProofResult(
            proof_name="ledger_continuity",
            passed=len(violations) == 0,
            violations=violations,
            entries_checked=len(ledger),
        )
    
    def prove_temporal_continuity(self, ledger: List[AVLEntry]) -> ProofResult:
        """Prove timestamps are monotonically increasing.
        
        Temporal continuity ensures that time always moves forward
        and no entries are out of order.
        
        Args:
            ledger: List of AVL entries to validate
        
        Returns:
            ProofResult with pass/fail and any violations
        """
        violations = []
        
        if len(ledger) < 2:
            return ProofResult(
                proof_name="temporal_continuity",
                passed=True,
                violations=[],
                entries_checked=len(ledger),
            )
        
        for i in range(1, len(ledger)):
            current = ledger[i]
            previous = ledger[i - 1]
            
            # Check elapsed_s is strictly increasing
            if current.elapsed_s <= previous.elapsed_s:
                violations.append(
                    f"Entry {i}: elapsed_s={current.elapsed_s} <= "
                    f"previous elapsed_s={previous.elapsed_s}"
                )
            
            # Check timestamps are ordered (string comparison works for ISO8601)
            if current.timestamp <= previous.timestamp:
                violations.append(
                    f"Entry {i}: timestamp={current.timestamp} <= "
                    f"previous timestamp={previous.timestamp}"
                )
        
        return ProofResult(
            proof_name="temporal_continuity",
            passed=len(violations) == 0,
            violations=violations,
            entries_checked=len(ledger),
        )
    
    def prove_amplitude_continuity(
        self,
        ledger: List[AVLEntry],
        max_delta: Optional[float] = None,
    ) -> ProofResult:
        """Prove no discontinuous jumps in amplitude parameters.
        
        Amplitude continuity ensures that posture adjustments
        (threshold_multiplier, traffic_limit) change smoothly
        without sudden jumps.
        
        Args:
            ledger: List of AVL entries to validate
            max_delta: Maximum allowed change (default: self._amplitude_delta)
        
        Returns:
            ProofResult with pass/fail and any violations
        """
        if max_delta is None:
            max_delta = self._amplitude_delta
        
        violations = []
        
        if len(ledger) < 2:
            return ProofResult(
                proof_name="amplitude_continuity",
                passed=True,
                violations=[],
                entries_checked=len(ledger),
            )
        
        for i in range(1, len(ledger)):
            current = ledger[i]
            previous = ledger[i - 1]
            
            # Check threshold_multiplier
            curr_mult = current.posture_adjustments.get("threshold_multiplier", 1.0)
            prev_mult = previous.posture_adjustments.get("threshold_multiplier", 1.0)
            mult_delta = abs(curr_mult - prev_mult)
            
            if mult_delta > max_delta:
                violations.append(
                    f"Entry {i}: threshold_multiplier jump {prev_mult:.3f} → "
                    f"{curr_mult:.3f} (delta={mult_delta:.3f} > {max_delta})"
                )
            
            # Check traffic_limit
            curr_limit = current.posture_adjustments.get("traffic_limit", 1.0)
            prev_limit = previous.posture_adjustments.get("traffic_limit", 1.0)
            limit_delta = abs(curr_limit - prev_limit)
            
            if limit_delta > max_delta:
                violations.append(
                    f"Entry {i}: traffic_limit jump {prev_limit:.3f} → "
                    f"{curr_limit:.3f} (delta={limit_delta:.3f} > {max_delta})"
                )
        
        return ProofResult(
            proof_name="amplitude_continuity",
            passed=len(violations) == 0,
            violations=violations,
            entries_checked=len(ledger),
        )
    
    def prove_regime_continuity(self, ledger: List[AVLEntry]) -> ProofResult:
        """Prove all transitions respect hysteresis + min-duration.
        
        Regime continuity ensures that the ORP invariants
        (hysteresis and minimum duration) are enforced for all entries.
        
        Args:
            ledger: List of AVL entries to validate
        
        Returns:
            ProofResult with pass/fail and any violations
        """
        violations = []
        
        for i, entry in enumerate(ledger):
            if not entry.hysteresis_enforced:
                violations.append(
                    f"Entry {i}: hysteresis not enforced at {entry.timestamp}"
                )
            
            if not entry.min_duration_enforced:
                violations.append(
                    f"Entry {i}: min-duration not enforced at {entry.timestamp}"
                )
        
        return ProofResult(
            proof_name="regime_continuity",
            passed=len(violations) == 0,
            violations=violations,
            entries_checked=len(ledger),
        )
    
    def prove_all(self, ledger: List[AVLEntry]) -> Dict[str, ProofResult]:
        """Run all proofs and return results dict.
        
        Args:
            ledger: List of AVL entries to validate
        
        Returns:
            Dict mapping proof name to ProofResult
        """
        return {
            "ledger_continuity": self.prove_ledger_continuity(ledger),
            "temporal_continuity": self.prove_temporal_continuity(ledger),
            "amplitude_continuity": self.prove_amplitude_continuity(ledger),
            "regime_continuity": self.prove_regime_continuity(ledger),
        }
    
    def prove_all_pass(self, ledger: List[AVLEntry]) -> Tuple[bool, Dict[str, ProofResult]]:
        """Run all proofs and return overall pass/fail.
        
        Args:
            ledger: List of AVL entries to validate
        
        Returns:
            Tuple of (all_passed, results_dict)
        """
        results = self.prove_all(ledger)
        all_passed = all(r.passed for r in results.values())
        return all_passed, results
    
    def get_summary(self, results: Dict[str, ProofResult]) -> Dict[str, Any]:
        """Get summary of proof results.
        
        Args:
            results: Dict of proof results from prove_all()
        
        Returns:
            Summary dict with counts and status
        """
        total = len(results)
        passed = sum(1 for r in results.values() if r.passed)
        failed = total - passed
        
        return {
            "total_proofs": total,
            "passed": passed,
            "failed": failed,
            "all_passed": failed == 0,
            "failed_proofs": [name for name, r in results.items() if not r.passed],
            "total_violations": sum(len(r.violations) for r in results.values()),
        }


# ---------- Global Singleton ----------
_GLOBAL_PROOF: Optional[ContinuityProof] = None


def get_continuity_proof() -> ContinuityProof:
    """Get or create global continuity proof instance."""
    global _GLOBAL_PROOF
    if _GLOBAL_PROOF is None:
        _GLOBAL_PROOF = ContinuityProof()
    return _GLOBAL_PROOF


def reset_continuity_proof() -> None:
    """Reset global continuity proof (for testing)."""
    global _GLOBAL_PROOF
    _GLOBAL_PROOF = None