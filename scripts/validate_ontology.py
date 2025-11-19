#!/usr/bin/env python3
"""
Validate Nova Framework Ontology against implementation.

Usage:
    python scripts/validate_ontology.py [--verbose]
"""

import sys
from pathlib import Path

# Add src to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from src.nova.ontology.loader import OntologyLoader
from src.nova.ontology.validator import OntologyValidator


def main():
    verbose = "--verbose" in sys.argv

    print("Loading Nova Framework Ontology...")
    loader = OntologyLoader()
    loader.load()

    print(f"Loaded {len(loader.frameworks)} frameworks")
    print(f"Loaded {len(loader.signals)} signals\n")

    print("Validating contracts against implementation...")
    validator = OntologyValidator(loader)
    passed, failed, skipped = validator.validate_all()

    validator.print_results(show_passed=verbose)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
