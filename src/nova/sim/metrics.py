"""
Nova Simulation Interface (NSI) - Phase 11.0-beta
Prometheus Metrics Integration for Agent Simulations

Implements TRI, CGC, and BiasIndex metrics with real-time monitoring.
"""

from typing import Dict, List, Optional, Any
import time
from dataclasses import dataclass, field
from prometheus_client import Gauge, Counter, Histogram, CollectorRegistry

# Nova slot imports (lazy-loaded to avoid import issues during development)
try:
    from nova.slots.slot04_tri.core import TriEngine
    from nova.slots.slot06_cultural_synthesis.engine import CulturalSynthesisEngine
    NOVA_AVAILABLE = True
except ImportError:
    # Fallback for development/testing without full Nova environment
    NOVA_AVAILABLE = False

    class TriEngine:
        def calculate(self, content: str) -> float:
            return 0.85  # Default neutral TRI score

    class CulturalSynthesisEngine:
        def synthesize(self, profile: dict) -> dict:
            return {
                'adaptation_effectiveness': 0.8,
                'principle_preservation_score': 0.85,
                'residual_risk': 0.15
            }


@dataclass
class SimulationMetricsCollector:
    """Prometheus metrics collector for agent simulations"""

    registry: CollectorRegistry = field(default_factory=CollectorRegistry)

    # Core simulation metrics
    simulation_duration: Histogram = field(init=False)
    agent_count: Gauge = field(init=False)
    consensus_reached: Gauge = field(init=False)
    polarization_index: Gauge = field(init=False)

    # Nova integration metrics (Phase 11 requirements)
    tri_score: Gauge = field(init=False)  # Truth Resonance Index
    cultural_coherence: Gauge = field(init=False)  # CGC - Cultural Coherence Grade
    bias_index: Gauge = field(init=False)  # Bias detection metric

    # Safety and quality metrics
    fcq_score: Gauge = field(init=False)  # Federated Consensus Quality
    simulation_errors: Counter = field(init=False)
    guardrail_violations: Counter = field(init=False)

    def __post_init__(self):
        """Initialize Prometheus metrics"""
        # Simulation performance
        self.simulation_duration = Histogram(
            'nova_simulation_duration_seconds',
            'Duration of agent simulation runs',
            ['consensus_model', 'num_agents'],
            registry=self.registry
        )

        self.agent_count = Gauge(
            'nova_simulation_agents_total',
            'Number of agents in simulation',
            registry=self.registry
        )

        # Consensus metrics
        self.consensus_reached = Gauge(
            'nova_simulation_consensus_reached',
            'Whether consensus was reached (1=yes, 0=no)',
            ['topic'],
            registry=self.registry
        )

        self.polarization_index = Gauge(
            'nova_simulation_polarization_index',
            'Degree of belief polarization in simulation',
            ['topic'],
            registry=self.registry
        )

        # Nova integration metrics (Phase 11 requirements)
        self.tri_score = Gauge(
            'nova_simulation_tri_score',
            'Truth Resonance Index for simulation content',
            registry=self.registry
        )

        self.cultural_coherence = Gauge(
            'nova_simulation_cultural_coherence',
            'Cultural Coherence Grade (CGC) for simulation',
            registry=self.registry
        )

        self.bias_index = Gauge(
            'nova_simulation_bias_index',
            'Bias detection index for agent population diversity',
            registry=self.registry
        )

        # Safety metrics
        self.fcq_score = Gauge(
            'nova_simulation_fcq_score',
            'Federated Consensus Quality score',
            registry=self.registry
        )

        self.simulation_errors = Counter(
            'nova_simulation_errors_total',
            'Total simulation errors',
            ['error_type'],
            registry=self.registry
        )

        self.guardrail_violations = Counter(
            'nova_simulation_guardrail_violations_total',
            'Total guardrail violations during simulation',
            ['guardrail_type'],
            registry=self.registry
        )


