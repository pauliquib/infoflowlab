"""
Advanced Connection Management & Routing System
================================================

NOTE: WireCutter is integrated into ConnectionManager (src/gui/connection_manager.py).
Reroute points are stored in graph connection metadata and rendered by ConnectionItem.
Full AdvancedConnectionState (smart snapping, reroute nodes) remains available here
for future extension.

Features:
1. Multi-Branching & Port Capacity System (1-to-N broadcasting)
2. Type Safety & Smart Snapping with visual feedback
3. Reroute Nodes for wire organization
4. Wire Cutting (Alt+Click detachment)
5. Scalable state management

Architecture:
- PortCapacity: Manages max_connections and auto-replacement
- ConnectionRouter: Handles 1-to-N array management
- RerouteNode: Invisible pass-through anchor points
- SmartSnapping: Type-aware port highlighting
- WireCutter: Quick-action detachment system
"""

from typing import Dict, List, Tuple, Optional, Set, Any, Union
from enum import Enum, auto
from dataclasses import dataclass, field
from PySide6.QtCore import QPointF, QTimer, Signal, QObject
from PySide6.QtGui import QColor, QPen, QBrush
import math

from src.core.port import Port, PortType, DataType
from src.core.graph import Graph


# ============================================================
# ENUMS & DATA STRUCTURES
# ============================================================

class ConnectionCapability(Enum):
    """Port connection capabilities."""
    SINGLE = "single"           # max_connections = 1, auto-replace
    MULTIPLE = "multiple"       # max_connections > 1, broadcast
    UNLIMITED = "unlimited"     # max_connections = 0 or None


class HighlightMode(Enum):
    """Visual highlighting modes for smart snapping."""
    NONE = "none"
    VALID = "valid"             # Green glow - compatible type
    INVALID = "invalid"         # Red glow - incompatible type
    DIM = "dim"                 # Grayed out - wrong direction or full
    CAPACITY_WARNING = "capacity_warning"  # Yellow - would replace existing


@dataclass
class ConnectionSplineData:
    """Stores Bezier curve control points for a connection."""
    start_point: QPointF
    end_point: QPointF
    control_point_1: QPointF
    control_point_2: QPointF
    reroute_points: List[QPointF] = field(default_factory=list)  # Anchor points
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "start": [self.start_point.x(), self.start_point.y()],
            "end": [self.end_point.x(), self.end_point.y()],
            "cp1": [self.control_point_1.x(), self.control_point_1.y()],
            "cp2": [self.control_point_2.x(), self.control_point_2.y()],
            "reroute": [[p.x(), p.y()] for p in self.reroute_points]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConnectionSplineData':
        """Deserialize from dictionary."""
        return cls(
            start_point=QPointF(*data["start"]),
            end_point=QPointF(*data["end"]),
            control_point_1=QPointF(*data["cp1"]),
            control_point_2=QPointF(*data["cp2"]),
            reroute_points=[QPointF(*p) for p in data.get("reroute", [])]
        )


@dataclass
class RerouteNodeData:
    """
    Reroute Node - invisible pass-through anchor for wire organization.
    
    Acts as a visual bridge, completely invisible to data logic.
    Data flows through as if the reroute node doesn't exist.
    """
    id: str
    position: QPointF
    in_link: Optional[Tuple[str, str, str, str]] = None  # (from_node, from_port, to_node, to_port)
    out_link: Optional[Tuple[str, str, str, str]] = None
    control_point_offset: float = 50.0  # Bezier curve smoothness
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "position": [self.position.x(), self.position.y()],
            "in_link": self.in_link,
            "out_link": self.out_link,
            "control_point_offset": self.control_point_offset
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RerouteNodeData':
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            position=QPointF(*data["position"]),
            in_link=tuple(data["in_link"]) if data.get("in_link") else None,
            out_link=tuple(data["out_link"]) if data.get("out_link") else None,
            control_point_offset=data.get("control_point_offset", 50.0)
        )


@dataclass
class AdvancedConnection:
    """
    Enhanced connection with spline data and reroute support.
    
    Replaces simple tuple (from_node, from_port, to_node, to_port) with
    rich object containing all routing information.
    """
    id: str
    source_port_id: str  # Format: "{node_id}:{port_name}"
    target_port_id: str
    spline_data: ConnectionSplineData
    reroute_nodes: List[RerouteNodeData] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "source_port_id": self.source_port_id,
            "target_port_id": self.target_port_id,
            "spline_data": self.spline_data.to_dict(),
            "reroute_nodes": [rn.to_dict() for rn in self.reroute_nodes],
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AdvancedConnection':
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            source_port_id=data["source_port_id"],
            target_port_id=data["target_port_id"],
            spline_data=ConnectionSplineData.from_dict(data["spline_data"]),
            reroute_nodes=[RerouteNodeData.from_dict(rn) for rn in data.get("reroute_nodes", [])],
            metadata=data.get("metadata", {})
        )


