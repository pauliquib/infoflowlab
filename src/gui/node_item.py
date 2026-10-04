"""
Vizuální reprezentace uzlů a spojení na canvasu s profesionálním dark theme.
Uzly: 180×90px, zaoblené rohy, gradient hlavičky, drop shadow, LED status.
Porty: 20px vizuálně, 28px hit-area, barva podle typu dat.
Spojení: Bézierova křivka s glow efektem při přenosu.
Animace paketů: Bézierova interpolace s easeInOutCubic.
"""

from typing import Optional, Dict, List, Tuple, Any
import math
from enum import Enum
from PySide6.QtWidgets import (
    QGraphicsItem, QGraphicsRectItem, QGraphicsEllipseItem,
    QGraphicsTextItem, QGraphicsPathItem, QGraphicsSceneMouseEvent,
    QMenu, QGraphicsDropShadowEffect, QGraphicsObject,
    QStyleOptionGraphicsItem, QWidget, QPushButton, QVBoxLayout, QWidgetAction
)
from PySide6.QtCore import (
    Qt, QRectF, QPointF, Signal, QObject, QEvent, QTimer,
    QPropertyAnimation, QEasingCurve, Property
)
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPainterPath,
    QLinearGradient, QRadialGradient, QPolygonF
)

from src.core.node_base import NodeBase, NodeStatus
from src.core.port import PortType, DataType


# ============================================================
# BAREVNÉ SCHÉMA DLE KATEGORIE
# ============================================================
CATEGORY_COLORS = {
    "sources":        ("#4CAF50", "#2E7D32", "#1B5E20", "#81C784", "Zelená"),
    "encoders":       ("#2196F3", "#1565C0", "#0D47A1", "#64B5F6", "Modrá"),
    "decoders":       ("#03A9F4", "#0288D1", "#01579B", "#4FC3F7", "Světle modrá"),
    "compressors":    ("#FFC107", "#FFA000", "#FF6F00", "#FFD54F", "Žlutá"),
    "decompressors":  ("#FF9800", "#F57C00", "#E65100", "#FFB74D", "Oranžová"),
    "channels":       ("#FF5722", "#D84315", "#BF360C", "#FF8A65", "Červeno-oranžová"),
    "ecc":            ("#F44336", "#C62828", "#B71C1C", "#E57373", "Červená"),
    "checksums":      ("#9C27B0", "#7B1FA2", "#4A148C", "#BA68C8", "Fialová"),
    "analyzers":      ("#00BCD4", "#0097A7", "#006064", "#4DD0E1", "Cyan"),
    "signal":         ("#8BC34A", "#689F38", "#33691E", "#AED581", "Lime"),
    "sinks":          ("#607D8B", "#455A64", "#263238", "#90A4AE", "Šedá"),
    "general":        ("#757575", "#616161", "#424242", "#BDBDBD", "Šedá"),
}

# Port colors by data type
DATATYPE_COLORS = {
    DataType.BINARY:  "#E0E0E0",
    DataType.TEXT:    "#64B5F6",
    DataType.AUDIO:   "#4DD0E1",
    DataType.IMAGE:   "#AED581",
    DataType.NUMERIC: "#CE93D8",
    DataType.MORSE:   "#FFD54F",
    DataType.HUFFMAN: "#FFB74D",
    DataType.BASE64:  "#A5D6A7",
    DataType.HEX:     "#90A4AE",
    DataType.ANY:     "#E0E0E0",
}

# Status LED colors
STATUS_COLORS = {
    NodeStatus.IDLE:       ("#555555", "#222222"),
    NodeStatus.PROCESSING: ("#FFD600", "#FFA000"),
    NodeStatus.ERROR:      ("#FF1744", "#D50000"),
    NodeStatus.DONE:       ("#00E676", "#00C853"),
    NodeStatus.BYPASSED:   ("#90A4AE", "#607D8B"),
}


def get_category_colors(category: str) -> Tuple[QColor, QColor, QColor, QColor, str]:
    """Get color tuple for a category: (header_gradient_start, header_gradient_end, body, port, name)."""
    colors = CATEGORY_COLORS.get(category, CATEGORY_COLORS["general"])
    return (QColor(colors[0]), QColor(colors[1]), QColor(colors[2]), QColor(colors[3]), colors[4])


