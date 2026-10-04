"""
Port - enhanced with data type, larger hit area, and compatibility checking.
"""

from enum import Enum, auto
from typing import Optional, List, Any, Dict
from PySide6.QtCore import QPointF


class PortType(Enum):
    INPUT = "input"
    OUTPUT = "output"


class DataType(Enum):
    """Supported data types for port compatibility checking."""
    BINARY = "binary"
    TEXT = "text"
    AUDIO = "audio"
    IMAGE = "image"
    NUMERIC = "numeric"
    MORSE = "morse"
    HUFFMAN = "huffman"
    BASE64 = "base64"
    HEX = "hex"
    ANY = "any"
    
    @staticmethod
    def is_compatible(source: 'DataType', target: 'DataType') -> bool:
        """Check if two data types are compatible (can be connected)."""
        if source == DataType.ANY or target == DataType.ANY:
            return True
        if source == target:
            return True
        # Text <-> Binary are compatible
        if {source, target} == {DataType.TEXT, DataType.BINARY}:
            return True
        # Numeric is compatible with text/binary
        if source == DataType.NUMERIC and target in (DataType.TEXT, DataType.BINARY):
            return True
        if target == DataType.NUMERIC and source in (DataType.TEXT, DataType.BINARY):
            return True
        return False


class Port:
    """
    Enhanced port with data type, larger hit area, and full compatibility checking.
    
    Hit area: 24x24 px visually, 16px rendered, 28px for hover detection.
    """
    
    HIT_AREA = 28  # px - detection area
    VISUAL_RADIUS = 10  # px - rendered circle radius
    
    def __init__(self, name: str, port_type: PortType, parent_node=None,
                 data_type: DataType = DataType.ANY):
        self.name = name
        self.type = port_type
        self.parent_node = parent_node
        self.connections: List['Port'] = []
        self.position = QPointF(0, 0)  # relative to node
        self.data_type = data_type
        self._is_active = False  # pulsing glow when data flows
        
    def can_connect(self, other: 'Port') -> tuple:
        """
        Check if connection is possible.
        Returns (can_connect: bool, reason: str).
        """
        if self.type == other.type:
            return False, "Cannot connect same port types (input-input or output-output)"
        if self.parent_node == other.parent_node:
            return False, "Cannot connect a node to itself"
        if self.data_type != DataType.ANY and other.data_type != DataType.ANY:
            if not DataType.is_compatible(self.data_type, other.data_type):
                return False, f"Incompatible data types: {self.data_type.value} -> {other.data_type.value}"
        if other in self.connections:
            return False, "Already connected"
        return True, "OK"
    
    def connect(self, other: 'Port') -> tuple:
        """Connect to another port. Returns (success, reason)."""
        can, reason = self.can_connect(other)
        if not can:
            return False, reason
        if other not in self.connections:
            self.connections.append(other)
        if self not in other.connections:
            other.connections.append(self)
        return True, "Connected"
    
    def disconnect(self, other: 'Port'):
        """Disconnect from another port."""
        if other in self.connections:
            self.connections.remove(other)
        if self in other.connections:
            other.connections.remove(self)
    
    def set_active(self, active: bool):
        """Set port activity state for visual feedback."""
        self._is_active = active
    
    @property
    def is_active(self) -> bool:
        return self._is_active
    
    def get_connected_node_ids(self) -> List[str]:
        """Get IDs of all connected nodes."""
        ids = []
        for conn in self.connections:
            if conn.parent_node:
                ids.append(conn.parent_node.node_id)
        return ids
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize port to dictionary."""
        return {
            "name": self.name,
            "type": self.type.value,
            "data_type": self.data_type.value,
            "position": [self.position.x(), self.position.y()]
        }