#!/usr/bin/env python3
"""
Extract Temporal Variance Data Pipeline for Phase 7.0

Pulls belief variance data from sealed Phase 6.0 archives and converts to
temporal resonance datasets. Read-only extraction with cryptographic verification.

Usage:
    python ops/tasks/extract_temporal_variance.py [--output OUTPUT.jsonl] [--verify-only]
"""

import argparse
import json
import tarfile
import hashlib
import os
from datetime import datetime
from typing import List, Tuple, Dict, Any
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from nova.slots.slot04_tri.core.temporal_schema import TemporalBeliefEntry
from nova.slots.slot04_tri.core.variance_decay import VarianceDecayModel


class TemporalVarianceExtractor:
    """
    Extracts and processes temporal variance data from sealed archives.

    Ensures read-only access to Phase 6.0 belief propagation archives
    with cryptographic integrity verification.
    """

    def __init__(self, archive_path: str, sha256_path: str):
        """
        Initialize extractor with archive paths.

        Args:
            archive_path: Path to Phase 6.0 sealed archive (.tar.gz)
            sha256_path: Path to SHA-256 verification file
        """
        self.archive_path = Path(archive_path)
        self.sha256_path = Path(sha256_path)
        self.decay_model = VarianceDecayModel()

    def verify_archive_integrity(self) -> bool:
        """
        Verify cryptographic integrity of sealed archive.

        Returns:
            True if archive hash matches expected value
        """
        if not self.sha256_path.exists():
            print(f"ERROR: SHA-256 file not found: {self.sha256_path}")
            return False

        # Read expected hash
        with open(self.sha256_path, 'r') as f:
            expected_hash = f.read().strip().split()[0]

        # Compute actual hash
        sha256 = hashlib.sha256()
        with open(self.archive_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)

        actual_hash = sha256.hexdigest()

        if actual_hash != expected_hash:
            print(f"ERROR: Archive hash mismatch!")
            print(f"Expected: {expected_hash}")
            print(f"Actual:   {actual_hash}")
            return False

        print(f"✓ Archive integrity verified: {actual_hash}")
        return True

    def extract_belief_states(self) -> List[Tuple[datetime, float, float, str]]:
        """
        Extract belief states from sealed archive.

        Returns:
            List of (timestamp, mean, variance, slot_id) tuples
        """
        belief_states = []

        try:
            with tarfile.open(self.archive_path, 'r:gz') as tar:
                # Look for belief data files (assuming JSONL format from Phase 6.0)
                for member in tar.getmembers():
                    if member.name.endswith('.jsonl') and 'belief' in member.name.lower():
                        print(f"Extracting belief data from: {member.name}")

                        # Extract file content
                        file_obj = tar.extractfile(member)
                        if file_obj:
                            content = file_obj.read().decode('utf-8')
                            lines = content.strip().split('\n')

                            for line_num, line in enumerate(lines, 1):
                                try:
                                    record = json.loads(line.strip())

                                    # Extract belief state fields (adapt based on Phase 6.0 schema)
                                    timestamp_str = record.get('timestamp')
                                    if not timestamp_str:
                                        continue

                                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                                    belief_mean = record.get('belief_mean', 0.5)
                                    belief_variance = record.get('belief_variance', 0.1)
                                    slot_id = record.get('slot_id', 'unknown')

                                    belief_states.append((timestamp, belief_mean, belief_variance, slot_id))

                                except (json.JSONDecodeError, KeyError, ValueError) as e:
                                    print(f"Warning: Skipping malformed record in {member.name}:{line_num} - {e}")
                                    continue

        except (tarfile.TarError, OSError) as e:
            print(f"ERROR: Failed to extract archive: {e}")
            return []

        print(f"✓ Extracted {len(belief_states)} belief states from archive")
        return belief_states

    def create_temporal_dataset(self,
                               belief_states: List[Tuple[datetime, float, float, str]],
                               reference_time: datetime,
                               phase_commit: str = "c3bab48") -> List[Dict[str, Any]]:
        """
        Create temporal resonance dataset from belief states.

        Args:
            belief_states: Raw belief state data
            reference_time: Reference point for temporal distance calculation
            phase_commit: Phase 6.0 commit hash for provenance

        Returns:
            List of temporal belief entries as dictionaries
        """
        temporal_entries = self.decay_model.create_temporal_entries(
            [(ts, mean, var) for ts, mean, var, _ in belief_states],
            reference_time,
            "slot04",  # Primary source slot
            phase_commit
        )

        # Convert to dictionary format for JSONL output
        dataset = []
        for entry, (_, _, _, slot_id) in zip(temporal_entries, belief_states):
            entry_dict = {
                'timestamp': entry.timestamp.isoformat(),
                'belief_mean': entry.belief_mean,
                'belief_variance': entry.belief_variance,
                'temporal_distance': entry.temporal_distance,
                'decay_weight': entry.decay_weight,
                'resonance_coefficient': entry.resonance_coefficient,
                'slot_id': slot_id,
                'phase_commit': entry.phase_commit,
                'extraction_timestamp': datetime.utcnow().isoformat()
            }
            dataset.append(entry_dict)

        print(f"✓ Created temporal dataset with {len(dataset)} entries")
        return dataset

    def save_dataset(self, dataset: List[Dict[str, Any]], output_path: str):
        """
        Save temporal dataset to JSONL file.

        Args:
            dataset: Temporal belief entries
            output_path: Output file path
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            for entry in dataset:
                json.dump(entry, f)
                f.write('\n')

        print(f"✓ Saved temporal dataset to: {output_file}")
        print(f"  File size: {output_file.stat().st_size} bytes")
        print(f"  Entry count: {len(dataset)}")


def main():
    """Main extraction pipeline."""
    parser = argparse.ArgumentParser(description="Extract temporal variance data from Phase 6.0 archives")
    parser.add_argument('--archive', default='attest/archives/Nova_Phase_6.0_Seal.tar.gz',
                       help='Path to Phase 6.0 sealed archive')
    parser.add_argument('--sha256', default='attest/archives/phase-6.0-archive.sha256',
                       help='Path to SHA-256 verification file')
    parser.add_argument('--output', default='ops/data/temporal_variance_dataset.jsonl',
                       help='Output path for temporal dataset')
    parser.add_argument('--reference-time', default=None,
                       help='Reference time for temporal distance (ISO format, default: now)')
    parser.add_argument('--verify-only', action='store_true',
                       help='Only verify archive integrity, do not extract')

    args = parser.parse_args()

    # Set reference time
    if args.reference_time:
        reference_time = datetime.fromisoformat(args.reference_time.replace('Z', '+00:00'))
    else:
        reference_time = datetime.utcnow()

    print("🌅 Phase 7.0 Temporal Variance Extraction Pipeline")
    print(f"Archive: {args.archive}")
    print(f"SHA-256: {args.sha256}")
    print(f"Reference Time: {reference_time.isoformat()}")
    print()

    # Initialize extractor
    extractor = TemporalVarianceExtractor(args.archive, args.sha256)

    # Verify archive integrity
    if not extractor.verify_archive_integrity():
        print("❌ Archive integrity check failed!")
        return 1

    if args.verify_only:
        print("✓ Verification complete (verify-only mode)")
        return 0

    # Extract belief states
    belief_states = extractor.extract_belief_states()
    if not belief_states:
        print("❌ No belief states extracted!")
        return 1

    # Create temporal dataset
    dataset = extractor.create_temporal_dataset(belief_states, reference_time)

    # Save dataset
    extractor.save_dataset(dataset, args.output)

    print()
    print("✅ Temporal variance extraction complete!")
    print(f"Dataset saved to: {args.output}")
    print(f"Ready for Phase 7.0 temporal resonance analysis.")

    return 0


if __name__ == '__main__':
    sys.exit(main())