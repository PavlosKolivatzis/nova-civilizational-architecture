"""
Nova Simulation Interface (NSI) - Phase 11.0-gold
Publication & Audit Tools for Agent Simulations

Implements cryptographic audit trails and publication validation.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json
import time
from pathlib import Path


@dataclass
class AuditEntry:
    """Cryptographic audit entry for simulation publication"""

    entry_id: str
    simulation_id: str
    entry_type: str  # "creation", "publication", "validation", "retraction"
    content_hash: str
    metadata: Dict[str, Any]
    previous_hash: Optional[str]
    timestamp: float = field(default_factory=time.time)
    signature: Optional[str] = None

    def calculate_hash(self) -> str:
        """Calculate SHA-256 hash of this entry"""
        data = {
            'entry_id': self.entry_id,
            'simulation_id': self.simulation_id,
            'entry_type': self.entry_type,
            'content_hash': self.content_hash,
            'metadata': self.metadata,
            'previous_hash': self.previous_hash,
            'timestamp': self.timestamp
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'entry_id': self.entry_id,
            'simulation_id': self.simulation_id,
            'entry_type': self.entry_type,
            'content_hash': self.content_hash,
            'metadata': self.metadata,
            'previous_hash': self.previous_hash,
            'timestamp': self.timestamp,
            'signature': self.signature,
            'calculated_hash': self.calculate_hash()
        }


@dataclass
class PublicationRecord:
    """Publication record with audit trail"""

    publication_id: str
    simulation_results: Dict[str, Any]
    methodology: Dict[str, Any]
    validation_results: Dict[str, Any]
    audit_chain: List[AuditEntry] = field(default_factory=list)
    published_at: Optional[float] = None
    retracted_at: Optional[float] = None
    status: str = "draft"  # draft, published, retracted

    def add_audit_entry(self, entry_type: str, content_hash: str,
                       metadata: Dict[str, Any]) -> AuditEntry:
        """Add entry to audit chain"""

        previous_hash = None
        if self.audit_chain:
            previous_hash = self.audit_chain[-1].calculate_hash()

        entry = AuditEntry(
            entry_id=f"{self.publication_id}_{len(self.audit_chain)}",
            simulation_id=self.simulation_results.get('simulation_id', 'unknown'),
            entry_type=entry_type,
            content_hash=content_hash,
            metadata=metadata,
            previous_hash=previous_hash
        )

        self.audit_chain.append(entry)
        return entry

    def get_chain_root_hash(self) -> Optional[str]:
        """Get root hash of audit chain"""
        if not self.audit_chain:
            return None
        return self.audit_chain[0].calculate_hash()

    def get_chain_head_hash(self) -> Optional[str]:
        """Get head hash of audit chain"""
        if not self.audit_chain:
            return None
        return self.audit_chain[-1].calculate_hash()

    def validate_chain_integrity(self) -> bool:
        """Validate audit chain integrity"""
        if not self.audit_chain:
            return True

        # Check chain continuity
        for i, entry in enumerate(self.audit_chain[1:], 1):
            expected_previous = self.audit_chain[i-1].calculate_hash()
            if entry.previous_hash != expected_previous:
                return False

        # Check individual entry hashes
        for entry in self.audit_chain:
            if entry.calculate_hash() != entry.content_hash:
                return False

        return True


@dataclass
class PublicationValidator:
    """Validates simulation publications against Nova standards"""

    required_fields = [
        'simulation_id', 'duration_steps', 'final_consensus',
        'avg_polarization', 'final_tri_score', 'cultural_coherence',
        'bias_index', 'fcq_score', 'agent_final_states'
    ]

    quality_thresholds = {
        'min_fcq': 0.70,        # Minimum FCQ for publication
        'max_bias_index': 0.30, # Maximum acceptable bias
        'min_cultural_coherence': 0.60,  # Minimum coherence
        'max_polarization': 0.80  # Maximum polarization
    }

    def validate_publication(self, results: Dict[str, Any],
                           methodology: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate simulation results for publication"""

        errors = []
        warnings = []

        # Check required fields
        for field in self.required_fields:
            if field not in results:
                errors.append(f"Missing required field: {field}")

        if not results:
            return False, ["Empty results provided"]

        # Validate FCQ score
        fcq = results.get('fcq_score', 0.0)
        if fcq < self.quality_thresholds['min_fcq']:
            errors.append(f"FCQ score {fcq:.3f} below minimum {self.quality_thresholds['min_fcq']}")

        # Validate bias index
        bias = results.get('bias_index', 1.0)
        if bias > self.quality_thresholds['max_bias_index']:
            warnings.append(f"High bias index {bias:.3f} - consider agent diversity")

        # Validate cultural coherence
        coherence = results.get('cultural_coherence', 0.0)
        if coherence < self.quality_thresholds['min_cultural_coherence']:
            warnings.append(f"Low cultural coherence {coherence:.3f}")

        # Validate polarization
        polarization = results.get('avg_polarization', 1.0)
        if polarization > self.quality_thresholds['max_polarization']:
            warnings.append(f"High polarization {polarization:.3f} - extreme opinions")

        # Validate methodology
        method_errors = self._validate_methodology(methodology)
        errors.extend(method_errors)

        # Overall assessment
        is_valid = len(errors) == 0

        if is_valid and warnings:
            # Convert warnings to informational notes for valid publications
            pass

        return is_valid, errors + warnings

    def _validate_methodology(self, methodology: Dict[str, Any]) -> List[str]:
        """Validate simulation methodology"""

        errors = []

        required_method_fields = ['consensus_model', 'num_agents', 'max_steps', 'topics']
        for field in required_method_fields:
            if field not in methodology:
                errors.append(f"Missing methodology field: {field}")

        # Validate agent count
        num_agents = methodology.get('num_agents', 0)
        if not (5 <= num_agents <= 50):
            errors.append(f"Agent count {num_agents} outside valid range [5, 50]")

        # Validate consensus model
        valid_models = ['degroot', 'friedkin_johnsen', 'independent_cascade', 'threshold']
        model = methodology.get('consensus_model', '')
        if model not in valid_models:
            errors.append(f"Invalid consensus model: {model}")

        return errors

    def generate_publication_report(self, results: Dict[str, Any],
                                  methodology: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive publication report"""

        is_valid, issues = self.validate_publication(results, methodology)

        return {
            'publication_ready': is_valid,
            'validation_timestamp': time.time(),
            'quality_metrics': {
                'fcq_score': results.get('fcq_score', 0.0),
                'bias_index': results.get('bias_index', 0.0),
                'cultural_coherence': results.get('cultural_coherence', 0.0),
                'avg_polarization': results.get('avg_polarization', 0.0)
            },
            'thresholds_applied': self.quality_thresholds,
            'issues': issues,
            'recommendations': self._generate_recommendations(results, issues)
        }

    def _generate_recommendations(self, results: Dict[str, Any],
                                issues: List[str]) -> List[str]:
        """Generate publication recommendations"""

        recommendations = []

        fcq = results.get('fcq_score', 0.0)
        if fcq < 0.80:
            recommendations.append("Consider increasing agent interaction rounds")
            recommendations.append("Review agent personality diversity")

        bias = results.get('bias_index', 0.0)
        if bias > 0.20:
            recommendations.append("Increase agent personality trait diversity")
            recommendations.append("Balance agent initial beliefs across topics")

        coherence = results.get('cultural_coherence', 0.0)
        if coherence < 0.70:
            recommendations.append("Extend simulation duration for better convergence")
            recommendations.append("Adjust consensus model parameters")

        if not recommendations:
            recommendations.append("Publication quality meets Nova standards")

        return recommendations


class PublicationManager:
    """Manages simulation publications with audit trails"""

    def __init__(self, audit_dir: str = "audit/publications"):
        self.audit_dir = Path(audit_dir)
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.validator = PublicationValidator()
        self.publications: Dict[str, PublicationRecord] = {}

    def create_publication(self, simulation_results: Dict[str, Any],
                          methodology: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Create a new publication with validation"""

        # Validate before creating
        validation_report = self.validator.generate_publication_report(
            simulation_results, methodology
        )

        if not validation_report['publication_ready']:
            return None, {
                'error': 'Validation failed',
                'issues': validation_report['issues']
            }

        # Create publication record
        publication_id = hashlib.sha256(
            f"{simulation_results.get('simulation_id', 'unknown')}:{time.time()}".encode()
        ).hexdigest()[:16]

        publication = PublicationRecord(
            publication_id=publication_id,
            simulation_results=simulation_results,
            methodology=methodology,
            validation_results=validation_report
        )

        # Create initial audit entry
        content_hash = hashlib.sha256(
            json.dumps(simulation_results, sort_keys=True).encode()
        ).hexdigest()

        publication.add_audit_entry(
            entry_type="creation",
            content_hash=content_hash,
            metadata={
                'methodology': methodology,
                'validation_report': validation_report
            }
        )

        self.publications[publication_id] = publication

        return publication_id, {
            'status': 'created',
            'publication_id': publication_id,
            'validation_report': validation_report
        }

    def publish(self, publication_id: str) -> bool:
        """Mark publication as published"""

        if publication_id not in self.publications:
            return False

        publication = self.publications[publication_id]

        # Add publication audit entry
        content_hash = publication.get_chain_head_hash()
        publication.add_audit_entry(
            entry_type="publication",
            content_hash=content_hash or "",
            metadata={'published_at': time.time()}
        )

        publication.status = "published"
        publication.published_at = time.time()

        # Save to audit file
        self._save_publication(publication)

        return True

    def retract(self, publication_id: str, reason: str) -> bool:
        """Retract a publication"""

        if publication_id not in self.publications:
            return False

        publication = self.publications[publication_id]

        # Add retraction audit entry
        content_hash = publication.get_chain_head_hash()
        publication.add_audit_entry(
            entry_type="retraction",
            content_hash=content_hash or "",
            metadata={'reason': reason, 'retracted_at': time.time()}
        )

        publication.status = "retracted"
        publication.retracted_at = time.time()

        # Save updated audit
        self._save_publication(publication)

        return True

    def get_publication(self, publication_id: str) -> Optional[PublicationRecord]:
        """Retrieve publication record"""
        return self.publications.get(publication_id)

    def list_publications(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """List publications with optional status filter"""

        publications = []
        for pub in self.publications.values():
            if status_filter and pub.status != status_filter:
                continue

            publications.append({
                'publication_id': pub.publication_id,
                'status': pub.status,
                'simulation_id': pub.simulation_results.get('simulation_id'),
                'published_at': pub.published_at,
                'fcq_score': pub.simulation_results.get('fcq_score', 0.0),
                'chain_integrity': pub.validate_chain_integrity()
            })

        return publications

    def _save_publication(self, publication: PublicationRecord):
        """Save publication to audit file"""

        audit_file = self.audit_dir / f"{publication.publication_id}.json"

        data = {
            'publication_record': {
                'publication_id': publication.publication_id,
                'simulation_results': publication.simulation_results,
                'methodology': publication.methodology,
                'validation_results': publication.validation_results,
                'published_at': publication.published_at,
                'retracted_at': publication.retracted_at,
                'status': publication.status
            },
            'audit_chain': [entry.to_dict() for entry in publication.audit_chain]
        }

        with open(audit_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)


# Global instance
_publication_manager = PublicationManager()

def get_publication_manager() -> PublicationManager:
    """Get global publication manager"""
    return _publication_manager


# Example usage
def demo_publication_flow():
    """Demonstrate publication workflow"""

    # Sample simulation results
    results = {
        'simulation_id': 'demo_sim_001',
        'duration_steps': 45,
        'final_consensus': {'topic1': False, 'topic2': True},
        'avg_polarization': 0.25,
        'final_tri_score': 0.87,
        'cultural_coherence': 0.82,
        'bias_index': 0.15,
        'fcq_score': 0.88,
        'agent_final_states': {'agent_1': {'beliefs': {'topic1': 0.7}}}
    }

    methodology = {
        'consensus_model': 'friedkin_johnsen',
        'num_agents': 25,
        'max_steps': 50,
        'topics': ['topic1', 'topic2']
    }

    manager = get_publication_manager()

    # Create publication
    pub_id, response = manager.create_publication(results, methodology)

    if pub_id:
        print(f"Publication created: {pub_id}")
        print(f"FCQ Score: {results['fcq_score']}")

        # Publish
        if manager.publish(pub_id):
            print("Publication successfully published")

            # List publications
            pubs = manager.list_publications()
            print(f"Total publications: {len(pubs)}")
    else:
        print(f"Publication failed: {response}")


if __name__ == "__main__":
    demo_publication_flow()