# ============================================================
# STATUS LED (MALÁ DIODA S PULZEM)
# ============================================================
class StatusLED(QGraphicsEllipseItem):
    """Status indicator LED (6px circle)."""
    
    def __init__(self, parent=None):
        super().__init__(-4, -4, 8, 8, parent)
        self._status = NodeStatus.IDLE
        self._pulse_timer = QTimer(None)
        self._pulse_timer.timeout.connect(self._pulse)
        self._pulse_value = 0
        self._pulse_dir = 1
        self.setZValue(20)
        self.update_color()
    
    def set_status(self, status: NodeStatus):
        self._status = status
        if status == NodeStatus.PROCESSING:
            if not self._pulse_timer.isActive():
                self._pulse_timer.start(50)
        else:
            self._pulse_timer.stop()
            self._pulse_value = 0
        self.update_color()
    
    def _pulse(self):
        self._pulse_value += self._pulse_dir * 0.15
        if self._pulse_value >= 1.0:
            self._pulse_dir = -1
        elif self._pulse_value <= 0.3:
            self._pulse_dir = 1
        self.update_color()
    
    def update_color(self):
        base_hex, _dark = STATUS_COLORS.get(self._status, STATUS_COLORS[NodeStatus.IDLE])
        base = QColor(base_hex)
        if self._status == NodeStatus.PROCESSING:
            # Pulse between base and bright
            r = base.red() + int((255 - base.red()) * self._pulse_value)
            g = base.green() + int((255 - base.green()) * self._pulse_value)
            b = base.blue() + int((255 - base.blue()) * self._pulse_value)
            color = QColor(min(255, r), min(255, g), min(255, b))
        else:
            color = base
        self.setBrush(QBrush(color))
        self.setPen(QPen(QColor("#FFFFFF"), 1))
        self.setZValue(20)


# ============================================================
# PORT ITEM (VYLEPŠENÝ)
# ============================================================
class PortItem(QGraphicsEllipseItem):
    """
    Vylepšený vizuální port.
    - 20px vizuální průměr, 28px hit-area
    - Barva podle typu dat
    - Při hover: scale 1.3× + glow
    """
    
    PORT_SIZE = 20      # vizuální průměr
    HIT_AREA = 28       # detekční zóna
    
    def __init__(self, parent_node_item: 'NodeItem', port_name: str, 
                 port_type: str, data_type: DataType = DataType.ANY):
        super().__init__(parent_node_item, -self.PORT_SIZE/2, -self.PORT_SIZE/2, self.PORT_SIZE, self.PORT_SIZE)
        self.parent_node_item = parent_node_item
        self.port_name = port_name
        self.port_type = port_type  # "input" or "output"
        self.data_type = data_type
        
        self._hovered = False
        self._glow_intensity = 0.0
        
        # Data for canvas connection detection
        self.setData(0, "port")
        self.setData(1, port_type)
        self.setData(2, port_name)
        
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)  # Must be selectable to receive mouse events
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, False)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.setZValue(10)
        
        self._update_appearance()
    
    def _get_color(self) -> QColor:
        """Get port color based on data type."""
        return QColor(DATATYPE_COLORS.get(self.data_type, "#E0E0E0"))
    
    def _update_appearance(self):
        color = self._get_color()
        self.setBrush(QBrush(color))
        self.setPen(QPen(color.darker(150), 2))
    
    def boundingRect(self):
        """Larger hit area for connection detection."""
        margin = (self.HIT_AREA - self.PORT_SIZE) / 2
        return QRectF(-self.PORT_SIZE/2 - margin, -self.PORT_SIZE/2 - margin,
                      self.PORT_SIZE + 2*margin, self.PORT_SIZE + 2*margin)
    
    def paint(self, painter: QPainter, option, widget=None):
        color = self._get_color()
        
        # Simple circle - no glow effects
        painter.setBrush(self.brush())
        painter.setPen(QPen(color.darker(150), 2))
        painter.drawEllipse(QPointF(0, 0), self.PORT_SIZE/2 - 1, self.PORT_SIZE/2 - 1)
        
        # Inner dot
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(0, 0), self.PORT_SIZE/4, self.PORT_SIZE/4)
    
    def hoverEnterEvent(self, event):
        self._hovered = True
        self.update()
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        self._hovered = False
        self.update()
        super().hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Directly notify canvas about port click
            scene = self.scene()
            if scene and scene.views():
                canvas = scene.views()[0]
                if hasattr(canvas, '_on_port_clicked'):
                    canvas._on_port_clicked(self)
                    event.accept()
                    return
        super().mousePressEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """Handle double-click to delete connections on this port."""
        if event.button() == Qt.LeftButton:
            scene = self.scene()
            if scene and scene.views():
                canvas = scene.views()[0]
                if hasattr(canvas, 'graph'):
                    node_id = self.parent_node_item.node.node_id
                    port_name = self.port_name
                    port_type = self.port_type

                    connections_to_remove = []
                    for conn in canvas.graph.connections:
                        if port_type == "input" and conn[2] == node_id and conn[3] == port_name:
                            connections_to_remove.append(conn)
                        elif port_type == "output" and conn[0] == node_id and conn[1] == port_name:
                            connections_to_remove.append(conn)

                    if connections_to_remove:
                        from src.core.undo_stack import RemoveConnectionCommand, MacroCommand
                        cmds = [
                            RemoveConnectionCommand(canvas, *conn)
                            for conn in connections_to_remove
                        ]
                        for conn in connections_to_remove:
                            canvas._connection_manager.remove_connection(*conn)
                        canvas.undo_stack.push_done(
                            MacroCommand("Odstranit spojení portu", cmds)
                        )
                        self._flash_port()
                        event.accept()
                        return

        super().mouseDoubleClickEvent(event)
    
    def _flash_port(self):
        """Brief visual feedback when connection is deleted."""
        # Flash to red briefly
        original_brush = self.brush()
        original_pen = self.pen()
        
        self.setBrush(QBrush(QColor("#FF1744")))
        self.setPen(QPen(QColor("#FF1744"), 3))
        self.update()
        
        # Restore after 200ms
        from PySide6.QtCore import QTimer
        QTimer.singleShot(200, lambda: self._restore_port_appearance(original_brush, original_pen))
    
    def _restore_port_appearance(self, original_brush, original_pen):
        """Restore port to original appearance."""
        self.setBrush(original_brush)
        self.setPen(original_pen)
        self.update()


