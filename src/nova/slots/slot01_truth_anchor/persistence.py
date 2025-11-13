"""Persistence layer for Truth Anchor Engine."""

import json
import tempfile
import threading
from pathlib import Path
from typing import Dict, Any, Optional
import logging


class AnchorPersistence:
    """File-based persistence for truth anchors with atomic writes."""

    def __init__(self, storage_path: Optional[str] = None, logger: Optional[logging.Logger] = None):
        """Initialize persistence layer.

        Args:
            storage_path: Path to storage file. If None, uses temp directory.
            logger: Logger instance. If None, creates one.
        """
        self.logger = logger or logging.getLogger("anchor_persistence")

        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            # Use a temp directory for default storage
            temp_dir = Path(tempfile.gettempdir()) / "nova_anchors"
            temp_dir.mkdir(exist_ok=True)
            self.storage_path = temp_dir / "truth_anchors.json"

        self._lock = threading.RLock()
        self.logger.debug(f"Anchor persistence initialized at: {self.storage_path}")

    def save(self, anchors: Dict[str, Any], metrics: Dict[str, Any]) -> bool:
        """Save anchors and metrics to persistent storage.

        Args:
            anchors: Dictionary of anchor_id -> anchor_data
            metrics: Dictionary of metrics data

        Returns:
            True if save successful, False otherwise
        """
        with self._lock:
            try:
                # Prepare data for serialization
                data = {
                    "version": "1.0",
                    "anchors": self._serialize_anchors(anchors),
                    "metrics": metrics,
                    "timestamp": self._get_timestamp()
                }

                # Atomic write: write to temp file first, then rename
                temp_path = self.storage_path.with_suffix('.tmp')

                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, default=str)

                # Atomic rename
                temp_path.replace(self.storage_path)

                self.logger.debug(f"Saved {len(anchors)} anchors to {self.storage_path}")
                return True

            except Exception as exc:
                self.logger.error(f"Failed to save anchors: {exc}")
                return False

    def load(self) -> Dict[str, Any]:
        """Load anchors and metrics from persistent storage.

        Returns:
            Dictionary with 'anchors' and 'metrics' keys, or empty dict if load fails
        """
        with self._lock:
            try:
                if not self.storage_path.exists():
                    self.logger.debug("No persistence file found, returning empty state")
                    return {"anchors": {}, "metrics": {}}

                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                anchors = self._deserialize_anchors(data.get("anchors", {}))
                metrics = data.get("metrics", {})

                self.logger.debug(f"Loaded {len(anchors)} anchors from {self.storage_path}")
                return {"anchors": anchors, "metrics": metrics}

            except Exception as exc:
                self.logger.error(f"Failed to load anchors: {exc}")
                return {"anchors": {}, "metrics": {}}

    def clear(self) -> bool:
        """Clear persistent storage.

        Returns:
            True if clear successful, False otherwise
        """
        with self._lock:
            try:
                if self.storage_path.exists():
                    self.storage_path.unlink()
                    self.logger.debug("Cleared persistent storage")
                return True
            except Exception as exc:
                self.logger.error(f"Failed to clear storage: {exc}")
                return False

    def get_storage_info(self) -> Dict[str, Any]:
        """Get information about the storage file.

        Returns:
            Dictionary with storage file information
        """
        try:
            if self.storage_path.exists():
                stat = self.storage_path.stat()
                return {
                    "path": str(self.storage_path),
                    "exists": True,
                    "size_bytes": stat.st_size,
                    "modified": stat.st_mtime
                }
            else:
                return {
                    "path": str(self.storage_path),
                    "exists": False,
                    "size_bytes": 0,
                    "modified": None
                }
        except Exception:
            return {
                "path": str(self.storage_path),
                "exists": False,
                "size_bytes": 0,
                "modified": None,
                "error": True
            }

    def _serialize_anchors(self, anchors: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize anchor records for JSON storage."""
        serialized = {}
        for anchor_id, record in anchors.items():
            try:
                # Handle AnchorRecord objects
                if hasattr(record, 'value') and hasattr(record, 'metadata'):
                    serialized[anchor_id] = {
                        "value": self._serialize_value(record.value),
                        "metadata": record.metadata
                    }
                else:
                    # Handle direct values
                    serialized[anchor_id] = {
                        "value": self._serialize_value(record),
                        "metadata": {}
                    }
            except Exception as exc:
                self.logger.warning(f"Failed to serialize anchor {anchor_id}: {exc}")

        return serialized

    def _deserialize_anchors(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Deserialize anchor records from JSON storage."""
        from .truth_anchor_engine import AnchorRecord

        anchors = {}
        for anchor_id, anchor_data in data.items():
            try:
                value = self._deserialize_value(anchor_data.get("value"))
                metadata = anchor_data.get("metadata", {})
                anchors[anchor_id] = AnchorRecord(value=value, metadata=metadata)
            except Exception as exc:
                self.logger.warning(f"Failed to deserialize anchor {anchor_id}: {exc}")

        return anchors

    def _serialize_value(self, value: Any) -> Any:
        """Serialize a value for JSON storage."""
        if isinstance(value, bytes):
            # Convert bytes to hex string for JSON compatibility
            return {"__bytes__": value.hex()}
        return value

    def _deserialize_value(self, value: Any) -> Any:
        """Deserialize a value from JSON storage."""
        if isinstance(value, dict) and "__bytes__" in value:
            # Convert hex string back to bytes
            return bytes.fromhex(value["__bytes__"])
        return value

    def _get_timestamp(self) -> float:
        """Get current timestamp."""
        import time
        return time.time()


# Global instance for easy access
_default_persistence = None
_persistence_lock = threading.Lock()


def get_default_persistence(storage_path: Optional[str] = None) -> AnchorPersistence:
    """Get the default persistence instance (singleton pattern)."""
    global _default_persistence

    with _persistence_lock:
        # Always honour an explicit storage_path by creating
        # a dedicated persistence instance for that location.
        if storage_path:
            return AnchorPersistence(storage_path)

        if _default_persistence is None:
            _default_persistence = AnchorPersistence()
        return _default_persistence


def set_default_persistence(persistence: AnchorPersistence) -> None:
    """Set the default persistence instance."""
    global _default_persistence

    with _persistence_lock:
        _default_persistence = persistence
