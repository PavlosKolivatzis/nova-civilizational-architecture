"""Contract emission infrastructure for Nova."""

from typing import Protocol, Any


class ContractEmitter(Protocol):
    """Protocol for emitting contracts to slots."""
    def emit(self, contract: Any) -> None: ...


class NoOpEmitter:
    """Default no-operation emitter."""
    def emit(self, contract: Any) -> None:
        pass


_emitter: ContractEmitter = NoOpEmitter()


def set_contract_emitter(emitter: ContractEmitter) -> None:
    """Set the global contract emitter."""
    global _emitter
    _emitter = emitter


def get_contract_emitter() -> ContractEmitter:
    """Get the current contract emitter."""
    return _emitter