"""
Nova Simulation Interface (NSI) - Phase 11.0-alpha
/simulate_agents REST API Endpoint

Provides HTTP interface for running LLM-agent simulations with Nova integration.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, validator
import asyncio
import uuid
from datetime import datetime

from nova.sim.agents import (
    MultiAgentSimulator, SimulationConfig, ConsensusModel,
    create_demo_config
)
from nova.sim.metrics import get_monitor, get_guardrails


router = APIRouter(prefix="/simulate", tags=["simulation"])


class SimulationRequest(BaseModel):
    """Request model for agent simulation"""

    num_agents: int = Field(10, ge=5, le=50, description="Number of agents (5-50)")
    max_steps: int = Field(100, ge=10, le=500, description="Maximum simulation steps")
    consensus_model: str = Field("degroot", description="Consensus algorithm")
    topics: List[str] = Field(
        default_factory=lambda: ["ai_safety", "climate_change", "social_justice"],
        description="Discussion topics"
    )
    network_density: float = Field(0.3, ge=0.0, le=1.0, description="Social network connectivity")
    stubbornness_alpha: Optional[float] = Field(0.3, description="Friedkin-Johnsen stubbornness")
    diffusion_probability: Optional[float] = Field(0.1, description="Information diffusion probability")
    threshold_tau: Optional[float] = Field(0.5, description="Threshold model activation threshold")
    enable_memory: bool = Field(True, description="Enable agent memory")
    enable_reflection: bool = Field(True, description="Enable agent reflection")

    @validator('consensus_model')
    def validate_consensus_model(cls, v):
        valid_models = [model.value for model in ConsensusModel]
        if v not in valid_models:
            raise ValueError(f'consensus_model must be one of {valid_models}')
        return v

    def to_config(self) -> SimulationConfig:
        """Convert to SimulationConfig"""
        return SimulationConfig(
            num_agents=self.num_agents,
            max_steps=self.max_steps,
            consensus_model=ConsensusModel(self.consensus_model),
            topics=self.topics,
            network_density=self.network_density,
            stubbornness_alpha=self.stubbornness_alpha,
            diffusion_probability=self.diffusion_probability,
            threshold_tau=self.threshold_tau,
            enable_memory=self.enable_memory,
            enable_reflection=self.enable_reflection
        )


class SimulationStatus(BaseModel):
    """Status response for running simulation"""

    simulation_id: str
    status: str  # "running", "completed", "failed"
    progress: float  # 0.0 to 1.0
    start_time: float
    estimated_completion: Optional[float]
    current_step: int
    max_steps: int
    metrics: Dict[str, Any] = Field(default_factory=dict)


class SimulationResult(BaseModel):
    """Complete simulation results"""

    simulation_id: str
    status: str
    duration_steps: int
    final_consensus: Dict[str, bool]
    avg_polarization: float
    final_tri_score: float
    cultural_coherence: float
    bias_index: float
    fcq_score: float
    guardrail_validation: Dict[str, Any]
    agent_final_states: Dict[str, Any]
    completed_at: float


# Global simulation registry
_active_simulations: Dict[str, Dict[str, Any]] = {}


@router.post("/agents", response_model=SimulationStatus)
async def start_agent_simulation(
    request: SimulationRequest,
    background_tasks: BackgroundTasks
) -> SimulationStatus:
    """Start a new multi-agent simulation"""

    simulation_id = str(uuid.uuid4())

    # Create simulation config
    config = request.to_config()

    # Initialize monitoring
    monitor = get_monitor()
    monitor.start_simulation(simulation_id, {
        'num_agents': config.num_agents,
        'max_steps': config.max_steps,
        'consensus_model': config.consensus_model.value
    })

    # Start simulation in background
    background_tasks.add_task(run_simulation_background, simulation_id, config)

    # Return initial status
    return SimulationStatus(
        simulation_id=simulation_id,
        status="running",
        progress=0.0,
        start_time=monitor.active_simulations[simulation_id]['start_time'],
        estimated_completion=None,
        current_step=0,
        max_steps=config.max_steps,
        metrics={}
    )


@router.get("/agents/{simulation_id}", response_model=SimulationStatus)
async def get_simulation_status(simulation_id: str) -> SimulationStatus:
    """Get status of a running simulation"""

    monitor = get_monitor()
    sim_data = monitor.get_simulation_status(simulation_id)

    if not sim_data:
        # Check if completed
        if simulation_id in _active_simulations:
            result = _active_simulations[simulation_id]
            if result['status'] == 'completed':
                return SimulationStatus(
                    simulation_id=simulation_id,
                    status="completed",
                    progress=1.0,
                    start_time=result['start_time'],
                    estimated_completion=result['completed_at'],
                    current_step=result['duration_steps'],
                    max_steps=result['config'].max_steps,
                    metrics=result
                )
        raise HTTPException(status_code=404, detail="Simulation not found")

    config = sim_data['config']
    metrics_history = sim_data['metrics_history']

    current_step = len(metrics_history)
    progress = min(current_step / config['max_steps'], 1.0)

    latest_metrics = metrics_history[-1] if metrics_history else {}

    return SimulationStatus(
        simulation_id=simulation_id,
        status="running",
        progress=progress,
        start_time=sim_data['start_time'],
        estimated_completion=None,  # Could estimate based on progress
        current_step=current_step,
        max_steps=config['max_steps'],
        metrics=latest_metrics
    )


@router.get("/agents/{simulation_id}/results", response_model=SimulationResult)
async def get_simulation_results(simulation_id: str) -> SimulationResult:
    """Get complete results of a finished simulation"""

    if simulation_id not in _active_simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")

    result = _active_simulations[simulation_id]
    if result['status'] != 'completed':
        raise HTTPException(status_code=202, detail="Simulation not yet completed")

    # Validate against guardrails
    guardrails = get_guardrails()
    validation = guardrails.validate_simulation(result)

    return SimulationResult(
        simulation_id=simulation_id,
        status=result['status'],
        duration_steps=result['duration_steps'],
        final_consensus=result['final_consensus'],
        avg_polarization=result['avg_polarization'],
        final_tri_score=result['final_tri_score'],
        cultural_coherence=result['cultural_coherence'],
        bias_index=result['bias_index'],
        fcq_score=result['fcq_score'],
        guardrail_validation=validation,
        agent_final_states=result['agent_final_states'],
        completed_at=result['completed_at']
    )


@router.post("/agents/demo")
async def run_demo_simulation(background_tasks: BackgroundTasks) -> SimulationStatus:
    """Run a demonstration simulation with default parameters"""

    simulation_id = str(uuid.uuid4())
    config = create_demo_config()

    # Initialize monitoring
    monitor = get_monitor()
    monitor.start_simulation(simulation_id, {
        'num_agents': config.num_agents,
        'max_steps': config.max_steps,
        'consensus_model': config.consensus_model.value
    })

    # Start demo simulation
    background_tasks.add_task(run_simulation_background, simulation_id, config)

    return SimulationStatus(
        simulation_id=simulation_id,
        status="running",
        progress=0.0,
        start_time=monitor.active_simulations[simulation_id]['start_time'],
        estimated_completion=None,
        current_step=0,
        max_steps=config.max_steps,
        metrics={}
    )


@router.get("/agents")
async def list_simulations() -> Dict[str, List[str]]:
    """List all active and completed simulations"""

    monitor = get_monitor()
    active = list(monitor.active_simulations.keys())
    completed = [sid for sid in _active_simulations.keys()
                if _active_simulations[sid]['status'] == 'completed']

    return {
        "active": active,
        "completed": completed,
        "total": len(active) + len(completed)
    }


async def run_simulation_background(simulation_id: str, config: SimulationConfig):
    """Background task to run simulation"""

    try:
        # Create and run simulator
        simulator = MultiAgentSimulator(config)

        # Run simulation with progress updates
        monitor = get_monitor()

        for step in range(config.max_steps):
            # Run one step
            await simulator._agent_interaction_step()
            simulator._consensus_step()
            simulator._update_metrics()

            # Update monitoring
            metrics_data = {
                'step_count': simulator.metrics.step_count,
                'consensus_reached': simulator.metrics.consensus_reached,
                'polarization_index': simulator.metrics.polarization_index,
                'tri_score': simulator.metrics.tri_scores[-1] if simulator.metrics.tri_scores else 0.0,
                'cultural_coherence': simulator.metrics.cultural_coherence[-1] if simulator.metrics.cultural_coherence else 0.0,
                'bias_index': simulator.metrics.bias_index,
                'fcq_score': simulator.metrics.fcq_score
            }

            monitor.update_simulation(simulation_id, metrics_data)

            # Check for convergence
            if simulator._check_convergence():
                break

            # Small delay to prevent overwhelming the system
            await asyncio.sleep(0.01)

        # Final evaluation
        final_results = simulator._evaluate_simulation()
        final_results.update({
            'simulation_id': simulation_id,
            'status': 'completed',
            'config': config,
            'start_time': monitor.active_simulations[simulation_id]['start_time'],
            'completed_at': asyncio.get_event_loop().time()
        })

        # Store results
        _active_simulations[simulation_id] = final_results

        # End monitoring
        monitor.end_simulation(simulation_id, final_results)

        print(f"✅ Simulation {simulation_id} completed successfully")

    except Exception as e:
        print(f"❌ Simulation {simulation_id} failed: {e}")

        # Mark as failed
        _active_simulations[simulation_id] = {
            'simulation_id': simulation_id,
            'status': 'failed',
            'error': str(e),
            'completed_at': asyncio.get_event_loop().time()
        }

        # Update monitoring
        monitor = get_monitor()
        monitor.end_simulation(simulation_id, {'error': str(e)})


# Health check endpoint for simulation service
@router.get("/health")
async def simulation_health() -> Dict[str, Any]:
    """Health check for simulation service"""

    monitor = get_monitor()
    guardrails = get_guardrails()

    return {
        "status": "healthy",
        "service": "nova-simulation-interface",
        "version": "11.0-alpha",
        "active_simulations": len(monitor.active_simulations),
        "completed_simulations": len([s for s in _active_simulations.values()
                                    if s.get('status') == 'completed']),
        "guardrails": {
            "tri_threshold": guardrails.thresholds['tri_minimum'],
            "cgc_threshold": guardrails.thresholds['cgc_minimum'],
            "fcq_freeze_threshold": guardrails.thresholds['fcq_freeze']
        },
        "timestamp": asyncio.get_event_loop().time()
    }