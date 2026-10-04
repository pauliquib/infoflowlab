"""
Undo/Redo command stack for canvas operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Any, Dict, TYPE_CHECKING

from PySide6.QtCore import QObject, Signal

if TYPE_CHECKING:
    from src.gui.canvas import Canvas


class UndoCommand(ABC):
    """Base class for undoable commands."""

    description: str = "Operation"

    @abstractmethod
    def execute(self) -> None:
        pass

    @abstractmethod
    def undo(self) -> None:
        pass


class MacroCommand(UndoCommand):
    """Group multiple commands into one undo step."""

    def __init__(self, description: str, commands: List[UndoCommand]):
        self.description = description
        self.commands = commands

    def execute(self) -> None:
        for cmd in self.commands:
            cmd.execute()

    def undo(self) -> None:
        for cmd in reversed(self.commands):
            cmd.undo()


class AddNodeCommand(UndoCommand):
    """Add a node to the canvas."""

    def __init__(self, canvas: "Canvas", type_key: str, position: Tuple[float, float],
                 params: Optional[Dict[str, Any]] = None):
        self.canvas = canvas
        self.type_key = type_key
        self.position = position
        self.params = params or {}
        self.node_id: Optional[str] = None
        self.description = f"Přidat uzel {type_key}"

    def execute(self) -> None:
        node = self.canvas._add_node_internal(self.type_key, self.position, self.params)
        if node:
            self.node_id = node.node_id

    def undo(self) -> None:
        if self.node_id:
            self.canvas._remove_node_internal(self.node_id)


class RemoveNodeCommand(UndoCommand):
    """Remove a node from the canvas."""

    def __init__(self, canvas: "Canvas", node_id: str):
        self.canvas = canvas
        self.node_id = node_id
        self.snapshot: Optional[Dict[str, Any]] = None
        self.connections: List[Tuple[str, str, str, str]] = []
        self.description = "Odstranit uzel"

    def _capture(self) -> None:
        node = self.canvas.graph.get_node(self.node_id)
        if node:
            self.snapshot = node.to_dict()
            self.connections = [
                conn for conn in self.canvas.graph.connections
                if conn[0] == self.node_id or conn[2] == self.node_id
            ]
            self.description = f"Odstranit uzel {node.name}"

    def execute(self) -> None:
        self._capture()
        self.canvas._remove_node_internal(self.node_id)

    def undo(self) -> None:
        if self.snapshot:
            self.canvas._restore_node_internal(self.snapshot, self.connections)
            self.node_id = self.snapshot["id"]


class MoveNodeCommand(UndoCommand):
    """Move a node to a new position."""

    def __init__(self, canvas: "Canvas", node_id: str,
                 old_pos: Tuple[float, float], new_pos: Tuple[float, float]):
        self.canvas = canvas
        self.node_id = node_id
        self.old_pos = old_pos
        self.new_pos = new_pos
        self.description = "Přesunout uzel"

    def execute(self) -> None:
        self.canvas._set_node_position(self.node_id, self.new_pos)

    def undo(self) -> None:
        self.canvas._set_node_position(self.node_id, self.old_pos)


class AddConnectionCommand(UndoCommand):
    """Add a connection between two nodes."""

    def __init__(self, canvas: "Canvas",
                 from_id: str, from_port: str, to_id: str, to_port: str):
        self.canvas = canvas
        self.conn = (from_id, from_port, to_id, to_port)
        self.description = "Přidat spojení"

    def execute(self) -> None:
        key = self.conn
        if key not in self.canvas.graph.connections:
            self.canvas._add_connection_internal(*self.conn)

    def undo(self) -> None:
        self.canvas._remove_connection_internal(*self.conn)


class RemoveConnectionCommand(UndoCommand):
    """Remove a connection between two nodes."""

    def __init__(self, canvas: "Canvas",
                 from_id: str, from_port: str, to_id: str, to_port: str):
        self.canvas = canvas
        self.conn = (from_id, from_port, to_id, to_port)
        self.description = "Odstranit spojení"

    def execute(self) -> None:
        if self.conn in self.canvas.graph.connections:
            self.canvas._remove_connection_internal(*self.conn)

    def undo(self) -> None:
        self.canvas._add_connection_internal(*self.conn)


class UndoStack(QObject):
    """Manages undo/redo history."""

    changed = Signal()

    def __init__(self, parent=None, max_depth: int = 100):
        super().__init__(parent)
        self._undo_stack: List[UndoCommand] = []
        self._redo_stack: List[UndoCommand] = []
        self._max_depth = max_depth
        self._recording = True

    def begin_macro(self, description: str) -> "MacroContext":
        return MacroContext(self, description)

    def push(self, command: UndoCommand) -> None:
        if not self._recording:
            command.execute()
            return
        command.execute()
        self.push_done(command)

    def push_done(self, command: UndoCommand) -> None:
        """Push an already-executed command onto the undo stack."""
        if not self._recording:
            return
        self._undo_stack.append(command)
        if len(self._undo_stack) > self._max_depth:
            self._undo_stack.pop(0)
        self._redo_stack.clear()
        self.changed.emit()

    def undo(self) -> bool:
        if not self._undo_stack:
            return False
        command = self._undo_stack.pop()
        command.undo()
        self._redo_stack.append(command)
        self.changed.emit()
        return True

    def redo(self) -> bool:
        if not self._redo_stack:
            return False
        command = self._redo_stack.pop()
        command.execute()
        self._undo_stack.append(command)
        self.changed.emit()
        return True

    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    def can_redo(self) -> bool:
        return bool(self._redo_stack)

    def undo_text(self) -> str:
        return self._undo_stack[-1].description if self._undo_stack else ""

    def redo_text(self) -> str:
        return self._redo_stack[-1].description if self._redo_stack else ""

    def clear(self) -> None:
        self._undo_stack.clear()
        self._redo_stack.clear()
        self.changed.emit()

    @property
    def recording(self) -> bool:
        return self._recording

    @recording.setter
    def recording(self, value: bool) -> None:
        self._recording = value


class MacroContext:
    """Context manager for grouping commands."""

    def __init__(self, stack: UndoStack, description: str):
        self.stack = stack
        self.description = description
        self.commands: List[UndoCommand] = []

    def __enter__(self) -> "MacroContext":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is None and self.commands:
            self.stack.push(MacroCommand(self.description, self.commands))

    def add(self, command: UndoCommand) -> None:
        self.commands.append(command)
