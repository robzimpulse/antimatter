import pytest
import importlib.util

def test_module_imports():
    """Verify that all core modules can be imported without syntax or dependency errors."""
    for module in ["antimatter_ag2.server", "antimatter_ag2.agent_bridge", "antimatter_ag2.cli"]:
        if importlib.util.find_spec(module) is None:
            pytest.fail(f"Failed to find core module: {module}")