# ============================================================
# NODE ITEM (KOMPLETNÍ REDESIGN)
# ============================================================
class NodeItem(QGraphicsRectItem):
    """
    Vizuální reprezentace uzlu na canvasu.
    - 180×90px, zaoblené rohy (radius 8px)
    - Gradient hlavičky dle kategorie
    - Drop shadow (blur 12px, opacity 0.4)
    - Status LED indikátor
    - Porty s barvou dle typu dat
    - Parametry jako micro-labels (max 2 řádky)
    - Tlačítka plus pro přidání portů
    """
    
    NODE_WIDTH = 180
    NODE_HEIGHT = 90
    HEADER_HEIGHT = 32
    CORNER_RADIUS = 8
    PORT_SPACING = 26
    
    def __init__(self, node: NodeBase, parent=None):
        super().__init__(parent)
        self.node = node
        
        # Rectangle with rounded corners
        self.setRect(0, 0, self.NODE_WIDTH, self.NODE_HEIGHT)
        
        # Position from node
        pos = getattr(node, 'position', (0, 0))
        self.setPos(pos[0], pos[1])
        
        # Flags
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        
        # Category colors
        self._header_start, self._header_end, self._body_color, self._port_color, _ = \
            get_category_colors(node.category)
        
        # Title text
        self.title_item = QGraphicsTextItem(node.name, self)
        self.title_item.setDefaultTextColor(Qt.white)
        title_font = QFont("Segoe UI", 10, QFont.Bold)
        self.title_item.setFont(title_font)
        self.title_item.setPos(28, 6)
        
        # Status LED
        self.status_led = StatusLED(self)
        self.status_led.setPos(12, self.HEADER_HEIGHT / 2)
        
        # Micro-labels for params (max 2 lines)
        self._param_labels: List[QGraphicsTextItem] = []
        self._update_param_labels()
        
        # Ports
        self.input_port_items: Dict[str, PortItem] = {}
        self.output_port_items: Dict[str, PortItem] = {}
        self._create_ports()
        
        
        # State
        self._hovered = False
        self._dragging = False
        
        # Connect node signals
        self.node.status_changed.connect(self._on_status_changed)
        self.node.param_changed.connect(self._on_param_changed)
    
    def _update_param_labels(self):
        """Update micro-labels showing node parameters."""
        # Remove old labels
        for label in self._param_labels:
            scene = self.scene()
            if scene:
                scene.removeItem(label)
            else:
                label.setParentItem(None)
        self._param_labels.clear()
        
        # Show first 2 params as micro-labels
        param_keys = list(self.node.params.keys())[:2]
        y_pos = self.HEADER_HEIGHT + 4
        for i, key in enumerate(param_keys):
            if i >= 2:
                break
            value = self.node.params.get(key, "")
            text = f"{key}: {str(value)[:15]}"
            label = QGraphicsTextItem(text, self)
            label.setDefaultTextColor(QColor("#AAAAAA"))
            font = QFont("Segoe UI", 7)
            label.setFont(font)
            label.setPos(6, y_pos)
            y_pos += 14
            self._param_labels.append(label)
        
        # Type label
        type_label = QGraphicsTextItem(self.node.node_type, self)
        type_label.setDefaultTextColor(QColor("#888888"))
        type_font = QFont("Segoe UI", 7)
        type_label.setFont(type_font)
        type_label.setPos(self.NODE_WIDTH - 60, self.NODE_HEIGHT - 14)
        self._param_labels.append(type_label)
    
    def _on_status_changed(self, status_str: str):
        """Update LED when node status changes."""
        try:
            status = NodeStatus(status_str)
            self.status_led.set_status(status)
        except ValueError:
            pass
    
    def _on_param_changed(self, key: str, value):
        """Update micro-labels when params change."""
        self._update_param_labels()
    
    def _create_ports(self):
        """Create visual ports for all node ports."""
        y_start = self.HEADER_HEIGHT + self.PORT_SPACING
        
        # Input ports (left side)
        for i, (name, port) in enumerate(self.node.input_ports.items()):
            port_item = PortItem(self, name, "input", port.data_type)
            port_item.setPos(0, y_start + i * self.PORT_SPACING)
            self.input_port_items[name] = port_item
        
        # Output ports (right side)
        for i, (name, port) in enumerate(self.node.output_ports.items()):
            port_item = PortItem(self, name, "output", port.data_type)
            port_item.setPos(self.NODE_WIDTH, y_start + i * self.PORT_SPACING)
            self.output_port_items[name] = port_item
    
    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        rect = QRectF(0, 0, self.NODE_WIDTH, self.NODE_HEIGHT)
        header_rect = QRectF(0, 0, self.NODE_WIDTH, self.HEADER_HEIGHT)
        body_rect = QRectF(0, self.HEADER_HEIGHT, self.NODE_WIDTH, self.NODE_HEIGHT - self.HEADER_HEIGHT)
        
        # Clip to rounded rect
        path = QPainterPath()
        path.addRoundedRect(rect, self.CORNER_RADIUS, self.CORNER_RADIUS)
        painter.setClipPath(path)
        
        # Flat header color (no gradient)
        painter.fillRect(header_rect, QBrush(self._header_start))
        
        # Body
        painter.fillRect(body_rect, QBrush(self._body_color))
        
        # Draw selection highlight (glowing border)
        if self.isSelected():
            # Outer glow effect
            glow_pen = QPen(QColor("#2196F3"), 3)
            glow_pen.setStyle(Qt.SolidLine)
            painter.setPen(glow_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect.adjusted(-2, -2, 2, 2), self.CORNER_RADIUS, self.CORNER_RADIUS)
            
            # Inner highlight
            highlight_pen = QPen(QColor("#64B5F6"), 2)
            painter.setPen(highlight_pen)
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), self.CORNER_RADIUS - 1, self.CORNER_RADIUS - 1)
        
    def hoverEnterEvent(self, event):
        self._hovered = True
        self.update()
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        self._hovered = False
        self.update()
        super().hoverLeaveEvent(event)
    
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            QTimer.singleShot(0, self._update_connections)
            # Update node position
            self.node.position = (self.pos().x(), self.pos().y())
        return super().itemChange(change, value)
    
    def set_dragging_enabled(self, enabled: bool):
        """Enable or disable node dragging."""
        self._original_movable = enabled
        self.setFlag(QGraphicsItem.ItemIsMovable, enabled)
    
    def mousePressEvent(self, event):
        """Intercept mouse press to allow port clicks."""
        if event.button() == Qt.LeftButton:
            for port_item in list(self.input_port_items.values()) + list(self.output_port_items.values()):
                if port_item.boundingRect().contains(port_item.mapFromParent(event.pos())):
                    port_item.mousePressEvent(event)
                    event.accept()
                    return

            scene = self.scene()
            if scene and scene.views():
                canvas = scene.views()[0]
                if hasattr(canvas, '_connection_manager') and canvas._connection_manager.is_connecting():
                    event.accept()
                    return
                if hasattr(canvas, 'on_node_drag_started'):
                    canvas.on_node_drag_started(self.node.node_id)

        super().mousePressEvent(event)

    def _update_connections(self):
        """Update all connections for this node."""
        scene = self.scene()
        if not scene or not scene.views():
            return
        view = scene.views()[0]
        if hasattr(view, '_update_connections_for_node'):
            view._update_connections_for_node(self.node.node_id)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        scene = self.scene()
        if scene and scene.views():
            canvas = scene.views()[0]
            if hasattr(canvas, '_connection_manager') and canvas._connection_manager.is_connecting():
                event.accept()
                return

        if event.buttons() == Qt.LeftButton:
            self._dragging = True
            super().mouseMoveEvent(event)
            self.node.position = (self.pos().x(), self.pos().y())

    def mouseReleaseEvent(self, event):
        self._dragging = False
        scene = self.scene()
        if scene and scene.views():
            canvas = scene.views()[0]
            if hasattr(canvas, 'on_node_drag_finished'):
                canvas.on_node_drag_finished(self.node.node_id)
        super().mouseReleaseEvent(event)
    
    def get_port_scene_pos(self, port_name: str, port_type: str) -> QPointF:
        """Get scene position of a port."""
        if port_type == "input" and port_name in self.input_port_items:
            return self.mapToScene(self.input_port_items[port_name].pos())
        elif port_type == "output" and port_name in self.output_port_items:
            return self.mapToScene(self.output_port_items[port_name].pos())
        return self.scenePos() + QPointF(self.NODE_WIDTH / 2, self.NODE_HEIGHT / 2)
    
    def contextMenuEvent(self, event):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu { background-color: #2d2d2d; color: white; border: 1px solid #555; }
            QMenu::item:selected { background-color: #094771; }
        """)
        
        duplicate_action = menu.addAction("📋 Duplikovat")
        menu.addSeparator()
        mute_action = menu.addAction("🔇 Vypnout" if not self.node._bypass else "🔊 Zapnout")
        menu.addSeparator()
        configure_action = menu.addAction("⚙️ Konfigurovat")
        help_action = menu.addAction("❓ Nápověda")
        menu.addSeparator()
        delete_action = menu.addAction("🗑️ Odstranit uzel")
        
        action = menu.exec(event.screenPos())
        
        if action == delete_action:
            scene = self.scene()
            if scene and scene.views():
                view = scene.views()[0]
                if hasattr(view, 'remove_node_item'):
                    view.remove_node_item(self)
        elif action == duplicate_action:
            scene = self.scene()
            if scene and scene.views():
                view = scene.views()[0]
                if hasattr(view, 'duplicate_node_item'):
                    view.duplicate_node_item(self)
        elif action == mute_action:
            self.node.set_param("bypass", not self.node._bypass)
        elif action == configure_action:
            # Select node for inspector
            self.setSelected(True)
        elif action == help_action:
            # Show help in console
            print(f"Help for {self.node.name}: {self.node.node_type}")
    
    def get_port_item(self, port_type: str, port_name: str) -> Optional[PortItem]:
        """Get PortItem by type and name."""
        if port_type == "input":
            return self.input_port_items.get(port_name)
        elif port_type == "output":
            return self.output_port_items.get(port_name)
        return None


# ============================================================
# CONNECTION ITEM (BÉZIER S GLOW EFEKTEM)
# ============================================================
class ConnectionItem(QGraphicsPathItem):
    """
    Spojení mezi uzly (Bézierova křivka) s glow efektem při přenosu.
    - Cached QPainterPath pro rychlé překreslování
    - Glow efekt při průchodu paketu
    - Badge s počtem paketů ve frontě
    - Selectable for deletion
    """
    
    def __init__(self, from_node: NodeItem, from_port: str,
                 to_node: NodeItem, to_port: str, parent=None):
        super().__init__(parent)
        self.from_node = from_node
        self.from_port = from_port
        self.to_node = to_node
        self.to_port = to_port
        
        # Make connection selectable
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        
        self.setPen(QPen(QColor("#B0BEC5"), 2))
        self.setZValue(1)  # Above nodes (0) but below ports (10)
        
        # Glow effect
        self._glow_opacity = 0.0
        self._glow_timer = QTimer()
        self._glow_timer.timeout.connect(self._fade_glow)
        self._glow_timer.setSingleShot(True)
        
        self._badge_count = 0
        self._badge_item: Optional[QGraphicsTextItem] = None
        
        self.update_path()
    
    def update_path(self):
        """Update the Bézier path, optionally through reroute points."""
        start = self.from_node.get_port_scene_pos(self.from_port, "output")
        end = self.to_node.get_port_scene_pos(self.to_port, "input")

        reroute_points = []
        graph = None
        scene = self.scene()
        if scene and scene.views():
            graph = scene.views()[0].graph
        if graph:
            meta = graph.get_connection_metadata(
                self.from_node.node.node_id, self.from_port,
                self.to_node.node.node_id, self.to_port
            )
            for pt in meta.get("reroute_points", []):
                reroute_points.append(QPointF(pt[0], pt[1]))

        path = QPainterPath()
        path.moveTo(start)

        if reroute_points:
            prev = start
            for rp in reroute_points:
                dx = abs(rp.x() - prev.x()) * 0.5
                if dx < 30:
                    dx = 30
                ctrl1 = QPointF(prev.x() + dx, prev.y())
                ctrl2 = QPointF(rp.x() - dx, rp.y())
                path.cubicTo(ctrl1, ctrl2, rp)
                prev = rp
            dx = abs(end.x() - prev.x()) * 0.5
            if dx < 30:
                dx = 30
            ctrl1 = QPointF(prev.x() + dx, prev.y())
            ctrl2 = QPointF(end.x() - dx, end.y())
            path.cubicTo(ctrl1, ctrl2, end)
        else:
            dx = abs(end.x() - start.x()) * 0.5
            if dx < 50:
                dx = 50
            ctrl1 = QPointF(start.x() + dx, start.y())
            ctrl2 = QPointF(end.x() - dx, end.y())
            path.cubicTo(ctrl1, ctrl2, end)

        self.setPath(path)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.modifiers() & Qt.AltModifier:
            scene = self.scene()
            if scene and scene.views():
                canvas = scene.views()[0]
                conn = (
                    self.from_node.node.node_id, self.from_port,
                    self.to_node.node.node_id, self.to_port
                )
                if hasattr(canvas, 'cut_wire_with_undo'):
                    canvas.cut_wire_with_undo(*conn)
                    event.accept()
                    return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Double-click to add reroute point on wire."""
        if event.button() == Qt.LeftButton:
            scene = self.scene()
            if scene and scene.views():
                canvas = scene.views()[0]
                pos = event.scenePos()
                if hasattr(canvas, '_connection_manager'):
                    canvas._connection_manager.add_reroute_point(
                        self.from_node.node.node_id, self.from_port,
                        self.to_node.node.node_id, self.to_port,
                        pos.x(), pos.y()
                    )
                    event.accept()
                    return
        super().mouseDoubleClickEvent(event)
    
    def boundingRect(self):
        """Return bounding rect with larger hit area for easier selection."""
        # Get the normal path bounding rect
        rect = super().boundingRect()
        # Add padding to make it easier to click (10px on each side)
        padding = 10
        return rect.adjusted(-padding, -padding, padding, padding)
    
    def shape(self):
        """Return shape with thicker stroke for better hit detection."""
        from PySide6.QtGui import QPainterPathStroker
        # Create a stroker to make the path thicker for hit detection
        stroker = QPainterPathStroker()
        stroker.setWidth(15)  # 15px wide hit area
        stroker.setCapStyle(Qt.SquareCap)
        stroker.setJoinStyle(Qt.MiterJoin)
        return stroker.createStroke(self.path())
    
    def trigger_glow(self):
        """Trigger glow effect when a packet passes through."""
        self._glow_opacity = 1.0
        self.update()
        self._glow_timer.start(300)
    
    def _fade_glow(self):
        """Fade out glow effect."""
        self._glow_opacity = 0.0
        self.update()
    
    def set_badge(self, count: int):
        """Set queue badge count."""
        self._badge_count = count
        if count > 1:
            if self._badge_item is None:
                self._badge_item = QGraphicsTextItem(self)
                self._badge_item.setDefaultTextColor(Qt.white)
                self._badge_item.setFont(QFont("Segoe UI", 8, QFont.Bold))
            self._badge_item.setPlainText(str(count))
            # Position at midpoint
            mid = self.path().pointAtPercent(0.5)
            self._badge_item.setPos(mid.x() - 8, mid.y() - 10)
        elif self._badge_item:
            if self._badge_item.scene():
                self._badge_item.scene().removeItem(self._badge_item)
            self._badge_item = None
    
    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Highlight if selected
        if self.isSelected():
            # Glow effect for selected connection
            glow_pen = QPen(QColor("#2196F3"), 4)
            glow_pen.setStyle(Qt.SolidLine)
            painter.setPen(glow_pen)
            painter.drawPath(self.path())
            
            # Inner line
            pen = QPen(QColor("#64B5F6"), 2)
            painter.setPen(pen)
            painter.drawPath(self.path())
        else:
            # Base line only - no glow effects
            pen = QPen(QColor("#B0BEC5"), 2)
            painter.setPen(pen)
            painter.drawPath(self.path())
    
    def update_positions(self):
        """Update path when nodes move."""
        self.update_path()
    
    def point_at_percent(self, t: float) -> QPointF:
        """Get point on curve at parameter t (0-1)."""
        return self.path().pointAtPercent(t)
    
    def tangent_at_percent(self, t: float) -> float:
        """Get tangent angle at parameter t."""
        pct = 0.01
        p1 = self.path().pointAtPercent(max(0, t - pct))
        p2 = self.path().pointAtPercent(min(1, t + pct))
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        if abs(dx) < 0.001 and abs(dy) < 0.001:
            return 0.0
        return math.degrees(math.atan2(dy, dx))


# ============================================================
# PACKET ANIMATION (BÉZIEROVA INTERPOLACE)
# ============================================================
PACKET_VISUAL_COLORS = {
    "text":    ("#1565C0", "#42A5F5", "#90CAF9"),
    "audio":   ("#00838F", "#26C6DA", "#80DEEA"),
    "binary":  ("#2E7D32", "#66BB6A", "#A5D6A7"),
    "image":   ("#558B2F", "#9CCC65", "#C5E1A5"),
    "error":   ("#C62828", "#EF5350", "#FFCDD2"),
    "default": ("#F57F17", "#FFCA28", "#FFF59D"),
}


class PacketOrbItem(QGraphicsObject):
    """Glowing orb with particle trail for packet transit."""

    def __init__(self, packet_type: str = "text", parent=None):
        super().__init__(parent)
        self.packet_type = packet_type
        self._pulse = 1.0
        self._trail: List[Tuple[float, float, float]] = []
        self.setZValue(15)
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations, False)

    def boundingRect(self) -> QRectF:
        radius = 18
        return QRectF(-radius, -radius, radius * 2, radius * 2)

    @Property(float)
    def pulse(self) -> float:
        return self._pulse

    @pulse.setter
    def pulse(self, value: float):
        self._pulse = value
        self.update()

    def add_trail_point(self):
        self._trail.insert(0, (0.0, 0.0, 1.0))
        self._trail = [
            (x, y, max(0.0, opacity - 0.18))
            for x, y, opacity in self._trail[:7]
            if opacity > 0.08
        ]
        self.update()

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing, True)
        core, mid, glow = PACKET_VISUAL_COLORS.get(
            self.packet_type, PACKET_VISUAL_COLORS["default"]
        )

        for i, (tx, ty, opacity) in enumerate(self._trail):
            size = 5.0 - i * 0.4
            grad = QRadialGradient(tx, ty, size * 1.6)
            grad.setColorAt(0.0, QColor(mid))
            grad.setColorAt(0.6, QColor(glow))
            grad.setColorAt(1.0, Qt.transparent)
            painter.setOpacity(opacity * 0.55)
            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(tx, ty), size, size)

        painter.setOpacity(1.0)
        outer = QRadialGradient(0, 0, 14 * self._pulse)
        outer.setColorAt(0.0, QColor(glow))
        outer.setColorAt(0.45, QColor(mid))
        outer.setColorAt(1.0, Qt.transparent)
        painter.setBrush(QBrush(outer))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(0, 0), 14 * self._pulse, 14 * self._pulse)

        inner = QRadialGradient(-1.5, -1.5, 6)
        inner.setColorAt(0.0, QColor("#FFFFFF"))
        inner.setColorAt(0.35, QColor(mid))
        inner.setColorAt(1.0, QColor(core))
        painter.setBrush(QBrush(inner))
        painter.drawEllipse(QPointF(0, 0), 5.5, 5.5)

        painter.setPen(QPen(QColor("#FFFFFF"), 1.2))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(0, 0), 6.5, 6.5)


