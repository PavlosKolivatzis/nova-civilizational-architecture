"""Intelligent repair planning for autonomous memory recovery."""

import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from statistics import mean

from .types import RepairDecision, RepairAction, HealthMetrics, SnapshotMeta
from .policy import Slot8Policy

logger = logging.getLogger(__name__)


class RepairPlanner:
    """Intelligent planning system for autonomous memory recovery."""

    def __init__(self, policy: Optional[Slot8Policy] = None):
        """Initialize repair planner with policy configuration."""
        self.policy = policy or Slot8Policy()

        # Recovery tracking
        self.repair_history = []
        self.success_rates = {}
        self.recovery_times = {}

        # Adaptive decision parameters
        self.confidence_threshold = 0.7
        self.learning_rate = 0.1

    def decide_repair_strategy(self, health_metrics: HealthMetrics,
                             available_snapshots: List[SnapshotMeta],
                             context: Dict[str, Any]) -> RepairDecision:
        """Make intelligent repair decision based on system health and available options."""

        # Analyze severity and type of corruption
        corruption_analysis = self._analyze_corruption(health_metrics, context)

        # Evaluate available repair options
        repair_options = self._evaluate_repair_options(available_snapshots, corruption_analysis)

        # Select best repair strategy
        selected_strategy = self._select_optimal_strategy(corruption_analysis, repair_options, context)

        # Calculate confidence in the decision
        confidence = self._calculate_decision_confidence(selected_strategy, corruption_analysis)

        # Estimate recovery time
        estimated_time = self._estimate_recovery_time(selected_strategy, context)

        repair_decision = RepairDecision(
            action=selected_strategy["action"],
            reason=selected_strategy["reason"],
            details=selected_strategy["details"],
            confidence=confidence,
            estimated_time_s=estimated_time
        )

        # Log decision for learning
        self._log_repair_decision(repair_decision, health_metrics, context)

        return repair_decision

    def _analyze_corruption(self, health_metrics: HealthMetrics,
                          context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the nature and severity of corruption."""
        analysis = {
            "severity": "unknown",
            "type": "unknown",
            "scope": "unknown",
            "confidence": 0.0,
            "indicators": []
        }

        # Determine corruption severity
        severity_score = 0.0

        if health_metrics.corruption_detected:
            severity_score += 0.3
            analysis["indicators"].append("corruption_detected")

        if health_metrics.tamper_evidence:
            severity_score += 0.4
            analysis["indicators"].append("tamper_evidence")
            analysis["type"] = "malicious"

        if health_metrics.checksum_mismatch:
            severity_score += 0.3
            analysis["indicators"].append("checksum_mismatch")

        if health_metrics.semantic_inversion:
            severity_score += 0.2
            analysis["indicators"].append("semantic_inversion")
            analysis["type"] = "logical"

        # High entropy indicates possible schema corruption
        if health_metrics.entropy_score > 0.8:
            severity_score += 0.2
            analysis["indicators"].append("high_entropy")

        # Multiple repair attempts suggest persistent issues
        if health_metrics.repair_attempts > 2:
            severity_score += 0.1 * health_metrics.repair_attempts
            analysis["indicators"].append("persistent_corruption")

        # Classify severity
        if severity_score >= 0.8:
            analysis["severity"] = "critical"
        elif severity_score >= 0.5:
            analysis["severity"] = "high"
        elif severity_score >= 0.2:
            analysis["severity"] = "medium"
        else:
            analysis["severity"] = "low"

        # Determine corruption type if not already set
        if analysis["type"] == "unknown":
            if health_metrics.checksum_mismatch:
                analysis["type"] = "data_corruption"
            elif health_metrics.semantic_inversion:
                analysis["type"] = "logical_corruption"
            else:
                analysis["type"] = "unknown_corruption"

        # Estimate scope based on available information
        affected_files = context.get("affected_files", [])
        total_files = context.get("total_files", 1)

        if len(affected_files) / total_files > 0.5:
            analysis["scope"] = "widespread"
        elif len(affected_files) > 10:
            analysis["scope"] = "moderate"
        else:
            analysis["scope"] = "localized"

        analysis["confidence"] = min(1.0, severity_score)

        return analysis

    def _evaluate_repair_options(self, available_snapshots: List[SnapshotMeta],
                                corruption_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluate available repair options based on snapshots and corruption type."""
        options = []

        # Option 1: Restore from last good snapshot
        if available_snapshots:
            latest_snapshot = max(available_snapshots, key=lambda s: s.ts_ms)
            age_hours = (time.time() * 1000 - latest_snapshot.ts_ms) / (1000 * 3600)

            restore_option = {
                "action": RepairAction.RESTORE_LAST_GOOD,
                "reason": f"Restore from snapshot {latest_snapshot.id}",
                "details": {
                    "snapshot_id": latest_snapshot.id,
                    "snapshot_age_hours": age_hours,
                    "snapshot_size": latest_snapshot.content_size,
                    "file_count": latest_snapshot.file_count
                },
                "success_probability": self._calculate_restore_success_probability(latest_snapshot, age_hours),
                "data_loss_risk": age_hours / 24.0,  # Risk proportional to age
                "recovery_time": self._estimate_restore_time(latest_snapshot)
            }
            options.append(restore_option)

        # Option 2: Majority vote from multiple snapshots
        if len(available_snapshots) >= 3:
            majority_option = {
                "action": RepairAction.MAJORITY_VOTE,
                "reason": "Consensus reconstruction from multiple snapshots",
                "details": {
                    "available_snapshots": len(available_snapshots),
                    "snapshot_ids": [s.id for s in available_snapshots[-5:]]  # Last 5
                },
                "success_probability": 0.8,  # Generally reliable
                "data_loss_risk": 0.1,  # Low risk with consensus
                "recovery_time": 30.0  # Takes longer to process multiple snapshots
            }
            options.append(majority_option)

        # Option 3: Semantic patch for logical corruption
        if corruption_analysis.get("type") == "logical_corruption":
            patch_option = {
                "action": RepairAction.SEMANTIC_PATCH,
                "reason": "Semantic reconstruction for logical corruption",
                "details": {
                    "corruption_type": corruption_analysis["type"],
                    "affected_scope": corruption_analysis["scope"]
                },
                "success_probability": 0.6,  # Moderate success rate
                "data_loss_risk": 0.2,  # Some risk of semantic changes
                "recovery_time": 15.0
            }
            options.append(patch_option)

        # Option 4: Block operations (safest but no recovery)
        block_option = {
            "action": RepairAction.BLOCK,
            "reason": "Block operations to prevent further damage",
            "details": {
                "requires_manual_intervention": True,
                "corruption_severity": corruption_analysis["severity"]
            },
            "success_probability": 1.0,  # Always succeeds at blocking
            "data_loss_risk": 1.0,  # No recovery, complete loss
            "recovery_time": 0.0  # Immediate
        }
        options.append(block_option)

        return options

    def _select_optimal_strategy(self, corruption_analysis: Dict[str, Any],
                               repair_options: List[Dict[str, Any]],
                               context: Dict[str, Any]) -> Dict[str, Any]:
        """Select the optimal repair strategy based on analysis and options."""

        # Score each option based on multiple criteria
        scored_options = []

        for option in repair_options:
            score = self._score_repair_option(option, corruption_analysis, context)
            scored_options.append((score, option))

        # Select highest scoring option
        scored_options.sort(key=lambda x: x[0], reverse=True)
        best_score, best_option = scored_options[0]

        # Add scoring information to decision
        best_option["selection_score"] = best_score
        best_option["alternatives_considered"] = len(repair_options)

        return best_option

    def _score_repair_option(self, option: Dict[str, Any],
                           corruption_analysis: Dict[str, Any],
                           context: Dict[str, Any]) -> float:
        """Score a repair option based on success probability, risk, and time."""

        # Base score from success probability
        score = option.get("success_probability", 0.0) * 40

        # Penalty for data loss risk
        data_loss_risk = option.get("data_loss_risk", 1.0)
        score -= data_loss_risk * 30

        # Penalty for long recovery time (but less important than success/risk)
        recovery_time = option.get("recovery_time", 0.0)
        if recovery_time > self.policy.mttr_target_s:
            score -= (recovery_time - self.policy.mttr_target_s) * 2

        # Bonus for appropriate action based on corruption type
        action = option.get("action")
        corruption_type = corruption_analysis.get("type", "unknown")

        if action == RepairAction.RESTORE_LAST_GOOD and corruption_type == "malicious":
            score += 10  # Good choice for malicious corruption
        elif action == RepairAction.SEMANTIC_PATCH and corruption_type == "logical_corruption":
            score += 15  # Excellent choice for logical issues
        elif action == RepairAction.MAJORITY_VOTE and corruption_analysis.get("scope") == "localized":
            score += 8   # Good for localized issues with multiple snapshots

        # Consider historical success rates
        historical_success = self.success_rates.get(action, 0.7)  # Default 70%
        score *= historical_success

        # Critical severity might require more conservative approaches
        if corruption_analysis.get("severity") == "critical":
            if action == RepairAction.BLOCK:
                score += 5  # Sometimes blocking is the right choice
            else:
                score *= 0.8  # Reduce confidence in recovery for critical issues

        return max(0.0, score)

    def _calculate_restore_success_probability(self, snapshot: SnapshotMeta, age_hours: float) -> float:
        """Calculate probability of successful restore from snapshot."""
        base_probability = 0.9

        # Reduce probability based on snapshot age
        age_penalty = min(0.3, age_hours / 168.0)  # Up to 30% penalty for week-old snapshots

        # Consider snapshot integrity
        if hasattr(snapshot.status, 'value'):
            # Handle enum status
            is_ok = snapshot.status.value == "OK"
        else:
            # Handle string status
            is_ok = snapshot.status == "OK"

        if not is_ok:
            base_probability *= 0.7

        # Historical success rate for this type of restore
        historical_rate = self.success_rates.get(RepairAction.RESTORE_LAST_GOOD, 0.85)

        return max(0.1, base_probability - age_penalty) * historical_rate

    def _estimate_restore_time(self, snapshot: SnapshotMeta) -> float:
        """Estimate time required to restore from snapshot."""
        # Base time for restore operation
        base_time = 5.0

        # Scale with content size (rough estimate)
        size_factor = snapshot.content_size / (1024 * 1024)  # MB
        size_time = size_factor * 0.1  # 0.1 seconds per MB

        # Scale with file count
        file_time = snapshot.file_count * 0.01  # 0.01 seconds per file

        return base_time + size_time + file_time

    def _estimate_recovery_time(self, strategy: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Estimate total recovery time for selected strategy."""
        base_time = strategy.get("recovery_time", 10.0)

        # Add overhead for validation and verification
        validation_time = 2.0

        # Add time for any required cleanup
        cleanup_time = 1.0

        return base_time + validation_time + cleanup_time

    def _calculate_decision_confidence(self, strategy: Dict[str, Any],
                                     corruption_analysis: Dict[str, Any]) -> float:
        """Calculate confidence in the repair decision."""

        # Start with base confidence from strategy scoring
        base_confidence = strategy.get("selection_score", 0.0) / 100.0

        # Adjust based on corruption analysis confidence
        analysis_confidence = corruption_analysis.get("confidence", 0.5)
        combined_confidence = (base_confidence + analysis_confidence) / 2.0

        # Reduce confidence if we've had recent failures
        recent_failures = len([r for r in self.repair_history[-5:]  # Last 5 repairs
                             if not r.get("success", False)])
        if recent_failures > 2:
            combined_confidence *= 0.8

        # Increase confidence if we have good historical data
        action = strategy.get("action")
        if action in self.success_rates and len(self.recovery_times.get(action, [])) > 3:
            combined_confidence *= 1.1

        return min(1.0, max(0.0, combined_confidence))

    def _log_repair_decision(self, decision: RepairDecision, health_metrics: HealthMetrics,
                           context: Dict[str, Any]):
        """Log repair decision for learning and analysis."""
        decision_log = {
            "timestamp": time.time(),
            "decision": decision,
            "health_metrics": health_metrics,
            "context": context,
            "success": None,  # Will be updated when repair completes
            "actual_time": None
        }

        self.repair_history.append(decision_log)

        # Keep history manageable
        if len(self.repair_history) > 100:
            self.repair_history = self.repair_history[-50:]

        logger.info(f"Repair decision: {decision.action.value} with confidence {decision.confidence:.2f}")

    def record_repair_outcome(self, decision: RepairDecision, success: bool, actual_time: float):
        """Record the outcome of a repair operation for learning."""
        # Find the corresponding decision in history
        for log_entry in reversed(self.repair_history):
            if (log_entry["decision"].action == decision.action and
                log_entry["success"] is None):  # Not yet recorded

                log_entry["success"] = success
                log_entry["actual_time"] = actual_time
                break

        # Update success rates
        action = decision.action
        if action not in self.success_rates:
            self.success_rates[action] = 0.7  # Default
        if action not in self.recovery_times:
            self.recovery_times[action] = []

        # Update running averages
        current_rate = self.success_rates[action]
        new_rate = current_rate + self.learning_rate * (1.0 if success else 0.0 - current_rate)
        self.success_rates[action] = max(0.1, min(0.95, new_rate))

        # Update timing estimates
        self.recovery_times[action].append(actual_time)
        if len(self.recovery_times[action]) > 20:
            self.recovery_times[action] = self.recovery_times[action][-10:]  # Keep recent

        logger.info(f"Repair outcome recorded: {action.value} success={success} time={actual_time:.1f}s")

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get repair planner performance metrics."""
        total_repairs = len([r for r in self.repair_history if r["success"] is not None])
        successful_repairs = len([r for r in self.repair_history if r["success"] is True])

        metrics = {
            "total_repair_decisions": len(self.repair_history),
            "completed_repairs": total_repairs,
            "successful_repairs": successful_repairs,
            "overall_success_rate": successful_repairs / max(1, total_repairs),
            "success_rates_by_action": dict(self.success_rates),
            "average_recovery_times": {}
        }

        # Calculate average recovery times
        for action, times in self.recovery_times.items():
            if times:
                metrics["average_recovery_times"][action.value] = mean(times)

        # Recent performance (last 10 repairs)
        recent_repairs = [r for r in self.repair_history[-10:] if r["success"] is not None]
        if recent_repairs:
            recent_successes = len([r for r in recent_repairs if r["success"]])
            metrics["recent_success_rate"] = recent_successes / len(recent_repairs)

        return metrics

    def get_repair_recommendations(self, health_metrics: HealthMetrics) -> List[str]:
        """Get proactive repair recommendations based on current health."""
        recommendations = []

        if health_metrics.integrity_score < 0.8:
            recommendations.append("Schedule integrity verification and potential snapshot creation")

        if health_metrics.last_snapshot_age_s > 3600:  # 1 hour
            recommendations.append("Create new snapshot - last snapshot is aging")

        if health_metrics.repair_attempts > 0:
            recommendations.append("Monitor system closely - recent repair attempts detected")

        if health_metrics.entropy_score > 0.7:
            recommendations.append("Investigate high entropy - possible schema drift")

        if health_metrics.quarantine_active:
            recommendations.append("Review quarantine status and consider recovery procedures")

        return recommendations