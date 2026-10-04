"""
Canvas - QGraphicsView with professional features:
- Dot grid background, snap-to-grid
- Zoom: Ctrl+Scroll (0.25x to 3.0x), Pan: Middle-mouse drag
- Rubber band multi-select
- Minimap (150x100px) in bottom-right corner
- Bezier temp lines during connection
- Packet animation management
"""

from typing import Dict, Optional, Tuple, List, Set
import math
from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem,
    QGraphicsEllipseItem, QGraphicsPathItem, QFrame,
    QGraphicsRectItem, QGraphicsTextItem, QWidget, QVBoxLayout,
    QAbstractScrollArea, QScrollArea, QApplication, QGraphicsPixmapItem
)
from PySide6.QtGui import QPixmap, QPainter, QPen, QBrush, QColor
from PySide6.QtCore import (
    Qt, QTimer, QPoint, QPointF, QRectF, Signal, QEvent, QSize, QObject
)
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QPainterPath, QTransform,
    QWheelEvent, QMouseEvent, QKeyEvent, QPalette, QKeySequence
)

from src.core.graph import Graph
from src.core.engine import SimulationEngine
from src.core.undo_stack import (
    UndoStack, AddNodeCommand, RemoveNodeCommand, MoveNodeCommand,
    AddConnectionCommand, RemoveConnectionCommand, MacroCommand
)
from src.gui.node_item import NodeItem, ConnectionItem, PacketAnimation, PortItem
from src.core.port import PortType, DataType
from src.gui.connection_manager import ConnectionManager, ConnectionState

# Import DATATYPE_COLORS from node_item for port color restoration
from src.gui.node_item import DATATYPE_COLORS


class MiniMapWidget(QWidget):
    """Minimap widget containing a QGraphicsView."""
    
    def __init__(self, scene: QGraphicsScene, parent=None):
        super().__init__(parent)
        self.main_scene = scene
        self._main_view: Optional[QGraphicsView] = None
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.view = QGraphicsView(scene)
        self.view.setScene(scene)
        self.view.setFixedSize(150, 100)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setRenderHint(QPainter.SmoothPixmapTransform)
        self.view.setStyleSheet("background: transparent; border: 1px solid #555;")
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setInteractive(False)
        
        layout.addWidget(self.view)
    
    def set_main_view(self, view: QGraphicsView):
        self._main_view = view
    
    def update_viewport(self):
        """Update minimap view."""
        if not self._main_view:
            return
        
        scene_rect = self.main_scene.sceneRect()
        if scene_rect.width() < 1 or scene_rect.height() < 1:
            return
        
        self.view.fitInView(scene_rect, Qt.KeepAspectRatio)