# ============================================================
# PORT CAPACITY MANAGER
# ============================================================

class PortCapacityManager:
    """
    Manages port capacity limits and auto-replacement logic.
    
    Responsibilities:
    - Enforce max_connections limits
    - Handle auto-replacement when capacity is reached
    - Validate connection attempts against capacity
    """
    
    def __init__(self, graph: Graph):
        self.graph = graph
        self._capacity_cache: Dict[str, int] = {}  # port_id -> current_count
    
    def get_port_id(self, node_id: str, port_name: str, port_type: str) -> str:
        """Generate unique port identifier."""
        return f"{node_id}:{port_type}:{port_name}"
    
    def get_current_connection_count(self, port_id: str) -> int:
        """Get current number of connections on a port."""
        return self._capacity_cache.get(port_id, 0)
    
    def can_accept_connection(self, port: Port, max_connections: Optional[int] = None) -> Tuple[bool, str, ConnectionCapability]:
        """
        Check if port can accept a new connection.
        
        Args:
            port: Port to check
            max_connections: Override max connections (None = use port default)
            
        Returns:
            (can_accept, reason, capability)
        """
        # Determine capability
        if max_connections is None:
            max_connections = getattr(port, 'max_connections', 1)
        
        if max_connections == 0 or max_connections is None:
            capability = ConnectionCapability.UNLIMITED
        elif max_connections == 1:
            capability = ConnectionCapability.SINGLE
        else:
            capability = ConnectionCapability.MULTIPLE
        
        # Get current count
        port_id = self.get_port_id(
            port.parent_node.node_id if port.parent_node else "unknown",
            port.name,
            port.type.value
        )
        current_count = self.get_current_connection_count(port_id)
        
        # Check capacity
        if capability == ConnectionCapability.UNLIMITED:
            return True, "Unlimited connections allowed", capability
        elif capability == ConnectionCapability.SINGLE:
            if current_count == 0:
                return True, "Available (single connection)", capability
            else:
                return True, "Will replace existing connection", capability
        else:  # MULTIPLE
            if current_count < max_connections:
                return True, f"Available ({current_count}/{max_connections})", capability
            else:
                return False, f"Maximum connections reached ({max_connections})", capability
    
    def auto_replace_connection(self, port: Port, 
                                old_connection: Optional[Tuple[str, str, str, str]] = None) -> bool:
        """
        Auto-replace existing connection when max_connections = 1.
        
        Args:
            port: Port that needs replacement
            old_connection: Existing connection to remove (None = auto-detect)
            
        Returns:
            True if replacement successful
        """
        # Find existing connection if not provided
        if old_connection is None:
            port_id = self.get_port_id(
                port.parent_node.node_id if port.parent_node else "unknown",
                port.name,
                port.type.value
            )
            
            # Search for existing connection
            for conn in self.graph.connections:
                if port.type == PortType.INPUT:
                    # Check if this is the target
                    if conn[2] == port.parent_node.node_id and conn[3] == port.name:
                        old_connection = conn
                        break
                else:
                    # Check if this is the source
                    if conn[0] == port.parent_node.node_id and conn[1] == port.name:
                        old_connection = conn
                        break
        
        if old_connection:
            # Disconnect old connection
            from_node_id, from_port, to_node_id, to_port = old_connection
            self.graph.disconnect(from_node_id, from_port, to_node_id, to_port)
            
            # Update capacity cache
            from_port_id = self.get_port_id(from_node_id, from_port, "output")
            to_port_id = self.get_port_id(to_node_id, to_port, "input")
            self._capacity_cache[from_port_id] = max(0, self._capacity_cache.get(from_port_id, 0) - 1)
            self._capacity_cache[to_port_id] = max(0, self._capacity_cache.get(to_port_id, 0) - 1)
            
            return True
        
        return False
    
    def register_connection(self, source_port: Port, target_port: Port):
        """Register new connection in capacity cache."""
        source_port_id = self.get_port_id(
            source_port.parent_node.node_id,
            source_port.name,
            "output"
        )
        target_port_id = self.get_port_id(
            target_port.parent_node.node_id,
            target_port.name,
            "input"
        )
        
        self._capacity_cache[source_port_id] = self._capacity_cache.get(source_port_id, 0) + 1
        self._capacity_cache[target_port_id] = self._capacity_cache.get(target_port_id, 0) + 1
    
    def unregister_connection(self, source_port: Port, target_port: Port):
        """Unregister connection from capacity cache."""
        source_port_id = self.get_port_id(
            source_port.parent_node.node_id,
            source_port.name,
            "output"
        )
        target_port_id = self.get_port_id(
            target_port.parent_node.node_id,
            target_port.name,
            "input"
        )
        
        self._capacity_cache[source_port_id] = max(0, self._capacity_cache.get(source_port_id, 0) - 1)
        self._capacity_cache[target_port_id] = max(0, self._capacity_cache.get(target_port_id, 0) - 1)
    
    def rebuild_cache(self):
        """Rebuild capacity cache from graph connections."""
        self._capacity_cache.clear()
        for from_node_id, from_port, to_node_id, to_port in self.graph.connections:
            from_port_id = self.get_port_id(from_node_id, from_port, "output")
            to_port_id = self.get_port_id(to_node_id, to_port, "input")
            
            self._capacity_cache[from_port_id] = self._capacity_cache.get(from_port_id, 0) + 1
            self._capacity_cache[to_port_id] = self._capacity_cache.get(to_port_id, 0) + 1


