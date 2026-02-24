import builtins
import importlib
import sys

import pytest


def test_single_federation_health_route():
    from nova.orchestrator.app import app

    if app is None:
        pytest.skip("FastAPI app not available")

    routes = [
        route
        for route in app.router.routes
        if getattr(route, "path", None) == "/federation/health"
        and "GET" in getattr(route, "methods", set())
    ]
    assert len(routes) == 1


def test_app_import_without_fastapi(monkeypatch):
    module_name = "nova.orchestrator.app"
    original_app_module = sys.modules.get(module_name)
    saved_fastapi_modules = {
        name: mod
        for name, mod in list(sys.modules.items())
        if name == "fastapi" or name.startswith("fastapi.")
    }

    original_import = builtins.__import__

    def blocked_fastapi_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "fastapi" or name.startswith("fastapi."):
            raise ImportError("simulated missing fastapi")
        return original_import(name, globals, locals, fromlist, level)

    try:
        sys.modules.pop(module_name, None)
        for name in list(saved_fastapi_modules):
            sys.modules.pop(name, None)

        monkeypatch.setattr(builtins, "__import__", blocked_fastapi_import)
        app_mod = importlib.import_module(module_name)

        assert app_mod.app is None
        assert hasattr(app_mod, "handle_request")
    finally:
        sys.modules.pop(module_name, None)
        for name in list(sys.modules):
            if name == "fastapi" or name.startswith("fastapi."):
                sys.modules.pop(name, None)
        sys.modules.update(saved_fastapi_modules)
        if original_app_module is not None:
            sys.modules[module_name] = original_app_module

