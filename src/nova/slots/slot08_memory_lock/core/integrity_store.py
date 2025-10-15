"""Merkle tree integrity verification for memory store."""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Tuple, cast


class MerkleIntegrityStore:
    """Cryptographic integrity verification using Merkle trees."""

    def __init__(self, hash_algorithm: str = "sha256"):
        """Initialize integrity store with specified hash algorithm."""
        self.hash_algorithm = hash_algorithm
        self._hasher = getattr(hashlib, hash_algorithm)

    def hash_content(self, content: bytes) -> str:
        """Hash content using configured algorithm."""
        return self._hasher(content).hexdigest()

    def hash_file(self, file_path: Path) -> str:
        """Calculate hash of a file."""
        try:
            content = file_path.read_bytes()
            return self.hash_content(content)
        except Exception as e:
            # For missing/unreadable files, return a sentinel hash
            return self.hash_content(f"ERROR:{str(e)}".encode())

    def merkle_root_for_dir(self, root_dir: Path, include_metadata: bool = True) -> str:
        """Calculate Merkle root hash for directory tree."""
        if not root_dir.exists():
            return self.hash_content(b"EMPTY_DIR")

        # Collect all file hashes
        file_hashes = []
        for file_path in sorted(root_dir.rglob("*")):
            if file_path.is_file():
                # Include file path in hash for structure integrity
                rel_path = file_path.relative_to(root_dir)
                content_hash = self.hash_file(file_path)

                if include_metadata:
                    # Include file metadata for tamper detection
                    stat = file_path.stat()
                    metadata = {
                        "path": str(rel_path),
                        "size": stat.st_size,
                        "mtime": int(stat.st_mtime),
                        "content_hash": content_hash
                    }
                    combined_data = json.dumps(metadata, sort_keys=True).encode()
                else:
                    combined_data = f"{rel_path}:{content_hash}".encode()

                file_hashes.append(self.hash_content(combined_data))

        return self._compute_merkle_root(file_hashes)

    def _compute_merkle_root(self, leaf_hashes: List[str]) -> str:
        """Compute Merkle root from leaf hashes."""
        if not leaf_hashes:
            return self.hash_content(b"EMPTY_TREE")

        # Handle single leaf case
        if len(leaf_hashes) == 1:
            return leaf_hashes[0]

        # Build Merkle tree bottom-up
        current_level = leaf_hashes[:]

        while len(current_level) > 1:
            next_level = []

            # Process pairs of nodes
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left

                # Combine hashes
                combined = f"{left}:{right}".encode()
                parent_hash = self.hash_content(combined)
                next_level.append(parent_hash)

            current_level = next_level

        return current_level[0]

    def verify_integrity(self, root_dir: Path, expected_root: str,
                        include_metadata: bool = True) -> Tuple[bool, Dict[str, Any]]:
        """Verify directory integrity against expected Merkle root."""
        current_root = self.merkle_root_for_dir(root_dir, include_metadata)
        is_valid = current_root == expected_root

        verification_result = {
            "is_valid": is_valid,
            "expected_root": expected_root,
            "current_root": current_root,
            "verification_timestamp": self._get_timestamp(),
            "include_metadata": include_metadata
        }

        if not is_valid:
            # Provide detailed corruption analysis
            verification_result.update(self._analyze_corruption(root_dir, expected_root))

        return is_valid, verification_result

    def _analyze_corruption(self, root_dir: Path, expected_root: str) -> Dict[str, Any]:
        """Analyze corruption details for forensics."""
        analysis = {
            "corruption_detected": True,
            "affected_files": [],
            "missing_files": [],
            "extra_files": [],
            "metadata_changes": []
        }

        try:
            # This would require storing the original file manifest
            # For now, provide basic analysis
            if root_dir.exists():
                file_count = len(list(root_dir.rglob("*")))
                analysis["current_file_count"] = file_count
            else:
                analysis["directory_missing"] = True

        except Exception as e:
            analysis["analysis_error"] = str(e)

        return analysis

    def _get_timestamp(self) -> int:
        """Get current timestamp in milliseconds."""
        import time
        return int(time.time() * 1000)

    def create_integrity_manifest(self, root_dir: Path) -> Dict[str, Any]:
        """Create detailed integrity manifest for a directory."""
        files: Dict[str, Dict[str, Any]] = {}
        manifest: Dict[str, Any] = {
            "merkle_root": self.merkle_root_for_dir(root_dir),
            "hash_algorithm": self.hash_algorithm,
            "created_timestamp": self._get_timestamp(),
            "files": files,
        }

        if root_dir.exists():
            for file_path in sorted(root_dir.rglob("*")):
                if file_path.is_file():
                    rel_path = str(file_path.relative_to(root_dir))
                    stat = file_path.stat()

                    files[rel_path] = {
                        "content_hash": self.hash_file(file_path),
                        "size": stat.st_size,
                        "mtime": int(stat.st_mtime),
                        "permissions": oct(stat.st_mode)[-3:]
                    }

        return manifest

    def verify_against_manifest(
        self,
        root_dir: Path,
        manifest: Mapping[str, Any],
    ) -> Tuple[bool, Dict[str, Any]]:
        """Verify directory against a detailed manifest."""
        current_manifest = self.create_integrity_manifest(root_dir)

        is_valid = (current_manifest["merkle_root"] == manifest["merkle_root"])

        verification: Dict[str, Any] = {
            "is_valid": is_valid,
            "verification_timestamp": self._get_timestamp(),
            "manifest_timestamp": manifest.get("created_timestamp"),
            "changes": []
        }

        if not is_valid:
            # Detailed change analysis
            verification["changes"] = self._compare_manifests(manifest, current_manifest)

        return is_valid, verification

    def _compare_manifests(
        self,
        original: Mapping[str, Any],
        current: Mapping[str, Any],
    ) -> List[Dict[str, Any]]:
        """Compare two manifests and return list of changes."""
        changes: List[Dict[str, Any]] = []

        original_files_map = cast(Mapping[str, Dict[str, Any]], original.get("files", {}))
        current_files_map = cast(Mapping[str, Dict[str, Any]], current.get("files", {}))

        original_files = set(original_files_map.keys())
        current_files = set(current_files_map.keys())

        # Deleted files
        for deleted_file in original_files - current_files:
            changes.append({
                "type": "deleted",
                "file": deleted_file,
                "original_hash": original_files_map[deleted_file]["content_hash"],
            })

        # Added files
        for added_file in current_files - original_files:
            changes.append({
                "type": "added",
                "file": added_file,
                "current_hash": current_files_map[added_file]["content_hash"],
            })

        # Modified files
        for common_file in original_files & current_files:
            orig_info = original_files_map[common_file]
            curr_info = current_files_map[common_file]

            if orig_info["content_hash"] != curr_info["content_hash"]:
                changes.append({
                    "type": "content_modified",
                    "file": common_file,
                    "original_hash": orig_info["content_hash"],
                    "current_hash": curr_info["content_hash"]
                })
            elif orig_info.get("mtime") != curr_info.get("mtime"):
                changes.append({
                    "type": "metadata_modified",
                    "file": common_file,
                    "change": "mtime"
                })

        return changes
