"""
GUI smoke tests for Sidebar, Inspector, and Canvas.
"""

import os
import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from src.core.graph import Graph
from src.core.engine import SimulationEngine
from src.gui.canvas import Canvas
from src.gui.sidebar import Sidebar
from src.gui.inspector import Inspector
from src.gui.main_window import MainWindow
from src.nodes.registry import SIDEBAR_NODE_MAP, build_node_factory
from src.nodes.sources import TextSourceNode

pytestmark = pytest.mark.usefixtures("qapp")


class TestSidebar:
    def test_categories_defined(self):
        sidebar = Sidebar()
        assert len(sidebar.CATEGORIES) >= 8
        names = {cat["id"] for cat in sidebar.CATEGORIES}
        assert "sources" in names
        assert "image_processing" in names

    def test_all_sidebar_items_in_registry(self):
        for cat in Sidebar.CATEGORIES:
            for item_name, _ in cat["items"]:
                assert item_name in SIDEBAR_NODE_MAP, f"Missing registry key: {item_name}"

    def test_search_filter(self):
        sidebar = Sidebar()
        sidebar.search_box.setText("Hamming")
        QTest.qWait(50)
        assert sidebar.search_box.text() == "Hamming"


class TestInspector:
    def test_set_node(self):
        inspector = Inspector()
        node = TextSourceNode("test_node")
        node.set_param("text", "Hello GUI")
        inspector.set_node(node)
        assert inspector.current_node is node

    def test_clear_node(self):
        inspector = Inspector()
        node = TextSourceNode("test_node")
        inspector.set_node(node)
        inspector.set_node(None)
        assert inspector.current_node is None


class TestCanvas:
    def test_add_node_via_undo(self):
        graph = Graph()
        engine = SimulationEngine(graph)
        canvas = Canvas(graph, engine)

        canvas.add_node_at("Text", (120, 80))
        assert len(graph.nodes) == 1
        assert canvas.undo_stack.can_undo()

        canvas.undo()
        assert len(graph.nodes) == 0
        assert canvas.undo_stack.can_redo()

    def test_connection_manager_has_wire_cutter(self):
        graph = Graph()
        engine = SimulationEngine(graph)
        canvas = Canvas(graph, engine)
        assert hasattr(canvas._connection_manager, '_wire_cutter')

    def test_factory_covers_registry(self):
        factory = build_node_factory()
        for key in SIDEBAR_NODE_MAP:
            assert key in factory


class TestMainWindow:
    def test_main_window_creates(self):
        window = MainWindow()
        assert window.canvas is not None
        assert window.sidebar is not None
        assert window.inspector is not None
        assert hasattr(window, 'action_undo')
        assert hasattr(window, 'action_redo')
        window.close()

    def test_undo_actions_connected(self):
        window = MainWindow()
        assert window.action_undo.isEnabled() is False
        window.canvas.add_node_at("Text", (0, 0))
        window._on_undo_state_changed(True, False)
        assert window.action_undo.isEnabled() is True
        window.close()
