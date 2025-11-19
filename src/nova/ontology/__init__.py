"""
Nova Framework Ontology - Runtime contracts and validation.

Provides:
- Ontology loading and parsing
- Contract compliance validation
- Runtime enforcement (impl_ref verification)
"""

from .loader import OntologyLoader
from .validator import OntologyValidator

__all__ = ["OntologyLoader", "OntologyValidator"]