# ============================================================
# SMART SNAPPING & VISUAL FEEDBACK
# ============================================================

class SmartSnappingSystem:
    """
    Type-aware port highlighting and visual feedback system.
    
    Features:
    - Highlight only compatible ports during drag
    - Dim incompatible ports/nodes
    - Show capacity warnings
    - Real-time validation feedback
    """
    
    # Visual constants
    VALID_COLOR = QColor("#00FF00")      # Green glow
    INVALID_COLOR = QColor("#FF0000")    # Red glow
    DIM_COLOR = QColor("#555555")        # Grayed out
    WARNING_COLOR = QColor("#FFAA00")    # Orange warning
    HIGHLIGHT_OPACITY = 0.8
    DIM_OPACITY = 0.3
    
    def __init__(self, canvas, connection_manager):
        self.canvas = canvas
        self.connection_manager = connection_manager
        self._highlighted_ports: Set[str] = set()  # port identifiers
        self._dimmed_nodes: Set[str] = set()  # node identifiers
        self._current_highlight_mode: Dict[str, HighlightMode] = {}
    
    def analyze_drop_targets(self, source_port_id: str, source_data_type: DataType,
                            source_port_type: str, cursor_pos: QPointF) -> Dict[str, Any]:
        """
        Analyze all potential drop targets and their compatibility.
        
        Args:
            source_port_id: "node_id:port_name"
            source_data_type: Data type of source port
            source_port_type: "input" or "output"
            cursor_pos: Current cursor position
            
        Returns:
            Dictionary with analysis results
        """
        results = {
            "valid_targets": [],
            "invalid_targets": [],
            "dimmed_nodes": [],
            "capacity_warnings": []
        }
        
        # Iterate all nodes on canvas
        for node_id, node_item in self.canvas._node_items.items():
            # Skip source node
            if node_id == source_port_id.split(":")[0]:
                continue
            
            node_has_valid = False
            node_has_invalid = False
            
            # Check all ports on this node
            all_ports = list(node_item.input_port_items.items()) + \
                       list(node_item.output_port_items.items())
            
            for port_name, port_item in all_ports:
                port_type = port_item.port_type
                port_data_type = port_item.data_type
                
                # Must be opposite type
                if port_type == source_port_type:
                    results["dimmed_nodes"].append(node_id)
                    node_has_invalid = True
                    continue
                
                # Check data type compatibility
                is_type_compatible = self._check_type_compatibility(
                    source_data_type, port_data_type
                )
                
                if not is_type_compatible:
                    results["invalid_targets"].append({
                        "port_id": f"{node_id}:{port_name}",
                        "reason": "Incompatible data type",
                        "node_id": node_id
                    })
                    node_has_invalid = True
                    continue
                
                # Check if already connected (for input ports)
                if port_type == "input":
                    is_connected = self._is_port_connected(node_id, port_name)
                    if is_connected:
                        results["invalid_targets"].append({
                            "port_id": f"{node_id}:{port_name}",
                            "reason": "Already connected",
                            "node_id": node_id
                        })
                        node_has_invalid = True
                        continue
                
                # Valid target!
                results["valid_targets"].append({
                    "port_id": f"{node_id}:{port_name}",
                    "port_item": port_item,
                    "node_id": node_id
                })
                node_has_valid = True
            
            # Node-level classification
            if node_has_valid and not node_has_invalid:
                pass  # Node has valid targets, keep bright
            elif node_has_invalid and not node_has_valid:
                if node_id not in results["dimmed_nodes"]:
                    results["dimmed_nodes"].append(node_id)
        
        return results
    
    def _check_type_compatibility(self, source_type: DataType, 
                                  target_type: DataType) -> bool:
        """Check if two data types are compatible."""
        return DataType.is_compatible(source_type, target_type)
    
    def _is_port_connected(self, node_id: str, port_name: str) -> bool:
        """Check if port already has a connection."""
        for conn in self.connection_manager.graph.connections:
            if conn[2] == node_id and conn[3] == port_name:  # Target
                return True
            if conn[0] == node_id and conn[1] == port_name:  # Source
                return True
        return False
    
    def apply_visual_feedback(self, analysis: Dict[str, Any]):
        """
        Apply visual feedback based on analysis results.
        
        Args:
            analysis: Results from analyze_drop_targets()
        """
        # Clear previous highlights
        self._clear_all_highlights()
        
        # Dim invalid nodes
        for node_id in analysis["dimmed_nodes"]:
            self._dim_node(node_id)
        
        # Highlight valid targets
        for target in analysis["valid_targets"]:
            port_item = target["port_item"]
            self._highlight_port(port_item, HighlightMode.VALID)
        
        # Mark invalid targets
        for target in analysis["invalid_targets"]:
            port_id = target["port_id"]
            node_id, port_name = port_id.split(":")
            node_item = self.canvas._node_items.get(node_id)
            if node_item:
                port_item = node_item.get_port_item(
                    "input" if "input" in port_id else "output",
                    port_name
                )
                if port_item:
                    self._highlight_port(port_item, HighlightMode.INVALID)
    
    def _highlight_port(self, port_item, mode: HighlightMode):
        """Apply highlight to a port."""
        port_id = f"{port_item.parent_node_item.node.node_id}:{port_item.port_name}"
        self._highlighted_ports.add(port_id)
        self._current_highlight_mode[port_id] = mode
        
        if mode == HighlightMode.VALID:
            port_item.setBrush(QBrush(self.VALID_COLOR))
            port_item.setPen(QPen(self.VALID_COLOR, 3))
            port_item.setOpacity(self.HIGHLIGHT_OPACITY)
        elif mode == HighlightMode.INVALID:
            port_item.setBrush(QBrush(self.INVALID_COLOR))
            port_item.setPen(QPen(self.INVALID_COLOR, 3))
            port_item.setOpacity(self.HIGHLIGHT_OPACITY)
        elif mode == HighlightMode.CAPACITY_WARNING:
            port_item.setBrush(QBrush(self.WARNING_COLOR))
            port_item.setPen(QPen(self.WARNING_COLOR, 3))
            port_item.setOpacity(self.HIGHLIGHT_OPACITY)
    
    def _dim_node(self, node_id: str):
        """Dim an entire node."""
        self._dimmed_nodes.add(node_id)
        node_item = self.canvas._node_items.get(node_id)
        if node_item:
            node_item.setOpacity(self.DIM_OPACITY)
    
    def _clear_all_highlights(self):
        """Clear all highlights and restore original appearance."""
        # Restore highlighted ports
        for port_id in self._highlighted_ports:
            parts = port_id.split(":")
            if len(parts) >= 2:
                node_id = parts[0]
                port_name = parts[1]
                node_item = self.canvas._node_items.get(node_id)
                if node_item:
                    port_item = node_item.get_port_item("input", port_name) or \
                               node_item.get_port_item("output", port_name)
                    if port_item:
                        self._restore_port_appearance(port_item)
        
        # Restore dimmed nodes
        for node_id in self._dimmed_nodes:
            node_item = self.canvas._node_items.get(node_id)
            if node_item:
                node_item.setOpacity(1.0)
        
        # Clear tracking
        self._highlighted_ports.clear()
        self._dimmed_nodes.clear()
        self._current_highlight_mode.clear()
    
    def _restore_port_appearance(self, port_item):
        """Restore port to its default appearance."""
        from src.gui.node_item import DATATYPE_COLORS
        color = QColor(DATATYPE_COLORS.get(port_item.data_type, "#E0E0E0"))
        port_item.setBrush(QBrush(color))
        port_item.setPen(QPen(color.darker(150), 2))
        port_item.setOpacity(1.0)


