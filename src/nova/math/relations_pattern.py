"""
Nova Civilizational Architecture - Relations Pattern Analysis
Phase 11: Universal Structure Detection

This module implements mathematical analysis of systemic patterns across domains,
detecting structural convergence in extraction architectures.

Core Concepts:
- Graph-based representation of actor relations
- Spectral analysis for structural invariants
- Harm propagation modeling
- Cross-domain similarity metrics
"""

from __future__ import annotations

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import networkx as nx
from scipy.sparse.linalg import eigsh
from scipy.spatial.distance import cosine


class RelationType(Enum):
    """Types of relations in systemic analysis"""
    EXTRACTIVE = "extractive"      # Profit/extraction flows
    PROTECTIVE = "protective"      # Safety/accountability flows
    DISTORTIVE = "distortive"      # Information manipulation
    EMPATHIC = "empathic"         # Care/response flows


@dataclass
class RelationTensor:
    """Tensor representation of relations between actors"""
    profit_weight: float = 0.0      # w^(p): extraction/profit
    harm_weight: float = 0.0        # w^(h): harm potential
    info_weight: float = 0.0        # w^(i): information distortion
    empathy_weight: float = 0.0     # w^(e): empathic response

    def to_vector(self) -> np.ndarray:
        """Convert to numpy vector for computation"""
        return np.array([self.profit_weight, self.harm_weight,
                        self.info_weight, self.empathy_weight])

    def extraction_gradient(self) -> float:
        """Compute extraction gradient: profit - empathy"""
        return self.profit_weight - self.empathy_weight


@dataclass
class SystemGraph:
    """Graph representation of a systemic domain"""
    actors: List[str]                    # V: set of actors/entities
    relations: Dict[Tuple[str, str], RelationTensor]  # E: directed relations
    metadata: Dict[str, Any] = None      # Domain-specific metadata

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_networkx(self) -> nx.DiGraph:
        """Convert to NetworkX graph for analysis"""
        G = nx.DiGraph()

        # Add nodes
        for actor in self.actors:
            G.add_node(actor)

        # Add edges with relation data
        for (source, target), tensor in self.relations.items():
            G.add_edge(source, target,
                      profit=tensor.profit_weight,
                      harm=tensor.harm_weight,
                      info=tensor.info_weight,
                      empathy=tensor.empathy_weight,
                      extraction_gradient=tensor.extraction_gradient())

        return G

    def adjacency_matrix(self) -> np.ndarray:
        """Compute adjacency matrix from relations"""
        n = len(self.actors)
        actor_idx = {actor: i for i, actor in enumerate(self.actors)}

        A = np.zeros((n, n))

        for (source, target), tensor in self.relations.items():
            i, j = actor_idx[source], actor_idx[target]
            # Weight by total relation strength
            weight = np.sum(tensor.to_vector())
            A[i, j] = weight

        return A

    def relation_tensor_matrix(self) -> np.ndarray:
        """Create 3D tensor matrix: actors x actors x relation_types"""
        n = len(self.actors)
        actor_idx = {actor: i for i, actor in enumerate(self.actors)}

        # 4 relation types: profit, harm, info, empathy
        R = np.zeros((n, n, 4))

        for (source, target), tensor in self.relations.items():
            i, j = actor_idx[source], actor_idx[target]
            R[i, j, :] = tensor.to_vector()

        return R


