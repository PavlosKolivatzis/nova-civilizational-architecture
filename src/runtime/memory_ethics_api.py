"""Minimal, robust API layer for Slot 8 integration."""

from typing import Any, Dict, Optional

from .memory_integrity import (
    EthicsGuard,
    SecurityError,
    audit_log,
)


class MemoryEthicsAPI:
    """Public API for Slot 8 integration."""

    @staticmethod
    def execute_command(command: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a command with the given payload."""
        try:
            handler = getattr(MemoryEthicsAPI, f"_handle_{command}", None)
            if not handler:
                return {
                    "status": "error",
                    "error": f"Unknown command: {command}",
                    "data": None,
                }

            actor = payload.get("actor")
            if not actor and command not in ("list",):
                return {
                    "status": "error",
                    "error": "Missing required field: 'actor'",
                    "data": None,
                }

            result = handler(payload, actor)
            return {"status": "success", "data": result, "error": None}

        except (SecurityError, PermissionError, KeyError, ValueError) as e:
            return {"status": "error", "error": str(e), "data": None}
        except Exception as e:  # pragma: no cover - unexpected errors
            audit_log("api_error", "system", "api", {"command": command, "error": str(e)})
            return {"status": "error", "error": "Internal system error", "data": None}

    @staticmethod
    def _handle_register(payload: Dict[str, Any], actor: str) -> str:
        name = payload["name"]
        data = payload["data"]
        readers = set(payload.get("readers", []))
        writers = set(payload.get("writers", []))

        EthicsGuard.register(
            name=name,
            data=data,
            readers=readers,
            writers=writers,
            actor=actor,
            read_only=payload.get("read_only", False),
        )
        return f"Registered '{name}'"

    @staticmethod
    def _handle_read(payload: Dict[str, Any], actor: str) -> Any:
        name = payload["name"]
        data = EthicsGuard.read(
            name=name,
            actor=actor,
            detach=payload.get("detach", True),
            metadata=payload.get("metadata"),
        )
        return data

    @staticmethod
    def _handle_write(payload: Dict[str, Any], actor: str) -> str:
        name = payload["name"]
        data = payload["data"]
        EthicsGuard.write(
            name=name,
            actor=actor,
            data=data,
            metadata=payload.get("metadata"),
        )
        return f"Written to '{name}'"

    @staticmethod
    def _handle_unregister(payload: Dict[str, Any], actor: str) -> str:
        name = payload["name"]
        EthicsGuard.unregister(name, actor)
        return f"Unregistered '{name}'"

    @staticmethod
    def _handle_list(payload: Dict[str, Any], actor: Optional[str] = None) -> Dict[str, Any]:
        actor = actor or "system"
        return EthicsGuard.list_objects(actor)

    @staticmethod
    def _handle_update_policies(payload: Dict[str, Any], actor: str) -> str:
        name = payload["name"]
        readers = set(payload.get("readers", []))
        writers = set(payload.get("writers", []))

        EthicsGuard.update_policies(
            name=name,
            actor=actor,
            readers=readers if "readers" in payload else None,
            writers=writers if "writers" in payload else None,
        )
        return f"Updated policies for '{name}'"


# Singleton instance for easy import
api = MemoryEthicsAPI()
