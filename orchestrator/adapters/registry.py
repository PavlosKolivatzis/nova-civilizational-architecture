# ruff: noqa: E402
from __future__ import annotations
from src_bootstrap import ensure_src_on_path
ensure_src_on_path()
"""Contract-based adapter registry with null adapter fallbacks."""

from typing import Any, Callable, Dict


class AdapterRegistry:
    """Registry for contract-based adapters with null fallbacks."""
    
    def __init__(self, loader):
        self._loader = loader
        self._nulls: Dict[str, Callable] = {}
    
    def register_null(self, contract_id: str, fn: Callable[[Any], Any]) -> None:
        """Register a null adapter for when no providers are available."""
        self._nulls[contract_id] = fn
    
    def call(self, contract_id: str, payload: Any) -> Any:
        """Call providers for a contract, falling back to null adapter if none available."""
        providers = self._loader.providers_for(contract_id)
        
        if not providers:
            # No providers available, use null adapter if registered
            null_fn = self._nulls.get(contract_id)
            if null_fn:
                try:
                    return null_fn(payload)
                except Exception as e:
                    return {"error": f"null_adapter_failed: {e}"}
            else:
                return {"error": f"no_provider_for_contract: {contract_id}"}
        
        # Single provider - return result directly
        if len(providers) == 1:
            slot_id, fn = next(iter(providers.items()))
            try:
                return fn(payload)
            except Exception as e:
                return {"error": f"{slot_id}_failed: {e}"}
        
        # Multiple providers - return dict with results from each
        results = {}
        for slot_id, fn in providers.items():
            try:
                results[slot_id] = fn(payload)
            except Exception as e:
                results[slot_id] = {"error": str(e)}
        return results
    
    def get_contracts(self) -> Dict[str, int]:
        """Get available contracts and their provider counts."""
        contracts = {}
        for slot in self._loader.items().values():
            for contract_id in slot.adapters.keys():
                contracts[contract_id] = contracts.get(contract_id, 0) + 1
        return contracts
    
    def get_null_adapters(self) -> list[str]:
        """Get list of registered null adapter contract IDs."""
        return list(self._nulls.keys())
