"""Compatibility shim exposing ``backend.app`` as ``app`` for tests."""
from importlib import import_module
import sys

backend_app = import_module("backend.app")
sys.modules.setdefault("app", backend_app)

for submodule in [
    "core",
    "services",
    "adapters",
]:
    sys.modules[f"app.{submodule}"] = import_module(f"backend.app.{submodule}")

__all__ = getattr(backend_app, "__all__", [])
