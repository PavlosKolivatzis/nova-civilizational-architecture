class ConstellationEngine:
    """Core engine for Slot 5 - Constellation mapping.

    The implementation is intentionally lightweight but provides enough
    behaviour for integration tests exercising TRI layer updates.
    """

    __version__ = "0.2.0"

    def __init__(self) -> None:
        self._position = 0.5
        self._stability = 1.0

    # ------------------------------------------------------------------
    def map(self, items: list[str]) -> dict:
        """Return a naive constellation mapping for provided items."""
        return {"constellation": items[:], "links": []}

    def get_current_position(self) -> float:
        return self._position

    def update_from_tri(self, tri_score: float, layer_scores: dict[str, float]) -> dict:
        influence = sum(layer_scores.values()) / max(1, len(layer_scores))
        delta = (tri_score - 0.5) * 0.1 - influence * 0.05
        self._position = max(0.0, min(1.0, self._position + delta))
        self._stability = max(0.0, min(1.0, 0.95 - influence * 0.1))
        return {"position": self._position, "stability_index": self._stability}