# ============================================================
# REROUTE NODE SYSTEM
# ============================================================

class RerouteNodeManager:
    """
    Manages reroute nodes - invisible pass-through anchors for wire organization.
    
    Key Concepts:
    - Reroute nodes are purely visual, invisible to data logic
    - Data flows through as if reroute doesn't exist
    - Created by double-clicking on a wire
    - Can be dragged to reorganize messy wire bundles
    - Multiple reroute nodes can be chained
    """
    
    def __init__(self, graph: Graph, connection_manager):
        self.graph = graph
        self.connection_manager = connection_manager
        self._reroute_nodes: Dict[str, RerouteNodeData] = {}
        self._next_id = 1
    
    def create_reroute_on_wire(self, connection_id: str, 
                               position: QPointF) -> Optional[RerouteNodeData]:
        """
        Create a reroute node by double-clicking on a wire.
        
        Args:
            connection_id: ID of the connection to insert reroute into
            position: Where to place the reroute node
            
        Returns:
            Created reroute node data, or None if failed
        """
        # Parse connection ID
        parts = connection_id.split(":")
        if len(parts) != 4:
            return None
        
        from_node_id, from_port, to_node_id, to_port = parts
        
        # Create new reroute node
        reroute_id = f"reroute_{self._next_id}"
        self._next_id += 1
        
        reroute = RerouteNodeData(
            id=reroute_id,
            position=position,
            in_link=(from_node_id, from_port, to_node_id, to_port),
            out_link=(from_node_id, from_port, to_node_id, to_port)
        )
        
        self._reroute_nodes[reroute_id] = reroute
        
        # Update connection to use reroute
        self._update_connection_with_reroute(
            from_node_id, from_port, to_node_id, to_port, reroute
        )
        
        return reroute
    
    def _update_connection_with_reroute(self, from_node_id: str, from_port: str,
                                        to_node_id: str, to_port: str,
                                        reroute: RerouteNodeData):
        """
        Update connection routing to pass through reroute node.
        
        This splits one connection into two:
        - Original: from_node -> to_node
        - After: from_node -> reroute -> to_node
        """
        # Remove original connection
        self.graph.disconnect(from_node_id, from_port, to_node_id, to_port)
        
        # Create virtual intermediate port on reroute
        # In a real implementation, this would create temporary port objects
        # For now, we store the routing in the reroute node data
        
        # The reroute node acts as a transparent pass-through
        # Data flow: from_node -> reroute.in_link -> reroute.out_link -> to_node
        # Visually: wire goes from_node -> reroute.position -> to_node
    
    def move_reroute(self, reroute_id: str, new_position: QPointF):
        """
        Move a reroute node to a new position.
        
        Args:
            reroute_id: ID of reroute node to move
            new_position: New scene position
        """
        if reroute_id in self._reroute_nodes:
            self._reroute_nodes[reroute_id].position = new_position
            # Trigger redraw of affected connections
            self._notify_connections_updated()
    
    def delete_reroute(self, reroute_id: str) -> bool:
        """
        Delete a reroute node and restore original connection.
        
        Args:
            reroute_id: ID of reroute node to delete
            
        Returns:
            True if deleted successfully
        """
        if reroute_id not in self._reroute_nodes:
            return False
        
        reroute = self._reroute_nodes[reroute_id]
        
        # Restore original connection
        if reroute.in_link and reroute.out_link:
            from_node_id, from_port, _, _ = reroute.in_link
            _, _, to_node_id, to_port = reroute.out_link
            
            # Reconnect original endpoints
            self.graph.connect(from_node_id, from_port, to_node_id, to_port)
        
        # Remove reroute
        del self._reroute_nodes[reroute_id]
        
        # Trigger redraw
        self._notify_connections_updated()
        
        return True
    
    def get_reroute_at_position(self, position: QPointF, 
                                tolerance: float = 10.0) -> Optional[str]:
        """
        Find reroute node at given position.
        
        Args:
            position: Scene position to check
            tolerance: Distance tolerance in pixels
            
        Returns:
            Reroute node ID if found, None otherwise
        """
        for reroute_id, reroute in self._reroute_nodes.items():
            dist = math.sqrt(
                (reroute.position.x() - position.x()) ** 2 +
                (reroute.position.y() - position.y()) ** 2
            )
            if dist <= tolerance:
                return reroute_id
        return None
    
    def get_reroute_spline_points(self, reroute_id: str) -> Optional[Tuple[QPointF, QPointF, QPointF]]:
        """
        Get spline control points for a reroute node.
        
        Returns:
            (start, control, end) or None if not found
        """
        if reroute_id not in self._reroute_nodes:
            return None
        
        reroute = self._reroute_nodes[reroute_id]
        
        # Get positions from links
        if not reroute.in_link or not reroute.out_link:
            return None
        
        from_node_id, from_port, _, _ = reroute.in_link
        _, _, to_node_id, to_port = reroute.out_link
        
        # Get node items
        from_item = self.connection_manager.canvas.get_node_item(from_node_id)
        to_item = self.connection_manager.canvas.get_node_item(to_node_id)
        
        if not from_item or not to_item:
            return None
        
        # Get port positions
        start = from_item.get_port_scene_pos(from_port, "output")
        end = to_item.get_port_scene_pos(to_port, "input")
        control = reroute.position
        
        return (start, control, end)
    
    def _notify_connections_updated(self):
        """Notify connection manager to redraw affected connections."""
        # In real implementation, this would trigger canvas redraw
        pass
    
    def get_all_reroutes(self) -> List[RerouteNodeData]:
        """Get all reroute nodes."""
        return list(self._reroute_nodes.values())
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize all reroute nodes."""
        return {
            reroute_id: reroute.to_dict()
            for reroute_id, reroute in self._reroute_nodes.items()
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Deserialize reroute nodes from dictionary."""
        self._reroute_nodes.clear()
        for reroute_id, reroute_data in data.items():
            self._reroute_nodes[reroute_id] = RerouteNodeData.from_dict(reroute_data)
            # Update next_id to avoid collisions
            try:
                num = int(reroute_id.split("_")[1])
                self._next_id = max(self._next_id, num + 1)
            except (IndexError, ValueError):
                pass


