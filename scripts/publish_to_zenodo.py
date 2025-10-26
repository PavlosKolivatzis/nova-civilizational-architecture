#!/usr/bin/env python3
"""
Nova Zenodo Publication Script
Phase 11B: Automated Zenodo deposition for reproducible research

Creates a minimal reproducibility kit and deposits to Zenodo with proper metadata.
Requires ZENODO_TOKEN environment variable for API access.

Usage:
    export ZENODO_TOKEN=your_sandbox_token_here
    python scripts/publish_to_zenodo.py --sandbox  # Test with sandbox first
    python scripts/publish_to_zenodo.py            # Production deposition
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, Any, Optional
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ZenodoPublisher:
    """Handles Zenodo deposition for Nova reproducibility packages"""

    def __init__(self, sandbox: bool = False):
        self.sandbox = sandbox
        self.base_url = "https://sandbox.zenodo.org/api" if sandbox else "https://zenodo.org/api"
        self.token = os.getenv("ZENODO_TOKEN")

        if not self.token:
            raise ValueError("ZENODO_TOKEN environment variable required")

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        })

    def create_deposition(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new deposition"""
        url = f"{self.base_url}/deposit/depositions"
        response = self.session.post(url, json={"metadata": metadata})

        if response.status_code != 201:
            raise RuntimeError(f"Failed to create deposition: {response.text}")

        deposition = response.json()
        logger.info(f"Created deposition: {deposition['id']}")
        return deposition

    def upload_file(self, deposition_id: str, file_path: Path, filename: str) -> Dict[str, Any]:
        """Upload a file to an existing deposition"""
        bucket_url = f"{self.base_url}/deposit/depositions/{deposition_id}"

        # Get bucket URL
        response = self.session.get(bucket_url)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to get deposition: {response.text}")

        bucket_url = response.json()["links"]["bucket"]

        # Upload file
        with open(file_path, 'rb') as f:
            response = self.session.put(
                f"{bucket_url}/{filename}",
                data=f,
                headers={"Content-Type": "application/octet-stream"}
            )

        if response.status_code not in [200, 201]:
            raise RuntimeError(f"Failed to upload file: {response.text}")

        logger.info(f"Uploaded {filename}")
        return response.json()

    def publish_deposition(self, deposition_id: str) -> Dict[str, Any]:
        """Publish the deposition"""
        url = f"{self.base_url}/deposit/depositions/{deposition_id}/actions/publish"
        response = self.session.post(url)

        if response.status_code != 202:
            raise RuntimeError(f"Failed to publish deposition: {response.text}")

        deposition = response.json()
        logger.info(f"Published deposition: {deposition['doi']}")
        return deposition

    def create_reproducibility_kit(self, output_path: Path) -> Path:
        """Create a minimal reproducibility kit"""
        kit_dir = Path(tempfile.mkdtemp()) / "nova_reproducibility_kit"
        kit_dir.mkdir(parents=True)

        # Copy essential files
        repo_root = Path(__file__).parent.parent

        files_to_copy = [
            "Makefile",
            "requirements.txt",
            "CITATION.cff",
            "schemas/arc_results.schema.json",
            "scripts/generate_arc_test_domains.py",
            "scripts/verify_vault.py",
            "src/nova/arc/run_calibration_cycle.py",
            "src/nova/arc/analyze_results.py",
            "src/nova/math/relations_pattern.py",
            "docs/papers/universal_structure_mathematics_arxiv.md",
            "docs/plans/phase-11b-arc-calibration-experiment.md",
            "docs/reports/phase11_commit_reflection.md"
        ]

        for file_path in files_to_copy:
            src = repo_root / file_path
            if src.exists():
                dst = kit_dir / file_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

        # Create README for the kit
        readme_content = f"""# Nova Civilizational Architecture - Reproducibility Kit
Version: v11.1-pre
Date: {datetime.now().isoformat()}

## Quick Start

1. Install dependencies:
   pip install -r requirements.txt

2. Run the complete ARC calibration experiment:
   make reproduce-arc-experiment

3. Run ablation studies:
   make arc-ablation

4. Verify vault integrity:
   python scripts/verify_vault.py

## Contents

- Makefile: Complete experiment orchestration
- schemas/: JSON schema validation for results
- scripts/: Core experimental scripts
- src/nova/: Mathematical foundations and ARC implementation
- docs/: Complete documentation and experimental protocols

## Expected Results

After successful execution, you should observe:
- Precision >= 0.90 across 80% of calibration cycles
- Recall >= 0.90 across 80% of calibration cycles
- Drift <= 0.20 across 90% of calibration cycles
- Statistically significant improvement trends (p < 0.01)

## Citation

See CITATION.cff for proper attribution to the Nova Team.

## License

Apache-2.0
"""

        (kit_dir / "README.md").write_text(readme_content)

        # Create zip archive
        zip_path = output_path / "nova_reproducibility_kit.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in kit_dir.rglob('*'):
                if file_path.is_file():
                    zf.write(file_path, file_path.relative_to(kit_dir))

        # Cleanup
        shutil.rmtree(kit_dir.parent)

        logger.info(f"Created reproducibility kit: {zip_path}")
        return zip_path

    def publish_reproducibility_kit(self) -> str:
        """Complete publication workflow"""
        # Load metadata
        metadata_path = Path(__file__).parent.parent / "zenodo-metadata.json"
        with open(metadata_path) as f:
            metadata = json.load(f)["metadata"]

        # Create reproducibility kit
        kit_path = self.create_reproducibility_kit(Path("."))

        # Create deposition
        deposition = self.create_deposition(metadata)

        # Upload kit
        self.upload_file(deposition["id"], kit_path, "nova_reproducibility_kit.zip")

        # Publish
        published = self.publish_deposition(deposition["id"])

        # Cleanup
        kit_path.unlink()

        doi = published["doi"]
        logger.info(f"Successfully published to Zenodo: {doi}")

        return doi


def main():
    parser = argparse.ArgumentParser(description='Publish Nova reproducibility kit to Zenodo')
    parser.add_argument('--sandbox', action='store_true', help='Use Zenodo sandbox for testing')

    args = parser.parse_args()

    publisher = ZenodoPublisher(sandbox=args.sandbox)
    doi = publisher.publish_reproducibility_kit()

    print(f"🎉 Published to {'sandbox ' if args.sandbox else ''}Zenodo: {doi}")
    print(f"📋 DOI Badge: [![DOI](https://zenodo.org/badge/DOI/{doi}.svg)](https://doi.org/{doi})")


if __name__ == '__main__':
    main()