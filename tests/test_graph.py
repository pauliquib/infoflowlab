"""
Tests for Graph class
"""

import pytest
from src.core.graph import Graph
from src.core.node_base import NodeBase
from src.core.port import Port, PortType
from src.core.packet import DataPacket


class GraphTestNode(NodeBase):
    """Helper node for graph tests."""
    def __init__(self, node_id: str):
        super().__init__(node_id, "test", "Test Node")
        self.add_input("in")
        self.add_output("out")
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        return packet


class TestGraph:
    """Test Graph functionality"""
    
    def test_add_node(self):
        """Test adding a node to the graph"""
        graph = Graph()
        node = GraphTestNode("node1")
        node_id = graph.add_node(node)
        assert node_id == "node1"
        assert "node1" in graph.nodes
        assert graph.nodes["node1"] == node
    
    def test_remove_node(self):
        """Test removing a node and its connections"""
        graph = Graph()
        node1 = GraphTestNode("node1")
        node2 = GraphTestNode("node2")
        graph.add_node(node1)
        graph.add_node(node2)
        graph.connect("node1", "out", "node2", "in")
        
        assert len(graph.connections) == 1
        graph.remove_node("node1")
        assert "node1" not in graph.nodes
        assert len(graph.connections) == 0
    
    def test_connect_nodes(self):
        """Test connecting two nodes"""
        graph = Graph()
        node1 = GraphTestNode("node1")
        node2 = GraphTestNode("node2")
        graph.add_node(node1)
        graph.add_node(node2)
        
        success, reason, warning = graph.connect("node1", "out", "node2", "in")
        assert success is True
        assert len(graph.connections) == 1
        assert warning == ""  # No cycle
    
    def test_connect_invalid_nodes(self):
        """Test connecting with invalid node IDs"""
        graph = Graph()
        node1 = GraphTestNode("node1")
        graph.add_node(node1)
        
        success, reason, warning = graph.connect("node1", "out", "nonexistent", "in")
        assert success is False
        assert "Node not found" in reason
    
    def test_connect_invalid_ports(self):
        """Test connecting with invalid port names"""
        graph = Graph()
        node1 = GraphTestNode("node1")
        node2 = GraphTestNode("node2")
        graph.add_node(node1)
        graph.add_node(node2)
        
        success, reason, warning = graph.connect("node1", "invalid_port", "node2", "in")
        assert success is False
        assert "not found" in reason
    
    def test_disconnect_nodes(self):
        """Test disconnecting nodes"""
        graph = Graph()
        node1 = GraphTestNode("node1")
        node2 = GraphTestNode("node2")
        graph.add_node(node1)
        graph.add_node(node2)
        graph.connect("node1", "out", "node2", "in")
        
        assert len(graph.connections) == 1
        success = graph.disconnect("node1", "out", "node2", "in")
        assert success is True
        assert len(graph.connections) == 0
    
    def test_cycle_detection(self):
        """Test cycle detection in graph"""
        graph = Graph()
        node1 = GraphTestNode("node1")
        node2 = GraphTestNode("node2")
        node3 = GraphTestNode("node3")
        
        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)
        
        # Create a chain: node1 -> node2 -> node3
        graph.connect("node1", "out", "node2", "in")
        graph.connect("node2", "out", "node3", "in")
        
        # Try to create a cycle: node3 -> node1
        success, reason, warning = graph.connect("node3", "out", "node1", "in")
        assert success is True
        assert "cycle" in warning.lower()
    
    def test_get_node(self):
        """Test getting a node by ID"""
        graph = Graph()
        node = GraphTestNode("node1")
        graph.add_node(node)
        
        retrieved = graph.get_node("node1")
        assert retrieved == node
        
        not_found = graph.get_node("nonexistent")
        assert not_found is None
    
    def test_get_nodes_by_type(self):
        """Test filtering nodes by type"""
        graph = Graph()
        node1 = GraphTestNode("node1")
        node1.node_type = "source"
        node2 = GraphTestNode("node2")
        node2.node_type = "sink"
        
        graph.add_node(node1)
        graph.add_node(node2)
        
        sources = graph.get_nodes_by_type("source")
        assert len(sources) == 1
        assert sources[0] == node1
    
    def test_get_sources(self):
        """Test getting source nodes (no input connections)"""
        graph = Graph()
        node1 = GraphTestNode("node1")
        node2 = GraphTestNode("node2")
        
        graph.add_node(node1)
        graph.add_node(node2)
        graph.connect("node1", "out", "node2", "in")
        
        sources = graph.get_sources()
        assert len(sources) == 1
        assert sources[0] == node1
    
    def test_get_sinks(self):
        """Test getting sink nodes (no output connections)"""
        graph = Graph()
        node1 = GraphTestNode("node1")
        node2 = GraphTestNode("node2")
        
        graph.add_node(node1)
        graph.add_node(node2)
        graph.connect("node1", "out", "node2", "in")
        
        sinks = graph.get_sinks()
        assert len(sinks) == 1
        assert sinks[0] == node2
    
    def test_to_dict(self):
        """Test graph serialization"""
        graph = Graph()
        node1 = GraphTestNode("node1")
        node1.position = (100, 200)
        node2 = GraphTestNode("node2")
        node2.position = (300, 400)
        
        graph.add_node(node1)
        graph.add_node(node2)
        graph.connect("node1", "out", "node2", "in")
        
        data = graph.to_dict()
        assert "nodes" in data
        assert "connections" in data
        assert len(data["nodes"]) == 2
        assert len(data["connections"]) == 1
    
    def test_from_dict(self):
        """Test graph deserialization"""
        graph = Graph()
        
        node_factory = {"test": GraphTestNode}
        
        data = {
            "nodes": [
                {
                    "id": "node1",
                    "type": "test",
                    "position": [100, 200],
                    "params": {}
                },
                {
                    "id": "node2",
                    "type": "test",
                    "position": [300, 400],
                    "params": {}
                }
            ],
            "connections": [
                {
                    "from_node": "node1",
                    "from_port": "out",
                    "to_node": "node2",
                    "to_port": "in"
                }
            ]
        }
        
        success = graph.from_dict(data, node_factory)
        assert success is True
        assert len(graph.nodes) == 2
        assert len(graph.connections) == 1
        assert "node1" in graph.nodes
        assert "node2" in graph.nodes
    
    def test_clear(self):
        """Test clearing the graph"""
        graph = Graph()
        node1 = GraphTestNode("node1")
        node2 = GraphTestNode("node2")
        
        graph.add_node(node1)
        graph.add_node(node2)
        graph.connect("node1", "out", "node2", "in")
        
        assert len(graph.nodes) == 2
        assert len(graph.connections) == 1
        
        graph.clear()
        
        assert len(graph.nodes) == 0
        assert len(graph.connections) == 0
    
    def test_connection_metadata(self):
        """Test connection metadata"""
        graph = Graph()
        node1 = GraphTestNode("node1")
        node2 = GraphTestNode("node2")
        
        graph.add_node(node1)
        graph.add_node(node2)
        graph.connect("node1", "out", "node2", "in")
        
        # Get metadata
        metadata = graph.get_connection_metadata("node1", "out", "node2", "in")
        assert "bandwidth" in metadata
        assert "latency_ms" in metadata
        
        # Set metadata
        graph.set_connection_metadata("node1", "out", "node2", "in", 
                                      {"bandwidth": 100, "latency_ms": 10})
        metadata = graph.get_connection_metadata("node1", "out", "node2", "in")
        assert metadata["bandwidth"] == 100
        assert metadata["latency_ms"] == 10