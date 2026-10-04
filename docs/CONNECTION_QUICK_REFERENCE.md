# Connection System Quick Reference

## Quick Start

### Basic Connection Flow

```python
# 1. User clicks on output port
canvas._on_port_clicked(port_item)
# → ConnectionManager.start_connection(port_item)
# → State: IDLE → DRAGGING_CONNECTION
# → Source port highlighted yellow
# → Temporary dashed line created

# 2. User moves mouse
canvas.mouseMoveEvent(event)
# → ConnectionManager.update_temp_connection(scene_pos)
# → Bezier curve follows cursor
# → Valid ports highlighted green
# → Invalid ports highlighted red

# 3. User releases on input port
canvas.mouseReleaseEvent(event)
# → ConnectionManager.complete_connection(target_port)
# → Validation checks run
# → Graph.connect() creates connection
# → ConnectionItem added to scene
# → State: DRAGGING_CONNECTION → IDLE

# 4. User releases on empty space or presses Escape
# → ConnectionManager.cancel_connection()
# → Temporary line removed
# → Port colors restored
# → State: DRAGGING_CONNECTION → IDLE
```

---

## Core Algorithms

### Bezier Curve Control Points

```python
# For output → input connection:
start = (x1, y1)  # Output port position
end = (x2, y2)    # Input port position

dx = abs(end.x - start.x) * 0.5
offset = max(dx, 50)  # Minimum 50px

# Control points (horizontal tangents)
ctrl1 = (start.x + offset, start.y)  # Exit right
ctrl2 = (end.x - offset, end.y)      # Enter left

# Cubic Bezier: B(t) = (1-t)³P0 + 3(1-t)²tP1 + 3(1-t)t²P2 + t³P3
```

### Validation Checklist

```python
✅ Nodes exist
✅ Not self-loop (from_id != to_id)
✅ Ports exist
✅ Not duplicate connection
✅ Data types compatible
✅ No cycles (warning)
✅ Direction: output → input
✅ Input port not already connected
```

### Event-Driven Update Flow

```python
# When node moves:
NodeItem.itemChange()
  → _update_connections()
    → canvas._update_connections_for_node(node_id)
      → connection_manager.on_node_moved(node_id)
        → Add to _pending_updates
        → Start QTimer (16ms)

# After 16ms:
QTimer.timeout
  → _flush_updates()
    → For each affected connection:
      → ConnectionItem.update_positions()
        → update_path()
          → _calculate_bezier_path()
```

---

## Common Operations

### Create Connection

```python
# Method 1: Via port click (automatic)
port_item.mousePressEvent(event)

# Method 2: Programmatic
success, reason, warning = graph.connect(
    from_node_id, from_port, to_node_id, to_port
)
if success:
    canvas._redraw_connections()
```

### Remove Connection

```python
# Method 1: Via connection manager
connection_manager.remove_connection(
    from_node_id, from_port, to_node_id, to_port
)

# Method 2: Direct graph access
graph.disconnect(from_node_id, from_port, to_node_id, to_port)
canvas._redraw_connections()
```

### Detach & Reassign

```python
# Detach connection from one port, attach to another
connection_key = ("node1", "out1", "node2", "in1")
new_target_port = get_port_item("node3", "in1")

connection_manager.detach_connection(connection_key, new_target_port)
```

### Validate Connection

```python
is_valid, reason = connection_manager.validate_connection(
    from_node_id="node1",
    from_port="out1",
    to_node_id="node2",
    to_port="in1"
)

if not is_valid:
    print(f"Invalid: {reason}")
```

### Get Connections for Node

```python
# Get all connections involving a node
connections = connection_manager.get_connections_for_node("node1")
# Returns: [("node1", "out1", "node2", "in1"), ...]
```

---

## State Machine Reference

### Current State

```python
state = connection_manager.state
# ConnectionState.IDLE
# ConnectionState.DRAGGING_CONNECTION
# ConnectionState.VALIDATING
# ConnectionState.CONNECTED
```