class Canvas(QGraphicsView):
    """Hlavní plátno s profesionálním zoomem, panem, gridem a minimap."""
    
    node_selected = Signal(object)  # NodeBase or None
    node_added = Signal(object)     # NodeBase
    node_removed = Signal(str)      # node_id
    connection_created = Signal(str, str, str, str)  # from_id, from_port, to_id, to_port
    undo_state_changed = Signal(bool, bool)  # can_undo, can_redo
    
    def __init__(self, graph: Graph, engine: SimulationEngine, parent=None):
        super().__init__(parent)
        self.graph = graph
        self.engine = engine
        self.undo_stack = UndoStack(self)
        self.undo_stack.changed.connect(self._emit_undo_state)
        self._drag_start_positions: Dict[str, Tuple[float, float]] = {}
        
        # Scene
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(-5000, -5000, 10000, 10000)
        # Transparent scene background so viewport and grid show through
        self.scene.setBackgroundBrush(QBrush(Qt.transparent))
        self.setScene(self.scene)
        
        # Visual mappings
        self._node_items: Dict[str, NodeItem] = {}
        self._connection_items: Dict[tuple, ConnectionItem] = {}
        self._animations: List[PacketAnimation] = []
        
        # Connection manager (replaces inline connection logic)
        self._connection_manager = ConnectionManager(self, graph, self)
        self._connection_manager.connection_created.connect(self._on_connection_created)
        
        # Pan state
        self._panning = False
        self._pan_start = QPointF()
        self._pan_start_pos = QPointF()
        
        # Marquee selection state
        self._marquee_active = False
        self._marquee_origin = QPointF()
        self._marquee_current = QPointF()
        self._marquee_rect_item: Optional[QGraphicsRectItem] = None
        self._selected_nodes: Set[str] = set()
        
        # View settings - optimized for performance
        # Disable antialiasing by default for better performance
        # It will be enabled only when needed (e.g., for connections)
        self.setRenderHint(QPainter.Antialiasing, False)
        self.setRenderHint(QPainter.TextAntialiasing, False)
        self.setRenderHint(QPainter.SmoothPixmapTransform, False)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # CRITICAL: Use MinimalViewportUpdate instead of FullViewportUpdate
        self.setViewportUpdateMode(QGraphicsView.MinimalViewportUpdate)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        
        # Eliminate all borders/frames
        self.setFrameShape(QFrame.NoFrame)
        self.setFrameShadow(QFrame.Plain)
        self.setLineWidth(0)
        self.setMidLineWidth(0)
        # Enable focus to receive keyboard events (DELETE key)
        self.setFocusPolicy(Qt.StrongFocus)
        self.viewport().setFocusPolicy(Qt.StrongFocus)
        # Dark background for viewport (shows through transparent scene)
        self.setStyleSheet("background: #1e1e1e;")
        self.viewport().setStyleSheet("background: #1e1e1e;")
        self.viewport().setAutoFillBackground(True)
        
        # Grid dots - back to original spacing (40px) for clean look
        self._grid_size = 40  # Original spacing restored
        self._snap_to_grid = True
        self._draw_grid_dots()
        
        # Minimap - will be positioned in bottom-right corner
        self._minimap = MiniMapWidget(self.scene, parent=self)
        self._minimap.set_main_view(self)

        self._animations_enabled = True
        self._max_concurrent_animations = 12

        # Packet flow animations (event-driven via engine.packet_moved)
        self.engine.packet_moved.connect(self._on_packet_moved)
        
        # Signals
        self.scene.selectionChanged.connect(self._on_selection_changed)
        
        # Install event filter for minimap and keyboard handling
        self.viewport().installEventFilter(self)
        
        # Also install event filter on self to catch key events
        self.installEventFilter(self)
    
    def _draw_grid_on_viewport(self, painter: QPainter, rect: QRectF):
        """Draw dotted grid directly on viewport - most reliable method."""
        grid_color = QColor("#666666")
        grid_size = self._grid_size
        
        # Calculate visible scene area
        top_left = self.mapToScene(int(rect.left()), int(rect.top()))
        bottom_right = self.mapToScene(int(rect.right()), int(rect.bottom()))
        
        # Find the starting grid positions (aligned to grid)
        start_x = int(top_left.x() / grid_size) * grid_size
        start_y = int(top_left.y() / grid_size) * grid_size
        
        # Set up painter for drawing dots
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(grid_color))
        
        # Draw dots
        x = start_x
        while x < bottom_right.x():
            y = start_y
            while y < bottom_right.y():
                # Convert scene coordinates to viewport coordinates
                view_pos = self.mapFromScene(x, y)
                # Only draw if within viewport
                if (rect.left() <= view_pos.x() <= rect.right() and 
                    rect.top() <= view_pos.y() <= rect.bottom()):
                    # Draw a visible dot (3x3 pixels)
                    painter.drawEllipse(int(view_pos.x()) - 1, int(view_pos.y()) - 1, 3, 3)
                y += grid_size
            x += grid_size
    
    def _draw_grid_dots(self):
        """Draw dot grid pattern as QGraphicsPixmapItem in scene - PERFORMANCE OPTIMIZED."""
        from src.utils.logger import perf_monitor
        
        with perf_monitor.measure("grid_drawing"):
            # Remove old grid if exists
            if hasattr(self, '_grid_item'):
                self.scene.removeItem(self._grid_item)
            
            scene_rect = self.scene.sceneRect()
            grid_color = QColor("#666666")
            grid_size = self._grid_size
            
            # Create a pixmap covering the entire scene
            width = int(scene_rect.width())
            height = int(scene_rect.height())
            
            # Create pixmap with TRANSPARENT background
            pixmap = QPixmap(width, height)
            pixmap.fill(Qt.transparent)
            
            # Draw grid dots on pixmap using QPainter
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing, False)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(grid_color))
            
            dot_count = 0
            for x in range(int(scene_rect.left()), int(scene_rect.right()), grid_size):
                for y in range(int(scene_rect.top()), int(scene_rect.bottom()), grid_size):
                    # Draw dot (3x3 pixels) - position relative to pixmap origin
                    painter.drawEllipse(x - int(scene_rect.left()) - 1, y - int(scene_rect.top()) - 1, 3, 3)
                    dot_count += 1
            
            painter.end()
            
            # Add pixmap to scene as single item at the back
            self._grid_item = QGraphicsPixmapItem(pixmap)
            self._grid_item.setPos(scene_rect.left(), scene_rect.top())
            self._grid_item.setZValue(-1000)  # Very low z-index to be behind everything
            self.scene.addItem(self._grid_item)
            
            # Log performance
            import logging
            logger = logging.getLogger("Canvas")
            elapsed = perf_monitor._measurements.get("grid_drawing", [0])[-1] if perf_monitor._measurements.get("grid_drawing") else 0
            logger.info(f"Grid drawn: {dot_count} dots in {elapsed*1000:.2f}ms (spacing={grid_size}px)")
    
    def paintEvent(self, event):
        """Paint event - let Qt handle default painting."""
        # Call parent to handle standard painting
        super().paintEvent(event)
    
    def _emit_undo_state(self):
        self.undo_state_changed.emit(self.undo_stack.can_undo(), self.undo_stack.can_redo())

    def _snap_pos(self, x: float, y: float) -> Tuple[float, float]:
        """Snap coordinates to grid."""
        if self._snap_to_grid:
            g = self._grid_size
            return (round(x / g) * g, round(y / g) * g)
        return (x, y)
    
    def _add_node_internal(self, node_type: str, pos: Tuple[float, float],
                           params: Optional[dict] = None):
        """Add node without recording undo (used by undo system)."""
        from src.nodes.registry import get_node_class, get_sidebar_key

        node_class = get_node_class(node_type)
        if not node_class:
            # Fallback: try matching by class name from saved data
            from src.nodes.registry import CLASS_NAME_MAP
            node_class = CLASS_NAME_MAP.get(node_type)
        if not node_class:
            return None

        import uuid
        node_id = f"node_{uuid.uuid4().hex[:8]}"
        node = node_class(node_id)
        node.position = self._snap_pos(pos[0], pos[1])

        if params:
            for k, v in params.items():
                if k not in ("processing_delay", "throughput_limit", "bypass", "buffer_maxsize"):
                    node.set_param(k, v)

        self.graph.add_node(node)

        node_item = NodeItem(node)
        node_item.setPos(node.position[0], node.position[1])
        self.scene.addItem(node_item)
        self._node_items[node_id] = node_item

        self.engine.register_node(node)
        self._redraw_connections()
        self.node_added.emit(node)
        return node

    def _remove_node_internal(self, node_id: str):
        """Remove node without recording undo."""
        node_item = self._node_items.get(node_id)
        if not node_item:
            return
        self._remove_node_connections(node_id)
        self.scene.removeItem(node_item)
        if node_id in self._node_items:
            del self._node_items[node_id]
        self.graph.remove_node(node_id)
        self.node_removed.emit(node_id)
        self.node_selected.emit(None)

    def _restore_node_internal(self, node_data: dict,
                               connections: List[Tuple[str, str, str, str]]):
        """Restore a previously removed node."""
        from src.nodes.registry import resolve_node_class

        node_class = resolve_node_class(node_data)
        if not node_class:
            return

        node_id = node_data.get("id", f"node_restored")
        node = node_class(node_id)
        pos = node_data.get("position", [0, 0])
        node.position = tuple(pos) if isinstance(pos, (list, tuple)) else (0, 0)

        for k, v in node_data.get("params", {}).items():
            node.set_param(k, v)
        for k, v in node_data.get("config", {}).items():
            node.set_param(k, v)

        self.graph.add_node(node)
        node_item = NodeItem(node)
        node_item.setPos(node.position[0], node.position[1])
        self.scene.addItem(node_item)
        self._node_items[node_id] = node_item
        self.engine.register_node(node)

        for conn in connections:
            self.graph.connect(*conn)

        self._redraw_connections()
        self.node_added.emit(node)

    def _set_node_position(self, node_id: str, pos: Tuple[float, float]):
        """Set node position without undo."""
        node_item = self._node_items.get(node_id)
        if not node_item:
            return
        snapped = self._snap_pos(pos[0], pos[1])
        node_item.setPos(snapped[0], snapped[1])
        node_item.node.position = snapped
        self._update_connections_for_node(node_id)

    def _add_connection_internal(self, from_id: str, from_port: str,
                                  to_id: str, to_port: str) -> bool:
        """Add connection without recording undo."""
        success, _, _ = self.graph.connect(from_id, from_port, to_id, to_port)
        if success:
            self._connection_manager._register_connection(
                from_id, from_port, to_id, to_port
            )
            self._redraw_connections()
        return success

    def _remove_connection_internal(self, from_id: str, from_port: str,
                                    to_id: str, to_port: str) -> bool:
        """Remove connection without recording undo."""
        if self.graph.disconnect(from_id, from_port, to_id, to_port):
            self._connection_manager._unregister_connection(
                from_id, from_port, to_id, to_port
            )
            key = (from_id, from_port, to_id, to_port)
            if key in self._connection_items:
                item = self._connection_items.pop(key)
                self.scene.removeItem(item)
            return True
        return False

    def add_node_at(self, node_type: str, pos: Tuple[float, float]):
        """Add a new node at the given position."""
        cmd = AddNodeCommand(self, node_type, pos)
        self.undo_stack.push(cmd)
        return self.graph.get_node(cmd.node_id) if cmd.node_id else None

    def remove_node_item(self, node_item: NodeItem):
        """Remove a node from the canvas."""
        cmd = RemoveNodeCommand(self, node_item.node.node_id)
        self.undo_stack.push(cmd)

    def duplicate_node_item(self, node_item: NodeItem):
        """Duplicate a node with offset."""
        old_node = node_item.node
        from src.nodes.registry import get_sidebar_key
        type_key = get_sidebar_key(type(old_node))
        if not type_key:
            type_key = type(old_node).__name__
        new_pos = self._snap_pos(
            old_node.position[0] + 40,
            old_node.position[1] + 40
        )
        params = dict(old_node.params)
        cmd = AddNodeCommand(self, type_key, new_pos, params)
        self.undo_stack.push(cmd)

    def on_node_drag_started(self, node_id: str):
        """Record position at start of drag for undo."""
        node_item = self._node_items.get(node_id)
        if node_item:
            self._drag_start_positions[node_id] = (
                node_item.node.position[0], node_item.node.position[1]
            )

    def on_node_drag_finished(self, node_id: str):
        """Record move command if position changed."""
        start = self._drag_start_positions.pop(node_id, None)
        node_item = self._node_items.get(node_id)
        if not start or not node_item:
            return
        end = node_item.node.position
        if start != end:
            self.undo_stack.push(MoveNodeCommand(self, node_id, start, end))

    def record_connection_added(self, from_id: str, from_port: str,
                                to_id: str, to_port: str):
        """Record connection creation for undo (already connected)."""
        self.undo_stack.push_done(
            AddConnectionCommand(self, from_id, from_port, to_id, to_port)
        )

    def undo(self) -> bool:
        return self.undo_stack.undo()

    def redo(self) -> bool:
        return self.undo_stack.redo()
    
    def _remove_node_connections(self, node_id: str):
        """Remove all connections for a node."""
        connections_to_remove = []
        for conn in self.graph.connections[:]:
            if conn[0] == node_id or conn[2] == node_id:
                connections_to_remove.append(conn)
        
        for conn in connections_to_remove:
            self.graph.disconnect(*conn)
            key = (conn[0], conn[1], conn[2], conn[3])
            if key in self._connection_items:
                item = self._connection_items.pop(key)
                self.scene.removeItem(item)
    
    def _cancel_connection(self):
        """Cancel ongoing connection and restore port colors."""
        self._connection_manager.cancel_connection()
    
    def _redraw_connections(self):
        """Redraw all connection items."""
        for item in self._connection_items.values():
            self.scene.removeItem(item)
        self._connection_items.clear()
        
        for from_id, from_port, to_id, to_port in self.graph.connections:
            from_item = self._node_items.get(from_id)
            to_item = self._node_items.get(to_id)
            if from_item and to_item:
                conn_item = ConnectionItem(from_item, from_port, to_item, to_port)
                self.scene.addItem(conn_item)
                self._connection_items[(from_id, from_port, to_id, to_port)] = conn_item
        
        # Rebuild connection manager registry
        self._connection_manager._rebuild_registry()
    
    def _update_connections_for_node(self, node_id: str):
        """Update all connections involving a specific node."""
        # Delegate to connection manager for optimized updates
        self._connection_manager.on_node_moved(node_id)
    
    def _on_selection_changed(self):
        """Handle selection change."""
        selected = self.scene.selectedItems()
        if selected:
            for item in selected:
                if isinstance(item, NodeItem):
                    self.node_selected.emit(item.node)
                    return
        self.node_selected.emit(None)
    
    # ========== ZOOM & PAN ==========
    
    def wheelEvent(self, event):
        """Zoom with Ctrl+Scroll, pan with plain scroll - OPTIMIZED."""
        if event.modifiers() == Qt.ControlModifier:
            # Temporarily enable antialiasing for smooth zoom
            self.setRenderHint(QPainter.Antialiasing, True)
            self.setRenderHint(QPainter.TextAntialiasing, True)
            
            factor = 1.15
            if event.angleDelta().y() > 0:
                if self.transform().m11() < 3.0:
                    self.scale(factor, factor)
            else:
                if self.transform().m11() > 0.25:
                    self.scale(1/factor, 1/factor)
            
            # Disable antialiasing after zoom
            self.setRenderHint(QPainter.Antialiasing, False)
            self.setRenderHint(QPainter.TextAntialiasing, False)
            
            self._update_minimap()
        else:
            super().wheelEvent(event)
    
    def _on_connection_created(self, from_id: str, from_port: str,
                                to_id: str, to_port: str):
        """Record undo and forward connection signal."""
        self.undo_stack.push_done(
            AddConnectionCommand(self, from_id, from_port, to_id, to_port)
        )
        self.connection_created.emit(from_id, from_port, to_id, to_port)

    def cut_wire_with_undo(self, from_id: str, from_port: str,
                           to_id: str, to_port: str):
        """Cut a wire with undo support (Alt+Click)."""
        self._connection_manager.cut_connection(from_id, from_port, to_id, to_port)
        self.undo_stack.push_done(
            RemoveConnectionCommand(self, from_id, from_port, to_id, to_port)
        )

    def _on_port_clicked(self, port_item: PortItem):
        """Handle port click for connection creation."""
        # Delegate to connection manager
        if self._connection_manager.is_connecting():
            self._connection_manager.complete_connection(port_item)
        else:
            if QApplication.keyboardModifiers() & Qt.AltModifier:
                removed = self._connection_manager.cut_port_connections(
                    port_item.parent_node_item.node.node_id,
                    port_item.port_name,
                    port_item.port_type
                )
                if removed:
                    with self.undo_stack.begin_macro("Odstranit spojení portu") as macro:
                        for conn in removed:
                            macro.add(RemoveConnectionCommand(self, *conn))
            else:
                self._connection_manager.start_connection(port_item)
    
    def mousePressEvent(self, event):
        """Handle mouse press for panning, connection, and marquee selection."""
        if event.button() == Qt.MiddleButton:
            # Panning
            self._panning = True
            self._pan_start = event.pos()
            self._pan_start_pos = QPointF(self.horizontalScrollBar().value(),
                                          self.verticalScrollBar().value())
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        
        if event.button() == Qt.LeftButton:
            # Check if we clicked on a port first
            items = self.items(event.pos())
            port_clicked = False
            for item in items:
                if isinstance(item, PortItem):
                    # Let the port handle the click
                    item.mousePressEvent(event)
                    event.accept()
                    port_clicked = True
                    break
            
            if not port_clicked:
                # Check if we clicked on a node
                node_clicked = False
                for item in items:
                    if isinstance(item, NodeItem):
                        node_clicked = True
                        break
                
                if not node_clicked:
                    # Clicked on empty canvas - start marquee selection
                    self._start_marquee_selection(event.pos())
                    event.accept()
                    return
                else:
                    # Cancel any ongoing connection if clicking on node
                    if self._connection_manager.is_connecting():
                        self._cancel_connection()
                    # Let parent handle node selection/movement
                    super().mousePressEvent(event)
            return
        
        super().mousePressEvent(event)
    
    # ========== MARQUEE SELECTION ==========
    
    def _start_marquee_selection(self, pos: QPoint):
        """Start marquee selection from mouse position (scene coordinates)."""
        self._marquee_active = True
        # CRITICAL: Convert viewport coordinates to scene coordinates
        scene_pos = self.mapToScene(pos)
        self._marquee_origin = scene_pos
        self._marquee_current = scene_pos
        
        # Clear previous selection unless Shift is held
        if not (QApplication.keyboardModifiers() & Qt.ShiftModifier):
            self._selected_nodes.clear()
            self._clear_all_selections()
        else:
            # Shift mode: re-apply existing selection visuals so they stay highlighted
            self._apply_selection_visuals()
        
        # Create selection rectangle item
        self._marquee_rect_item = QGraphicsRectItem()
        self._marquee_rect_item.setPen(QPen(QColor("#2196F3"), 1))  # Solid blue border
        self._marquee_rect_item.setBrush(QBrush(QColor(33, 150, 243, 50)))  # Light blue, semi-transparent
        self._marquee_rect_item.setZValue(1000)  # Above all other items
        self._marquee_rect_item.setRect(QRectF(self._marquee_origin, self._marquee_current))
        self.scene.addItem(self._marquee_rect_item)
    
    def _update_marquee_selection(self, pos: QPoint):
        """Update marquee selection rectangle (scene coordinates)."""
        if not self._marquee_active:
            return
        
        # CRITICAL: Convert viewport coordinates to scene coordinates
        self._marquee_current = self.mapToScene(pos)
        
        # Update rectangle geometry
        if self._marquee_rect_item:
            rect = QRectF(self._marquee_origin, self._marquee_current).normalized()
            self._marquee_rect_item.setRect(rect)
            
            # Check for node intersections and highlight
            self._update_selection_highlight(rect)
    
    def _end_marquee_selection(self):
        """Finalize marquee selection."""
        if not self._marquee_active:
            return
        
        # Finalize selection
        if self._marquee_rect_item:
            final_rect = self._marquee_rect_item.rect()
            self._finalize_selection(final_rect)
            
            # Remove rectangle from scene
            self.scene.removeItem(self._marquee_rect_item)
            self._marquee_rect_item = None
        
        self._marquee_active = False
        self._marquee_origin = QPointF()
        self._marquee_current = QPointF()
    
    def _update_selection_highlight(self, rect: QRectF):
        """Update node and connection highlighting based on current marquee rectangle."""
        # Clear previous temporary highlights (but preserve Shift-selected items)
        self._clear_selection_highlight()
        
        # Find intersecting nodes
        intersecting_nodes = self._get_intersecting_nodes(rect)
        
        # Highlight them (temporary during drag)
        for node_id in intersecting_nodes:
            node_item = self._node_items.get(node_id)
            if node_item:
                node_item.setSelected(True)
        
        # Find intersecting connections
        intersecting_connections = self._get_intersecting_connections(rect)
        
        # Highlight them (temporary during drag)
        for conn_item in intersecting_connections:
            conn_item.setSelected(True)
    
    def _finalize_selection(self, rect: QRectF):
        """Finalize selection and update selected items."""
        # Get all intersecting nodes
        intersecting_nodes = self._get_intersecting_nodes(rect)
        
        # Get all intersecting connections
        intersecting_connections = self._get_intersecting_connections(rect)
        
        # Update selected_nodes set
        if not (QApplication.keyboardModifiers() & Qt.ShiftModifier):
            # Clear all selections if not Shift
            self._clear_all_selections()
        
        # Update visual selection for nodes
        for node_id in intersecting_nodes:
            node_item = self._node_items.get(node_id)
            if node_item:
                node_item.setSelected(True)
                self._selected_nodes.add(node_id)
        
        # Update visual selection for connections
        for conn_item in intersecting_connections:
            conn_item.setSelected(True)
    
    def _get_intersecting_nodes(self, rect: QRectF) -> Set[str]:
        """
        Get set of node IDs whose bounding boxes intersect with or are contained within the selection rectangle.
        
        Args:
            rect: Selection rectangle in scene coordinates
            
        Returns:
            Set of node IDs that intersect with the rectangle
        """
        intersecting = set()
        
        for node_id, node_item in self._node_items.items():
            # Get node bounding box in scene coordinates
            node_scene_rect = node_item.sceneBoundingRect()
            
            # Check if rectangles intersect (partial or full containment)
            if rect.intersects(node_scene_rect):
                intersecting.add(node_id)
        
        return intersecting
    
    def _get_intersecting_connections(self, rect: QRectF) -> List[ConnectionItem]:
        """
        Get list of connection items whose paths intersect with the selection rectangle.
        
        Args:
            rect: Selection rectangle in scene coordinates
            
        Returns:
            List of ConnectionItem objects that intersect with the rectangle
        """
        intersecting = []
        
        for conn_item in self._connection_items.values():
            # Check if the connection's shape intersects with the rectangle
            # We use the connection's shape which has a thicker hit area
            if conn_item.shape().boundingRect().intersects(rect):
                intersecting.append(conn_item)
        
        return intersecting
    
    def _apply_selection_visuals(self):
        """Apply visual highlighting to all selected nodes."""
        for node_id in self._selected_nodes:
            node_item = self._node_items.get(node_id)
            if node_item:
                node_item.setSelected(True)
    
    def _clear_selection_highlight(self):
        """Clear temporary highlighting during marquee selection."""
        # Deselect all nodes temporarily
        for node_item in self._node_items.values():
            node_item.setSelected(False)
        # Deselect all connections temporarily
        for conn_item in self._connection_items.values():
            conn_item.setSelected(False)
    
    def _clear_all_selections(self):
        """Clear all selections (nodes and connections)."""
        # Clear node selections
        for node_item in self._node_items.values():
            node_item.setSelected(False)
        self._selected_nodes.clear()
        
        # Clear connection selections
        for conn_item in self._connection_items.values():
            conn_item.setSelected(False)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        if event.button() == Qt.MiddleButton and self._panning:
            self._panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return
        
        # End marquee selection if active
        if event.button() == Qt.LeftButton and self._marquee_active:
            self._end_marquee_selection()
            event.accept()
            return
        
        # Handle connection completion
        if event.button() == Qt.LeftButton and self._connection_manager.is_connecting():
            target_port = self._connection_manager._highlighted_port
            self._connection_manager.complete_connection(target_port)
            event.accept()
            return
        
        super().mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for panning, temp line, and marquee selection."""
        if self._panning:
            delta = event.pos() - self._pan_start
            self.horizontalScrollBar().setValue(int(self._pan_start_pos.x() - delta.x()))
            self.verticalScrollBar().setValue(int(self._pan_start_pos.y() - delta.y()))
            event.accept()
            return
        
        # Update marquee selection if active
        if self._marquee_active:
            self._update_marquee_selection(event.pos())
            event.accept()
            return
        
        # Update temp connection line via connection manager
        if self._connection_manager.is_connecting():
            scene_pos = self.mapToScene(event.pos())
            self._connection_manager.update_temp_connection(scene_pos)
        
        super().mouseMoveEvent(event)
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events."""
        if event.matches(QKeySequence.Undo):
            self.undo()
            event.accept()
            return
        if event.matches(QKeySequence.Redo):
            self.redo()
            event.accept()
            return
        if event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
            self._delete_selected_items()
            event.accept()
            return
        super().keyPressEvent(event)

    def _delete_selected_items(self):
        """Delete all selected items (nodes and connections)."""
        selected_items = self.scene.selectedItems()

        nodes_to_delete = []
        connections_to_delete = []

        for item in selected_items:
            if isinstance(item, NodeItem):
                nodes_to_delete.append(item)
            elif isinstance(item, ConnectionItem):
                connections_to_delete.append(item)

        if not nodes_to_delete and not connections_to_delete:
            return

        with self.undo_stack.begin_macro("Hromadné odstranění") as macro:
            for conn_item in connections_to_delete:
                macro.add(RemoveConnectionCommand(
                    self,
                    conn_item.from_node.node.node_id, conn_item.from_port,
                    conn_item.to_node.node.node_id, conn_item.to_port
                ))
            for node_item in nodes_to_delete:
                macro.add(RemoveNodeCommand(self, node_item.node.node_id))

    def _delete_connection_item(self, conn_item: ConnectionItem):
        """Delete a single connection item."""
        self.undo_stack.push(RemoveConnectionCommand(
            self,
            conn_item.from_node.node.node_id, conn_item.from_port,
            conn_item.to_node.node.node_id, conn_item.to_port
        ))
    
    def eventFilter(self, obj, event):
        """Handle events for minimap and keyboard."""
        # Handle key events at the viewport level
        if obj == self.viewport() and event.type() == QEvent.KeyPress:
            key_event = event  # QKeyEvent
            if key_event.key() == Qt.Key_Delete or key_event.key() == Qt.Key_Backspace:
                self._delete_selected_items()
                return True  # Event handled
        # Handle resize events for minimap
        elif obj == self.viewport() and event.type() == QEvent.Resize:
            self._update_minimap_position()
        return super().eventFilter(obj, event)
    
    def _update_minimap_position(self):
        """Position minimap in bottom-right corner."""
        if self._minimap:
            x = self.viewport().width() - self._minimap.width() - 10
            y = self.viewport().height() - self._minimap.height() - 10
            self._minimap.move(x, y)
            self._minimap.raise_()
    
    def _update_minimap(self):
        """Update minimap viewport indicator."""
        if self._minimap:
            self._minimap.update_viewport()
    
    def resizeEvent(self, event):
        """Handle resize."""
        super().resizeEvent(event)
        self._update_minimap_position()
        self._update_minimap()
    
    # ========== DRAG & DROP ==========
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)
    
    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)
    
    def dropEvent(self, event):
        if event.mimeData().hasText():
            node_type = event.mimeData().text()
            scene_pos = self.mapToScene(event.pos())
            pos = (scene_pos.x(), scene_pos.y())
            self.add_node_at(node_type, pos)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)
    
    # ========== SCENE MANAGEMENT ==========
    
    def clear_scene(self):
        """Clear the entire scene - PERFORMANCE OPTIMIZED."""
        self.undo_stack.clear()
        self._node_items.clear()
        self._connection_items.clear()
        
        # Cleanup connection manager
        self._connection_manager.cleanup()
        
        # Stop and clear animations
        for anim in self._animations:
            anim.stop()
        self._animations.clear()
        
        # Clear scene
        self.scene.clear()
        
        # Redraw grid
        self._draw_grid_dots()
        
        # Remove old minimap if exists
        if hasattr(self, '_minimap') and self._minimap:
            self._minimap.setParent(None)
            self._minimap.deleteLater()
        
        # Create new minimap with proper parent
        self._minimap = MiniMapWidget(self.scene, parent=self)
        self._minimap.set_main_view(self)
        self._update_minimap_position()
    
    def get_node_item(self, node_id: str) -> Optional[NodeItem]:
        """Get NodeItem by node ID."""
        return self._node_items.get(node_id)
    
    # ========== PACKET ANIMATION ==========

    def _animation_duration_ms(self) -> int:
        """Scale animation length with simulation speed."""
        speed = max(0.1, getattr(self.engine, "speed", 1.0))
        return max(120, int(PacketAnimation.BASE_DURATION_MS / speed))

    def _find_connection_item(self, from_id: str, to_id: str) -> Optional["ConnectionItem"]:
        """Find visual connection between two nodes."""
        from_node = self.graph.get_node(from_id)
        if not from_node:
            return None
        for port_name, port in from_node.output_ports.items():
            for conn in port.connections:
                if conn.parent_node and conn.parent_node.node_id == to_id:
                    key = (from_id, port_name, to_id, conn.name)
                    conn_item = self._connection_items.get(key)
                    if conn_item:
                        return conn_item
        return None

    def _on_packet_moved(self, packet_id: str, from_id: str, to_id: str, packet_type: str):
        """Spawn animation when engine reports packet transit."""
        if not self._animations_enabled:
            return

        conn_item = self._find_connection_item(from_id, to_id)
        if not conn_item:
            return

        self._spawn_packet_animation(conn_item, packet_type)

    def _spawn_packet_animation(self, conn_item, packet_type: str):
        """Create and track a packet animation on a connection."""
        self._prune_finished_animations()

        if len(self._animations) >= self._max_concurrent_animations:
            oldest = self._animations.pop(0)
            oldest.stop()

        anim = PacketAnimation(
            conn_item,
            packet_type=packet_type,
            duration_ms=self._animation_duration_ms(),
        )
        anim.finished.connect(lambda a=anim: self._remove_animation(a))
        self._animations.append(anim)
        anim.start()

    def _prune_finished_animations(self):
        self._animations = [a for a in self._animations if a.is_active]

    def _remove_animation(self, anim):
        if anim in self._animations:
            self._animations.remove(anim)

    def start_animation(self):
        """Enable packet animations (simulation running)."""
        self._animations_enabled = True

    def pause_animations(self):
        """Pause in-flight animations without destroying them."""
        self._animations_enabled = False
        for anim in self._animations:
            anim.pause()

    def resume_animations(self):
        """Resume animations after pause or start."""
        self._animations_enabled = True
        for anim in self._animations:
            anim.resume()

    def stop_animation(self):
        """Stop and clear all packet animations."""
        self._animations_enabled = False
        for anim in list(self._animations):
            anim.stop()
        self._animations.clear()
    
    def clear_packets(self):
        """Clear all packet animations."""
        for anim in self._animations:
            anim.stop()
        self._animations.clear()
    
    def set_snap_to_grid(self, enabled: bool):
        """Enable/disable snap-to-grid."""
        self._snap_to_grid = enabled
    
    def zoom_to_fit(self):
        """Zoom to fit all nodes in the viewport."""
        if not self._node_items:
            return
        
        # Get bounding rect of all nodes
        rect = QRectF()
        for node_item in self._node_items.values():
            rect = rect.united(node_item.sceneBoundingRect())
        
        # Add some padding
        rect.adjust(-50, -50, 50, 50)
        
        # Fit the rect in the view
        self.fitInView(rect, Qt.KeepAspectRatio)
        
        # Clamp zoom level
        current_scale = self.transform().m11()
        if current_scale > 3.0:
            self.scale(3.0 / current_scale, 3.0 / current_scale)
        elif current_scale < 0.25:
            self.scale(0.25 / current_scale, 0.25 / current_scale)
        
        self._update_minimap()
    
    def export_to_image(self, file_path: str) -> bool:
        """
        Export canvas to image file.
        
        Args:
            file_path: Path to save the image
            
        Returns:
            True if successful
        """
        try:
            # Create a pixmap of the scene
            scene_rect = self.scene.sceneRect()
            pixmap = QPixmap(int(scene_rect.width()), int(scene_rect.height()))
            pixmap.fill(Qt.white)
            
            # Render scene to pixmap
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.TextAntialiasing)
            self.scene.render(painter)
            painter.end()
            
            # Save to file
            return pixmap.save(file_path)
        except Exception as e:
            import logging
            logger = logging.getLogger("Canvas")
            logger.error(f"Failed to export image: {e}")
            return False
