"""
Connection Manager - Advanced wire rendering and connection lifecycle management.

Features:
- Formal state machine (IDLE, DRAGGING_CONNECTION, CONNECTED)
- Smooth cubic Bezier curves with dynamic control points
- Comprehensive validation and safety rules
- Port detachment and reassignment
- Event-driven optimization with observer pattern
- 60 FPS smooth updates during node dragging
"""

from typing import Dict, List, Tuple, Optional, Set, Any
from enum import Enum, auto
from PySide6.QtCore import QPointF, QTimer, Signal, QObject, Qt, QRectF
from PySide6.QtGui import QPainterPath, QPen, QBrush, QColor, QPainter
from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsItem

from src.core.graph import Graph
from src.core.port import PortType, DataType
from src.core.advanced_connection_system import WireCutter
from src.gui.node_item import NodeItem, PortItem, DATATYPE_COLORS


class ConnectionState(Enum):
    """Connection interaction states."""
    IDLE = auto()                  # No active connection
    DRAGGING_CONNECTION = auto()   # User is drawing a new connection
    VALIDATING = auto()            # Checking if drop target is valid
    CONNECTED = auto()             # Connection successfully created


class ConnectionManager(QObject):
    """
    Manages all connection-related operations with formal state machine.
    
    Responsibilities:
    - Connection lifecycle (creation, validation, deletion)
    - Bezier curve rendering with smooth control points
    - Port detachment and reassignment
    - Event-driven updates for optimal performance
    - Validation rules enforcement
    """
    
    # Signals for event-driven architecture
    connection_started = Signal(str, str, str)  # node_id, port_name, port_type
    connection_cancelled = Signal()
    connection_created = Signal(str, str, str, str)  # from_id, from_port, to_id, to_port
    connection_removed = Signal(str, str, str, str)  # from_id, from_port, to_id, to_port
    port_highlighted = Signal(bool, str)  # is_valid, port_id
    
    def __init__(self, canvas, graph: Graph, parent=None):
        super().__init__(parent)
        self.canvas = canvas
        self.graph = graph
        
        # State machine
        self._state = ConnectionState.IDLE
        self._connecting_from: Optional[Tuple[str, str, str, DataType]] = None  # (node_id, port_name, port_type, data_type)
        
        # Visual elements
        self._temp_line: Optional[QGraphicsPathItem] = None
        self._highlighted_port: Optional[PortItem] = None
        
        # Connection registry (independent of visual rendering)
        self._connection_registry: Dict[Tuple[str, str, str, str], Dict[str, Any]] = {}
        
        # Observer pattern for efficient updates
        self._node_observers: Dict[str, Set[str]] = {}  # node_id -> set of connection_keys
        
        # Performance optimization
        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._flush_updates)
        self._pending_updates: Set[str] = set()
        
        # Initialize from existing graph
        self._rebuild_registry()

        # Wire cutter from advanced connection system
        self._wire_cutter = WireCutter(graph, self)
    
    # ============================================================
    # STATE MACHINE
    # ============================================================
    
    @property
    def state(self) -> ConnectionState:
        """Get current connection state."""
        return self._state
    
    def _set_state(self, new_state: ConnectionState):
        """Transition to new state with cleanup."""
        old_state = self._state
        self._state = new_state
        
        # State transition logic
        if old_state == ConnectionState.DRAGGING_CONNECTION and new_state == ConnectionState.IDLE:
            self._cleanup_dragging()
        elif new_state == ConnectionState.DRAGGING_CONNECTION:
            self._setup_dragging()
    
    def _setup_dragging(self):
        """Initialize dragging state."""
        if self._connecting_from:
            node_id, port_name, port_type, data_type = self._connecting_from
            self.connection_started.emit(node_id, port_name, port_type)
    
    def _cleanup_dragging(self):
        """Clean up dragging state."""
        self._remove_temp_line()
        self._unhighlight_port()
        self._connecting_from = None
        # Re-enable node dragging
        self._enable_all_node_dragging()
    
    # ============================================================
    # CONNECTION LIFECYCLE
    # ============================================================
    
    def start_connection(self, port_item: PortItem) -> bool:
        """
        Start a new connection from a port.
        
        Args:
            port_item: The port to start connection from
            
        Returns:
            True if connection started successfully
        """
        if self._state != ConnectionState.IDLE:
            return False
        
        node_id = port_item.parent_node_item.node.node_id
        port_name = port_item.port_name
        port_type = port_item.port_type
        data_type = port_item.data_type
        
        # Store connection origin
        self._connecting_from = (node_id, port_name, port_type, data_type)
        
        # Disable dragging on ALL nodes during connection creation
        self._disable_all_node_dragging()
        
        # Highlight source port
        self._highlight_source_port(port_item)
        
        # Create temporary line
        self._create_temp_line(port_item)
        
        # Transition state
        self._set_state(ConnectionState.DRAGGING_CONNECTION)
        
        return True
    
    def _disable_all_node_dragging(self):
        """Disable dragging on all nodes in the canvas."""
        if hasattr(self.canvas, '_node_items'):
            for node_item in self.canvas._node_items.values():
                if hasattr(node_item, 'set_dragging_enabled'):
                    node_item.set_dragging_enabled(False)
    
    def _enable_all_node_dragging(self):
        """Re-enable dragging on all nodes in the canvas."""
        if hasattr(self.canvas, '_node_items'):
            for node_item in self.canvas._node_items.values():
                if hasattr(node_item, 'set_dragging_enabled'):
                    node_item.set_dragging_enabled(True)
    
    def update_temp_connection(self, scene_pos: QPointF):
        """
        Update temporary connection line to follow cursor.
        
        Args:
            scene_pos: Current cursor position in scene coordinates
        """
        if self._state != ConnectionState.DRAGGING_CONNECTION:
            return
        
        if not self._temp_line or not self._connecting_from:
            return
        
        node_id, port_name, port_type, data_type = self._connecting_from
        node_item = self.canvas.get_node_item(node_id)
        
        if not node_item:
            return
        
        # Get source port position
        start_pos = node_item.get_port_scene_pos(port_name, port_type)
        
        # Calculate smooth Bezier curve
        path = self._calculate_bezier_path(start_pos, scene_pos, port_type)
        
        # Update temp line
        self._temp_line.setPath(path)
        
        # Check for valid drop targets and highlight
        self._check_drop_target(scene_pos)
    
    def complete_connection(self, target_port: Optional[PortItem]) -> bool:
        """
        Complete connection to target port.
        
        Args:
            target_port: The port to connect to, or None if dropped on empty space
            
        Returns:
            True if connection was successfully created
        """
        if self._state != ConnectionState.DRAGGING_CONNECTION:
            return False
        
        success = False
        
        if target_port:
            success = self._try_connect_to_port(target_port)
        
        # Cleanup regardless of success
        self._set_state(ConnectionState.IDLE)
        
        return success
    
    def cancel_connection(self):
        """Cancel ongoing connection."""
        if self._state == ConnectionState.DRAGGING_CONNECTION:
            self.connection_cancelled.emit()
            self._set_state(ConnectionState.IDLE)
    
    def _try_connect_to_port(self, target_port: PortItem) -> bool:
        """
        Attempt to create connection to target port.
        
        Args:
            target_port: Target port item
            
        Returns:
            True if connection created successfully
        """
        if not self._connecting_from:
            return False
        
        from_node_id, from_port_name, from_type, from_data_type = self._connecting_from
        to_node_id = target_port.parent_node_item.node.node_id
        to_port_name = target_port.port_name
        to_type = target_port.port_type
        
        # Determine direction (output -> input)
        if from_type == "output" and to_type == "input":
            success, reason, warning = self.graph.connect(
                from_node_id, from_port_name, to_node_id, to_port_name
            )
        elif from_type == "input" and to_type == "output":
            success, reason, warning = self.graph.connect(
                to_node_id, to_port_name, from_node_id, from_port_name
            )
        else:
            return False  # Same port types
        
        if success:
            # Register connection for event-driven updates
            self._register_connection(from_node_id, from_port_name, to_node_id, to_port_name)
            
            # Redraw connections
            self.canvas._redraw_connections()
            
            # Emit signal
            self.connection_created.emit(from_node_id, from_port_name, to_node_id, to_port_name)
        
        return success
    
    def remove_connection(self, from_node_id: str, from_port: str, 
                         to_node_id: str, to_port: str):
        """
        Remove a connection.
        
        Args:
            from_node_id: Source node ID
            from_port: Source port name
            to_node_id: Target node ID
            to_port: Target port name
        """
        # Remove from graph
        self.graph.disconnect(from_node_id, from_port, to_node_id, to_port)
        
        # Unregister from event system
        self._unregister_connection(from_node_id, from_port, to_node_id, to_port)
        
        # Redraw
        self.canvas._redraw_connections()
        
        # Emit signal
        self.connection_removed.emit(from_node_id, from_port, to_node_id, to_port)

    def cut_port_connections(self, node_id: str, port_name: str,
                             port_type: str) -> List[Tuple[str, str, str, str]]:
        """Alt+Click: cut all connections from a port."""
        removed = self._wire_cutter.cut_port_connections(node_id, port_name, port_type)
        for conn in removed:
            self.connection_removed.emit(*conn)
        return removed

    def cut_connection(self, from_id: str, from_port: str,
                       to_id: str, to_port: str) -> bool:
        """Alt+Click on wire: cut a single connection."""
        key = (from_id, from_port, to_id, to_port)
        if key in self.graph.connections:
            self.remove_connection(from_id, from_port, to_id, to_port)
            return True
        return False

    def add_reroute_point(self, from_id: str, from_port: str,
                          to_id: str, to_port: str, x: float, y: float) -> bool:
        """Add a reroute anchor point to a connection."""
        key = (from_id, from_port, to_id, to_port)
        if key not in self.graph.connections:
            return False
        meta = self.graph.get_connection_metadata(from_id, from_port, to_id, to_port)
        points = meta.get("reroute_points", [])
        points.append([x, y])
        meta["reroute_points"] = points
        self.graph.set_connection_metadata(from_id, from_port, to_id, to_port, meta)
        self.canvas._redraw_connections()
        return True
    
    def detach_connection(self, connection_key: Tuple[str, str, str, str], 
                         new_target_port: Optional[PortItem] = None) -> bool:
        """
        Detach an existing connection and optionally reassign to new port.
        
        Args:
            connection_key: (from_node_id, from_port, to_node_id, to_port)
            new_target_port: New target port, or None to just disconnect
            
        Returns:
            True if detachment successful
        """
        from_node_id, from_port, to_node_id, to_port = connection_key
        
        # Remove old connection
        self.remove_connection(from_node_id, from_port, to_node_id, to_port)
        
        # If new target provided, create new connection
        if new_target_port:
            # Start new connection from source
            from_node_item = self.canvas.get_node_item(from_node_id)
            if from_node_item:
                source_port_item = from_node_item.get_port_item("output", from_port)
                if source_port_item:
                    self._connecting_from = (
                        from_node_id, from_port, "output",
                        source_port_item.data_type
                    )
                    self._set_state(ConnectionState.DRAGGING_CONNECTION)
                    return self._try_connect_to_port(new_target_port)
        
        return True
    
    # ============================================================
    # BEZIER CURVE RENDERING
    # ============================================================
    
    def _calculate_bezier_path(self, start: QPointF, end: QPointF, 
                               start_port_type: str) -> QPainterPath:
        """
        Calculate smooth cubic Bezier curve between two points.
        
        The curve always exits horizontally from source and enters horizontally
        into target, creating natural, fluid wire appearance.
        
        Args:
            start: Start point (source port position)
            end: End point (target position or cursor)
            start_port_type: "input" or "output" - determines curve direction
            
        Returns:
            QPainterPath with cubic Bezier curve
        """
        path = QPainterPath()
        path.moveTo(start)
        
        # Calculate horizontal offset for control points
        # Minimum offset of 50px ensures smooth curves even for short distances
        dx = abs(end.x() - start.x()) * 0.5
        min_offset = 50.0
        offset = max(dx, min_offset)
        
        # Control points ensure horizontal entry/exit
        if start_port_type == "output":
            # Exit to the right
            ctrl1 = QPointF(start.x() + offset, start.y())
            # Enter from the left
            ctrl2 = QPointF(end.x() - offset, end.y())
        else:
            # Exit to the left (input port)
            ctrl1 = QPointF(start.x() - offset, start.y())
            # Enter from the right
            ctrl2 = QPointF(end.x() + offset, end.y())
        
        # Create cubic Bezier curve
        path.cubicTo(ctrl1, ctrl2, end)
        
        return path
    
    def calculate_connection_path(self, from_node_id: str, from_port: str,
                                  to_node_id: str, to_port: str) -> QPainterPath:
        """
        Calculate Bezier path for an existing connection.
        
        Args:
            from_node_id: Source node ID
            from_port: Source port name
            to_node_id: Target node ID
            to_port: Target port name
            
        Returns:
            QPainterPath for the connection
        """
        from_item = self.canvas.get_node_item(from_node_id)
        to_item = self.canvas.get_node_item(to_node_id)
        
        if not from_item or not to_item:
            return QPainterPath()
        
        start = from_item.get_port_scene_pos(from_port, "output")
        end = to_item.get_port_scene_pos(to_port, "input")
        
        return self._calculate_bezier_path(start, end, "output")
    
    # ============================================================
    # VISUAL FEEDBACK
    # ============================================================
    
    def _create_temp_line(self, port_item: PortItem):
        """Create temporary connection line."""
        if self._temp_line:
            self._remove_temp_line()
        
        # Create dashed yellow line
        self._temp_line = self.canvas.scene.addPath(
            QPainterPath(),
            QPen(QColor("#FFFF00"), 2, Qt.DashLine)
        )
        self._temp_line.setZValue(100)  # Above everything
    
    def _remove_temp_line(self):
        """Remove temporary connection line."""
        if self._temp_line and self._temp_line.scene():
            self.canvas.scene.removeItem(self._temp_line)
            self._temp_line = None
    
    def _highlight_source_port(self, port_item: PortItem):
        """Highlight source port during connection."""
        port_item.setBrush(QBrush(QColor("#FFFF00")))
        port_item.setPen(QPen(QColor("#FFFF00"), 3))
    
    def _unhighlight_source_port(self, port_item: PortItem):
        """Restore source port appearance."""
        color = QColor(DATATYPE_COLORS.get(port_item.data_type, "#E0E0E0"))
        port_item.setBrush(QBrush(color))
        port_item.setPen(QPen(color.darker(150), 2))
    
    def _check_drop_target(self, scene_pos: QPointF):
        """
        Check if cursor is over a valid port and highlight it.
        
        Args:
            scene_pos: Cursor position in scene coordinates
        """
        # Unhighlight previous port
        self._unhighlight_port()
        
        # Check all nodes for ports near the cursor
        for node_item in self.canvas._node_items.values():
            # Check input ports
            for port_item in node_item.input_port_items.values():
                port_rect = port_item.sceneBoundingRect()
                # Add some tolerance for easier detection
                tolerance = 5.0
                if (port_rect.contains(scene_pos) or 
                    QRectF(port_rect.left() - tolerance, port_rect.top() - tolerance,
                           port_rect.width() + 2*tolerance, port_rect.height() + 2*tolerance).contains(scene_pos)):
                    if self._is_valid_target(port_item):
                        self._highlight_port(port_item, valid=True)
                    else:
                        self._highlight_port(port_item, valid=False)
                    return
            
            # Check output ports
            for port_item in node_item.output_port_items.values():
                port_rect = port_item.sceneBoundingRect()
                # Add some tolerance for easier detection
                tolerance = 5.0
                if (port_rect.contains(scene_pos) or 
                    QRectF(port_rect.left() - tolerance, port_rect.top() - tolerance,
                           port_rect.width() + 2*tolerance, port_rect.height() + 2*tolerance).contains(scene_pos)):
                    if self._is_valid_target(port_item):
                        self._highlight_port(port_item, valid=True)
                    else:
                        self._highlight_port(port_item, valid=False)
                    return
    
    def _is_valid_target(self, port_item: PortItem) -> bool:
        """
        Check if port is a valid connection target.
        
        Args:
            port_item: Port to validate
            
        Returns:
            True if valid target
        """
        if not self._connecting_from:
            return False
        
        from_node_id, from_port_name, from_type, from_data_type = self._connecting_from
        to_node_id = port_item.parent_node_item.node.node_id
        to_type = port_item.port_type
        
        # Must be opposite type
        if from_type == to_type:
            return False
        
        # Cannot connect to self
        if from_node_id == to_node_id:
            return False
        
        # Check data type compatibility
        if from_data_type != DataType.ANY and port_item.data_type != DataType.ANY:
            if not DataType.is_compatible(from_data_type, port_item.data_type):
                return False
        
        # Check if already connected
        from_node = self.graph.nodes.get(from_node_id)
        to_node = self.graph.nodes.get(to_node_id)
        if from_node and to_node:
            if from_type == "output":
                target_port = to_node.input_ports.get(port_item.port_name)
            else:
                target_port = from_node.input_ports.get(port_item.port_name)
            
            if target_port and target_port.connections:
                return False
        
        return True
    
    def _highlight_port(self, port_item: PortItem, valid: bool):
        """
        Highlight a port with valid/invalid color.
        
        Args:
            port_item: Port to highlight
            valid: True for green (valid), False for red (invalid)
        """
        self._highlighted_port = port_item
        
        if valid:
            port_item.setBrush(QBrush(QColor("#00FF00")))
            port_item.setPen(QPen(QColor("#00FF00"), 3))
        else:
            port_item.setBrush(QBrush(QColor("#FF0000")))
            port_item.setPen(QPen(QColor("#FF0000"), 3))
        
        self.port_highlighted.emit(valid, f"{port_item.parent_node_item.node.node_id}:{port_item.port_name}")
    
    def _unhighlight_port(self):
        """Remove highlight from previously highlighted port."""
        if self._highlighted_port:
            # Restore original color
            color = QColor(DATATYPE_COLORS.get(self._highlighted_port.data_type, "#E0E0E0"))
            self._highlighted_port.setBrush(QBrush(color))
            self._highlighted_port.setPen(QPen(color.darker(150), 2))
            self._highlighted_port = None
    
    # ============================================================
    # EVENT-DRIVEN OPTIMIZATION (OBSERVER PATTERN)
    # ============================================================
    
    def _register_connection(self, from_node_id: str, from_port: str,
                            to_node_id: str, to_port: str):
        """
        Register connection for event-driven updates.
        
        Only connections involving a specific node are redrawn when that node moves.
        """
        key = (from_node_id, from_port, to_node_id, to_port)
        
        self._connection_registry[key] = {
            "from_node": from_node_id,
            "to_node": to_node_id,
            "from_port": from_port,
            "to_port": to_port
        }
        
        # Add to node observers
        if from_node_id not in self._node_observers:
            self._node_observers[from_node_id] = set()
        if to_node_id not in self._node_observers:
            self._node_observers[to_node_id] = set()
        
        self._node_observers[from_node_id].add(key)
        self._node_observers[to_node_id].add(key)
    
    def _unregister_connection(self, from_node_id: str, from_port: str,
                              to_node_id: str, to_port: str):
        """Unregister connection from event system."""
        key = (from_node_id, from_port, to_node_id, to_port)
        
        if key in self._connection_registry:
            del self._connection_registry[key]
        
        # Remove from node observers
        if from_node_id in self._node_observers:
            self._node_observers[from_node_id].discard(key)
        if to_node_id in self._node_observers:
            self._node_observers[to_node_id].discard(key)
    
    def _rebuild_registry(self):
        """Rebuild connection registry from graph (e.g., after load)."""
        self._connection_registry.clear()
        self._node_observers.clear()
        
        for from_node_id, from_port, to_node_id, to_port in self.graph.connections:
            self._register_connection(from_node_id, from_port, to_node_id, to_port)
    
    def on_node_moved(self, node_id: str):
        """
        Called when a node is moved - triggers redraw of only affected connections.
        
        This is the key optimization: instead of redrawing ALL connections,
        we only redraw connections involving the moved node.
        """
        if node_id not in self._node_observers:
            return
        
        # Add to pending updates (batched for performance)
        self._pending_updates.add(node_id)
        
        # Schedule flush (debouncing for smooth 60 FPS)
        if not self._update_timer.isActive():
            self._update_timer.start(16)  # ~60 FPS
    
    def _flush_updates(self):
        """Flush batched updates - redraw affected connections."""
        for node_id in self._pending_updates:
            if node_id in self._node_observers:
                for conn_key in self._node_observers[node_id]:
                    if conn_key in self.canvas._connection_items:
                        conn_item = self.canvas._connection_items[conn_key]
                        conn_item.update_positions()
        
        self._pending_updates.clear()
    
    def get_connections_for_node(self, node_id: str) -> List[Tuple[str, str, str, str]]:
        """
        Get all connections involving a specific node.
        
        Args:
            node_id: Node ID
            
        Returns:
            List of connection tuples (from_id, from_port, to_id, to_port)
        """
        if node_id not in self._node_observers:
            return []
        
        return list(self._node_observers[node_id])
    
    # ============================================================
    # VALIDATION & SAFETY RULES
    # ============================================================
    
    def validate_connection(self, from_node_id: str, from_port: str,
                           to_node_id: str, to_port: str) -> Tuple[bool, str]:
        """
        Comprehensive connection validation.
        
        Args:
            from_node_id: Source node ID
            from_port: Source port name
            to_node_id: Target node ID
            to_port: Target port name
            
        Returns:
            (is_valid, reason)
        """
        # Rule 1: Nodes must exist
        if from_node_id not in self.graph.nodes:
            return False, f"Source node '{from_node_id}' not found"
        if to_node_id not in self.graph.nodes:
            return False, f"Target node '{to_node_id}' not found"
        
        # Rule 2: No self-loops
        if from_node_id == to_node_id:
            return False, "Cannot connect node to itself"
        
        from_node = self.graph.nodes[from_node_id]
        to_node = self.graph.nodes[to_node_id]
        
        # Rule 3: Ports must exist
        if from_port not in from_node.output_ports:
            return False, f"Source port '{from_port}' not found"
        if to_port not in to_node.input_ports:
            return False, f"Target port '{to_port}' not found"
        
        # Rule 4: No duplicate connections
        key = (from_node_id, from_port, to_node_id, to_port)
        if key in self.graph.connections:
            return False, "Connection already exists"
        
        # Rule 5: Data type compatibility
        from_port_obj = from_node.output_ports[from_port]
        to_port_obj = to_node.input_ports[to_port]
        
        can_connect, reason = from_port_obj.can_connect(to_port_obj)
        if not can_connect:
            return False, reason
        
        # Rule 6: No cycles (warning, not error)
        has_cycle, cycle_warning = self.graph._check_cycle(from_node_id, to_node_id)
        if has_cycle:
            return False, cycle_warning
        
        return True, "Valid"
    
    def check_port_available(self, node_id: str, port_name: str, 
                            port_type: str) -> Tuple[bool, str]:
        """
        Check if a port is available for connection.
        
        Args:
            node_id: Node ID
            port_name: Port name
            port_type: "input" or "output"
            
        Returns:
            (is_available, reason)
        """
        if node_id not in self.graph.nodes:
            return False, "Node not found"
        
        node = self.graph.nodes[node_id]
        
        if port_type == "output":
            if port_name not in node.output_ports:
                return False, "Port not found"
            # Output ports can have multiple connections
            return True, "Available"
        else:
            if port_name not in node.input_ports:
                return False, "Port not found"
            # Input ports can only have one connection
            port = node.input_ports[port_name]
            if port.connections:
                return False, "Input port already connected"
            return True, "Available"
    
    # ============================================================
    # UTILITY METHODS
    # ============================================================
    
    def get_connection_data(self, from_node_id: str, from_port: str,
                           to_node_id: str, to_port: str) -> Optional[Dict[str, Any]]:
        """Get connection metadata."""
        key = (from_node_id, from_port, to_node_id, to_port)
        return self._connection_registry.get(key)
    
    def get_all_connections(self) -> List[Tuple[str, str, str, str]]:
        """Get all registered connections."""
        return list(self._connection_registry.keys())
    
    def is_connecting(self) -> bool:
        """Check if currently in connection dragging state."""
        return self._state == ConnectionState.DRAGGING_CONNECTION
    
    def get_connecting_from(self) -> Optional[Tuple[str, str, str]]:
        """Get current connection origin (node_id, port_name, port_type)."""
        if self._connecting_from:
            node_id, port_name, port_type, _ = self._connecting_from
            return (node_id, port_name, port_type)
        return None
    
    def cleanup(self):
        """Cleanup manager resources."""
        self._set_state(ConnectionState.IDLE)
        self._connection_registry.clear()
        self._node_observers.clear()
        self._pending_updates.clear()
        if self._update_timer.isActive():
            self._update_timer.stop()