### State Checks

```python
if connection_manager.is_connecting():
    # User is currently drawing a connection
    pass

origin = connection_manager.get_connecting_from()
# Returns: (node_id, port_name, port_type) or None
```

### Force State Change

```python
# Cancel any ongoing connection
connection_manager.cancel_connection()

# Cleanup (e.g., on app close)
connection_manager.cleanup()
```

---

## Visual Feedback

### Port Highlighting

```python
# During connection dragging:
# - Source port: Yellow (#FFFF00)
# - Valid target: Green (#00FF00)
# - Invalid target: Red (#FF0000)
# - Normal: Data type color

# Automatic via connection_manager._check_drop_target()
```

### Temporary Line

```python
# Created during dragging:
# - Color: Yellow (#FFFF00)
# - Style: Dashed line
# - Width: 2px
# - Z-value: 100 (above everything)

# Automatically managed by connection_manager
```

### Connection Glow

```python
# Triggered when packet passes through:
connection_item.trigger_glow()
# → Opacity animates from 1.0 to 0.0 over 300ms
```

---

## Performance Tips

### 1. Use Batched Updates

```python
# ✅ GOOD: Batched with debouncing
connection_manager.on_node_moved(node_id)
# → Updates queued, flushed after 16ms

# ❌ BAD: Immediate redraw
canvas._redraw_connections()
# → Redraws ALL connections
```

### 2. O(1) Lookups

```python
# ✅ GOOD: Dictionary lookup
conn_item = canvas._connection_items.get(key)

# ❌ BAD: Linear search
for conn in canvas._connection_items:
    if conn == key:
        ...
```

### 3. Minimize Redraws

```python
# ✅ GOOD: Update only affected connections
for conn_key in connection_manager._node_observers[node_id]:
    conn_item.update_positions()

# ❌ BAD: Redraw everything
canvas._redraw_connections()
```

---

## Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Check Connection State

```python
print(f"State: {connection_manager.state}")
print(f"Connecting from: {connection_manager.get_connecting_from()}")
print(f"All connections: {connection_manager.get_all_connections()}")
```

### Validate Connection

```python
is_valid, reason = connection_manager.validate_connection(
    "node1", "out1", "node2", "in1"
)
print(f"Valid: {is_valid}, Reason: {reason}")
```

### Check Port Availability

```python
available, reason = connection_manager.check_port_available(
    "node1", "in1", "input"
)
print(f"Available: {available}, Reason: {reason}")
```

---

## Common Issues & Solutions

### Issue: Connection not appearing

```python
# Check 1: Node items exist
if from_id not in canvas._node_items:
    print("Source node not in canvas")

# Check 2: Port positions valid
start_pos = from_item.get_port_scene_pos(from_port, "output")
if start_pos.isNull():
    print("Invalid port position")

# Check 3: Connection registered
key = (from_id, from_port, to_id, to_port)
if key not in connection_manager._connection_registry:
    print("Connection not registered")
```

### Issue: Lag during dragging

```python
# Check 1: Batched updates enabled
if not connection_manager._update_timer.isActive():
    print("Updates not batched!")

# Check 2: Not redrawing all connections
# Ensure using on_node_moved() instead of _redraw_connections()

# Check 3: Antialiasing disabled
canvas.setRenderHint(QPainter.Antialiasing, False)
```

### Issue: Invalid connections passing

```python
# Check validation logic
is_valid, reason = connection_manager.validate_connection(...)
print(f"Validation result: {is_valid}, {reason}")

# Check data type compatibility
from src.core.port import DataType
print(DataType.is_compatible(DataType.TEXT, DataType.BINARY))  # Should be True
```

### Issue: Port highlighting not working

```python
# Check 1: _check_drop_target called in mouseMoveEvent
# Check 2: Port items have correct data
print(port_item.port_type, port_item.port_name)

# Check 3: Valid target check
print(connection_manager._is_valid_target(port_item))
```

---

## File Structure

