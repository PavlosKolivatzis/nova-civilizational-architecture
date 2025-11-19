# ruff: noqa: E402
from src_bootstrap import ensure_src_on_path
ensure_src_on_path()
from typing import Any, Optional, Dict


class Slot4TRIAdapter:
    """Smart TRI adapter that routes to the appropriate engine:
    - Operational (Engine 1): real-time monitoring / latest report
    - Content (Engine 2): plugin-based content analysis
    """

    available: bool = True

    def __init__(self) -> None:
        self._operational_engine: Any = None
        self._content_engine: Any = None

    # ---- engine loaders -------------------------------------------------
    def _get_operational_engine(self):
        """Get the operational TRI engine for real-time monitoring."""
        if self._operational_engine is None:
            try:
                from nova.slots.slot04_tri.core.tri_engine import TriEngine  # Engine 1
                self._operational_engine = TriEngine()
            except Exception:
                self._operational_engine = False
        return self._operational_engine if self._operational_engine is not False else None

    def _get_content_engine(self):
        """Get the content-analysis TRI engine for plugin-based scoring."""
        if self._content_engine is None:
            try:
                from nova.slots.slot04_tri_engine.engine import TRIEngine  # Engine 2
                self._content_engine = TRIEngine()
            except Exception:
                self._content_engine = False
        return self._content_engine if self._content_engine is not False else None

    async def calibrate(self, payload: Any) -> None:  # pragma: no cover - trivial
        return None

    def get_latest_report(self) -> dict:
        """Return the latest operational TRI report for monitoring/gates."""
        engine = self._get_operational_engine()
        if engine and hasattr(engine, "assess"):
            try:
                health = engine.assess()
                # Safely extract attributes with sane defaults
                report = {
                    "coherence": getattr(health, "coherence", 0.7),
                    "phase_jitter": getattr(health, "phase_jitter", 0.15),
                    "tri_score": getattr(health, "tri_score", 0.75),
                    "tri_mean": getattr(health, "tri_mean", None),
                    "drift_z": getattr(health, "drift_z", None),
                    "n_samples": getattr(health, "n_samples", None),
                }
                self._attach_truth_signal(report)
                return report
            except Exception:
                # fall through to safe defaults below
                pass

        # Fallback: safe, deterministic defaults to keep gates functional
        report = {"coherence": 0.7, "phase_jitter": 0.15, "tri_score": 0.75}
        self._attach_truth_signal(report)
        return report

    def calculate(self, content: str, context: Optional[Dict] = None) -> Dict:
        """Calculate TRI for content analysis (Engine 2), with graceful fallbacks."""
        content_engine = self._get_content_engine()
        if content_engine and hasattr(content_engine, "calculate"):
            try:
                return content_engine.calculate(content, context)
            except Exception:
                pass

        # Fallback: some operational engines provide a calculate() too
        op_engine = self._get_operational_engine()
        if op_engine and hasattr(op_engine, "calculate"):
            try:
                return op_engine.calculate(content)
            except Exception:
                pass

        # Final fallback: explicit "safe no-op" structure
        return {
            "score": 0.0,
            "layer_scores": {"structural": 0.0, "semantic": 0.0, "expression": 0.0},
            "metadata": {"fallback": True, "reason": "No TRI engines available"},
        }

    def _attach_truth_signal(self, report: Dict[str, Any]) -> None:
        """Enrich TRI report with canonical truth signal if possible."""
        try:
            from orchestrator.tri_truth_bridge import process_tri_truth_signal

            truth_signal = process_tri_truth_signal(report)
            if truth_signal:
                report["truth_signal"] = truth_signal
        except Exception:
            # Never let truth bridge failures break downstream consumers
            pass
