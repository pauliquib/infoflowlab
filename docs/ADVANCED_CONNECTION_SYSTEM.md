# Advanced Connection Management & Routing System
## InfoSim - Architecture Documentation

---

## Table of Contents
1. [Overview](#overview)
2. [Core Concepts](#core-concepts)
3. [Data Structures](#data-structures)
4. [Multi-Branching & Port Capacity](#multi-branching--port-capacity)
5. [Type Safety & Smart Snapping](#type-safety--smart-snapping)
6. [Reroute Nodes](#reroute-nodes)
7. [Wire Cutting](#wire-cutting)
8. [Integration Guide](#integration-guide)
9. [API Reference](#api-reference)

---

## Overview

The Advanced Connection Management System upgrades basic 1-to-1 wire connections into a modern, flexible routing system inspired by Unreal Engine Blueprints and Blender Geometry Nodes.

### Key Features
- **1-to-N Broadcasting**: Single output → multiple inputs
- **Port Capacity Limits**: Configurable max_connections per port
- **Auto-Replacement**: Automatic old wire removal when capacity = 1
- **Type Safety**: Data-type aware connection validation
- **Smart Snapping**: Visual highlighting of compatible ports
- **Reroute Nodes**: Invisible anchor points for wire organization
- **Wire Cutting**: Alt+Click quick detachment

### Architecture Philosophy
```
┌─────────────────────────────────────────────────────────┐
│         AdvancedConnectionState (Central State)         │
│  ┌───────────────┬──────────────┬──────────────────┐  │
│  │ Capacity      │ Reroute      │ Smart Snapping   │  │
│  │ Manager       │ Node Manager │ System           │  │
│  └───────────────┴──────────────┴──────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │         Wire Cutter (Alt+Click)                  │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
         ↓ manages          ↓ manages
┌─────────────────────────────────────────────────────────┐
│              Graph (Core Data Layer)                     │
│  - Nodes, Ports, Connections                            │
│  - Cycle detection, validation                          │
└─────────────────────────────────────────────────────────┘
         ↓ renders
┌─────────────────────────────────────────────────────────┐
│         ConnectionManager (GUI Layer)                    │
│  - Bezier curves, visual feedback                       │
│  - Event-driven updates, 60 FPS optimization            │
└─────────────────────────────────────────────────────────┘
```

---

## Core Concepts

### 1. Port Capacity System

Every port has a `max_connections` property defining its capacity:

| Mode | max_connections | Behavior |
|------|----------------|----------|
| `SINGLE` | 1 | Only one connection, auto-replaces old |
| `MULTIPLE` | N | Up to N connections (broadcasting) |
| `UNLIMITED` | 0 or None | Unlimited connections |

**Example:**
```python
# Output port can broadcast to 5 inputs
output_port.max_connections = 5

# Input port accepts only one, auto-replaces
input_port.max_connections = 1

# Unlimited (default)
port.max_connections = 0
```

### 2. Connection Data Flow

```
Output Port (1) ──┬──→ Input Port A
                  ├──→ Input Port B
                  ├──→ Input Port C
                  └──→ Input Port D
                   
1-to-N Broadcasting: One source, multiple targets
```

### 3. Reroute Nodes

Reroute nodes are **purely visual** - they don't affect data flow:

```
Original: Node A ──────────────→ Node B
                    ↓ double-click
With Reroute: Node A ──→ [REROUTE] ──→ Node B
                         (invisible)
                         
Data flow: A → B (unchanged)
Visual: A → reroute.position → B (organized)
```

---

## Data Structures

### ConnectionSplineData
Stores Bezier curve geometry for a connection:

```python
@dataclass
class ConnectionSplineData:
    start_point: QPointF          # Source port position
    end_point: QPointF            # Target port position
    control_point_1: QPointF      # First Bezier control point
    control_point_2: QPointF      # Second Bezier control point
    reroute_points: List[QPointF] # Anchor points for reroutes
```

### RerouteNodeData
Invisible pass-through anchor:

```python
@dataclass
class RerouteNodeData:
    id: str                       # Unique ID (e.g., "reroute_1")
    position: QPointF             # Scene position
    in_link: Tuple                # (from_node, from_port, to_node, to_port)
    out_link: Tuple               # Same as in_link (transparent)
    control_point_offset: float   # Bezier smoothness (default: 50px)
```

### AdvancedConnection
Rich connection object:

```python
@dataclass
class AdvancedConnection:
    id: str                       # "conn_1", "conn_2", etc.
    source_port_id: str           # "node_id:port_name"
    target_port_id: str           # "node_id:port_name"
    spline_data: ConnectionSplineData
    reroute_nodes: List[RerouteNodeData]
    metadata: Dict[str, Any]      # bandwidth, latency, etc.
```

---

## Multi-Branching & Port Capacity

### Implementation Logic

#### 1. Capacity Check
```python
def can_accept_connection(self, port: Port, max_connections: int = None):
    """Check if port can accept new connection."""
    
    # Determine capability
    if max_connections == 0 or max_connections is None:
        capability = ConnectionCapability.UNLIMITED
    elif max_connections == 1:
        capability = ConnectionCapability.SINGLE
    else:
        capability = ConnectionCapability.MULTIPLE
    
    # Get current count
    current_count = self._capacity_cache.get(port_id, 0)
    
    # Validate
    if capability == ConnectionCapability.UNLIMITED:
        return True, "Unlimited"
    elif capability == ConnectionCapability.SINGLE:
        if current_count == 0:
            return True, "Available"
        else:
            return True, "Will replace"  # Auto-replace enabled
    else:  # MULTIPLE
        if current_count < max_connections:
            return True, f"{current_count}/{max_connections}"
        else:
            return False, "Full"
```

#### 2. Auto-Replacement Logic
```python
def auto_replace_connection(self, port: Port, old_connection: tuple):
    """
    When max_connections = 1 and user drags new wire:
    1. Find existing connection
    2. Disconnect old wire
    3. Update capacity cache
    4. Allow new connection
    """
    
    # Find existing connection
    for conn in self.graph.connections:
        if conn[2] == port.parent_node.node_id and conn[3] == port.name:
            old_connection = conn
            break
    
    # Disconnect old
    self.graph.disconnect(*old_connection)
    
    # Update cache
    self._capacity_cache[old_from] -= 1
    self._capacity_cache[old_to] -= 1
    
    return True
```

#### 3. 1-to-N Broadcasting
```python
# Output port with max_connections = 5
output_port.max_connections = 5

# Can connect to multiple inputs:
output_port.connect(input_port_1)  # ✓
output_port.connect(input_port_2)  # ✓
output_port.connect(input_port_3)  # ✓
output_port.connect(input_port_4)  # ✓
output_port.connect(input_port_5)  # ✓
output_port.connect(input_port_6)  # ✗ (max reached)
```

### Visual: Multiple Splines from Same Point
```python
def draw_broadcast_wires(self, output_pos: QPointF, 
                         input_positions: List[QPointF]):
    """
    Draw multiple Bezier curves from same output point.
    Critical: All curves must originate from exact same coordinate.
    """
    for i, input_pos in enumerate(input_positions):
        # Slight vertical offset to prevent visual overlap
        offset = QPointF(0, i * 2)  # 2px spacing
        
        path = QPainterPath()
        path.moveTo(output_pos + offset)
        
        # Calculate control points
        dx = abs(input_pos.x() - output_pos.x()) * 0.5
        ctrl1 = QPointF(output_pos.x() + dx, output_pos.y())
        ctrl2 = QPointF(input_pos.x() - dx, input_pos.y())
        
        path.cubicTo(ctrl1, ctrl2, input_pos)
        
        # Draw with slight opacity variation
        pen = QPen(QColor("#B0BEC5"), 2)
        pen.setOpacity(1.0 - (i * 0.1))  # Fade out later wires
        self.scene.addPath(path, pen)
```

---

## Type Safety & Smart Snapping

### Type Compatibility Matrix

```python
class DataType(Enum):
    BINARY = "binary"
    TEXT = "text"
    AUDIO = "audio"
    IMAGE = "image"
    NUMERIC = "numeric"
    ANY = "any"  # Universal connector
    
    @staticmethod
    def is_compatible(source: DataType, target: DataType) -> bool:
        # ANY connects to everything
        if source == DataType.ANY or target == DataType.ANY:
            return True
        
        # Same types always compatible
        if source == target:
            return True
        
        # Special compatibilities
        compatibilities = [
            {DataType.TEXT, DataType.BINARY},      # Text ↔ Binary
            {DataType.NUMERIC, DataType.TEXT},     # Numeric ↔ Text
            {DataType.NUMERIC, DataType.BINARY},   # Numeric ↔ Binary
        ]
        
        return {source, target} in compatibilities
```

### Smart Snapping Visual Feedback

When user drags a wire from an output port:

```
Scene State During Drag:
┌─────────────────────────────────────────────┐
│  Node A (Output: BINARY)                    │
│    ○ ────────── (dragging...)               │
│                                             │
│  Node B (Input: TEXT)     Node C (Input: BINARY) │
│    ○ [GREEN ✓]              ○ [GREEN ✓]     │
│    (compatible)             (compatible)     │
│                                             │
│  Node D (Input: AUDIO)     Node E (Input: TEXT)│
│    ○ [RED ✗]                ○ [GRAY ⊘]      │
│    (incompatible)           (already used)   │
│                                             │
│  Node F (Input: BINARY)    Node G (Input: BINARY)│
│    ○ [ORANGE !]             ○ [ORANGE !]     │
│    (will replace)           (will replace)   │
└─────────────────────────────────────────────┘

Legend:
  ✓ Green = Valid target
  ✗ Red = Invalid (wrong type)
  ⊘ Gray = Invalid (already connected)
  ! Orange = Valid but will replace existing
```

### Implementation: Highlight System

```python
class SmartSnappingSystem:
    """Type-aware port highlighting during wire drag."""
    
    def analyze_drop_targets(self, source_port_id: str, 
                            source_data_type: DataType,
                            source_port_type: str) -> Dict:
        """
        Analyze all ports and classify them.
        Returns categorized lists for rendering.
        """
        results = {
            "valid_targets": [],      # Green highlight
            "invalid_type": [],       # Red highlight
            "already_connected": [],  # Gray/dim
            "capacity_warnings": []   # Orange highlight
        }
        
        for node_id, node_item in canvas.items():
            if node_id == source_node_id:
                continue  # Skip self
            
            for port_name, port_item in node_item.ports:
                # Must be opposite type
                if port_item.port_type == source_port_type:
                    results["invalid_type"].append(port_item)
                    continue
                
                # Check type compatibility
                if not DataType.is_compatible(source_data_type, 
                                             port_item.data_type):
                    results["invalid_type"].append(port_item)
                    continue
                
                # Check if already connected
                if self._is_port_connected(node_id, port_name):
                    results["already_connected"].append(port_item)
                    continue
                
                # Check capacity
                if port_item.max_connections == 1:
                    results["capacity_warnings"].append(port_item)
                else:
                    results["valid_targets"].append(port_item)
        
        return results
    
    def apply_visual_feedback(self, analysis: Dict):
        """Apply colors to ports based on analysis."""
        
        # Valid targets → Green glow
        for port in analysis["valid_targets"]:
            port.setBrush(QBrush(QColor("#00FF00")))
            port.setPen(QPen(QColor("#00FF00"), 3))
        
        # Invalid type → Red
        for port in analysis["invalid_type"]:
            port.setBrush(QBrush(QColor("#FF0000")))
            port.setPen(QPen(QColor("#FF0000"), 3))
        
        # Already connected → Dimmed
        for port in analysis["already_connected"]:
            port.setOpacity(0.3)
        
        # Capacity warning → Orange
        for port in analysis["capacity_warnings"]:
            port.setBrush(QBrush(QColor("#FFAA00")))
            port.setPen(QPen(QColor("#FFAA00"), 3))
```

---

## Reroute Nodes

### Concept

Reroute nodes are **invisible to data logic** - they only affect visual wire routing:

```
Data Flow (unchanged):
Node A → Node B

Visual Flow (with reroute):
Node A ──→ [REROUTE at (300, 200)] ──→ Node B
              ↑
              User double-clicked wire here
              Can drag reroute to organize wires
```

### Creation: Double-Click on Wire

```python
def on_wire_double_click(self, connection_id: str, 
                         scene_pos: QPointF):
    """
    User double-clicks on a wire → create reroute node.
    """
    
    # Parse connection
    from_node, from_port, to_node, to_port = connection_id.split(":")
    
    # Create reroute node
    reroute_id = f"reroute_{self._next_id}"
    reroute = RerouteNodeData(
        id=reroute_id,
        position=scene_pos,
        in_link=(from_node, from_port, to_node, to_port),
        out_link=(from_node, from_port, to_node, to_port)
    )
    
    # Store reroute
    self.reroute_nodes[reroute_id] = reroute
    
    # Update connection routing
    # Original: A → B
    # New: A → reroute → B
    self._split_connection_with_reroute(
        from_node, from_port, to_node, to_port, reroute
    )
    
    # Create visual anchor point (tiny, subtle)
    self._create_reroute_visual(reroute)
```

### Bezier Curve Through Reroute

```python
def calculate_reroute_spline(self, start: QPointF, 
                             reroute: QPointF,
                             end: QPointF) -> QPainterPath:
    """
    Calculate Bezier curve passing through reroute node.
    
    Splits into two curves:
    1. start → reroute
    2. reroute → end
    """
    path = QPainterPath()
    
    # First segment: start → reroute
    path.moveTo(start)
    
    dx1 = abs(reroute.x() - start.x()) * 0.5
    ctrl1 = QPointF(start.x() + dx1, start.y())
    ctrl2 = QPointF(reroute.x() - dx1, reroute.y())
    path.cubicTo(ctrl1, ctrl2, reroute)
    
    # Second segment: reroute → end
    dx2 = abs(end.x() - reroute.x()) * 0.5
    ctrl3 = QPointF(reroute.x() + dx2, reroute.y())
    ctrl4 = QPointF(end.x() - dx2, end.y())
    path.cubicTo(ctrl3, ctrl4, end)
    
    return path
```

### Reroute Node Interaction

```python
class RerouteNodeItem(QGraphicsEllipseItem):
    """
    Visual representation of reroute node.
    - Tiny (8px diameter)
    - Subtle gray color
    - Only visible on hover
    - Draggable
    """
    
    SIZE = 8
    COLOR = QColor("#888888")
    
    def __init__(self, reroute_data: RerouteNodeData):
        super().__init__(-self.SIZE/2, -self.SIZE/2, 
                        self.SIZE, self.SIZE)
        self.reroute_data = reroute_data
        
        # Initially invisible
        self.setOpacity(0.0)
        
        # Show on hover
        self.setAcceptHoverEvents(True)
    
    def hoverEnterEvent(self, event):
        """Fade in on hover."""
        self.setOpacity(0.8)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Fade out when not hovering."""
        self.setOpacity(0.0)
        super().hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):
        """Start dragging."""
        self._drag_start = event.scenePos()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Update position during drag."""
        delta = event.scenePos() - self._drag_start
        self.reroute_data.position += delta
        self._drag_start = event.scenePos()
        
        # Trigger connection redraw
        self.scene().views()[0]._redraw_connections()
        
        super().mouseMoveEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """Delete reroute on double-click."""
        self.scene().views()[0]._delete_reroute(self.reroute_data.id)
        super().mouseDoubleClickEvent(event)
```

### Chaining Reroute Nodes

Multiple reroutes can be chained for complex routing:

```
Node A ──→ [R1] ──→ [R2] ──→ [R3] ──→ Node B
              ↑          ↑          ↑
           (300,200)  (400,150)  (500,200)
           
Each reroute is independent and draggable.
Wire smoothly curves through all anchor points.
```

---

## Wire Cutting

### Alt+Click Detachment

```python
class WireCutter:
    """Quick-action wire cutting system."""
    
    def on_port_alt_click(self, node_id: str, port_name: str, 
                         port_type: str):
        """
        Alt+Click on port → remove all connections.
        
        Interaction:
        1. User holds Alt key
        2. Clicks on a port
        3. All wires connected to that port are instantly removed
        4. Visual feedback: brief red flash on port
        """
        
        # Find all connections involving this port
        if port_type == "output":
            connections = [
                conn for conn in self.graph.connections
                if conn[0] == node_id and conn[1] == port_name
            ]
        else:
            connections = [
                conn for conn in self.graph.connections
                if conn[2] == node_id and conn[3] == port_name
            ]
        
        # Remove all connections
        for conn in connections:
            self.graph.disconnect(*conn)
            self.connection_manager._unregister_connection(*conn)
        
        # Trigger redraw
        self.canvas._redraw_connections()
        
        # Visual feedback
        self._flash_port_red(node_id, port_name, port_type)
        
        return len(connections)  # Return count for feedback
```

### Scissors Tool Mode

```python
def toggle_scissors_mode(self, enabled: bool):
    """
    Toggle scissors tool for cutting wires.
    
    When enabled:
    - Cursor changes to scissors icon
    - Clicking on a wire cuts it
    - Clicking on empty space cancels mode
    """
    self._scissors_mode = enabled
    
    if enabled:
        self.canvas.setCursor(Qt.CrossCursor)  # Or custom scissors cursor
    else:
        self.canvas.setCursor(Qt.ArrowCursor)

def on_wire_click(self, connection_id: str, scene_pos: QPointF):
    """
    Click on wire in scissors mode → cut it.
    """
    if not self._scissors_mode:
        return False
    
    # Parse connection
    parts = connection_id.split(":")
    from_node, from_port, to_node, to_port = parts
    
    # Remove connection
    success = self.graph.disconnect(from_node, from_port, 
                                    to_node, to_port)
    
    if success:
        self.connection_manager._unregister_connection(
            from_node, from_port, to_node, to_port
        )
        self.canvas._redraw_connections()
        
        # Visual feedback
        self._show_cut_effect(scene_pos)
    
    return success
```

### Visual Feedback for Cutting

```python
def _show_cut_effect(self, position: QPointF):
    """
    Show brief visual effect when wire is cut.
    - Small explosion of particles
    - Fades out over 300ms
    """
    # Create particle effect
    particles = []
    for i in range(8):
        particle = self.scene.addEllipse(
            -3, -3, 6, 6,
            QPen(Qt.NoPen),
            QBrush(QColor("#FF5722"))
        )
        particle.setPos(position)
        particles.append(particle)
        
        # Animate outward
        angle = (i / 8) * 2 * math.pi
        distance = 20
        target_x = position.x() + math.cos(angle) * distance
        target_y = position.y() + math.sin(angle) * distance
        
        # Use QPropertyAnimation for smooth fade
        anim = QPropertyAnimation(particle, b"pos")
        anim.setDuration(300)
        anim.setEndValue(QPointF(target_x, target_y))
        anim.finished.connect(lambda p=particle: self.scene.removeItem(p))
        anim.start()
```

---

## Integration Guide

### Step 1: Initialize Advanced System

```python
# In your main application or canvas initialization
from src.core.advanced_connection_system import AdvancedConnectionState
from src.core.graph import Graph

# Create graph (existing)
graph = Graph()

# Create advanced connection state
advanced_state = AdvancedConnectionState(graph)

# Connect to existing systems
advanced_state.set_managers(
    connection_manager=connection_manager,
    canvas=canvas
)
```

### Step 2: Update Port Class

Add `max_connections` property to Port:

```python
# In src/core/port.py
class Port:
    def __init__(self, name: str, port_type: PortType, 
                 parent_node=None, data_type: DataType = DataType.ANY,
                 max_connections: int = 1):  # NEW
        
        self.name = name
        self.type = port_type
        self.parent_node = parent_node
        self.data_type = data_type
        self.max_connections = max_connections  # NEW
        
        # Existing code...
        self.connections: List['Port'] = []
```

### Step 3: Update Connection Manager

Integrate with existing `ConnectionManager`:

```python
# In src/gui/connection_manager.py
class ConnectionManager:
    def __init__(self, canvas, graph: Graph, parent=None):
        super().__init__(parent)
        
        # Existing initialization...
        self.canvas = canvas
        self.graph = graph
        
        # NEW: Advanced connection system
        from src.core.advanced_connection_system import AdvancedConnectionState
        self.advanced_state = AdvancedConnectionState(graph)
        self.advanced_state.set_managers(self, canvas)
    
    def _try_connect_to_port(self, target_port: PortItem) -> bool:
        """Enhanced with capacity and type checking."""
        
        # Get data types
        from_node_id, from_port_name, from_type, from_data_type = self._connecting_from
        to_node_id = target_port.parent_node_item.node.node_id
        to_port_name = target_port.port_name
        
        # Use advanced state for connection
        success, message, advanced_conn = self.advanced_state.create_connection(
            source_port_id=f"{from_node_id}:{from_port_name}",
            target_port_id=f"{to_node_id}:{to_port_name}",
            source_data_type=from_data_type,
            target_data_type=target_port.data_type
        )
        
        if success:
            # Existing redraw logic...
            self.canvas._redraw_connections()
            self.connection_created.emit(...)
        
        return success
```

### Step 4: Add Smart Snapping to Drag

```python
def update_temp_connection(self, scene_pos: QPointF):
    """Enhanced with smart snapping."""
    
    # Existing Bezier curve update...
    path = self._calculate_bezier_path(start_pos, scene_pos, port_type)
    self._temp_line.setPath(path)
    
    # NEW: Smart snapping analysis
    if self._connecting_from:
        node_id, port_name, port_type, data_type = self._connecting_from
        
        analysis = self.advanced_state.smart_snapping.analyze_drop_targets(
            source_port_id=f"{node_id}:{port_name}",
            source_data_type=data_type,
            source_port_type=port_type,
            cursor_pos=scene_pos
        )
        
        # Apply visual feedback
        self.advanced_state.smart_snapping.apply_visual_feedback(analysis)
```

### Step 5: Add Reroute Node Support

```python
# In canvas or main window
def mouseDoubleClickEvent(self, event):
    """Handle double-click for reroute creation."""
    
    # Check if clicked on a connection
    item = self.itemAt(event.pos())
    if isinstance(item, ConnectionItem):
        # Create reroute node
        reroute = self.advanced_state.reroute_manager.create_reroute_on_wire(
            connection_id=item.connection_id,
            position=event.scenePos()
        )
        
        if reroute:
            # Create visual representation
            self._create_reroute_visual(reroute)
    
    super().mouseDoubleClickEvent(event)
```

### Step 6: Add Alt+Click Support

```python
def keyPressEvent(self, event):
    """Handle modifier keys."""
    
    if event.key() == Qt.Key_Alt:
        self._alt_pressed = True
        self.setCursor(Qt.PointingHandCursor)  # Indicate Alt mode
    
    super().keyPressEvent(event)

def keyReleaseEvent(self, event):
    """Handle modifier key release."""
    
    if event.key() == Qt.Key_Alt:
        self._alt_pressed = False
        self.setCursor(Qt.ArrowCursor)
    
    super().keyReleaseEvent(event)

def mousePressEvent(self, event):
    """Enhanced with Alt+Click wire cutting."""
    
    # Check for Alt+Click on port
    if self._alt_pressed and event.button() == Qt.LeftButton:
        item = self.itemAt(event.pos())
        
        if isinstance(item, PortItem):
            # Cut all connections from this port
            node_id = item.parent_node_item.node.node_id
            port_name = item.port_name
            port_type = item.port_type
            
            removed = self.advanced_state.wire_cutter.cut_port_connections(
                node_id, port_name, port_type
            )
            
            # Show feedback
            self._show_cut_feedback(f"Removed {len(removed)} connections")
            event.accept()
            return
    
    super().mousePressEvent(event)
```

---

## API Reference

### AdvancedConnectionState

Central state manager for all advanced connection features.

#### Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `create_connection(source_id, target_id, src_type, tgt_type, max_conn=None)` | Create new connection with validation | `(bool, str, AdvancedConnection)` |
| `remove_connection(conn_id)` | Remove connection and cleanup | `bool` |
| `get_connection(conn_id)` | Get connection by ID | `Optional[AdvancedConnection]` |
| `get_all_connections()` | Get all connections | `List[AdvancedConnection]` |
| `get_connections_for_node(node_id)` | Get connections for node | `List[AdvancedConnection]` |
| `to_dict()` | Serialize state | `Dict` |
| `from_dict(data)` | Deserialize state | `None` |

### PortCapacityManager

Manages port capacity limits and auto-replacement.

#### Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `can_accept_connection(port, max_conn=None)` | Check if port can accept connection | `(bool, str, ConnectionCapability)` |
| `auto_replace_connection(port, old_conn=None)` | Replace existing connection | `bool` |
| `register_connection(src_port, tgt_port)` | Register new connection | `None` |
| `unregister_connection(src_port, tgt_port)` | Unregister connection | `None` |
| `rebuild_cache()` | Rebuild from graph | `None` |

### RerouteNodeManager

Manages reroute nodes for wire organization.

#### Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `create_reroute_on_wire(conn_id, position)` | Create reroute by double-clicking wire | `Optional[RerouteNodeData]` |
| `move_reroute(reroute_id, new_pos)` | Move reroute node | `None` |
| `delete_reroute(reroute_id)` | Delete reroute and restore connection | `bool` |
| `get_reroute_at_position(pos, tolerance=10)` | Find reroute at position | `Optional[str]` |
| `get_all_reroutes()` | Get all reroute nodes | `List[RerouteNodeData]` |

### SmartSnappingSystem

Type-aware port highlighting and visual feedback.

#### Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `analyze_drop_targets(src_id, src_type, src_port_type, cursor_pos)` | Analyze all potential targets | `Dict` |
| `apply_visual_feedback(analysis)` | Apply highlights/dimming | `None` |
| `clear_highlights()` | Clear all visual feedback | `None` |

### WireCutter

Quick-action wire detachment system.

#### Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `cut_port_connections(node_id, port_name, port_type)` | Cut all connections from port (Alt+Click) | `List[Tuple]` |
| `cut_connection_at_point(conn_id, point)` | Cut connection at point (scissors) | `bool` |
| `toggle_scissors_mode(enabled)` | Toggle scissors tool | `None` |

---

## Performance Considerations

### 1. Event-Driven Updates
```python
# Only redraw connections involving moved node
def on_node_moved(self, node_id: str):
    affected_connections = self._get_connections_for_node(node_id)
    for conn in affected_connections:
        conn.update_positions()  # Not all connections!
```

### 2. Batched Operations
```python
# Batch multiple changes before redraw
self._pending_updates.add(node_id)
if not self._update_timer.isActive():
    self._update_timer.start(16)  # ~60 FPS
```

### 3. Spatial Indexing (Future)
```python
# Use QGraphicsScene's built-in spatial index
# for O(log n) port lookup instead of O(n)
```

---

## Serialization

### Save State
```python
state_dict = advanced_state.to_dict()

# Add to existing save format
save_data = {
    "graph": graph.to_dict(),
    "advanced_connections": state_dict,
    "version": "2.0"
}

with open("save.json", "w") as f:
    json.dump(save_data, f)
```

### Load State
```python
with open("save.json", "r") as f:
    save_data = json.load(f)

# Restore graph
graph.from_dict(save_data["graph"], node_factory)

# Restore advanced state
advanced_state.from_dict(save_data["advanced_connections"])
```

---

## Testing

### Unit Test Example
```python
def test_multi_branching():
    """Test 1-to-N broadcasting."""
    graph = Graph()
    state = AdvancedConnectionState(graph)
    
    # Create nodes
    source = create_test_node("source", output_ports=["out"])
    target1 = create_test_node("target1", input_ports=["in"])
    target2 = create_test_node("target2", input_ports=["in"])
    
    graph.add_node(source)
    graph.add_node(target1)
    graph.add_node(target2)
    
    # Set max_connections
    source.output_ports["out"].max_connections = 5
    
    # Connect to multiple targets
    success1, _, _ = state.create_connection(
        "source:out", "target1:in", DataType.BINARY, DataType.BINARY
    )
    success2, _, _ = state.create_connection(
        "source:out", "target2:in", DataType.BINARY, DataType.BINARY
    )
    
    assert success1 and success2
    assert len(state.get_connections_for_node("source")) == 2

def test_auto_replacement():
    """Test auto-replace when max_connections = 1."""
    graph = Graph()
    state = AdvancedConnectionState(graph)
    
    # Create nodes
    source = create_test_node("source", output_ports=["out"])
    target1 = create_test_node("target1", input_ports=["in"])
    target2 = create_test_node("target2", input_ports=["in"])
    
    graph.add_node(source)
    graph.add_node(target1)
    graph.add_node(target2)
    
    # Set max_connections = 1
    target1.input_ports["in"].max_connections = 1
    
    # First connection
    state.create_connection("source:out", "target1:in", 
                           DataType.BINARY, DataType.BINARY)
    
    # Second connection should auto-replace
    success, _, _ = state.create_connection("source:out", "target2:in",
                                           DataType.BINARY, DataType.BINARY)
    
    assert success
    assert len(graph.connections) == 1
    assert graph.connections[0][2] == "target2"  # New target
```

---

## Future Enhancements

1. **Spatial Indexing**: Use quadtree for O(log n) port lookup
2. **Connection Bundling**: Visually group related wires
3. **Conditional Routing**: Data-type based routing rules
4. **Wire Styling**: Per-connection color/width/pattern
5. **Animation Presets**: Pre-built wire animation styles
6. **Batch Operations**: Multi-select and edit connections
7. **Connection History**: Undo/redo for connection changes
8. **Smart Auto-Routing**: AI-assisted wire organization

---

## Summary

The Advanced Connection Management System provides:

✅ **Multi-Branching**: 1-to-N broadcasting with visual clarity  
✅ **Port Capacity**: Configurable limits with auto-replacement  
✅ **Type Safety**: Data-type aware validation and highlighting  
✅ **Smart Snapping**: Real-time visual feedback during drag  
✅ **Reroute Nodes**: Invisible anchors for wire organization  
✅ **Wire Cutting**: Quick Alt+Click detachment  
✅ **Scalable Architecture**: Centralized state management  
✅ **Performance**: Event-driven updates, 60 FPS optimization  

This system transforms basic wires into a professional-grade visual routing system comparable to Unreal Engine Blueprints or Blender Geometry Nodes.