```
src/gui/
├── connection_manager.py      # Core connection logic
│   ├── ConnectionState (enum)
│   ├── ConnectionManager (class)
│   │   ├── State machine
│   │   ├── Lifecycle methods
│   │   ├── Bezier calculator
│   │   ├── Visual feedback
│   │   ├── Event system
│   │   └── Validation
│   └── [All connection logic]
│
├── canvas.py                  # Canvas integration
│   ├── ConnectionManager instance
│   ├── Event handlers
│   └── Delegation to manager
│
└── node_item.py              # Visual elements
    ├── PortItem
    ├── ConnectionItem
    └── PacketAnimation

docs/
├── CONNECTION_SYSTEM_ARCHITECTURE.md  # Full documentation
└── CONNECTION_QUICK_REFERENCE.md      # This file
```

---

## Testing Checklist

- [ ] Click output port → temporary line appears
- [ ] Drag to input port → connection created
- [ ] Drag to empty space → connection cancelled
- [ ] Press Escape → connection cancelled
- [ ] Try self-loop → blocked
- [ ] Try duplicate connection → blocked
- [ ] Try input→input → blocked
- [ ] Try incompatible types → blocked
- [ ] Move node → only affected wires update
- [ ] 100+ connections → still 60 FPS
- [ ] Zoom in/out → wires scale correctly
- [ ] Delete node → connections removed
- [ ] Detach connection → works correctly

---

## API Cheat Sheet

### ConnectionManager

```python
# State
.state → ConnectionState
.is_connecting() → bool
.get_connecting_from() → (node_id, port_name, port_type)

# Lifecycle
.start_connection(port_item) → bool
.update_temp_connection(scene_pos) → None
.complete_connection(target_port) → bool
.cancel_connection() → None
.remove_connection(from_id, from_port, to_id, to_port) → None
.detach_connection(key, new_port) → bool

# Bezier
._calculate_bezier_path(start, end, port_type) → QPainterPath
.calculate_connection_path(from_id, from_port, to_id, to_port) → QPainterPath

# Validation
.validate_connection(from_id, from_port, to_id, to_port) → (bool, str)
.check_port_available(node_id, port_name, port_type) → (bool, str)

# Events
.on_node_moved(node_id) → None
.get_connections_for_node(node_id) → List[tuple]
.get_all_connections() → List[tuple]

# Signals
.connection_started → Signal(node_id, port_name, port_type)
.connection_cancelled → Signal()
.connection_created → Signal(from_id, from_port, to_id, to_port)
.connection_removed → Signal(from_id, from_port, to_id, to_port)
.port_highlighted → Signal(is_valid, port_id)
```

---

## Mathematical Formulas

### Cubic Bezier Curve

```
B(t) = (1-t)³P0 + 3(1-t)²tP1 + 3(1-t)t²P2 + t³P3

where:
  t ∈ [0, 1]
  P0 = start point
  P1 = control point 1
  P2 = control point 2
  P3 = end point
```

### Control Point Offset

```
offset = max(|x2 - x1| * 0.5, 50)

if output_port:
  ctrl1 = (x1 + offset, y1)
  ctrl2 = (x2 - offset, y2)
else:
  ctrl1 = (x1 - offset, y1)
  ctrl2 = (x2 + offset, y2)
```

### Tangent Angle

```
tangent(t) = atan2(
  pointAtPercent(t + ε).y - pointAtPercent(t - ε).y,
  pointAtPercent(t + ε).x - pointAtPercent(t - ε).x
)

where ε = 0.01
```

---

## Summary

The connection system is:
- ✅ **Modular**: ConnectionManager handles all logic
- ✅ **Performant**: Event-driven, batched updates
- ✅ **Safe**: 8 validation rules
- ✅ **Smooth**: 60 FPS Bezier curves
- ✅ **Flexible**: Detach/reassign support
- ✅ **Documented**: Comprehensive docs

For full details, see [CONNECTION_SYSTEM_ARCHITECTURE.md](CONNECTION_SYSTEM_ARCHITECTURE.md)