class StructuralAnalyzer:
    """Mathematical analysis of systemic structures"""

    @staticmethod
    def normalized_laplacian_spectrum(G: SystemGraph, k: int = 10) -> np.ndarray:
        """
        Compute normalized Laplacian spectrum for structural fingerprint

        Args:
            G: System graph to analyze
            k: Number of eigenvalues to compute

        Returns:
            Array of k smallest eigenvalues (structural signature)
        """
        A = G.adjacency_matrix()
        n = A.shape[0]

        if n == 0:
            return np.array([])

        # Degree matrix
        degrees = np.sum(A, axis=1)

        # Handle isolated nodes
        nonzero_degrees = degrees > 0
        if not np.any(nonzero_degrees):
            return np.zeros(k)

        # Normalized Laplacian: L_norm = D^(-1/2) * (D - A) * D^(-1/2)
        D_sqrt_inv = np.diag(1.0 / np.sqrt(degrees[nonzero_degrees]))

        # Extract connected subgraph
        A_connected = A[np.ix_(nonzero_degrees, nonzero_degrees)]
        L_connected = D_sqrt_inv @ (np.diag(np.sum(A_connected, axis=1)) - A_connected) @ D_sqrt_inv

        # Compute eigenvalues
        try:
            eigenvals = eigsh(L_connected, k=min(k, L_connected.shape[0]-1),
                            which='SM', return_eigenvectors=False)
            # Pad with zeros if needed
            if len(eigenvals) < k:
                eigenvals = np.pad(eigenvals, (0, k - len(eigenvals)), 'constant')
        except Exception:
            # Fallback for small or problematic matrices
            eigenvals = np.zeros(k)

        return np.sort(eigenvals)

    @staticmethod
    def harm_propagation_model(G: SystemGraph,
                              initial_harm: np.ndarray,
                              alpha: float = 0.8,
                              steps: int = 50) -> np.ndarray:
        """
        Model harm propagation through the system

        Args:
            G: System graph
            initial_harm: Initial harm state vector
            alpha: Propagation factor (0-1)
            steps: Number of time steps to simulate

        Returns:
            Harm state at each time step
        """
        A = G.adjacency_matrix()
        n = A.shape[0]

        if n == 0:
            return np.array([])

        # Normalize adjacency matrix
        degrees = np.sum(A, axis=1)
        degrees = np.where(degrees == 0, 1, degrees)  # Avoid division by zero
        A_norm = A / degrees[:, np.newaxis]

        # Initialize harm state
        H = initial_harm.copy()
        if len(H) != n:
            H = np.zeros(n)  # Default to no initial harm

        harm_history = [H.copy()]

        # Simulate propagation
        for _ in range(steps):
            # H(t+1) = alpha * A_norm * H(t) + (1-alpha) * baseline_vulnerability
            # For simplicity, assume uniform baseline vulnerability
            baseline = np.ones(n) * 0.1
            H_new = alpha * A_norm @ H + (1 - alpha) * baseline
            H = H_new
            harm_history.append(H.copy())

        return np.array(harm_history)

    @staticmethod
    def extraction_equilibrium_check(G: SystemGraph) -> Dict[str, float]:
        """
        Check if system is in extraction equilibrium

        Returns dict with equilibrium metrics:
        - total_extraction_gradient: sum of all extraction gradients
        - max_local_gradient: maximum local extraction gradient
        - equilibrium_ratio: ratio of protective to extractive forces
        """
        total_gradient = 0.0
        max_gradient = 0.0
        total_protective = 0.0
        total_extractive = 0.0

        for tensor in G.relations.values():
            gradient = tensor.extraction_gradient()
            total_gradient += gradient
            max_gradient = max(max_gradient, abs(gradient))

            total_extractive += tensor.profit_weight + tensor.harm_weight
            total_protective += tensor.empathy_weight

        equilibrium_ratio = total_protective / max(total_extractive, 1e-6)

        return {
            'total_extraction_gradient': total_gradient,
            'max_local_gradient': max_gradient,
            'equilibrium_ratio': equilibrium_ratio,
            'in_equilibrium': abs(total_gradient) < 0.1  # Threshold for equilibrium
        }

    @staticmethod
    def structural_similarity(G1: SystemGraph, G2: SystemGraph) -> float:
        """
        Compute structural similarity between two systems

        Args:
            G1, G2: System graphs to compare

        Returns:
            Similarity score (0-1, where 1 is identical structure)
        """
        # Compare spectral signatures
        spectrum1 = StructuralAnalyzer.normalized_laplacian_spectrum(G1)
        spectrum2 = StructuralAnalyzer.normalized_laplacian_spectrum(G2)

        if len(spectrum1) == 0 or len(spectrum2) == 0:
            return 0.0

        # Cosine similarity of spectra
        similarity = 1 - cosine(spectrum1, spectrum2)

        # Also compare equilibrium states
        eq1 = StructuralAnalyzer.extraction_equilibrium_check(G1)
        eq2 = StructuralAnalyzer.extraction_equilibrium_check(G2)

        equilibrium_similarity = 1.0 if eq1['in_equilibrium'] == eq2['in_equilibrium'] else 0.0

        # Weighted combination
        return 0.7 * similarity + 0.3 * equilibrium_similarity


