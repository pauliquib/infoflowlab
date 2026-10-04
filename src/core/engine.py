"""
SimulationEngine - hybrid real-time/step simulation engine with event-driven processing.

Features:
- Real-time mode: QTimer with configurable interval (1-1000ms), smooth packet flow
- Step mode: One step at a time for debugging/education
- Event-driven: Nodes process as soon as they receive a packet
- Configurable speed multiplier (0.1x - 5.0x)
- Packet injection and flow control
"""

from typing import Dict, List, Optional, Set, Callable
from enum import Enum, auto
from PySide6.QtCore import QObject, Signal, QTimer, QElapsedTimer
from src.core.graph import Graph
from src.core.packet import DataPacket
from src.core.node_base import NodeBase, NodeStatus
from src.utils.logger import get_logger
import time
import uuid


class SimulationMode(Enum):
    """Simulation operating modes."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STEP = "step"


class SimulationEngine(QObject):
    """
    Hybrid simulation engine supporting real-time and step modes.
    
    Real-time mode uses QTimer for smooth packet flow.
    Step mode processes one tick at a time for educational purposes.
    Event-driven processing: nodes process packets as they arrive.
    """
    
    # Signals
    simulation_started = Signal()
    simulation_stopped = Signal()
    simulation_paused = Signal()
    mode_changed = Signal(str)  # SimulationMode value
    packet_moved = Signal(str, str, str, str)  # packet_id, from_node, to_node, format
    packet_created = Signal(object)  # DataPacket
    packet_dropped = Signal(object)  # DataPacket
    tick_processed = Signal(int)  # tick number
    error_occurred = Signal(str, str)  # node_id, error_message
    log_message = Signal(str, str)  # category, message
    
    def __init__(self, graph: Graph):
        super().__init__()
        self.graph = graph
        self.logger = get_logger("SimulationEngine")
        self.mode = SimulationMode.IDLE
        self.speed = 1.0  # speed multiplier (0.1 - 5.0)
        self.tick_interval_ms = 100  # base interval in ms
        self.current_tick = 0
        self.max_ticks = 0  # 0 = unlimited
        self.active_packets: List[DataPacket] = []
        self.processed_packets: List[DataPacket] = []
        self.dropped_packets: List[DataPacket] = []
        
        # Timing
        self._timer: Optional[QTimer] = None
        self._elapsed_timer = QElapsedTimer()
        self._simulation_time_ms = 0.0
        self._last_tick_time = 0.0
        
        # Event log for replay
        self.event_log: List[Dict] = []
        self._record_events = False
        
        # Statistics
        self.total_packets_created = 0
        self.total_packets_processed = 0
        self.total_packets_dropped = 0
        self.total_errors = 0
        
        # Connect graph node signals
        self._connect_node_signals()
        
        self.logger.debug("SimulationEngine initialized")
    
    def _connect_node_signals(self):
        """Connect signals from all nodes in the graph."""
        for node in self.graph.nodes.values():
            self._connect_single_node(node)
    
    def register_node(self, node: NodeBase):
        """Register a node added to the graph after engine initialization."""
        self._connect_single_node(node)

    def _connect_single_node(self, node: NodeBase):
        """Connect signals for a single node."""
        node.data_processed.connect(lambda pkt, n=node: self._on_node_processed(n, pkt))
        node.packet_dropped.connect(lambda pkt, n=node: self._on_packet_dropped(n, pkt))
        node.status_changed.connect(lambda status, n=node: self._on_node_status_changed(n, status))
        node.packet_forwarded.connect(self._on_packet_forwarded)

    def _on_packet_forwarded(self, packet_id: str, from_id: str, to_id: str, fmt: str):
        """Relay packet movement to GUI animation layer."""
        self.packet_moved.emit(packet_id, from_id, to_id, fmt)
    
    def _on_node_processed(self, node: NodeBase, packet: DataPacket):
        """Handle node processing completion."""
        self.total_packets_processed += 1
        if self._record_events:
            self.event_log.append({
                "type": "process",
                "tick": self.current_tick,
                "time_ms": self._simulation_time_ms,
                "node_id": node.node_id,
                "packet_id": packet.id
            })
    
    def _on_packet_dropped(self, node: NodeBase, packet: DataPacket):
        """Handle packet drop."""
        self.total_packets_dropped += 1
        self.dropped_packets.append(packet)
        self.packet_dropped.emit(packet)
        self.log_message.emit("warning", f"Packet {packet.id} dropped by {node.name}")
        
        if self._record_events:
            self.event_log.append({
                "type": "drop",
                "tick": self.current_tick,
                "node_id": node.node_id,
                "packet_id": packet.id
            })
    
    def _on_node_status_changed(self, node: NodeBase, status: str):
        """Handle node status change."""
        if status == NodeStatus.ERROR.value:
            self.total_errors += 1
            self.error_occurred.emit(node.node_id, f"Error in {node.name}")
    
    def start(self):
        """Start simulation in real-time mode."""
        if self.mode == SimulationMode.RUNNING:
            self.logger.warning("Start called but simulation already running")
            return
        
        self.logger.info(f"Starting simulation (speed={self.speed}x, interval={self.tick_interval_ms}ms)")
        self.mode = SimulationMode.RUNNING
        self._simulation_time_ms = 0.0
        self._elapsed_timer.start()
        
        # Start timer for real-time processing
        if self._timer is None:
            self._timer = QTimer(self)
            self._timer.timeout.connect(self._on_timer_tick)
        
        interval = max(1, int(self.tick_interval_ms / max(0.1, self.speed)))
        self._timer.start(interval)
        
        self.simulation_started.emit()
        self.mode_changed.emit(self.mode.value)
        self.log_message.emit("info", "Simulation started")
    
    def stop(self):
        """Stop simulation."""
        self.logger.info(f"Stopping simulation at tick {self.current_tick}")
        if self._timer:
            self._timer.stop()
        
        self.mode = SimulationMode.IDLE
        self.current_tick = 0
        self.simulation_stopped.emit()
        self.mode_changed.emit(self.mode.value)
        self.log_message.emit("info", "Simulation stopped")
    
    def pause(self):
        """Pause simulation."""
        if self.mode != SimulationMode.RUNNING:
            self.logger.warning("Pause called but simulation not running")
            return
        
        self.logger.info(f"Pausing simulation at tick {self.current_tick}")
        if self._timer:
            self._timer.stop()
        
        self.mode = SimulationMode.PAUSED
        self.simulation_paused.emit()
        self.mode_changed.emit(self.mode.value)
        self.log_message.emit("info", "Simulation paused")
    
    def resume(self):
        """Resume from paused state."""
        if self.mode != SimulationMode.PAUSED:
            self.logger.warning("Resume called but simulation not paused")
            return
        
        self.logger.info(f"Resuming simulation at tick {self.current_tick}")
        self.mode = SimulationMode.RUNNING
        if not self._elapsed_timer.isValid():
            self._elapsed_timer.start()
        
        interval = max(1, int(self.tick_interval_ms / max(0.1, self.speed)))
        if self._timer:
            self._timer.start(interval)
        
        self.simulation_started.emit()
        self.mode_changed.emit(self.mode.value)
        self.log_message.emit("info", "Simulation resumed")
    
    def step(self):
        """Execute a single simulation step (for step mode)."""
        self.logger.debug(f"Step mode: processing tick {self.current_tick + 1}")
        if self.mode == SimulationMode.IDLE:
            self.mode = SimulationMode.STEP
            self.mode_changed.emit(self.mode.value)
        
        self._process_tick()
        self.tick_processed.emit(self.current_tick)
    
    def _on_timer_tick(self):
        """Called by QTimer in real-time mode."""
        if self.mode != SimulationMode.RUNNING:
            return
        
        self._process_tick()
        self.tick_processed.emit(self.current_tick)
        
        # Check max ticks
        if self.max_ticks > 0 and self.current_tick >= self.max_ticks:
            self.stop()
    
    def _process_tick(self):
        """Process one simulation tick."""
        self.current_tick += 1
        tick_start = time.time()
        
        # Update simulation time
        self._simulation_time_ms += self.tick_interval_ms * self.speed
        
        # Process all nodes that have buffered packets
        nodes_processed = 0
        for node in list(self.graph.nodes.values()):
            if node.buffer and node.status == NodeStatus.IDLE:
                packet = node.buffer[0]  # Peek at first packet
                # Find which input port received it
                for port_name, port in node.input_ports.items():
                    if port.connections:
                        # Check if any connected output has this packet
                        for conn in port.connections:
                            if conn.parent_node:
                                # Process the packet
                                node.receive_input(packet, port_name)
                                if node.buffer:
                                    node.buffer.popleft()  # Remove processed packet
                                nodes_processed += 1
                                break
                    break
        
        # Process source nodes (generate packets)
        sources_processed = 0
        for node in self.graph.get_sources():
            if node.status == NodeStatus.IDLE and not node.input_ports:
                # Source node - generate a packet
                pkt = DataPacket(
                    id=f"pkt_{uuid.uuid4().hex[:8]}",
                    payload=b"",
                    source_format="text"
                )
                self.inject_packet(node.node_id, pkt)
                sources_processed += 1
        
        # Log tick details at debug level
        tick_time = (time.time() - tick_start) * 1000
        self.logger.debug(
            f"Tick {self.current_tick} processed: "
            f"{nodes_processed} nodes, {sources_processed} sources, "
            f"{tick_time:.2f}ms"
        )
        
        # Record event
        if self._record_events:
            self.event_log.append({
                "type": "tick",
                "tick": self.current_tick,
                "time_ms": self._simulation_time_ms,
                "active_packets": len(self.active_packets)
            })
    
    def inject_packet(self, node_id: str, packet: DataPacket):
        """
        Inject a packet into a specific node.
        
        For source nodes (no inputs), calls process directly.
        For other nodes, sends to the first input port.
        """
        node = self.graph.get_node(node_id)
        if not node:
            error_msg = f"Node {node_id} not found for injection"
            self.logger.error(error_msg)
            self.log_message.emit("error", error_msg)
            return
        
        self.logger.debug(f"Injecting packet {packet.id} into node {node.name}")
        self.total_packets_created += 1
        self.active_packets.append(packet)
        self.packet_created.emit(packet)
        
        if not node.input_ports:
            # Source node - process through standard pipeline
            node._do_process(packet, "auto")
        elif node.input_ports:
            # Send to first input port
            first_input = list(node.input_ports.keys())[0]
            node.receive_input(packet, first_input)
        
        if self._record_events:
            self.event_log.append({
                "type": "inject",
                "tick": self.current_tick,
                "node_id": node_id,
                "packet_id": packet.id
            })
    
    def set_speed(self, speed: float):
        """Set simulation speed multiplier (0.1 - 5.0)."""
        self.speed = max(0.1, min(5.0, speed))
        self.logger.debug(f"Speed changed to {self.speed}x")
        
        # Update timer interval if running
        if self._timer and self._timer.isActive():
            interval = max(1, int(self.tick_interval_ms / max(0.1, self.speed)))
            self._timer.setInterval(interval)
        
        self.log_message.emit("info", f"Speed set to {self.speed}x")
    
    def set_tick_interval(self, interval_ms: int):
        """Set base tick interval in milliseconds (1-1000)."""
        self.tick_interval_ms = max(1, min(1000, interval_ms))
        
        if self._timer and self._timer.isActive():
            interval = max(1, int(self.tick_interval_ms / max(0.1, self.speed)))
            self._timer.setInterval(interval)
    
    def reset(self):
        """Reset simulation state."""
        self.logger.info("Resetting simulation state")
        self.stop()
        self.current_tick = 0
        self._simulation_time_ms = 0.0
        self.active_packets.clear()
        self.processed_packets.clear()
        self.dropped_packets.clear()
        self.event_log.clear()
        self.total_packets_created = 0
        self.total_packets_processed = 0
        self.total_packets_dropped = 0
        self.total_errors = 0
        
        # Reset all nodes
        for node in self.graph.nodes.values():
            node.reset()
        
        self.log_message.emit("info", "Simulation reset")
    
    def start_recording(self):
        """Start recording event log for replay."""
        self._record_events = True
        self.event_log.clear()
    
    def stop_recording(self):
        """Stop recording event log."""
        self._record_events = False
    
    def get_statistics(self) -> Dict:
        """Get simulation statistics."""
        return {
            "mode": self.mode.value,
            "speed": self.speed,
            "tick_interval_ms": self.tick_interval_ms,
            "current_tick": self.current_tick,
            "simulation_time_ms": self._simulation_time_ms,
            "total_packets_created": self.total_packets_created,
            "total_packets_processed": self.total_packets_processed,
            "total_packets_dropped": self.total_packets_dropped,
            "total_errors": self.total_errors,
            "active_packets": len(self.active_packets),
            "processed_packets": len(self.processed_packets),
            "dropped_packets": len(self.dropped_packets),
            "node_count": len(self.graph.nodes),
            "connection_count": len(self.graph.connections)
        }
    
    def to_dict(self) -> Dict:
        """Serialize engine state to dictionary."""
        return {
            "config": {
                "speed": self.speed,
                "tick_interval_ms": self.tick_interval_ms,
                "max_ticks": self.max_ticks
            },
            "statistics": self.get_statistics(),
            "graph": self.graph.to_dict()
        }