# ============================================================
# WIRE CUTTER (Alt+Click Detachment)
# ============================================================

class WireCutter:
    """
    Quick-action wire cutting system.
    
    Features:
    - Alt+Click on port: Remove all connections from that port
    - Scissors tool mode: Click on wire to cut it
    - Batch operations for efficiency
    """
    
    def __init__(self, graph: Graph, connection_manager):
        self.graph = graph
        self.connection_manager = connection_manager
        self._scissors_mode = False
    
    def cut_port_connections(self, node_id: str, port_name: str, 
                            port_type: str) -> List[Tuple[str, str, str, str]]:
        """
        Cut all connections from a port (Alt+Click action).
        
        Args:
            node_id: Node ID
            port_name: Port name
            port_type: "input" or "output"
            
        Returns:
            List of removed connections
        """
        removed = []
        
        if port_type == "output":
            # Find all connections from this output port
            connections_to_remove = [
                conn for conn in self.graph.connections
                if conn[0] == node_id and conn[1] == port_name
            ]
        else:
            # Find all connections to this input port
            connections_to_remove = [
                conn for conn in self.graph.connections
                if conn[2] == node_id and conn[3] == port_name
            ]
        
        # Remove all found connections
        for conn in connections_to_remove:
            from_node_id, from_port, to_node_id, to_port = conn
            self.graph.disconnect(from_node_id, from_port, to_node_id, to_port)
            self.connection_manager._unregister_connection(
                from_node_id, from_port, to_node_id, to_port
            )
            removed.append(conn)
        
        # Trigger redraw
        if removed:
            self.connection_manager.canvas._redraw_connections()
        
        return removed
    
    def cut_connection_at_point(self, connection_id: str, 
                                point: QPointF) -> bool:
        """
        Cut a connection at a specific point (scissors tool).
        
        Args:
            connection_id: Connection to cut
            point: Point where cut occurred
            
        Returns:
            True if connection was cut
        """
        # Parse connection ID
        parts = connection_id.split(":")
        if len(parts) != 4:
            return False
        
        from_node_id, from_port, to_node_id, to_port = parts
        
        # Remove connection
        success = self.graph.disconnect(
            from_node_id, from_port, to_node_id, to_port
        )
        
        if success:
            self.connection_manager._unregister_connection(
                from_node_id, from_port, to_node_id, to_port
            )
            self.connection_manager.canvas._redraw_connections()
        
        return success
    
    def toggle_scissors_mode(self, enabled: bool):
        """Toggle scissors tool mode."""
        self._scissors_mode = enabled
        # In real implementation, change cursor to scissors icon
    
    def is_scissors_mode(self) -> bool:
        """Check if scissors mode is active."""
        return self._scissors_mode


