"""
Tests for SimulationEngine
"""

import pytest
from src.core.engine import SimulationEngine, SimulationMode
from src.core.graph import Graph
from src.core.node_base import NodeBase
from src.core.packet import DataPacket

pytestmark = pytest.mark.usefixtures("qapp")


class SimpleNode(NodeBase):
    """Simple test node"""
    def __init__(self, node_id: str):
        super().__init__(node_id, "test", "Simple Node")
        self.add_input("in")
        self.add_output("out")
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        # Return modified packet
        result = DataPacket(
            id=f"processed_{packet.id}",
            payload=packet.payload,
            source_format=packet.source_format
        )
        result.add_step(self.name, len(packet.payload), len(result.payload), "Processed")
        return result


class SourceNode(NodeBase):
    """Source node that generates packets"""
    def __init__(self, node_id: str):
        super().__init__(node_id, "source", "Source")
        self.add_output("out")
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        # Generate new packet
        pkt = DataPacket(
            id=f"gen_{packet.id if packet else 'new'}",
            payload=b"test_data",
            source_format="text"
        )
        return pkt


class TestSimulationEngine:
    """Test SimulationEngine functionality"""

    def test_engine_initialization(self):
        """Test engine initialization"""
        graph = Graph()
        engine = SimulationEngine(graph)
        assert engine.mode == SimulationMode.IDLE
        assert engine.speed == 1.0
        assert engine.current_tick == 0
    
    def test_start_stop(self):
        """Test starting and stopping simulation"""
        graph = Graph()
        engine = SimulationEngine(graph)
        
        engine.start()
        assert engine.mode == SimulationMode.RUNNING
        
        engine.stop()
        assert engine.mode == SimulationMode.IDLE
        assert engine.current_tick == 0
    
    def test_pause_resume(self):
        """Test pausing and resuming simulation"""
        graph = Graph()
        engine = SimulationEngine(graph)
        
        engine.start()
        assert engine.mode == SimulationMode.RUNNING
        
        engine.pause()
        assert engine.mode == SimulationMode.PAUSED
        
        engine.resume()
        assert engine.mode == SimulationMode.RUNNING
    
    def test_step_mode(self):
        """Test step-by-step execution"""
        graph = Graph()
        engine = SimulationEngine(graph)
        
        engine.step()
        assert engine.current_tick == 1
        assert engine.mode == SimulationMode.STEP
        
        engine.step()
        assert engine.current_tick == 2
    
    def test_inject_packet(self):
        """Test packet injection"""
        graph = Graph()
        engine = SimulationEngine(graph)
        
        node = SourceNode("source1")
        graph.add_node(node)
        
        pkt = DataPacket(id="test_pkt", payload=b"hello", source_format="text")
        engine.inject_packet("source1", pkt)
        
        assert engine.total_packets_created == 1
        assert len(engine.active_packets) == 1
    
    def test_speed_control(self):
        """Test speed multiplier"""
        graph = Graph()
        engine = SimulationEngine(graph)
        
        engine.set_speed(2.0)
        assert engine.speed == 2.0
        
        engine.set_speed(0.5)
        assert engine.speed == 0.5
        
        # Test clamping
        engine.set_speed(10.0)
        assert engine.speed == 5.0  # Max
        
        engine.set_speed(0.01)
        assert engine.speed == 0.1  # Min
    
    def test_tick_interval(self):
        """Test tick interval setting"""
        graph = Graph()
        engine = SimulationEngine(graph)
        
        engine.set_tick_interval(200)
        assert engine.tick_interval_ms == 200
        
        # Test clamping
        engine.set_tick_interval(2000)
        assert engine.tick_interval_ms == 1000  # Max
        
        engine.set_tick_interval(0)
        assert engine.tick_interval_ms == 1  # Min
    
    def test_reset(self):
        """Test simulation reset"""
        graph = Graph()
        engine = SimulationEngine(graph)
        
        node = SourceNode("source1")
        graph.add_node(node)
        engine.register_node(node)
        
        # Run a bit
        engine.start()
        engine.step()
        assert engine.current_tick >= 1
        engine.stop()
        
        engine.reset()
        assert engine.current_tick == 0
        assert engine.mode == SimulationMode.IDLE
        assert len(engine.active_packets) == 0
    
    def test_statistics(self):
        """Test statistics gathering"""
        graph = Graph()
        engine = SimulationEngine(graph)
        
        stats = engine.get_statistics()
        assert "mode" in stats
        assert "speed" in stats
        assert "current_tick" in stats
        assert "total_packets_created" in stats
        assert stats["mode"] == "idle"
        assert stats["speed"] == 1.0
    
    def test_node_processing_chain(self):
        """Test processing through a chain of nodes"""
        graph = Graph()
        engine = SimulationEngine(graph)
        
        source = SourceNode("source")
        processor = SimpleNode("processor")
        
        graph.add_node(source)
        graph.add_node(processor)
        engine.register_node(source)
        engine.register_node(processor)
        graph.connect("source", "out", "processor", "in")
        
        # Inject packet
        pkt = DataPacket(id="chain_test", payload=b"data", source_format="text")
        engine.inject_packet("source", pkt)
        
        # Process one tick
        engine.step()
        
        # Check that packet was processed
        assert engine.total_packets_processed > 0
    
    def test_event_recording(self):
        """Test event recording for replay"""
        graph = Graph()
        engine = SimulationEngine(graph)
        
        engine.start_recording()
        engine.step()
        engine.step()
        engine.stop_recording()
        
        assert len(engine.event_log) > 0
        # Should have at least 2 tick events
        tick_events = [e for e in engine.event_log if e["type"] == "tick"]
        assert len(tick_events) >= 2
    
    def test_get_sources(self):
        """Test getting source nodes from engine"""
        graph = Graph()
        engine = SimulationEngine(graph)
        
        source1 = SourceNode("source1")
        source2 = SourceNode("source2")
        processor = SimpleNode("processor")
        
        graph.add_node(source1)
        graph.add_node(source2)
        graph.add_node(processor)
        
        sources = [n for n in graph.get_sources() if not n.input_ports]
        assert len(sources) == 2
    
    def test_get_sinks(self):
        """Test getting sink nodes from graph"""
        graph = Graph()
        engine = SimulationEngine(graph)
        
        source = SourceNode("source")
        processor1 = SimpleNode("processor1")
        processor2 = SimpleNode("processor2")
        sink = SimpleNode("sink")
        
        graph.add_node(source)
        graph.add_node(processor1)
        graph.add_node(processor2)
        graph.add_node(sink)
        
        graph.connect("source", "out", "processor1", "in")
        graph.connect("processor1", "out", "processor2", "in")
        graph.connect("processor2", "out", "sink", "in")
        
        sinks = graph.get_sinks()
        assert len(sinks) == 1