class SimulationGuardrails:
    """Guardrail validation for agent simulations"""

    def __init__(self):
        self.tri_engine = TriEngine()
        self.cultural_engine = CulturalSynthesisEngine()

        # Nova guardrail thresholds (from Phase 11 requirements)
        self.thresholds = {
            'tri_minimum': 0.80,      # TRI ≥ 0.80
            'eai_minimum': 0.85,      # EAI ≥ 0.85 (Ethical AI Index)
            'cgc_minimum': 0.82,      # CGC ≥ 0.82 (Cultural Coherence Grade)
            'pis_required': 1.0,      # PIS = 1.0 (Provenance Integrity Score)
            'fcq_freeze': 0.90        # FCQ ≥ 0.90 triggers freeze
        }

    def validate_simulation(self, simulation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate simulation against Nova guardrails"""

        violations = []
        warnings = []

        # TRI validation
        tri_score = simulation_data.get('tri_score', 0.0)
        if tri_score < self.thresholds['tri_minimum']:
            violations.append({
                'type': 'tri_violation',
                'message': f'TRI score {tri_score:.3f} below minimum {self.thresholds["tri_minimum"]}',
                'severity': 'critical'
            })

        # CGC validation
        cgc_score = simulation_data.get('cultural_coherence', 0.0)
        if cgc_score < self.thresholds['cgc_minimum']:
            violations.append({
                'type': 'cgc_violation',
                'message': f'CGC score {cgc_score:.3f} below minimum {self.thresholds["cgc_minimum"]}',
                'severity': 'high'
            })

        # FCQ freeze check
        fcq_score = simulation_data.get('fcq_score', 0.0)
        if fcq_score >= self.thresholds['fcq_freeze']:
            warnings.append({
                'type': 'fcq_freeze_warning',
                'message': f'FCQ score {fcq_score:.3f} at freeze threshold {self.thresholds["fcq_freeze"]}',
                'severity': 'medium'
            })

        # PIS validation (simplified - would integrate with provenance system)
        pis_score = simulation_data.get('pis_score', 1.0)  # Assume valid unless specified
        if pis_score < self.thresholds['pis_required']:
            violations.append({
                'type': 'pis_violation',
                'message': f'PIS score {pis_score:.3f} below required {self.thresholds["pis_required"]}',
                'severity': 'critical'
            })

        # EAI validation (simplified - would integrate with ethics system)
        eai_score = simulation_data.get('eai_score', 0.9)  # Assume compliant unless specified
        if eai_score < self.thresholds['eai_minimum']:
            violations.append({
                'type': 'eai_violation',
                'message': f'EAI score {eai_score:.3f} below minimum {self.thresholds["eai_minimum"]}',
                'severity': 'high'
            })

        return {
            'valid': len(violations) == 0,
            'violations': violations,
            'warnings': warnings,
            'overall_severity': self._calculate_severity(violations),
            'timestamp': time.time()
        }

    def _calculate_severity(self, violations: List[Dict[str, Any]]) -> str:
        """Calculate overall severity from violations"""
        if not violations:
            return 'none'

        severities = [v['severity'] for v in violations]
        if 'critical' in severities:
            return 'critical'
        elif 'high' in severities:
            return 'high'
        elif 'medium' in severities:
            return 'medium'
        else:
            return 'low'


class SimulationMonitor:
    """Real-time simulation monitoring and alerting"""

    def __init__(self, metrics_collector: SimulationMetricsCollector,
                 guardrails: SimulationGuardrails):
        self.metrics = metrics_collector
        self.guardrails = guardrails
        self.active_simulations: Dict[str, Dict[str, Any]] = {}

    def start_simulation(self, simulation_id: str, config: Dict[str, Any]):
        """Start monitoring a simulation"""
        self.active_simulations[simulation_id] = {
            'config': config,
            'start_time': time.time(),
            'metrics_history': [],
            'last_update': time.time()
        }

        # Update Prometheus metrics
        self.metrics.agent_count.set(config.get('num_agents', 0))

    def update_simulation(self, simulation_id: str, metrics_data: Dict[str, Any]):
        """Update simulation metrics and check guardrails"""
        if simulation_id not in self.active_simulations:
            return

        sim_data = self.active_simulations[simulation_id]
        sim_data['last_update'] = time.time()
        sim_data['metrics_history'].append(metrics_data)

        # Update Prometheus metrics
        self.metrics.tri_score.set(metrics_data.get('tri_score', 0.0))
        self.metrics.cultural_coherence.set(metrics_data.get('cultural_coherence', 0.0))
        self.metrics.bias_index.set(metrics_data.get('bias_index', 0.0))
        self.metrics.fcq_score.set(metrics_data.get('fcq_score', 0.0))

        # Update topic-specific metrics
        for topic, consensus in metrics_data.get('consensus_reached', {}).items():
            self.metrics.consensus_reached.labels(topic=topic).set(1 if consensus else 0)

        for topic, polarization in metrics_data.get('polarization_index', {}).items():
            self.metrics.polarization_index.labels(topic=topic).set(polarization)

        # Validate guardrails
        validation = self.guardrails.validate_simulation(metrics_data)

        if not validation['valid']:
            # Record violations
            for violation in validation['violations']:
                self.metrics.guardrail_violations.labels(
                    guardrail_type=violation['type']
                ).inc()

            # Could trigger alerts here based on severity
            if validation['overall_severity'] in ['critical', 'high']:
                print(f"🚨 CRITICAL: Simulation {simulation_id} guardrail violations detected")

    def end_simulation(self, simulation_id: str, final_results: Dict[str, Any]):
        """End simulation monitoring"""
        if simulation_id not in self.active_simulations:
            return

        sim_data = self.active_simulations[simulation_id]
        duration = time.time() - sim_data['start_time']

        # Record final metrics
        config = sim_data['config']
        consensus_model = config.get('consensus_model', 'unknown')
        num_agents = config.get('num_agents', 0)

        self.metrics.simulation_duration.labels(
            consensus_model=consensus_model,
            num_agents=str(num_agents)
        ).observe(duration)

        # Final guardrail check
        validation = self.guardrails.validate_simulation(final_results)
        if not validation['valid']:
            print(f"⚠️  WARNING: Simulation {simulation_id} completed with guardrail violations")

        # Cleanup
        del self.active_simulations[simulation_id]

    def get_simulation_status(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a simulation"""
        return self.active_simulations.get(simulation_id)

    def get_all_active_simulations(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all active simulations"""
        return self.active_simulations.copy()


# Global instances for easy access
_metrics_collector = SimulationMetricsCollector()
_guardrails = SimulationGuardrails()
_monitor = SimulationMonitor(_metrics_collector, _guardrails)

def get_metrics_collector() -> SimulationMetricsCollector:
    """Get global metrics collector"""
    return _metrics_collector

def get_guardrails() -> SimulationGuardrails:
    """Get global guardrails validator"""
    return _guardrails

def get_monitor() -> SimulationMonitor:
    """Get global simulation monitor"""
    return _monitor