"""
Scenario serialization - save/load simulation scenarios.
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional, TYPE_CHECKING
from pathlib import Path

from src.core.graph import Graph
from src.nodes.registry import build_node_factory

if TYPE_CHECKING:
    from src.core.engine import SimulationEngine


class ScenarioSerializer:
    """Serialize simulation scenarios to JSON."""

    VERSION = "1.0"

    @staticmethod
    def serialize(engine: "SimulationEngine", scenario_name: str = "Untitled") -> Dict[str, Any]:
        """Serialize entire simulation state."""
        return {
            "version": ScenarioSerializer.VERSION,
            "name": scenario_name,
            "timestamp": datetime.now().isoformat(),
            "config": {
                "speed": engine.speed,
                "tick_interval_ms": engine.tick_interval_ms,
            },
            "graph": engine.graph.to_dict(),
        }

    @staticmethod
    def save_to_file(engine: "SimulationEngine", file_path: str,
                     scenario_name: str = "Untitled") -> bool:
        """Save scenario to JSON file."""
        try:
            data = ScenarioSerializer.serialize(engine, scenario_name)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving scenario: {e}")
            return False

    @staticmethod
    def to_json(engine: "SimulationEngine", scenario_name: str = "Untitled") -> str:
        """Convert scenario to JSON string."""
        data = ScenarioSerializer.serialize(engine, scenario_name)
        return json.dumps(data, indent=2, ensure_ascii=False)


class ScenarioLoader:
    """Load simulation scenarios from JSON."""

    def load_from_file(self, file_path: str) -> Optional[Graph]:
        """Load scenario from JSON file and return a Graph."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return self.load_from_dict(data)
        except Exception as e:
            print(f"Error loading scenario: {e}")
            return None

    def load_from_dict(self, data: Dict[str, Any]) -> Optional[Graph]:
        """Load scenario from dictionary and return a Graph."""
        try:
            graph = Graph()
            graph_data = data.get("graph", data)
            node_factory = build_node_factory()
            graph.from_dict(graph_data, node_factory)
            return graph
        except Exception as e:
            print(f"Error loading scenario from dict: {e}")
            return None

    @staticmethod
    def from_json(json_string: str) -> Optional[Graph]:
        """Load scenario from JSON string."""
        try:
            data = json.loads(json_string)
            loader = ScenarioLoader()
            return loader.load_from_dict(data)
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            return None


def export_scenario(engine: "SimulationEngine", file_path: str, name: str = "Untitled") -> bool:
    """Convenience function to export scenario."""
    return ScenarioSerializer.save_to_file(engine, file_path, name)


def import_scenario(file_path: str) -> Optional[Graph]:
    """Convenience function to import scenario as a Graph."""
    return ScenarioLoader().load_from_file(file_path)
