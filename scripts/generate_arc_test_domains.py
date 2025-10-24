#!/usr/bin/env python3
"""
Nova ARC Test Domain Generator
Phase 11B: Autonomous Reflection Cycle

Generates synthetic test domains for ARC calibration experiments.
Supports both standard extraction systems and adversarial domains for robustness testing.

Usage:
    python scripts/generate_arc_test_domains.py --count 100 --output data/arc_test_domains.json
    python scripts/generate_arc_test_domains.py --count 50 --adversarial 20 --mismatch-equilibrium --output data/arc_adversarial_domains.json
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from nova.math.relations_pattern import StructuralAnalyzer, SystemGraph, create_example_extraction_system

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ARCTestDomainGenerator:
    """Generates test domains for ARC calibration"""

    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)

    def generate_extraction_system(self, system_id: str) -> Dict[str, Any]:
        """Generate a standard extraction system domain"""
        graph = create_example_extraction_system()

        # Add some realistic variation
        self._add_realistic_noise(graph)

        return {
            'id': system_id,
            'type': 'extraction_system',
            'graph_data': self._graph_to_dict(graph),
            'ground_truth': 'extraction_system',
            'expected_pattern': True,
            'description': 'Standard extraction system with harm propagation and equilibrium dynamics'
        }

    def generate_noise_domain(self, system_id: str) -> Dict[str, Any]:
        """Generate a noise domain without extraction structure"""
        graph = SystemGraph()

        # Create random graph
        num_nodes = random.randint(15, 25)
        for i in range(num_nodes):
            graph.add_node(f'node_{i}', {'value': np.random.random()})

        # Add random edges
        num_edges = random.randint(num_nodes, num_nodes * 2)
        for _ in range(num_edges):
            src = f'node_{random.randint(0, num_nodes-1)}'
            dst = f'node_{random.randint(0, num_nodes-1)}'
            if src != dst:
                graph.add_edge(src, dst, {'weight': np.random.random()})

        return {
            'id': system_id,
            'type': 'noise',
            'graph_data': self._graph_to_dict(graph),
            'ground_truth': None,
            'expected_pattern': False,
            'description': 'Random noise graph without extraction structure'
        }

    def generate_adversarial_domain_spectral_match(self, system_id: str) -> Dict[str, Any]:
        """Generate adversarial domain: spectrally similar but no extraction equilibrium"""
        # Start with a real extraction system
        base_graph = create_example_extraction_system()

        # Get spectral signature
        base_spectrum = StructuralAnalyzer.normalized_laplacian_spectrum(base_graph)

        # Create a new graph that matches the spectral signature but breaks equilibrium
        graph = SystemGraph()

        # Use same number of nodes
        num_nodes = len(base_graph.nodes)
        for i in range(num_nodes):
            graph.add_node(f'node_{i}', {'value': np.random.random()})

        # Create a different topology that might have similar spectrum
        # Use a regular lattice or different connectivity pattern
        for i in range(num_nodes):
            # Connect to 2-4 neighbors in a ring-like fashion
            for j in range(2, min(5, num_nodes)):
                neighbor = (i + j) % num_nodes
                if i != neighbor:
                    graph.add_edge(f'node_{i}', f'node_{neighbor}',
                                 {'weight': np.random.random()})

        # Add some random edges to match connectivity
        target_edges = len(base_graph.edges)
        current_edges = len(graph.edges)

        while current_edges < target_edges:
            src = f'node_{random.randint(0, num_nodes-1)}'
            dst = f'node_{random.randint(0, num_nodes-1)}'
            if src != dst and not graph.has_edge(src, dst):
                graph.add_edge(src, dst, {'weight': np.random.random()})
                current_edges += 1

        return {
            'id': system_id,
            'type': 'adversarial_spectral_match',
            'graph_data': self._graph_to_dict(graph),
            'ground_truth': None,
            'expected_pattern': False,
            'description': 'Adversarial: spectrally similar to extraction system but no equilibrium dynamics',
            'adversarial_type': 'spectral_match'
        }

    def generate_adversarial_domain_equilibrium_mismatch(self, system_id: str) -> Dict[str, Any]:
        """Generate adversarial domain: extraction-like equilibrium but wrong spectral properties"""
        graph = SystemGraph()

        # Create nodes with extraction-like value distribution
        num_nodes = random.randint(18, 22)
        for i in range(num_nodes):
            # Create extraction-like gradient: high values at "extraction points", low elsewhere
            if i < 3:  # Extraction nodes
                value = np.random.uniform(0.8, 1.0)
            elif i < 8:  # Intermediate nodes
                value = np.random.uniform(0.4, 0.7)
            else:  # Base nodes
                value = np.random.uniform(0.0, 0.3)
            graph.add_node(f'node_{i}', {'value': value})

        # Create topology that breaks spectral properties
        # Use a star topology or other non-extraction-like structure
        center_node = 'node_0'
        for i in range(1, num_nodes):
            graph.add_edge(center_node, f'node_{i}', {'weight': np.random.random()})

        # Add some peripheral connections to create different spectral properties
        for i in range(1, num_nodes - 1):
            if random.random() < 0.3:
                graph.add_edge(f'node_{i}', f'node_{i+1}', {'weight': np.random.random()})

        return {
            'id': system_id,
            'type': 'adversarial_equilibrium_mismatch',
            'graph_data': self._graph_to_dict(graph),
            'ground_truth': None,
            'expected_pattern': False,
            'description': 'Adversarial: extraction-like equilibrium values but star topology breaks spectral invariants',
            'adversarial_type': 'equilibrium_mismatch'
        }

    def generate_adversarial_domain_shield_bypass(self, system_id: str) -> Dict[str, Any]:
        """Generate adversarial domain: bypasses shield mechanisms"""
        # Start with extraction system
        graph = create_example_extraction_system()

        # Modify to create shield bypass
        # Add a "backdoor" path that circumvents regulation
        nodes = list(graph.nodes())
        if len(nodes) > 5:
            # Add high-capacity bypass edges
            for i in range(3):
                src_idx = random.randint(0, len(nodes)//2)
                dst_idx = random.randint(len(nodes)//2, len(nodes)-1)
                src = nodes[src_idx]
                dst = nodes[dst_idx]

                # Add high-weight bypass edge
                graph.add_edge(src, dst, {'weight': np.random.uniform(0.8, 1.0), 'bypass': True})

        return {
            'id': system_id,
            'type': 'adversarial_shield_bypass',
            'graph_data': self._graph_to_dict(graph),
            'ground_truth': 'extraction_system',  # Technically still extraction but bypasses shields
            'expected_pattern': True,  # Still counts as positive for basic detection
            'description': 'Adversarial: extraction system with shield-bypassing backdoor paths',
            'adversarial_type': 'shield_bypass'
        }

    def _add_realistic_noise(self, graph: SystemGraph):
        """Add realistic noise to make domains more challenging"""
        # Add small random perturbations to node values
        for node in graph.nodes():
            current_value = graph.nodes[node]['value']
            noise = np.random.normal(0, 0.05)  # Small noise
            new_value = np.clip(current_value + noise, 0.0, 1.0)
            graph.nodes[node]['value'] = new_value

        # Add/remove small number of edges
        nodes = list(graph.nodes())
        current_edges = len(graph.edges)

        # Remove some edges (up to 10%)
        edges_to_remove = min(2, current_edges // 10)
        edges_list = list(graph.edges())
        for _ in range(edges_to_remove):
            if edges_list:
                edge = random.choice(edges_list)
                graph.remove_edge(edge[0], edge[1])
                edges_list.remove(edge)

        # Add some edges (up to 5%)
        target_add = min(3, current_edges // 20)
        for _ in range(target_add):
            src = random.choice(nodes)
            dst = random.choice(nodes)
            if src != dst and not graph.has_edge(src, dst):
                graph.add_edge(src, dst, {'weight': np.random.random()})

    def _graph_to_dict(self, graph: SystemGraph) -> Dict[str, Any]:
        """Convert SystemGraph to serializable dict"""
        return {
            'nodes': dict(graph.nodes(data=True)),
            'edges': [{'source': u, 'target': v, 'data': d}
                     for u, v, d in graph.edges(data=True)]
        }

    def generate_domains(self, count: int, adversarial: int = 0, mismatch_equilibrium: bool = False) -> List[Dict[str, Any]]:
        """Generate the complete set of test domains"""
        domains = []

        # Calculate distribution
        if adversarial > 0:
            standard_count = count - adversarial
            adversarial_per_type = adversarial // 3  # Split across adversarial types
            spectral_match = adversarial_per_type
            equilibrium_mismatch = adversarial_per_type
            shield_bypass = adversarial - 2 * adversarial_per_type  # Remainder
        else:
            standard_count = count
            spectral_match = equilibrium_mismatch = shield_bypass = 0

        # Generate standard extraction systems
        extraction_count = standard_count // 2
        for i in range(extraction_count):
            domains.append(self.generate_extraction_system(f'extraction_{i}'))

        # Generate noise domains
        noise_count = standard_count - extraction_count
        for i in range(noise_count):
            domains.append(self.generate_noise_domain(f'noise_{i}'))

        # Generate adversarial domains
        for i in range(spectral_match):
            domains.append(self.generate_adversarial_domain_spectral_match(f'adversarial_spectral_{i}'))

        if mismatch_equilibrium:
            for i in range(equilibrium_mismatch):
                domains.append(self.generate_adversarial_domain_equilibrium_mismatch(f'adversarial_equilibrium_{i}'))

        for i in range(shield_bypass):
            domains.append(self.generate_adversarial_domain_shield_bypass(f'adversarial_shield_{i}'))

        # Shuffle to avoid ordering bias
        random.shuffle(domains)

        logger.info(f"Generated {len(domains)} domains: "
                   f"{extraction_count} extraction, {noise_count} noise, "
                   f"{spectral_match} spectral adversarial, "
                   f"{equilibrium_mismatch} equilibrium adversarial, "
                   f"{shield_bypass} shield adversarial")

        return domains


def main():
    parser = argparse.ArgumentParser(description='Generate ARC test domains')
    parser.add_argument('--count', type=int, default=100, help='Total number of domains to generate')
    parser.add_argument('--adversarial', type=int, default=0, help='Number of adversarial domains to include')
    parser.add_argument('--mismatch-equilibrium', action='store_true', help='Include equilibrium mismatch adversarial domains')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')
    parser.add_argument('--output', type=str, required=True, help='Output file path')

    args = parser.parse_args()

    # Generate domains
    generator = ARCTestDomainGenerator(seed=args.seed)
    domains = generator.generate_domains(
        count=args.count,
        adversarial=args.adversarial,
        mismatch_equilibrium=args.mismatch_equilibrium
    )

    # Save to file
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(domains, f, indent=2)

    logger.info(f"Saved {len(domains)} domains to {output_path}")


if __name__ == '__main__':
    main()