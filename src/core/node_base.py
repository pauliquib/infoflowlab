"""
NodeBase - enhanced with processing delay, throughput limit, parameter schema,
buffer management with maxsize, and introspection for dynamic UI generation.
"""

from typing import List, Dict, Optional, Any, Callable
from collections import deque
from enum import Enum, auto
from PySide6.QtCore import QObject, Signal, QTimer
from src.core.port import Port, PortType, DataType
from src.core.packet import DataPacket


class NodeStatus(Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    ERROR = "error"
    DONE = "done"
    BYPASSED = "bypassed"


class ParamType(Enum):
    """Supported parameter types for schema-driven UI generation."""
    INT = "int"
    FLOAT = "float"
    STR = "str"
    BOOL = "bool"
    CHOICE = "choice"
    TEXT = "text"
    COLOR = "color"
    RANGE = "range"
    FILE = "file"


class NodeBase(QObject):
    """
    Enhanced base node with:
    - processing_delay (ms) – simulates node latency
    - throughput_limit (bps) – simulates bandwidth constraints
    - Buffer as collections.deque with maxsize for overflow/drop simulation
    - Introspective get_param_schema() for dynamic UI generation
    - status LED (idle/processing/error/done/bypassed)
    """
    
    # Signals for GUI
    data_processed = Signal(object)  # DataPacket
    status_changed = Signal(str)     # NodeStatus value
    param_changed = Signal(str, object)  # key, value
    packet_dropped = Signal(object)  # DataPacket that was dropped
    packet_forwarded = Signal(str, str, str, str)  # packet_id, from_id, to_id, format
    
    def __init__(self, node_id: str, node_type: str, name: str, 
                 category: str = "general"):
        super().__init__()
        self.node_id = node_id
        self.node_type = node_type
        self.name = name
        self.category = category  # "sources", "encoders", "decoders", "compressors", etc.
        self.position = (0, 0)
        self.input_ports: Dict[str, Port] = {}
        self.output_ports: Dict[str, Port] = {}
        self.params: Dict[str, Any] = {}
        self.status = NodeStatus.IDLE
        
        # Enhanced buffer with maxsize for overflow simulation
        self.buffer: deque = deque(maxlen=100)
        self.buffer_maxsize = 100
        self.packets_processed = 0
        self.packets_dropped = 0
        self.total_processing_time_ms = 0.0
        self.average_latency_ms = 0.0
        
        # Performance simulation
        self._processing_delay: int = 0  # ms
        self._throughput_limit: int = 0  # bps (0 = unlimited)
        self._processing_timer: Optional[QTimer] = None
        self._pending_packet: Optional[DataPacket] = None
        self._pending_input_port: str = ""
        
        # Bypass mode
        self._bypass = False
    
    def add_input(self, name: str, data_type: DataType = DataType.ANY):
        """Add an input port with optional data type."""
        self.input_ports[name] = Port(name, PortType.INPUT, self, data_type)
    
    def add_output(self, name: str, data_type: DataType = DataType.ANY):
        """Add an output port with optional data type."""
        self.output_ports[name] = Port(name, PortType.OUTPUT, self, data_type)
    
    def get_param_schema(self) -> Dict[str, Dict[str, Any]]:
        """
        Return parameter schema for dynamic UI generation.
        
        Schema format:
        {
            "param_name": {
                "type": ParamType,
                "label": str,
                "default": Any,
                "min": Optional[float],
                "max": Optional[float],
                "step": Optional[float],
                "choices": Optional[List[str]],
                "description": str,
                "unit": str,
                "category": str  # "basic", "advanced", "statistics"
            }
        }
        
        Override in subclasses to define custom parameters.
        """
        return {
            "processing_delay": {
                "type": ParamType.INT,
                "label": "Processing Delay",
                "default": 0,
                "min": 0,
                "max": 10000,
                "step": 1,
                "description": "Simulated processing latency in milliseconds",
                "unit": "ms",
                "category": "advanced"
            },
            "throughput_limit": {
                "type": ParamType.INT,
                "label": "Throughput Limit",
                "default": 0,
                "min": 0,
                "max": 1000000000,
                "step": 1000,
                "description": "Maximum throughput in bits per second (0 = unlimited)",
                "unit": "bps",
                "category": "advanced"
            },
            "bypass": {
                "type": ParamType.BOOL,
                "label": "Bypass Mode",
                "default": False,
                "description": "When enabled, packets pass through without processing",
                "category": "basic"
            }
        }
    
    def can_process(self, packet: DataPacket) -> bool:
        """
        Validate packet format before processing.
        Override in subclasses for custom validation.
        """
        return True
    
    def process(self, packet: DataPacket, input_port: str) -> Optional[DataPacket]:
        """
        Process a packet. Override in subclasses.
        
        Args:
            packet: The incoming data packet
            input_port: Name of the input port that received the packet
            
        Returns:
            Processed packet or None if packet is consumed/dropped
        """
        raise NotImplementedError("Subclasses must implement process()")
    
    def _do_process(self, packet: DataPacket, input_port: str):
        """Internal processing with delay simulation."""
        if self._bypass:
            # Bypass mode: pass through without processing
            self.send_output(packet, list(self.output_ports.keys())[0])
            self.status = NodeStatus.IDLE
            self.status_changed.emit(self.status.value)
            return
        
        try:
            import time
            start = time.time()
            
            result = self.process(packet, input_port)
            
            elapsed_ms = (time.time() - start) * 1000
            self.packets_processed += 1
            self.total_processing_time_ms += elapsed_ms
            self.average_latency_ms = self.total_processing_time_ms / max(1, self.packets_processed)
            
            if result:
                # Update packet metadata
                result.record_latency(max(elapsed_ms, self._processing_delay))
                result.add_step(
                    node_name=self.name,
                    operation=self.node_type,
                    in_size=len(packet.payload),
                    out_size=len(result.payload),
                    processing_time_ms=elapsed_ms,
                    details=f"processed by {self.name}"
                )
                self.data_processed.emit(result)
                
                # Send to output ports
                if self.output_ports:
                    self.send_output(result, list(self.output_ports.keys())[0])
            
            self.status = NodeStatus.IDLE
            self.status_changed.emit(self.status.value)
            
        except Exception as e:
            self.status = NodeStatus.ERROR
            self.status_changed.emit(self.status.value)
            import traceback
            traceback.print_exc()
    
    def _forward_packet(self, packet: DataPacket, conn, output_port: str):
        """Deliver packet to a connected node and notify listeners."""
        if not conn.parent_node:
            return
        conn.parent_node.receive_input(packet, conn.name)
        self.packet_forwarded.emit(
            packet.id, self.node_id, conn.parent_node.node_id, packet.source_format
        )

    def send_output(self, packet: DataPacket, output_port: str):
        """Send packet to all connected nodes via the specified output port."""
        if self._bypass:
            # In bypass mode, send to first connected input
            for port in self.output_ports.values():
                for conn in port.connections:
                    if conn.parent_node:
                        self._forward_packet(packet, conn, port.name)
                        return
        
        port = self.output_ports.get(output_port)
        if port:
            # Apply throughput limit
            if self._throughput_limit > 0:
                import time
                bits = packet.size_bits
                delay = (bits / self._throughput_limit) * 1000  # ms
                time.sleep(delay / 1000)  # Non-blocking in real app would use timer
            
            for conn in port.connections:
                self._forward_packet(packet, conn, output_port)
    
    def receive_input(self, packet: DataPacket, input_port: str):
        """Receive and queue a packet. Process immediately if possible."""
        if not self.can_process(packet):
            self.packets_dropped += 1
            self.packet_dropped.emit(packet)
            return
        
        # Add to buffer
        self.buffer.append(packet)
        
        if self.status == NodeStatus.IDLE or self.status == NodeStatus.DONE:
            self.status = NodeStatus.PROCESSING
            self.status_changed.emit(self.status.value)
            
            if self._processing_delay > 0:
                # Schedule delayed processing
                self._pending_packet = packet
                self._pending_input_port = input_port
                if self._processing_timer is None:
                    self._processing_timer = QTimer(self)
                    self._processing_timer.setSingleShot(True)
                    self._processing_timer.timeout.connect(self._on_delayed_process)
                self._processing_timer.start(self._processing_delay)
            else:
                # Process immediately
                self._do_process(packet, input_port)
    
    def _on_delayed_process(self):
        """Called after processing delay timer fires."""
        if self._pending_packet:
            self._do_process(self._pending_packet, self._pending_input_port)
            self._pending_packet = None
            self._pending_input_port = ""
    
    def set_param(self, key: str, value):
        """Set a parameter and emit change signal."""
        old = self.params.get(key)
        self.params[key] = value
        
        # Handle special meta-parameters
        if key == "processing_delay":
            self._processing_delay = int(value)
        elif key == "throughput_limit":
            self._throughput_limit = int(value)
        elif key == "bypass":
            self._bypass = bool(value)
            self.status = NodeStatus.BYPASSED if self._bypass else NodeStatus.IDLE
            self.status_changed.emit(self.status.value)
        
        if old != value:
            self.param_changed.emit(key, value)
    
    def get_param(self, key: str, default=None):
        """Get a parameter value."""
        return self.params.get(key, default)
    
    def reset(self):
        """Reset node statistics."""
        self.buffer.clear()
        self.packets_processed = 0
        self.packets_dropped = 0
        self.total_processing_time_ms = 0.0
        self.average_latency_ms = 0.0
        self.status = NodeStatus.IDLE
        self.status_changed.emit(self.status.value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize node to dictionary."""
        from src.nodes.registry import get_sidebar_key
        type_key = get_sidebar_key(type(self))
        return {
            "id": self.node_id,
            "type": self.node_type,
            "class_name": type(self).__name__,
            "type_key": type_key,
            "name": self.name,
            "category": self.category,
            "position": list(self.position),
            "params": {k: v for k, v in self.params.items() 
                      if k not in ("processing_delay", "throughput_limit", "bypass")},
            "config": {
                "processing_delay": self._processing_delay,
                "throughput_limit": self._throughput_limit,
                "bypass": self._bypass,
                "buffer_maxsize": self.buffer_maxsize
            },
            "input_ports": {name: port.to_dict() for name, port in self.input_ports.items()},
            "output_ports": {name: port.to_dict() for name, port in self.output_ports.items()}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], node_id: Optional[str] = None) -> 'NodeBase':
        """Deserialize node from dictionary. Subclasses should override to parse params."""
        nid = node_id or data.get("id", "unknown")
        # Factory method - subclasses register themselves
        node = cls(nid)
        node.position = tuple(data.get("position", [0, 0]))
        for k, v in data.get("params", {}).items():
            node.set_param(k, v)
        for k, v in data.get("config", {}).items():
            node.set_param(k, v)
        return node