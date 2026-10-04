"""
Graph - enhanced with complete CRUD, from_dict(), cycle detection, and data type validation.
"""

from typing import Dict, List, Optional, Tuple, Set
from src.core.node_base import NodeBase
from src.core.packet import DataPacket
from src.core.port import Port, PortType, DataType


class Graph:
    """
    Directed graph of simulation nodes with full CRUD operations.
    
    Features:
    - Complete CRUD for nodes and connections
    - from_dict() for deserialization
    - Cycle detection (warning on cycle)
    - Data type compatibility validation at connection time
    - Connection metadata (bandwidth, latency per link)
    """
    
    def __init__(self):
        self.nodes: Dict[str, NodeBase] = {}
        self.connections: List[tuple] = []  # (from_node_id, from_port, to_node_id, to_port)
        self._connection_metadata: Dict[tuple, Dict] = {}  # metadata per connection
    
    def add_node(self, node: NodeBase) -> str:
        """Add a node to the graph."""
        self.nodes[node.node_id] = node
        return node.node_id
    
    def remove_node(self, node_id: str):
        """Remove a node and all its connections."""
        if node_id in self.nodes:
            node = self.nodes[node_id]
            # Remove all connections involving this node
            self.connections = [
                c for c in self.connections 
                if c[0] != node_id and c[2] != node_id
            ]
            # Clean up connection metadata
            self._connection_metadata = {
                k: v for k, v in self._connection_metadata.items()
                if k[0] != node_id and k[2] != node_id
            }
            # Disconnect all ports
            for port in list(node.input_ports.values()) + list(node.output_ports.values()):
                for conn in list(port.connections):
                    port.disconnect(conn)
            del self.nodes[node_id]
    
    def connect(self, from_node_id: str, from_port: str, 
                to_node_id: str, to_port: str) -> tuple:
        """
        Connect two nodes via specified ports.
        Returns (success: bool, reason: str, warning: str).
        """
        if from_node_id not in self.nodes or to_node_id not in self.nodes:
            return False, "Node not found", ""
        
        from_node = self.nodes[from_node_id]
        to_node = self.nodes[to_node_id]
        
        if from_port not in from_node.output_ports:
            return False, f"Output port '{from_port}' not found on {from_node.name}", ""
        if to_port not in to_node.input_ports:
            return False, f"Input port '{to_port}' not found on {to_node.name}", ""
        
        from_port_obj = from_node.output_ports[from_port]
        to_port_obj = to_node.input_ports[to_port]
        
        can, reason = from_port_obj.can_connect(to_port_obj)
        if not can:
            return False, reason, ""
        
        # Check for cycles
        has_cycle, cycle_warning = self._check_cycle(from_node_id, to_node_id)
        
        # Establish connection
        from_port_obj.connect(to_port_obj)
        key = (from_node_id, from_port, to_node_id, to_port)
        self.connections.append(key)
        self._connection_metadata[key] = {
            "bandwidth": 0,  # 0 = unlimited
            "latency_ms": 0,
            "packet_loss": 0.0,
            "jitter_ms": 0
        }
        
        return True, "Connected", cycle_warning
    
    def disconnect(self, from_node_id: str, from_port: str, 
                   to_node_id: str, to_port: str) -> bool:
        """Disconnect two nodes."""
        key = (from_node_id, from_port, to_node_id, to_port)
        if key in self.connections:
            from_node = self.nodes.get(from_node_id)
            to_node = self.nodes.get(to_node_id)
            if from_node and to_node:
                from_node.output_ports[from_port].disconnect(
                    to_node.input_ports[to_port]
                )
            self.connections.remove(key)
            self._connection_metadata.pop(key, None)
            return True
        return False
    
    def get_node(self, node_id: str) -> Optional[NodeBase]:
        """Get a node by ID."""
        return self.nodes.get(node_id)
    
    def get_connection_metadata(self, from_node_id: str, from_port: str,
                                 to_node_id: str, to_port: str) -> Dict:
        """Get metadata for a specific connection."""
        key = (from_node_id, from_port, to_node_id, to_port)
        return self._connection_metadata.get(key, {})
    
    def set_connection_metadata(self, from_node_id: str, from_port: str,
                                 to_node_id: str, to_port: str, metadata: Dict):
        """Set metadata for a specific connection."""
        key = (from_node_id, from_port, to_node_id, to_port)
        if key in self._connection_metadata:
            self._connection_metadata[key].update(metadata)
    
    def get_nodes_by_type(self, node_type: str) -> List[NodeBase]:
        """Get all nodes of a given type."""
        return [n for n in self.nodes.values() if n.node_type == node_type]
    
    def get_nodes_by_category(self, category: str) -> List[NodeBase]:
        """Get all nodes of a given category."""
        return [n for n in self.nodes.values() if n.category == category]
    
    def get_sources(self) -> List[NodeBase]:
        """Get all source nodes (nodes with no input connections)."""
        connected_inputs = set(c[2] for c in self.connections)
        return [n for n in self.nodes.values() if n.node_id not in connected_inputs]
    
    def get_sinks(self) -> List[NodeBase]:
        """Get all sink nodes (nodes with no output connections)."""
        connected_outputs = set(c[0] for c in self.connections)
        sinks = [n for n in self.nodes.values() 
                if n.node_id not in connected_outputs and not n.output_ports]
        # Also include nodes whose outputs are not connected
        for n in self.nodes.values():
            if n.output_ports:
                all_connected = all(
                    not port.connections 
                    for port in n.output_ports.values()
                )
                if all_connected and n.node_id not in sinks:
                    sinks.append(n)
        return sinks
    
    def _check_cycle(self, from_id: str, to_id: str) -> tuple:
        """
        Check if adding a connection from_id -> to_id would create a cycle.
        Returns (has_cycle: bool, warning: str).
        """
        # BFS from to_id to see if we can reach from_id
        visited: Set[str] = set()
        queue: List[str] = [to_id]
        
        while queue:
            current = queue.pop(0)
            if current == from_id:
                return True, "Warning: Connection would create a cycle in the graph"
            if current in visited:
                continue
            visited.add(current)
            # Find all nodes reachable from current
            for conn in self.connections:
                if conn[0] == current:  # current is source
                    if conn[2] not in visited:
                        queue.append(conn[2])
        
        return False, ""
    
    def to_dict(self) -> dict:
        """Serialize entire graph to dictionary."""
        return {
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "connections": [
                {
                    "from_node": c[0],
                    "from_port": c[1],
                    "to_node": c[2],
                    "to_port": c[3],
                    "metadata": self._connection_metadata.get(c, {})
                }
                for c in self.connections
            ]
        }
    
    def from_dict(self, data: dict, node_factory: Dict[str, type]) -> bool:
        """
        Deserialize graph from dictionary.
        
        Args:
            data: Dictionary with "nodes" and "connections" keys
            node_factory: Mapping of node_type -> NodeBase subclass
            
        Returns:
            True if successful
        """
        # Clear existing graph
        self.nodes.clear()
        self.connections.clear()
        self._connection_metadata.clear()
        
        # Rebuild nodes
        from src.nodes.registry import resolve_node_class
        node_id_map = {}  # old_id -> new_node
        for node_data in data.get("nodes", []):
            node_class = resolve_node_class(node_data)
            if not node_class:
                node_type = node_data.get("type", "")
                node_class = node_factory.get(node_type)
            if not node_class:
                import warnings
                warnings.warn(f"Unknown node type: {node_type}, skipping")
                continue
            
            from inspect import signature
            try:
                sig = signature(node_class.__init__)
                params = list(sig.parameters.keys())
                if "node_id" in params:
                    node = node_class(node_id=node_data.get("id", "unknown"))
                else:
                    node = node_class()
                    node.node_id = node_data.get("id", node.node_id)
            except Exception as e:
                import warnings
                warnings.warn(f"Failed to create node {node_data.get('id')}: {e}")
                continue
            
            # Restore position
            pos = node_data.get("position", [0, 0])
            node.position = tuple(pos) if isinstance(pos, (list, tuple)) else (0, 0)
            
            # Restore params
            for k, v in node_data.get("params", {}).items():
                node.set_param(k, v)
            
            # Restore config
            for k, v in node_data.get("config", {}).items():
                node.set_param(k, v)
            
            self.add_node(node)
            node_id_map[node_data.get("id", node.node_id)] = node
        
        # Rebuild connections
        for conn_data in data.get("connections", []):
            from_node = node_id_map.get(conn_data.get("from_node"))
            to_node = node_id_map.get(conn_data.get("to_node"))
            from_port = conn_data.get("from_port")
            to_port = conn_data.get("to_port")
            
            if from_node and to_node and from_port and to_port:
                success, reason, warning = self.connect(
                    from_node.node_id, from_port,
                    to_node.node_id, to_port
                )
                if not success:
                    import warnings
                    warnings.warn(f"Failed to restore connection: {reason}")
        
        return True
    
    def clear(self):
        """Remove all nodes and connections."""
        self.nodes.clear()
        self.connections.clear()
        self._connection_metadata.clear()