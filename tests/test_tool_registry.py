from src.tools import build_tool_registry, load_tool_metadata


def test_tool_metadata_has_30_tools():
    metadata = load_tool_metadata()
    assert len(metadata) == 30


def test_tool_registry_has_30_callables():
    registry = build_tool_registry()
    assert len(registry) == 30
    assert all(callable(fn) for fn in registry.values())


def test_all_metadata_tools_have_implementations():
    metadata = load_tool_metadata()
    registry = build_tool_registry()
    for entry in metadata:
        assert entry["name"] in registry
