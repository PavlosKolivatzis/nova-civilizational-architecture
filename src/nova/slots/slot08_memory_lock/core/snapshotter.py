"""Signed, rolling, crash-safe snapshots for memory integrity."""

import os
import json
import time
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

from .types import SnapshotMeta, SnapshotStatus
from .integrity_store import MerkleIntegrityStore
from .policy import Slot8Policy

logger = logging.getLogger(__name__)


class DevelopmentSigner:
    """Development-only signer for testing. DO NOT USE IN PRODUCTION."""

    def __init__(self, key_id: str = "slot8-dev"):
        self.key_id = key_id

    def pubkey_fpr(self) -> str:
        """Return public key fingerprint."""
        return self.key_id

    def sign(self, data: bytes) -> bytes:
        """Sign data (development implementation)."""
        import hashlib
        # This is NOT cryptographically secure - for development only
        return hashlib.sha256(data + self.key_id.encode()).digest()

    def verify(self, data: bytes, signature: bytes) -> bool:
        """Verify signature (development implementation)."""
        expected = self.sign(data)
        return expected == signature


class IntegritySnapshotter:
    """Cryptographically signed snapshots with crash safety."""

    def __init__(self, store_dir: Path, snapshot_dir: Path,
                 signer=None, policy: Optional[Slot8Policy] = None):
        """Initialize snapshotter with store and snapshot directories."""
        self.store_dir = store_dir
        self.snapshot_dir = snapshot_dir
        self.signer = signer or DevelopmentSigner()
        self.policy = policy or Slot8Policy()
        self.integrity_store = MerkleIntegrityStore()

        # Ensure directories exist
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

        # Performance tracking
        self._snapshot_count = 0
        self._total_snapshot_time = 0.0

    def take_snapshot(self, parent_id: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> SnapshotMeta:
        """Take a cryptographically signed snapshot."""
        start_time = time.time()

        try:
            # Calculate integrity hash
            merkle_root = self.integrity_store.merkle_root_for_dir(self.store_dir)

            # Generate snapshot metadata
            snapshot_id = self._generate_snapshot_id()
            current_time = int(time.time() * 1000)

            # Count files and calculate size
            file_count, content_size = self._calculate_store_metrics()

            # Create snapshot metadata
            meta_dict = {
                "id": snapshot_id,
                "parent_id": parent_id,
                "ts_ms": current_time,
                "merkle_root": merkle_root,
                "signer": self.signer.pubkey_fpr(),
                "content_size": content_size,
                "file_count": file_count,
                "policy_version": "1.0"
            }

            # Add custom metadata if provided
            if metadata:
                meta_dict["custom_metadata"] = metadata

            # Sign the metadata
            metadata_json = json.dumps(meta_dict, sort_keys=True)
            signature = self.signer.sign(metadata_json.encode())
            meta_dict["sig"] = signature.hex()

            # Create SnapshotMeta object
            snapshot_meta = SnapshotMeta(
                id=snapshot_id,
                parent_id=parent_id,
                ts_ms=current_time,
                merkle_root=merkle_root,
                signer=self.signer.pubkey_fpr(),
                sig=signature.hex(),  # Store as hex string
                status=SnapshotStatus.OK,
                content_size=content_size,
                file_count=file_count
            )

            # Write snapshot metadata atomically
            self._write_snapshot_metadata(snapshot_meta, meta_dict)

            # Optionally create store backup
            if self.policy.retention_snapshots > 0:
                self._create_store_backup(snapshot_id)

            # Clean up old snapshots
            self._cleanup_old_snapshots()

            # Update performance metrics
            duration = time.time() - start_time
            self._snapshot_count += 1
            self._total_snapshot_time += duration

            logger.info(f"Snapshot {snapshot_id} created successfully in {duration:.3f}s")
            return snapshot_meta

        except Exception as e:
            logger.error(f"Snapshot creation failed: {e}")
            raise

    def verify_snapshot(self, snapshot_id: str) -> bool:
        """Verify a snapshot's cryptographic signature and integrity."""
        try:
            metadata_file = self.snapshot_dir / f"{snapshot_id}.json"
            if not metadata_file.exists():
                logger.error(f"Snapshot metadata not found: {snapshot_id}")
                return False

            # Load metadata
            metadata_content = metadata_file.read_text()
            metadata = json.loads(metadata_content)

            # Extract signature
            signature_hex = metadata.pop("sig", None)
            if not signature_hex:
                logger.error(f"No signature found in snapshot {snapshot_id}")
                return False

            signature = bytes.fromhex(signature_hex)

            # Verify signature
            metadata_json = json.dumps(metadata, sort_keys=True)
            if not self.signer.verify(metadata_json.encode(), signature):
                logger.error(f"Signature verification failed for snapshot {snapshot_id}")
                return False

            logger.debug(f"Snapshot {snapshot_id} signature verified successfully")
            return True

        except Exception as e:
            logger.error(f"Snapshot verification failed for {snapshot_id}: {e}")
            return False

    def list_snapshots(self, include_invalid: bool = False) -> List[SnapshotMeta]:
        """List all available snapshots, optionally including invalid ones."""
        snapshots = []

        for metadata_file in sorted(self.snapshot_dir.glob("*.json")):
            try:
                snapshot_id = metadata_file.stem

                # Verify snapshot if requested
                if not include_invalid and not self.verify_snapshot(snapshot_id):
                    continue

                # Load metadata
                metadata = json.loads(metadata_file.read_text())
                bytes.fromhex(metadata.get("sig", ""))

                snapshot_meta = SnapshotMeta(
                    id=metadata["id"],
                    parent_id=metadata.get("parent_id"),
                    ts_ms=metadata["ts_ms"],
                    merkle_root=metadata["merkle_root"],
                    signer=metadata["signer"],
                    sig=metadata.get("sig", ""),  # Keep as hex string
                    status=SnapshotStatus.OK,
                    content_size=metadata.get("content_size", 0),
                    file_count=metadata.get("file_count", 0)
                )

                snapshots.append(snapshot_meta)

            except Exception as e:
                logger.warning(f"Failed to load snapshot metadata from {metadata_file}: {e}")
                continue

        return sorted(snapshots, key=lambda s: s.ts_ms, reverse=True)

    def get_latest_snapshot(self) -> Optional[SnapshotMeta]:
        """Get the most recent valid snapshot."""
        snapshots = self.list_snapshots()
        return snapshots[0] if snapshots else None

    def restore_from_snapshot(self, snapshot_id: str, target_dir: Optional[Path] = None) -> bool:
        """Restore store from a snapshot backup."""
        if target_dir is None:
            target_dir = self.store_dir

        try:
            # Verify snapshot first
            if not self.verify_snapshot(snapshot_id):
                logger.error(f"Cannot restore from invalid snapshot {snapshot_id}")
                return False

            # Check if backup exists
            backup_dir = self.snapshot_dir / f"{snapshot_id}_backup"
            if not backup_dir.exists():
                logger.error(f"Snapshot backup not found: {backup_dir}")
                return False

            # Create temporary restore location
            temp_restore = target_dir.parent / f"{target_dir.name}_restore_temp"

            # Copy backup to temporary location
            if temp_restore.exists():
                shutil.rmtree(temp_restore)
            shutil.copytree(backup_dir, temp_restore)

            # Verify restored content
            metadata_file = self.snapshot_dir / f"{snapshot_id}.json"
            metadata = json.loads(metadata_file.read_text())
            expected_root = metadata["merkle_root"]

            current_root = self.integrity_store.merkle_root_for_dir(temp_restore)
            if current_root != expected_root:
                logger.error("Restored content integrity check failed")
                shutil.rmtree(temp_restore)
                return False

            # Atomic swap
            backup_old = target_dir.parent / f"{target_dir.name}_old"
            if target_dir.exists():
                target_dir.rename(backup_old)

            temp_restore.rename(target_dir)

            # Clean up old backup
            if backup_old.exists():
                shutil.rmtree(backup_old)

            logger.info(f"Successfully restored from snapshot {snapshot_id}")
            return True

        except Exception as e:
            logger.error(f"Restore from snapshot {snapshot_id} failed: {e}")
            return False

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get snapshotter performance metrics."""
        avg_time = self._total_snapshot_time / max(1, self._snapshot_count)

        return {
            "total_snapshots": self._snapshot_count,
            "total_snapshot_time": self._total_snapshot_time,
            "average_snapshot_time": avg_time,
            "snapshots_available": len(self.list_snapshots()),
            "store_size_bytes": self._calculate_store_metrics()[1],
            "snapshot_directory_size": self._calculate_directory_size(self.snapshot_dir)
        }

    def _generate_snapshot_id(self) -> str:
        """Generate unique snapshot ID."""
        return f"snap_{int(time.time() * 1000)}_{os.getpid()}"

    def _calculate_store_metrics(self) -> tuple[int, int]:
        """Calculate file count and total size of store directory."""
        if not self.store_dir.exists():
            return 0, 0

        file_count = 0
        total_size = 0

        for file_path in self.store_dir.rglob("*"):
            if file_path.is_file():
                file_count += 1
                try:
                    total_size += file_path.stat().st_size
                except OSError:
                    pass  # Skip files we can't read

        return file_count, total_size

    def _calculate_directory_size(self, directory: Path) -> int:
        """Calculate total size of directory."""
        total = 0
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                try:
                    total += file_path.stat().st_size
                except OSError:
                    pass
        return total

    def _write_snapshot_metadata(self, snapshot_meta: SnapshotMeta, meta_dict: Dict[str, Any]):
        """Write snapshot metadata atomically."""
        metadata_file = self.snapshot_dir / f"{snapshot_meta.id}.json"
        temp_file = metadata_file.with_suffix(".tmp")

        # Write to temporary file first
        temp_file.write_text(json.dumps(meta_dict, indent=2, sort_keys=True))

        # Sync to disk (handle Windows compatibility)
        try:
            with temp_file.open("rb") as f:
                os.fsync(f.fileno())
        except OSError:
            # Windows may not support fsync on all file systems
            pass

        # Atomic rename
        temp_file.rename(metadata_file)

    def _create_store_backup(self, snapshot_id: str):
        """Create a backup copy of the store for this snapshot."""
        if not self.store_dir.exists():
            return

        backup_dir = self.snapshot_dir / f"{snapshot_id}_backup"
        try:
            shutil.copytree(self.store_dir, backup_dir)
        except Exception as e:
            logger.warning(f"Failed to create store backup for {snapshot_id}: {e}")

    def _cleanup_old_snapshots(self):
        """Clean up old snapshots based on retention policy."""
        snapshots = self.list_snapshots(include_invalid=True)

        if len(snapshots) <= self.policy.retention_snapshots:
            return

        # Remove oldest snapshots
        to_remove = snapshots[self.policy.retention_snapshots:]

        for snapshot in to_remove:
            try:
                # Remove metadata file
                metadata_file = self.snapshot_dir / f"{snapshot.id}.json"
                if metadata_file.exists():
                    metadata_file.unlink()

                # Remove backup if it exists
                backup_dir = self.snapshot_dir / f"{snapshot.id}_backup"
                if backup_dir.exists():
                    shutil.rmtree(backup_dir)

                logger.debug(f"Removed old snapshot {snapshot.id}")

            except Exception as e:
                logger.warning(f"Failed to remove old snapshot {snapshot.id}: {e}")