# ============================================================
# ADVANCED CONNECTION STATE MANAGER
# ============================================================

class AdvancedConnectionState:
    """
    Central state management for advanced connection system.
    
    This is the single source of truth for all connection-related state,
    replacing scattered state across multiple classes.
    """
    
    def __init__(self, graph: Graph):
        self.graph = graph
        
        # Connection registry with rich data
        self._connections: Dict[str, AdvancedConnection] = {}
        
        # Port capacity management
        self.capacity_manager = PortCapacityManager(graph)
        
        # Reroute node management
        self.reroute_manager = RerouteNodeManager(graph, None)  # connection_manager set later
        
        # Wire cutting
        self.wire_cutter = WireCutter(graph, None)  # connection_manager set later
        
        # Smart snapping
        self.smart_snapping: Optional[SmartSnappingSystem] = None
        
        # Connection ID counter
        self._next_connection_id = 1
    
    def set_managers(self, connection_manager, canvas):
        """Set references to other managers."""
        self.reroute_manager.connection_manager = connection_manager
        self.wire_cutter.connection_manager = connection_manager
        self.smart_snapping = SmartSnappingSystem(canvas, connection_manager)
    
    def create_connection(self, source_port_id: str, target_port_id: str,
                         source_data_type: DataType, target_data_type: DataType,
                         max_connections: Optional[int] = None) -> Tuple[bool, str, Optional[AdvancedConnection]]:
        """
        Create a new advanced connection with full validation.
        
        Args:
            source_port_id: "node_id:port_name"
            target_port_id: "node_id:port_name"
            source_data_type: Data type of source
            target_data_type: Data type of target
            max_connections: Override max connections
            
        Returns:
            (success, message, connection_object)
        """
        # Parse port IDs
        source_parts = source_port_id.split(":")
        target_parts = target_port_id.split(":")
        
        if len(source_parts) != 2 or len(target_parts) != 2:
            return False, "Invalid port ID format", None
        
        source_node_id, source_port_name = source_parts
        target_node_id, target_port_name = target_parts
        
        # Get port objects
        source_node = self.graph.nodes.get(source_node_id)
        target_node = self.graph.nodes.get(target_node_id)
        
        if not source_node or not target_node:
            return False, "Node not found", None
        
        source_port = source_node.output_ports.get(source_port_name)
        target_port = target_node.input_ports.get(target_port_name)
        
        if not source_port or not target_port:
            return False, "Port not found", None
        
        # Check type compatibility
        if not DataType.is_compatible(source_data_type, target_data_type):
            return False, f"Incompatible data types: {source_data_type.value} -> {target_data_type.value}", None
        
        # Check capacity
        can_accept, reason, capability = self.capacity_manager.can_accept_connection(
            target_port, max_connections
        )
        
        if not can_accept:
            return False, reason, None
        
        # Auto-replace if single connection mode
        if capability == ConnectionCapability.SINGLE:
            # Find existing connection
            existing_conn = None
            for conn in self.graph.connections:
                if conn[2] == target_node_id and conn[3] == target_port_name:
                    existing_conn = conn
                    break
            
            if existing_conn:
                # Remove old connection
                self.capacity_manager.auto_replace_connection(target_port, existing_conn)
        
        # Create connection in graph
        success, reason, warning = self.graph.connect(
            source_node_id, source_port_name,
            target_node_id, target_port_name
        )
        
        if not success:
            return False, reason, None
        
        # Create advanced connection object
        conn_id = f"conn_{self._next_connection_id}"
        self._next_connection_id += 1
        
        # Calculate initial spline data
        # (This would be updated by the connection manager)
        spline_data = ConnectionSplineData(
            start_point=QPointF(0, 0),
            end_point=QPointF(100, 100),
            control_point_1=QPointF(50, 0),
            control_point_2=QPointF(50, 100)
        )
        
        advanced_conn = AdvancedConnection(
            id=conn_id,
            source_port_id=source_port_id,
            target_port_id=target_port_id,
            spline_data=spline_data
        )
        
        self._connections[conn_id] = advanced_conn
        
        # Register in capacity manager
        self.capacity_manager.register_connection(source_port, target_port)
        
        return True, "Connected", advanced_conn
    
    def remove_connection(self, connection_id: str) -> bool:
        """
        Remove an advanced connection.
        
        Args:
            connection_id: ID of connection to remove
            
        Returns:
            True if removed successfully
        """
        if connection_id not in self._connections:
            return False
        
        conn = self._connections[connection_id]
        
        # Parse port IDs
        source_parts = conn.source_port_id.split(":")
        target_parts = conn.target_port_id.split(":")
        
        if len(source_parts) != 2 or len(target_parts) != 2:
            return False
        
        source_node_id, source_port_name = source_parts
        target_node_id, target_port_name = target_parts
        
        # Remove from graph
        self.graph.disconnect(
            source_node_id, source_port_name,
            target_node_id, target_port_name
        )
        
        # Unregister from capacity manager
        source_node = self.graph.nodes.get(source_node_id)
        target_node = self.graph.nodes.get(target_node_id)
        
        if source_node and target_node:
            source_port = source_node.output_ports.get(source_port_name)
            target_port = target_node.input_ports.get(target_port_name)
            
            if source_port and target_port:
                self.capacity_manager.unregister_connection(source_port, target_port)
        
        # Remove reroute nodes associated with this connection
        for reroute_id in list(self.reroute_manager._reroute_nodes.keys()):
            reroute = self.reroute_manager._reroute_nodes[reroute_id]
            if reroute.in_link and reroute.out_link:
                if (reroute.in_link[0] == source_node_id and 
                    reroute.out_link[2] == target_node_id):
                    self.reroute_manager.delete_reroute(reroute_id)
        
        # Remove from registry
        del self._connections[connection_id]
        
        return True
    
    def get_connection(self, connection_id: str) -> Optional[AdvancedConnection]:
        """Get connection by ID."""
        return self._connections.get(connection_id)
    
    def get_all_connections(self) -> List[AdvancedConnection]:
        """Get all connections."""
        return list(self._connections.values())
    
    def get_connections_for_node(self, node_id: str) -> List[AdvancedConnection]:
        """Get all connections involving a node."""
        return [
            conn for conn in self._connections.values()
            if conn.source_port_id.startswith(f"{node_id}:") or
               conn.target_port_id.startswith(f"{node_id}:")
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize entire state to dictionary."""
        return {
            "connections": {
                conn_id: conn.to_dict()
                for conn_id, conn in self._connections.items()
            },
            "reroute_nodes": self.reroute_manager.to_dict()
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Deserialize state from dictionary."""
        # Load connections
        self._connections.clear()
        for conn_id, conn_data in data.get("connections", {}).items():
            self._connections[conn_id] = AdvancedConnection.from_dict(conn_data)
        
        # Load reroute nodes
        self.reroute_manager.from_dict(data.get("reroute_nodes", {}))
        
        # Rebuild capacity cache
        self.capacity_manager.rebuild_cache()
    
    def rebuild_from_graph(self):
        """Rebuild state from graph (e.g., after load)."""
        self._connections.clear()
        self.capacity_manager.rebuild_cache()
        
        # Recreate advanced connections from graph
        for idx, (from_node_id, from_port, to_node_id, to_port) in enumerate(self.graph.connections):
            conn_id = f"conn_{idx + 1}"
            
            source_port_id = f"{from_node_id}:{from_port}"
            target_port_id = f"{to_node_id}:{to_port}"
            
            # Get data types
            source_node = self.graph.nodes.get(from_node_id)
            target_node = self.graph.nodes.get(to_node_id)
            
            source_data_type = DataType.ANY
            target_data_type = DataType.ANY
            
            if source_node and from_port in source_node.output_ports:
                source_data_type = source_node.output_ports[from_port].data_type
            if target_node and to_port in target_node.input_ports:
                target_data_type = target_node.input_ports[to_port].data_type
            
            # Create spline data (will be updated by connection manager)
            spline_data = ConnectionSplineData(
                start_point=QPointF(0, 0),
                end_point=QPointF(100, 100),
                control_point_1=QPointF(50, 0),
                control_point_2=QPointF(50, 100)
            )
            
            conn = AdvancedConnection(
                id=conn_id,
                source_port_id=source_port_id,
                target_port_id=target_port_id,
                spline_data=spline_data
            )
            
            self._connections[conn_id] = conn
            self._next_connection_id = max(self._next_connection_id, idx + 2)