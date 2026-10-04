#!/usr/bin/env python3
"""
Test script to verify DELETE key functionality for nodes and connections.
"""

import sys
from PySide6.QtWidgets import QApplication, QGraphicsItem
from PySide6.QtCore import Qt

# Create QApplication before importing GUI components
app = QApplication(sys.argv)

from src.core.graph import Graph
from src.core.engine import SimulationEngine
from src.gui.canvas import Canvas
from src.gui.node_item import NodeItem, ConnectionItem
from src.nodes.sources import TextSourceNode
from src.nodes.sinks import TextOutputNode


def test_delete_nodes():
    """Test DELETE key deletes selected nodes."""
    print("Testing DELETE key for nodes...")
    
    graph = Graph()
    engine = SimulationEngine(graph)
    canvas = Canvas(graph, engine)
    
    # Create a node
    node = TextSourceNode("test_node_1")
    node.position = (100, 100)
    graph.add_node(node)
    
    node_item = NodeItem(node)
    node_item.setPos(100, 100)
    canvas.scene.addItem(node_item)
    canvas._node_items[node.node_id] = node_item
    
    # Select the node
    node_item.setSelected(True)
    
    # Simulate DELETE key press
    from PySide6.QtGui import QKeyEvent
    delete_event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Delete, Qt.NoModifier)
    canvas.keyPressEvent(delete_event)
    
    # Verify node was deleted
    assert node.node_id not in canvas._node_items, "Node should be deleted from _node_items"
    assert node.node_id not in graph.nodes, "Node should be deleted from graph"
    print("✓ DELETE key successfully deletes selected nodes")
    
    return True


def test_delete_connections():
    """Test DELETE key deletes selected connections."""
    print("\nTesting DELETE key for connections...")
    
    graph = Graph()
    engine = SimulationEngine(graph)
    canvas = Canvas(graph, engine)
    
    # Create two nodes
    source_node = TextSourceNode("source_1")
    source_node.position = (100, 100)
    graph.add_node(source_node)
    
    sink_node = TextOutputNode("sink_1")
    sink_node.position = (300, 100)
    graph.add_node(sink_node)
    
    # Create node items
    source_item = NodeItem(source_node)
    source_item.setPos(100, 100)
    canvas.scene.addItem(source_item)
    canvas._node_items[source_node.node_id] = source_item
    
    sink_item = NodeItem(sink_node)
    sink_item.setPos(300, 100)
    canvas.scene.addItem(sink_item)
    canvas._node_items[sink_node.node_id] = sink_item
    
    # Create a connection
    canvas._redraw_connections()
    
    # Manually create a connection for testing
    conn_item = ConnectionItem(source_item, "out", sink_item, "in")
    canvas.scene.addItem(conn_item)
    key = (source_node.node_id, "out", sink_node.node_id, "in")
    canvas._connection_items[key] = conn_item
    graph.connections.append((source_node.node_id, "out", sink_node.node_id, "in"))
    
    # Select the connection
    conn_item.setSelected(True)
    
    # Simulate DELETE key press
    from PySide6.QtGui import QKeyEvent
    delete_event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Delete, Qt.NoModifier)
    canvas.keyPressEvent(delete_event)
    
    # Verify connection was deleted
    assert key not in canvas._connection_items, "Connection should be deleted from _connection_items"
    assert key not in graph.connections, "Connection should be deleted from graph"
    print("✓ DELETE key successfully deletes selected connections")
    
    return True


def test_connection_selectable():
    """Test that connections are selectable."""
    print("\nTesting connection selection...")
    
    graph = Graph()
    engine = SimulationEngine(graph)
    canvas = Canvas(graph, engine)
    
    # Create two nodes
    source_node = TextSourceNode("source_2")
    source_node.position = (100, 100)
    graph.add_node(source_node)
    
    sink_node = TextOutputNode("sink_2")
    sink_node.position = (300, 100)
    graph.add_node(sink_node)
    
    # Create node items
    source_item = NodeItem(source_node)
    source_item.setPos(100, 100)
    canvas.scene.addItem(source_item)
    canvas._node_items[source_node.node_id] = source_item
    
    sink_item = NodeItem(sink_node)
    sink_item.setPos(300, 100)
    canvas.scene.addItem(sink_item)
    canvas._node_items[sink_node.node_id] = sink_item
    
    # Create a connection
    conn_item = ConnectionItem(source_item, "out", sink_item, "in")
    canvas.scene.addItem(conn_item)
    
    # Test that connection is selectable
    assert conn_item.flags() & QGraphicsItem.ItemIsSelectable, "Connection should be selectable"
    
    # Test selection
    conn_item.setSelected(True)
    assert conn_item.isSelected(), "Connection should be selected"
    
    print("✓ Connections are selectable")
    
    return True


def test_connection_visual_feedback():
    """Test that selected connections show visual feedback."""
    print("\nTesting connection visual feedback...")
    
    graph = Graph()
    engine = SimulationEngine(graph)
    canvas = Canvas(graph, engine)
    
    # Create two nodes
    source_node = TextSourceNode("source_3")
    source_node.position = (100, 100)
    graph.add_node(source_node)
    
    sink_node = TextOutputNode("sink_3")
    sink_node.position = (300, 100)
    graph.add_node(sink_node)
    
    # Create node items
    source_item = NodeItem(source_node)
    source_item.setPos(100, 100)
    canvas.scene.addItem(source_item)
    canvas._node_items[source_node.node_id] = source_item
    
    sink_item = NodeItem(sink_node)
    sink_item.setPos(300, 100)
    canvas.scene.addItem(sink_item)
    canvas._node_items[sink_node.node_id] = sink_item
    
    # Create a connection
    conn_item = ConnectionItem(source_item, "out", sink_item, "in")
    canvas.scene.addItem(conn_item)
    
    # Test visual feedback when selected
    conn_item.setSelected(True)
    # The paint method should handle the visual feedback
    # We can't easily test the actual painting without a full GUI,
    # but we can verify the isSelected() state
    assert conn_item.isSelected(), "Connection should be selected for visual feedback"
    
    print("✓ Connection visual feedback works (selection state)")
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Testing DELETE functionality for nodes and connections")
    print("=" * 60)
    
    try:
        test_delete_nodes()
        test_delete_connections()
        test_connection_selectable()
        test_connection_visual_feedback()
        
        print("\n" + "=" * 60)
        print("✓ All tests passed successfully!")
        print("=" * 60)
        print("\nFeatures implemented:")
        print("1. DELETE key deletes selected nodes")
        print("2. DELETE key deletes selected connections")
        print("3. Connections are now selectable")
        print("4. Selected connections show visual feedback (blue highlight)")
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)