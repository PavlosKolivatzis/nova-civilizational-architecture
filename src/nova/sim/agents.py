"""
Nova Simulation Interface (NSI) - Phase 11.0-alpha
LLM-Agent Simulation Environment with Civilizational Ethics

Implements multi-agent simulations using:
- (PO)MDP for decision-making
- DeGroot/Friedkin-Johnsen for opinion dynamics
- Independent Cascade for information diffusion
- Threshold models for social influence
- Federated Consensus Quality (FCQ) validation
"""

from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import asyncio
import time
from datetime import datetime

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


class AgentState(Enum):
    """Agent cognitive states in simulation"""
    BELIEF_UPDATE = "belief_update"
    PLANNING = "planning"
    ACTION = "action"
    REFLECTION = "reflection"
    SOCIAL_INTERACTION = "social_interaction"


class ConsensusModel(Enum):
    """Opinion dynamics models"""
    DEGROOT = "degroot"  # Simple averaging
    FRIEDKIN_JOHNSEN = "friedkin_johnsen"  # With stubbornness
    INDEPENDENT_CASCADE = "independent_cascade"  # Information diffusion
    THRESHOLD = "threshold"  # Granovetter model


@dataclass
class AgentBelief:
    """Agent belief state with uncertainty"""
    value: float  # Current belief [0,1]
    confidence: float  # Confidence in belief [0,1]
    volatility: float  # Belief stability [0,1]
    last_update: float  # Timestamp
    evidence_count: int  # Supporting evidence


@dataclass
class AgentMemory:
    """Agent episodic memory with recency weighting"""
    episodes: List[Dict[str, Any]] = field(default_factory=list)
    half_life_hours: float = 24.0  # Recency decay parameter
    max_episodes: int = 1000

    def add_episode(self, episode: Dict[str, Any]):
        """Add episode with timestamp"""
        episode['timestamp'] = time.time()
        self.episodes.append(episode)
        if len(self.episodes) > self.max_episodes:
            self.episodes.pop(0)

    def get_weighted_traits(self) -> Dict[str, float]:
        """Extract personality traits using recency weighting"""
        if not self.episodes:
            return {}

        traits = {}
        current_time = time.time()

        for episode in self.episodes:
            age_hours = (current_time - episode['timestamp']) / 3600
            weight = 2 ** (-age_hours / self.half_life_hours)  # Exponential decay

            for trait, value in episode.get('traits', {}).items():
                if trait not in traits:
                    traits[trait] = 0.0
                traits[trait] += weight * value

        # Normalize by total weight
        total_weight = sum(2 ** (-(current_time - ep['timestamp']) / 3600 / self.half_life_hours)
                          for ep in self.episodes)
        if total_weight > 0:
            traits = {k: v / total_weight for k, v in traits.items()}

        return traits


@dataclass
class SimulationAgent:
    """Individual agent in multi-agent simulation"""
    agent_id: str
    name: str
    personality_traits: Dict[str, float]  # openness, conscientiousness, etc.
    initial_beliefs: Dict[str, AgentBelief]
    memory: AgentMemory = field(default_factory=AgentMemory)
    social_network: List[str] = field(default_factory=list)  # Connected agent IDs
    state: AgentState = AgentState.BELIEF_UPDATE

    def update_belief(self, topic: str, new_value: float, evidence_strength: float = 1.0):
        """Bayesian belief update with evidence"""
        if topic not in self.initial_beliefs:
            self.initial_beliefs[topic] = AgentBelief(0.5, 0.5, 0.5, time.time(), 0)

        belief = self.initial_beliefs[topic]

        # Simple Bayesian update (could be extended to full probabilistic model)
        prior_weight = belief.confidence * belief.evidence_count
        evidence_weight = evidence_strength

        updated_value = (belief.value * prior_weight + new_value * evidence_weight) / (prior_weight + evidence_weight)
        updated_confidence = min(1.0, belief.confidence + evidence_strength * 0.1)
        updated_evidence = belief.evidence_count + 1

        belief.value = updated_value
        belief.confidence = updated_confidence
        belief.evidence_count = updated_evidence
        belief.last_update = time.time()

        # Record in memory for reflection
        self.memory.add_episode({
            'type': 'belief_update',
            'topic': topic,
            'old_value': belief.value,
            'new_value': updated_value,
            'evidence_strength': evidence_strength,
            'traits': self.personality_traits
        })


