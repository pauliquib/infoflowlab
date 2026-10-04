"""
Tests for scenario serialization and node registry.
"""

import json
import pytest
from src.core.graph import Graph
from src.core.engine import SimulationEngine
from src.nodes.registry import resolve_node_class, build_node_factory, get_sidebar_key
from src.nodes.sources import TextSourceNode, ImageSourceNode
from src.nodes.channels import GilbertElliottChannelNode
from src.nodes.ecc import ReedSolomonEncoderNode
from src.nodes.analyzers import EntropyMeterNode
from src.utils.serialization import ScenarioSerializer, ScenarioLoader, import_scenario


class TestNodeRegistry:
    """Test central node registry."""

    def test_sidebar_key_roundtrip(self):
        assert get_sidebar_key(TextSourceNode) == "Text"
        assert get_sidebar_key(ImageSourceNode) == "ImageSrc"

    def test_resolve_by_class_name(self):
        data = {"class_name": "ImageSourceNode", "type": "source"}
        assert resolve_node_class(data) is ImageSourceNode

    def test_resolve_legacy_by_name_hint(self):
        data = {
            "type": "source",
            "name": "🖼️ Obrázek",
        }
        assert resolve_node_class(data) is ImageSourceNode

        data = {
            "type": "channel",
            "name": "📡 Gilbert-Elliott",
        }
        assert resolve_node_class(data) is GilbertElliottChannelNode

        data = {
            "type": "ecc",
            "name": "🔴 RS Enc",
        }
        assert resolve_node_class(data) is ReedSolomonEncoderNode

        data = {
            "type": "analyzer",
            "name": "📊 Entropie",
        }
        assert resolve_node_class(data) is EntropyMeterNode


class TestSerialization:
    """Test save/load round-trip."""

    def test_graph_roundtrip(self):
        graph = Graph()
        node1 = TextSourceNode("node_1")
        node1.position = (100, 200)
        node1.set_param("text", "Test roundtrip")
        graph.add_node(node1)

        data = graph.to_dict()
        restored = Graph()
        restored.from_dict(data, build_node_factory())

        assert len(restored.nodes) == 1
        node = list(restored.nodes.values())[0]
        assert isinstance(node, TextSourceNode)
        assert node.position == (100, 200)
        assert node.get_param("text") == "Test roundtrip"

    def test_legacy_scenario_load(self):
        """Load saves/scenario.json with legacy generic types."""
        import os
        scenario_path = os.path.join(
            os.path.dirname(__file__), "..", "saves", "scenario.json"
        )
        if not os.path.exists(scenario_path):
            pytest.skip("scenario.json not found")

        graph = import_scenario(scenario_path)
        assert graph is not None
        assert len(graph.nodes) == 4

        classes = {type(n).__name__ for n in graph.nodes.values()}
        assert "ImageSourceNode" in classes
        assert "GilbertElliottChannelNode" in classes
        assert "ReedSolomonEncoderNode" in classes
        assert "EntropyMeterNode" in classes

    def test_scenario_serializer(self):
        graph = Graph()
        graph.add_node(TextSourceNode("src1"))
        engine = SimulationEngine(graph)

        data = ScenarioSerializer.serialize(engine, "Test")
        assert data["version"] == "1.0"
        assert data["name"] == "Test"
        assert len(data["graph"]["nodes"]) == 1

        loader = ScenarioLoader()
        restored = loader.load_from_dict(data)
        assert restored is not None
        assert len(restored.nodes) == 1

    def test_to_dict_includes_type_key(self):
        node = TextSourceNode("n1")
        data = node.to_dict()
        assert data["type_key"] == "Text"
        assert data["class_name"] == "TextSourceNode"