class UniversalStructureDetector:
    """High-level detector for universal systemic patterns"""

    def __init__(self):
        self.known_patterns = {}  # Pattern name -> reference graph

    def register_pattern(self, name: str, reference_graph: SystemGraph):
        """Register a known systemic pattern"""
        self.known_patterns[name] = reference_graph

    def detect_pattern(self, target_graph: SystemGraph,
                      threshold: float = 0.85) -> Optional[str]:
        """
        Detect which known pattern the target graph matches

        Args:
            target_graph: Graph to analyze
            threshold: Similarity threshold for match

        Returns:
            Pattern name if match found, None otherwise
        """
        best_match = None
        best_similarity = 0.0

        for pattern_name, reference_graph in self.known_patterns.items():
            similarity = StructuralAnalyzer.structural_similarity(
                target_graph, reference_graph)

            if similarity > threshold and similarity > best_similarity:
                best_match = pattern_name
                best_similarity = similarity

        return best_match

    def analyze_domain(self, domain_graph: SystemGraph) -> Dict[str, Any]:
        """
        Complete analysis of a domain for universal structure detection

        Returns comprehensive analysis including:
        - Spectral signature
        - Harm propagation equilibrium
        - Extraction equilibrium status
        - Pattern matches
        """
        spectrum = StructuralAnalyzer.normalized_laplacian_spectrum(domain_graph)
        equilibrium = StructuralAnalyzer.extraction_equilibrium_check(domain_graph)

        # Simulate harm propagation with random initial conditions
        n_actors = len(domain_graph.actors)
        initial_harm = np.random.random(n_actors) * 0.1
        harm_trajectory = StructuralAnalyzer.harm_propagation_model(
            domain_graph, initial_harm)

        # Detect known patterns
        detected_pattern = self.detect_pattern(domain_graph)

        return {
            'spectral_signature': spectrum.tolist(),
            'extraction_equilibrium': equilibrium,
            'harm_trajectory_final': harm_trajectory[-1].tolist() if len(harm_trajectory) > 0 else [],
            'detected_pattern': detected_pattern,
            'is_extraction_system': equilibrium['equilibrium_ratio'] < 0.5,
            'analysis_timestamp': np.datetime64('now').astype(str)
        }


# Example usage and test data
def create_example_extraction_system() -> SystemGraph:
    """Create example extraction system graph (e.g., corporate harm pattern)"""
    actors = ['Corporation', 'Workers', 'Customers', 'Regulators', 'Victims']

    relations = {
        # Corporation extracts from workers
        ('Corporation', 'Workers'): RelationTensor(
            profit_weight=0.9, harm_weight=0.3, info_weight=0.2, empathy_weight=0.1
        ),
        # Corporation extracts from customers
        ('Corporation', 'Customers'): RelationTensor(
            profit_weight=0.8, harm_weight=0.4, info_weight=0.3, empathy_weight=0.1
        ),
        # Workers suffer harm
        ('Workers', 'Victims'): RelationTensor(
            profit_weight=0.0, harm_weight=0.6, info_weight=0.1, empathy_weight=0.2
        ),
        # Regulators are weak/influenced
        ('Corporation', 'Regulators'): RelationTensor(
            profit_weight=0.7, harm_weight=0.1, info_weight=0.5, empathy_weight=0.1
        ),
        # System protects itself
        ('Regulators', 'Corporation'): RelationTensor(
            profit_weight=0.0, harm_weight=0.0, info_weight=0.0, empathy_weight=0.8
        )
    }

    return SystemGraph(actors=actors, relations=relations,
                      metadata={'domain': 'corporate_extraction', 'example': True})


if __name__ == "__main__":
    # Example analysis
    detector = UniversalStructureDetector()

    # Register known extraction pattern
    extraction_pattern = create_example_extraction_system()
    detector.register_pattern('extraction_system', extraction_pattern)

    # Analyze the same system (should match itself)
    analysis = detector.analyze_domain(extraction_pattern)

    print("Universal Structure Analysis Results:")
    print(f"Detected Pattern: {analysis['detected_pattern']}")
    print(f"Is Extraction System: {analysis['is_extraction_system']}")
    print(f"Equilibrium Ratio: {analysis['extraction_equilibrium']['equilibrium_ratio']:.3f}")
    print(f"Spectral Signature (first 5): {analysis['spectral_signature'][:5]}")