class PacketAnimation(QObject):
    """
    Animace paketu po Bézierově křivce spojení.
    - easeInOutCubic interpolace
    - Typově barevný orb s pulzujícím jádrem a částicovým ocasem
    - Rotace dle tangenty křivky, glow na spojení při průchodu
    """

    finished = Signal()
    BASE_DURATION_MS = 650

    def __init__(self, connection_item: ConnectionItem, packet_type: str = "text",
                 duration_ms: Optional[int] = None, parent=None):
        super().__init__(parent)
        self.connection = connection_item
        self.packet_type = packet_type
        self.duration_ms = duration_ms or self.BASE_DURATION_MS

        self._main_item: Optional[PacketOrbItem] = None
        self._t = 0.0
        self._animation: Optional[QPropertyAnimation] = None
        self._pulse_animation: Optional[QPropertyAnimation] = None
        self._mid_glow_triggered = False
        self._active = False

    @Property(float)
    def t(self):
        return self._t

    @t.setter
    def t(self, value: float):
        self._t = value
        self._update_position()

    def start(self):
        """Start the animation."""
        if self._active and self._animation and self._animation.state() == QPropertyAnimation.Running:
            return

        scene = self.connection.scene()
        if not scene:
            return

        self._active = True
        self._mid_glow_triggered = False
        self._main_item = PacketOrbItem(self.packet_type)
        scene.addItem(self._main_item)
        self.connection.trigger_glow()

        self._animation = QPropertyAnimation(self, b"t")
        self._animation.setDuration(self.duration_ms)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.setEasingCurve(QEasingCurve.InOutCubic)
        self._animation.finished.connect(self._on_finished)
        self._animation.start()

        self._pulse_animation = QPropertyAnimation(self._main_item, b"pulse")
        self._pulse_animation.setDuration(420)
        self._pulse_animation.setStartValue(0.85)
        self._pulse_animation.setEndValue(1.15)
        self._pulse_animation.setEasingCurve(QEasingCurve.InOutSine)
        self._pulse_animation.setLoopCount(-1)
        self._pulse_animation.start()

    def _update_position(self):
        """Update packet position along the Bézier curve."""
        if not self._main_item:
            return

        pos = self.connection.point_at_percent(self._t)
        angle = self.connection.tangent_at_percent(self._t)

        self._main_item.setPos(pos)
        self._main_item.setRotation(angle)
        self._main_item.add_trail_point()

        if self._t >= 0.45 and not self._mid_glow_triggered:
            self._mid_glow_triggered = True
            self.connection.trigger_glow()

    def _on_finished(self):
        """Clean up when animation completes."""
        if self._pulse_animation:
            self._pulse_animation.stop()
            self._pulse_animation = None

        if self._main_item and self._main_item.scene():
            self._main_item.scene().removeItem(self._main_item)
        self._main_item = None
        self._active = False

        self.connection.trigger_glow()
        self.finished.emit()

    def pause(self):
        """Pause animation in sync with simulation pause."""
        if self._animation and self._animation.state() == QPropertyAnimation.Running:
            self._animation.pause()
        if self._pulse_animation and self._pulse_animation.state() == QPropertyAnimation.Running:
            self._pulse_animation.pause()

    def resume(self):
        """Resume paused animation."""
        if self._animation and self._animation.state() == QPropertyAnimation.Paused:
            self._animation.resume()
        if self._pulse_animation and self._pulse_animation.state() == QPropertyAnimation.Paused:
            self._pulse_animation.resume()

    def stop(self):
        """Stop animation immediately."""
        if self._animation:
            self._animation.stop()
        if self._pulse_animation:
            self._pulse_animation.stop()
        self._on_finished()

    @property
    def is_active(self) -> bool:
        return self._active