@dataclass
class SimulationConfig:
    """Configuration for multi-agent simulation"""
    num_agents: int = 10
    max_steps: int = 100
    consensus_model: ConsensusModel = ConsensusModel.DEGROOT
    topics: List[str] = field(default_factory=lambda: ["climate_change", "ai_safety", "social_justice"])
    network_density: float = 0.3  # Social network connectivity
    stubbornness_alpha: float = 0.3  # For Friedkin-Johnsen model
    diffusion_probability: float = 0.1  # For Independent Cascade
    threshold_tau: float = 0.5  # For Threshold model
    enable_memory: bool = True
    enable_reflection: bool = True


@dataclass
class SimulationMetrics:
    """Real-time simulation monitoring"""
    step_count: int = 0
    consensus_reached: Dict[str, bool] = field(default_factory=dict)
    polarization_index: Dict[str, float] = field(default_factory=dict)
    information_spread: Dict[str, int] = field(default_factory=dict)
    belief_volatility: Dict[str, float] = field(default_factory=dict)
    tri_scores: List[float] = field(default_factory=list)
    cultural_coherence: List[float] = field(default_factory=list)
    bias_index: float = 0.0
    fcq_score: float = 0.0
    timestamp: float = field(default_factory=time.time)


class ConsensusEngine:
    """Implements various opinion dynamics models"""

    def __init__(self, config: SimulationConfig):
        self.config = config

    def degroot_consensus(self, beliefs: np.ndarray, adjacency: np.ndarray,
                         max_iterations: int = 100, tolerance: float = 1e-6) -> np.ndarray:
        """DeGroot model: x_{t+1} = W x_t where W is row-stochastic"""
        x = beliefs.copy()

        for _ in range(max_iterations):
            x_new = adjacency @ x
            if np.max(np.abs(x_new - x)) < tolerance:
                break
            x = x_new

        return x

    def friedkin_johnsen_consensus(self, beliefs: np.ndarray, adjacency: np.ndarray,
                                  initial_beliefs: np.ndarray, alpha: float = 0.3,
                                  max_iterations: int = 100) -> np.ndarray:
        """Friedkin-Johnsen: x_{t+1} = α W x_t + (1-α) x_0"""
        x = beliefs.copy()
        x0 = initial_beliefs.copy()

        for _ in range(max_iterations):
            x = alpha * (adjacency @ x) + (1 - alpha) * x0

        return x

    def independent_cascade(self, seeds: List[int], adjacency: np.ndarray,
                           probability: float = 0.1) -> set:
        """Independent Cascade model for information diffusion"""
        activated = set(seeds)
        newly_activated = set(seeds)

        while newly_activated:
            next_newly = set()
            for node in newly_activated:
                for neighbor in np.where(adjacency[node] > 0)[0]:
                    if neighbor not in activated:
                        if np.random.random() < probability:
                            activated.add(neighbor)
                            next_newly.add(neighbor)
            newly_activated = next_newly

        return activated

    def threshold_model(self, beliefs: np.ndarray, adjacency: np.ndarray,
                       thresholds: np.ndarray) -> np.ndarray:
        """Granovetter threshold model"""
        activated = beliefs > 0.5  # Initial activation
        changed = True

        while changed:
            changed = False
            for i in range(len(beliefs)):
                if not activated[i]:
                    active_neighbors = np.sum(activated * adjacency[i])
                    degree = np.sum(adjacency[i])
                    if degree > 0 and (active_neighbors / degree) >= thresholds[i]:
                        activated[i] = True
                        changed = True

        return activated.astype(float)


