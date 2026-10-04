"""
Tests for undo/redo command stack.
"""

import pytest
from src.core.graph import Graph
from src.core.engine import SimulationEngine
from src.core.undo_stack import (
    AddNodeCommand, RemoveNodeCommand, MoveNodeCommand,
    AddConnectionCommand, RemoveConnectionCommand, MacroCommand
)
from src.gui.canvas import Canvas

pytestmark = pytest.mark.usefixtures("qapp")


@pytest.fixture
def canvas():
    graph = Graph()
    engine = SimulationEngine(graph)
    c = Canvas(graph, engine)
    return c


class TestUndoStack:
    def test_add_and_undo_node(self, canvas):
        canvas._add_node_internal("Text", (100, 200))
        assert len(canvas.graph.nodes) == 1

        cmd = AddNodeCommand(canvas, "Random", (50, 50))
        canvas.undo_stack.push(cmd)
        assert len(canvas.graph.nodes) == 2

        canvas.undo_stack.undo()
        assert len(canvas.graph.nodes) == 1

        canvas.undo_stack.redo()
        assert len(canvas.graph.nodes) == 2

    def test_remove_and_undo_node(self, canvas):
        node = canvas._add_node_internal("Text", (0, 0))
        node_id = node.node_id

        canvas.undo_stack.push(RemoveNodeCommand(canvas, node_id))
        assert node_id not in canvas.graph.nodes

        canvas.undo_stack.undo()
        assert node_id in canvas.graph.nodes

    def test_move_node_undo(self, canvas):
        node = canvas._add_node_internal("Text", (80, 80))
        node_id = node.node_id

        canvas.undo_stack.push(MoveNodeCommand(canvas, node_id, (80, 80), (160, 200)))
        assert canvas.graph.nodes[node_id].position == (160, 200)

        canvas.undo_stack.undo()
        assert canvas.graph.nodes[node_id].position == (80, 80)

    def test_connection_undo(self, canvas):
        n1 = canvas._add_node_internal("Text", (0, 0))
        n2 = canvas._add_node_internal("Konzole", (200, 0))

        canvas._add_connection_internal(n1.node_id, "out", n2.node_id, "in")
        assert len(canvas.graph.connections) == 1

        conn = canvas.graph.connections[0]
        canvas.undo_stack.push(RemoveConnectionCommand(canvas, *conn))
        assert len(canvas.graph.connections) == 0

        canvas.undo_stack.undo()
        assert len(canvas.graph.connections) == 1

    def test_macro_command(self, canvas):
        cmds = [
            AddNodeCommand(canvas, "Text", (0, 0)),
            AddNodeCommand(canvas, "Random", (100, 0)),
        ]
        canvas.undo_stack.push(MacroCommand("Add two", cmds))
        assert len(canvas.graph.nodes) == 2

        canvas.undo_stack.undo()
        assert len(canvas.graph.nodes) == 0