class MultiAgentSimulator:
    """Core multi-agent simulation engine"""

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.agents: Dict[str, SimulationAgent] = {}
        self.consensus_engine = ConsensusEngine(config)
        self.tri_engine = TriEngine()
        self.cultural_engine = CulturalSynthesisEngine()
        self.metrics = SimulationMetrics()

        # Initialize agents
        self._initialize_agents()

    def _initialize_agents(self):
        """Create diverse agent population"""
        personality_dimensions = ['openness', 'conscientiousness', 'extraversion',
                                'agreeableness', 'neuroticism']

        for i in range(self.config.num_agents):
            # Generate diverse personality traits
            traits = {dim: np.random.beta(2, 2) for dim in personality_dimensions}

            # Initialize beliefs with some diversity
            beliefs = {}
            for topic in self.config.topics:
                base_belief = np.random.beta(2, 2)  # Centered around 0.5
                # Personality influences initial beliefs
                personality_effect = (traits['openness'] - 0.5) * 0.2  # Openness increases extremism
                belief_value = np.clip(base_belief + personality_effect, 0.1, 0.9)

                beliefs[topic] = AgentBelief(
                    value=belief_value,
                    confidence=np.random.beta(3, 2),  # Slightly optimistic confidence
                    volatility=np.random.beta(2, 3),  # Low volatility
                    last_update=time.time(),
                    evidence_count=1
                )

            # Create social network (Erdős–Rényi model)
            social_network = []
            for j in range(self.config.num_agents):
                if i != j and np.random.random() < self.config.network_density:
                    social_network.append(f"agent_{j}")

            agent = SimulationAgent(
                agent_id=f"agent_{i}",
                name=f"Agent_{i}",
                personality_traits=traits,
                initial_beliefs=beliefs,
                social_network=social_network
            )

            self.agents[agent.agent_id] = agent

    async def run_simulation(self) -> Dict[str, Any]:
        """Execute multi-agent simulation with monitoring"""
        print(f"Starting simulation with {self.config.num_agents} agents...")

        for step in range(self.config.max_steps):
            self.metrics.step_count = step

            # Agent interaction phase
            await self._agent_interaction_step()

            # Consensus formation
            self._consensus_step()

            # Update metrics
            self._update_metrics()

            # Check termination conditions
            if self._check_convergence():
                break

        # Final evaluation
        final_results = self._evaluate_simulation()

        print(f"Simulation completed in {self.metrics.step_count} steps")
        print(f"Final FCQ: {self.metrics.fcq_score:.3f}")

        return final_results

    async def _agent_interaction_step(self):
        """Simulate agent-agent interactions"""
        # Simple pairwise interactions
        agent_ids = list(self.agents.keys())

        for i in range(0, len(agent_ids), 2):
            if i + 1 < len(agent_ids):
                agent1 = self.agents[agent_ids[i]]
                agent2 = self.agents[agent_ids[i + 1]]

                # Social influence based on personality
                influence_strength = (agent1.personality_traits['extraversion'] +
                                    agent2.personality_traits['agreeableness']) / 2

                # Exchange beliefs on random topic
                topic = np.random.choice(self.config.topics)
                await self._belief_exchange(agent1, agent2, topic, influence_strength)

                # Update memories
                if self.config.enable_memory:
                    agent1.memory.add_episode({
                        'type': 'social_interaction',
                        'partner': agent2.agent_id,
                        'topic': topic,
                        'influence': influence_strength,
                        'traits': agent1.personality_traits
                    })

    async def _belief_exchange(self, agent1: SimulationAgent, agent2: SimulationAgent,
                             topic: str, influence: float) -> Dict[str, Any]:
        """Model belief exchange between two agents"""
        belief1 = agent1.initial_beliefs[topic]
        belief2 = agent2.initial_beliefs[topic]

        # Weighted average based on confidence and influence
        total_weight = belief1.confidence + belief2.confidence
        if total_weight > 0:
            new_belief1 = (belief1.value * belief1.confidence + belief2.value * belief2.confidence * influence) / total_weight
            new_belief2 = (belief2.value * belief2.confidence + belief1.value * belief1.confidence * influence) / total_weight

            # Update beliefs with some resistance to change
            resistance1 = 1 - agent1.personality_traits.get('openness', 0.5)
            resistance2 = 1 - agent2.personality_traits.get('openness', 0.5)

            agent1.update_belief(topic, new_belief1, (1 - resistance1) * influence)
            agent2.update_belief(topic, new_belief2, (1 - resistance2) * influence)

        return {'topic': topic, 'influence': influence}

    def _consensus_step(self):
        """Apply consensus model to belief evolution"""
        for topic in self.config.topics:
            beliefs = np.array([agent.initial_beliefs[topic].value for agent in self.agents.values()])

            # Create adjacency matrix from social networks
            n = len(self.agents)
            adjacency = np.zeros((n, n))

            agent_list = list(self.agents.values())
            for i, agent in enumerate(agent_list):
                for connected_id in agent.social_network:
                    if connected_id in self.agents:
                        j = [a.agent_id for a in agent_list].index(connected_id)
                        adjacency[i, j] = 1

            # Make row-stochastic
            row_sums = adjacency.sum(axis=1)
            row_sums[row_sums == 0] = 1  # Avoid division by zero
            adjacency = adjacency / row_sums[:, np.newaxis]

            # Apply consensus model
            if self.config.consensus_model == ConsensusModel.DEGROOT:
                new_beliefs = self.consensus_engine.degroot_consensus(beliefs, adjacency)
            elif self.config.consensus_model == ConsensusModel.FRIEDKIN_JOHNSEN:
                initial_beliefs = np.array([agent.initial_beliefs[topic].value for agent in agent_list])
                new_beliefs = self.consensus_engine.friedkin_johnsen_consensus(
                    beliefs, adjacency, initial_beliefs, self.config.stubbornness_alpha)
            else:
                new_beliefs = beliefs  # No change for other models

            # Update agent beliefs
            for i, agent in enumerate(agent_list):
                agent.update_belief(topic, new_beliefs[i], 0.5)

    def _update_metrics(self):
        """Update simulation metrics"""
        for topic in self.config.topics:
            beliefs = [agent.initial_beliefs[topic].value for agent in self.agents.values()]
            beliefs_array = np.array(beliefs)

            # Consensus check (DeGroot convergence)
            consensus_threshold = 0.05
            self.metrics.consensus_reached[topic] = np.std(beliefs_array) < consensus_threshold

            # Polarization (variance)
            self.metrics.polarization_index[topic] = np.var(beliefs_array)

            # Information spread (simplified)
            self.metrics.information_spread[topic] = len([b for b in beliefs if b > 0.5])

            # Belief volatility
            self.metrics.belief_volatility[topic] = np.std(beliefs_array)

        # TRI and cultural evaluation
        sample_content = f"Simulation beliefs: {self.metrics.consensus_reached}"
        tri_score = self.tri_engine.calculate(sample_content)
        self.metrics.tri_scores.append(tri_score)

        # Cultural coherence (simplified)
        coherence = 1.0 - np.mean(list(self.metrics.polarization_index.values()))
        self.metrics.cultural_coherence.append(coherence)

        # Bias index (simplified diversity measure)
        personality_diversity = np.std([agent.personality_traits['openness'] for agent in self.agents.values()])
        self.metrics.bias_index = personality_diversity

        # FCQ calculation (simplified)
        alignment_scores = [1.0 - pol for pol in self.metrics.polarization_index.values()]
        provenance_scores = [0.9] * len(alignment_scores)  # Simplified
        weights = [1.0] * len(alignment_scores)

        if alignment_scores:
            fcq = sum(w * a * p for w, a, p in zip(weights, alignment_scores, provenance_scores)) / sum(weights)
            self.metrics.fcq_score = fcq

    def _check_convergence(self) -> bool:
        """Check if simulation should terminate"""
        # Terminate if consensus reached on all topics or max steps hit
        all_consensus = all(self.metrics.consensus_reached.values())
        return all_consensus or self.metrics.step_count >= self.config.max_steps - 1

    def _evaluate_simulation(self) -> Dict[str, Any]:
        """Final simulation evaluation"""
        return {
            'duration_steps': self.metrics.step_count,
            'final_consensus': self.metrics.consensus_reached,
            'avg_polarization': np.mean(list(self.metrics.polarization_index.values())),
            'final_tri_score': self.metrics.tri_scores[-1] if self.metrics.tri_scores else 0.0,
            'cultural_coherence': np.mean(self.metrics.cultural_coherence),
            'bias_index': self.metrics.bias_index,
            'fcq_score': self.metrics.fcq_score,
            'agent_final_states': {
                agent_id: {
                    'beliefs': {topic: agent.initial_beliefs[topic].value
                              for topic in self.config.topics},
                    'personality': agent.personality_traits,
                    'social_connections': len(agent.social_network)
                }
                for agent_id, agent in self.agents.items()
            }
        }


# Convenience functions for external use
async def run_agent_simulation(config: SimulationConfig = None) -> Dict[str, Any]:
    """Run a multi-agent simulation with default or custom config"""
    if config is None:
        config = SimulationConfig()

    simulator = MultiAgentSimulator(config)
    return await simulator.run_simulation()


def create_demo_config() -> SimulationConfig:
    """Create demonstration configuration (5-50 agents as requested)"""
    return SimulationConfig(
        num_agents=25,  # Mid-range for demo
        max_steps=50,
        consensus_model=ConsensusModel.FRIEDKIN_JOHNSEN,
        topics=["ai_alignment", "climate_policy", "social_equality"],
        network_density=0.4,
        stubbornness_alpha=0.2,
        enable_memory=True,
        enable_reflection=True
    )
