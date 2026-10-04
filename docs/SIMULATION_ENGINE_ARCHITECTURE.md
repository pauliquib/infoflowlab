# InfoSim Simulation Engine Architecture
## Complete Architectural Design for Information Theory Simulation

---

## 1. The Universal Data Carrier: DataPacket

### Core Properties
```python
@dataclass
class DataPacket:
    id: str                           # Unique packet identifier
    payload: bytes                    # The actual data (raw text, compressed bits, etc.)
    data_type: DataType               # RAW_TEXT, BINARY, COMPRESSED, ENCODED
    metadata: Dict[str, Any]          # Historical tracking dictionary
```

### Metadata Dictionary Structure
The `metadata` field tracks the complete lifecycle:
```python
{
    "original_size": int,            # Size before any processing
    "current_size": int,             # Current payload size in bytes
    "compression_ratio": float,      # original_size / current_size
    "entropy": float,                # Shannon entropy (bits/byte)
    "applied_operations": List[str], # ["huffman_encode", "bsc_channel", "hamming_decode"]
    "error_flags": List[str],        # ["bsc_corrupted", "parity_failed"]
    "latency_ms": float,             # Total accrued latency
    "hops": int,                     # Number of nodes traversed
    "created_tick": int,             # Simulation tick when created
    "received_tick": int,            # Simulation tick when received
}
```

### Data Type Enumeration
```python
class DataType(Enum):
    RAW_TEXT = "raw_text"            # Original text input
    BINARY = "binary"                # Raw binary data
    COMPRESSED = "compressed"        # After compression (Huffman, LZ77, etc.)
    ENCODED = "encoded"              # After channel coding (Hamming, CRC)
    NOISY = "noisy"                  # After passing through noisy channel
    DECODED = "decoded"              # After error correction decoding
```

---

## 2. The Global Simulation Engine (Tick System)

### Tick Lifecycle (60 Ticks/Second)
Every tick follows this strict sequence:

```
TICK START
│
├─ PHASE A: NODE PROCESSING (Parallel)
│   ├─ Each node reads input queues
│   ├─ Processes pending packets (apply compression, noise, etc.)
│   └─ Places results in output queues
│
├─ PHASE B: TRANSPORT & ROUTING (Sequential)
│   ├─ Engine reads all output queues
│   ├─ For each packet:
│   │   ├─ Create routing animation (t: 0.0 → 1.0 along Bezier curve)
│   │   ├─ Deliver to target input queue
│   │   └─ Update packet.metadata["hops"] += 1
│   └─ Handle buffer overflow (drop packets if queue full)
│
└─ PHASE C: ANALYTICS & STATE (Async)
    ├─ Collect node states (compression ratio, entropy, queue depth)
    ├─ Emit state updates to UI (non-blocking)
    └─ Update global statistics
```

### Core Engine Implementation
```python
class SimulationEngine:
    def __init__(self, tick_rate_hz: int = 60):
        self.tick_rate_hz = tick_rate_hz
        self.tick_duration_ms = 1000 / tick_rate_hz
        self.current_tick = 0
        self.nodes: Dict[str, AbstractInfoNode] = {}
        self.connections: List[Connection] = []
        self.routing_animations: List[RoutingAnimation] = []
        
    def tick(self):
        """Execute one simulation tick."""
        self.current_tick += 1
        
        # Phase A: Process all nodes
        self._phase_node_processing()
        
        # Phase B: Route packets
        self._phase_transport_routing()
        
        # Phase C: Update analytics (async to UI)
        self._phase_analytics()
    
    def _phase_node_processing(self):
        """Phase A: All nodes process their input queues."""
        for node in self.nodes.values():
            if node.has_pending_packets():
                node.process(self.tick_duration_ms)
    
    def _phase_transport_routing(self):
        """Phase B: Route packets from outputs to inputs."""
        for node in self.nodes.values():
            for port_name, packets in node.output_queue.items():
                for packet in packets:
                    # Find all connected target nodes
                    targets = self._get_connected_targets(node.node_id, port_name)
                    
                    # Multi-connection broadcasting
                    for target_node, target_port in targets:
                        if target_node.input_queue.has_space():
                            # Create routing animation
                            anim = RoutingAnimation(
                                packet_id=packet.id,
                                source=(node.x, node.y),
                                target=(target_node.x, target_node.y),
                                start_tick=self.current_tick,
                                duration_ticks=5  # Takes 5 ticks to travel
                            )
                            self.routing_animations.append(anim)
                            
                            # Deliver packet (will arrive after duration_ticks)
                            target_node.input_queue.enqueue(packet, target_port)
                        else:
                            # Buffer bloat - drop packet
                            self._handle_packet_drop(packet, "buffer_overflow")
                
                # Clear output queue
                node.output_queue.clear(port_name)
    
    def _phase_analytics(self):
        """Phase C: Emit state updates asynchronously."""
        states = {}
        for node in self.nodes.values():
            states[node.node_id] = node.get_state()
        
        # Non-blocking emit to UI thread
        self.state_update_signal.emit_async(states)
```

---

## 3. Base Node Architecture (AbstractInfoNode)

### Abstract Base Class
```python
from abc import ABC, abstractmethod
from collections import deque
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

@dataclass
class NodeState:
    """Real-time state for UI display."""
    compression_ratio: float = 1.0
    entropy: float = 0.0
    queue_depth: int = 0
    queue_max: int = 10
    packets_processed: int = 0
    last_operation: str = "idle"
    status: str = "idle"  # idle, processing, error

class AbstractInfoNode(ABC):
    """
    Base class for all simulation nodes.
    
    Key Features:
    - Input/Output buffers with configurable max sizes
    - Buffer bloat simulation (drop packets when full)
    - Multi-connection broadcasting (clone packets for parallel distribution)
    - Async state emission to UI
    """
    
    def __init__(self, node_id: str, name: str):
        self.node_id = node_id
        self.name = name
        
        # Input buffers (per port)
        self.input_buffers: Dict[str, InputBuffer] = {}
        
        # Output buffers (per port)
        self.output_buffers: Dict[str, OutputBuffer] = {}
        
        # Node configuration
        self.config: Dict[str, Any] = {}
        
        # Statistics
        self.stats = NodeStats()
        
        # State for UI
        self._state = NodeState()
    
    # ─────────────────────────────────────────
    # Buffer Management
    # ─────────────────────────────────────────
    
    def add_input_port(self, port_name: str, max_size: int = 10):
        """Add an input buffer with max capacity."""
        self.input_buffers[port_name] = InputBuffer(max_size)
    
    def add_output_port(self, port_name: str, max_size: int = 10):
        """Add an output buffer with max capacity."""
        self.output_buffers[port_name] = OutputBuffer(max_size)
    
    def receive_packet(self, packet: DataPacket, port_name: str):
        """
        Receive a packet into input buffer.
        Implements buffer bloat: drops packet if buffer full.
        """
        buffer = self.input_buffers.get(port_name)
        if buffer and buffer.has_space():
            buffer.enqueue(packet)
            self.stats.packets_received += 1
        else:
            self.stats.packets_dropped_buffer_full += 1
            self._on_buffer_overflow(packet)
    
    def send_packet(self, packet: DataPacket, port_name: str):
        """
        Send packet to output buffer.
        Handles multi-connection broadcasting.
        """
        buffer = self.output_buffers.get(port_name)
        if buffer:
            buffer.enqueue(packet)
    
    def broadcast_packet(self, packet: DataPacket, port_name: str):
        """
        Broadcast: Clone packet for each connected target node.
        
        If output port "out" is connected to 3 nodes:
        - Creates 3 independent packet copies
        - Each copy gets unique routing ID
        - Original packet stays with this node (for analytics)
        """
        connections = self.get_connections(port_name)
        
        for i, target in enumerate(connections):
            # Clone packet for this connection
            cloned = self._clone_packet(packet)
            cloned.metadata["broadcast_id"] = f"{packet.id}_bc_{i}"
            cloned.metadata["target_node"] = target.node_id
            
            # Send to output buffer
            self.send_packet(cloned, port_name)
    
    def _clone_packet(self, packet: DataPacket) -> DataPacket:
        """Create a deep copy of packet for broadcasting."""
        return DataPacket(
            id=f"{packet.id}_clone_{uuid.uuid4().hex[:6]}",
            payload=packet.payload,  # Share payload reference (read-only)
            data_type=packet.data_type,
            metadata=packet.metadata.copy()  # Shallow copy of metadata
        )
    
    # ─────────────────────────────────────────
    # Processing (Override in subclasses)
    # ─────────────────────────────────────────
    
    @abstractmethod
    def process(self, packet: DataPacket, tick_delta: float) -> DataPacket:
        """
        Process input packet and return output packet.
        
        Args:
            packet: Input DataPacket
            tick_delta: Time since last tick (ms)
            
        Returns:
            Processed DataPacket (or None if consumed)
        """
        pass
    
    def process_tick(self, tick_delta: float):
        """
        Called by engine every tick.
        Processes all packets in input buffers.
        """
        for port_name, buffer in self.input_buffers.items():
            while not buffer.is_empty():
                packet = buffer.dequeue()
                
                try:
                    # Process the packet
                    result = self.process(packet, tick_delta)
                    
                    if result:
                        # Update packet metadata
                        result.metadata["hops"] += 1
                        result.metadata["last_node"] = self.node_id
                        
                        # Send to output
                        self.broadcast_packet(result, "out")
                        
                        # Update state
                        self._update_state(result)
                        
                except Exception as e:
                    self._on_processing_error(packet, e)
    
    # ─────────────────────────────────────────
    # State Management (Async UI Updates)
    # ─────────────────────────────────────────
    
    def get_state(self) -> NodeState:
        """Return current state for UI display."""
        return self._state
    
    def _update_state(self, packet: DataPacket):
        """Update internal state after processing."""
        self._state.compression_ratio = packet.metadata.get("compression_ratio", 1.0)
        self._state.entropy = packet.metadata.get("entropy", 0.0)
        self._state.packets_processed += 1
        self._state.last_operation = self._get_last_operation_name()
        
        # Calculate queue depths
        total_input = sum(len(b) for b in self.input_buffers.values())
        total_output = sum(len(b) for b in self.output_buffers.values())
        self._state.queue_depth = total_input + total_output
    
    def _on_buffer_overflow(self, packet: DataPacket):
        """Handle buffer overflow (packet drop)."""
        self.stats.packets_dropped_buffer_full += 1
        # Emit async signal to UI
        self.state_update_signal.emit_async({
            "node_id": self.node_id,
            "event": "buffer_overflow",
            "packet_id": packet.id
        })
    
    def _on_processing_error(self, packet: DataPacket, error: Exception):
        """Handle processing errors."""
        self.stats.packets_dropped_error += 1
        self._state.status = "error"
        # Emit async signal to UI
        self.error_signal.emit_async(self.node_id, str(error))
    
    @abstractmethod
    def _get_last_operation_name(self) -> str:
        """Return human-readable name of last operation."""
        pass
```

### Buffer Classes
```python
class InputBuffer:
    """Thread-safe input buffer with overflow protection."""
    
    def __init__(self, max_size: int = 10):
        self.max_size = max_size
        self.queue: deque = deque(maxlen=max_size)
    
    def has_space(self) -> bool:
        return len(self.queue) < self.max_size
    
    def enqueue(self, packet: DataPacket):
        """Add packet to buffer. Drops oldest if full."""
        if len(self.queue) >= self.max_size:
            self.queue.popleft()  # Buffer bloat: drop oldest
        self.queue.append(packet)
    
    def dequeue(self) -> DataPacket:
        return self.queue.popleft()
    
    def is_empty(self) -> bool:
        return len(self.queue) == 0
    
    def __len__(self) -> int:
        return len(self.queue)

class OutputBuffer:
    """Output buffer for routing animations."""
    
    def __init__(self, max_size: int = 10):
        self.max_size = max_size
        self.queue: deque = deque(maxlen=max_size)
    
    def enqueue(self, packet: DataPacket):
        self.queue.append(packet)
    
    def clear(self):
        self.queue.clear()
```

---

## 4. Specific Node Implementations

### 4.1 Sources (Generators)

```python
class TextSourceNode(AbstractInfoNode):
    """Generates text packets from user input."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "Text Source")
        self.add_input_port("trigger")  # Optional trigger input
        self.add_output_port("out")
        self.config["text"] = "Hello World!"
        self.config["encoding"] = "utf-8"
    
    def process(self, packet: DataPacket, tick_delta: float) -> DataPacket:
        text = self.config["text"]
        encoding = self.config["encoding"]
        payload = text.encode(encoding)
        
        # Create new packet
        new_packet = DataPacket(
            id=packet.id if packet else f"pkt_{uuid.uuid4().hex[:8]}",
            payload=payload,
            data_type=DataType.RAW_TEXT,
            metadata={
                "original_size": len(payload),
                "current_size": len(payload),
                "compression_ratio": 1.0,
                "entropy": self._calculate_entropy(payload),
                "applied_operations": ["source_generated"],
                "error_flags": [],
                "latency_ms": 0.0,
                "hops": 0,
                "created_tick": self.engine.current_tick
            }
        )
        
        return new_packet
    
    def _get_last_operation_name(self) -> str:
        return "text_generation"

class RandomSourceNode(AbstractInfoNode):
    """Generates random binary data with configurable entropy."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "Random Source")
        self.add_output_port("out")
        self.config["length"] = 100
        self.config["entropy_target"] = 4.0
    
    def process(self, packet: DataPacket, tick_delta: float) -> DataPacket:
        length = self.config["length"]
        target_entropy = self.config["entropy_target"]
        
        # Generate data with target entropy
        payload = self._generate_entropy_data(length, target_entropy)
        
        new_packet = DataPacket(
            id=packet.id if packet else f"pkt_{uuid.uuid4().hex[:8]}",
            payload=payload,
            data_type=DataType.BINARY,
            metadata={
                "original_size": len(payload),
                "current_size": len(payload),
                "compression_ratio": 1.0,
                "entropy": target_entropy,
                "applied_operations": ["random_generation"],
                "error_flags": [],
                "latency_ms": 0.0,
                "hops": 0
            }
        )
        
        return new_packet
```

### 4.2 Compressors (Source Coding)

```python
class HuffmanCompressorNode(AbstractInfoNode):
    """Huffman coding compression."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "Huffman Compressor")
        self.add_input_port("in")
        self.add_output_port("out")
    
    def process(self, packet: DataPacket, tick_delta: float) -> DataPacket:
        # Only compress RAW_TEXT or BINARY
        if packet.data_type not in [DataType.RAW_TEXT, DataType.BINARY]:
            return packet  # Pass through
        
        # Apply Huffman compression
        original_size = len(packet.payload)
        compressed_payload, codebook = huffman_encode(packet.payload)
        compressed_size = len(compressed_payload)
        
        # Calculate entropy
        entropy = self._calculate_entropy(packet.payload)
        compression_ratio = original_size / compressed_size
        
        # Create output packet
        output = DataPacket(
            id=packet.id,
            payload=compressed_payload,
            data_type=DataType.COMPRESSED,
            metadata={
                **packet.metadata,
                "current_size": compressed_size,
                "compression_ratio": compression_ratio,
                "entropy": entropy,
                "applied_operations": packet.metadata["applied_operations"] + ["huffman_compress"],
                "codebook": codebook  # Store for decompression
            }
        )
        
        return output
    
    def _get_last_operation_name(self) -> str:
        return "huffman_compression"

class LZ77CompressorNode(AbstractInfoNode):
    """LZ77 sliding window compression."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "LZ77 Compressor")
        self.add_input_port("in")
        self.add_output_port("out")
        self.config["window_size"] = 4096
    
    def process(self, packet: DataPacket, tick_delta: float) -> DataPacket:
        original_size = len(packet.payload)
        window_size = self.config["window_size"]
        
        # Apply LZ77 compression
        compressed = lz77_compress(packet.payload, window_size)
        compressed_size = len(compressed)
        
        compression_ratio = original_size / compressed_size
        
        output = DataPacket(
            id=packet.id,
            payload=compressed,
            data_type=DataType.COMPRESSED,
            metadata={
                **packet.metadata,
                "current_size": compressed_size,
                "compression_ratio": compression_ratio,
                "applied_operations": packet.metadata["applied_operations"] + ["lz77_compress"]
            }
        )
        
        return output
```

### 4.3 Channel Coders (Security/Error Correction)

```python
class HammingEncoderNode(AbstractInfoNode):
    """Hamming(7,4) error correction encoder."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "Hamming Encoder")
        self.add_input_port("in")
        self.add_output_port("out")
    
    def process(self, packet: DataPacket, tick_delta: float) -> DataPacket:
        # Convert payload to bit array
        bits = self._bytes_to_bits(packet.payload)
        
        # Encode with Hamming(7,4)
        encoded_bits = []
        for i in range(0, len(bits), 4):
            chunk = bits[i:i+4]
            while len(chunk) < 4:
                chunk.append(0)
            encoded_bits.extend(hamming_74_encode(chunk))
        
        # Convert back to bytes
        encoded_payload = self._bits_to_bytes(encoded_bits)
        
        output = DataPacket(
            id=packet.id,
            payload=encoded_payload,
            data_type=DataType.ENCODED,
            metadata={
                **packet.metadata,
                "current_size": len(encoded_payload),
                "applied_operations": packet.metadata["applied_operations"] + ["hamming_encode"],
                "encoding_rate": "4/7"
            }
        )
        
        return output

class HammingDecoderNode(AbstractInfoNode):
    """Hamming(7,4) decoder with error correction."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "Hamming Decoder")
        self.add_input_port("in")
        self.add_output_port("out")
    
    def process(self, packet: DataPacket, tick_delta: float) -> DataPacket:
        bits = self._bytes_to_bits(packet.payload)
        
        decoded_bits = []
        errors_fixed = 0
        
        for i in range(0, len(bits), 7):
            chunk = bits[i:i+7]
            while len(chunk) < 7:
                chunk.append(0)
            
            decoded_chunk, error_corrected = hamming_74_decode(chunk)
            decoded_bits.extend(decoded_chunk)
            
            if error_corrected:
                errors_fixed += 1
        
        decoded_payload = self._bits_to_bytes(decoded_bits)
        
        # Update metadata
        metadata = packet.metadata.copy()
        metadata["applied_operations"] = metadata["applied_operations"] + ["hamming_decode"]
        if errors_fixed > 0:
            metadata["error_flags"] = metadata["error_flags"] + [f"hamming_fixed_{errors_fixed}"]
        
        output = DataPacket(
            id=packet.id,
            payload=decoded_payload,
            data_type=DataType.DECODED,
            metadata=metadata
        )
        
        return output
```

### 4.4 Channels (Environment/Noise)

```python
class BinarySymmetricChannelNode(AbstractInfoNode):
    """
    Binary Symmetric Channel (BSC) with error probability p.
    
    Flips each bit with probability p.
    """
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "BSC Channel")
        self.add_input_port("in")
        self.add_output_port("out")
        self.config["error_prob"] = 0.05  # p = 0.05
        self.stats.total_bits_processed = 0
        self.stats.total_errors_introduced = 0
    
    def process(self, packet: DataPacket, tick_delta: float) -> DataPacket:
        p = self.config["error_prob"]
        
        # Flip bits with probability p
        noisy_payload = bytearray()
        error_bitmask = 0
        
        for byte_idx, byte_val in enumerate(packet.payload):
            noisy_byte = 0
            for bit_idx in range(8):
                bit = (byte_val >> bit_idx) & 1
                
                if random.random() < p:
                    # Flip bit
                    bit ^= 1
                    error_bitmask |= (1 << (byte_idx * 8 + bit_idx))
                    self.stats.total_errors_introduced += 1
                
                noisy_byte |= (bit << bit_idx)
            
            noisy_payload.append(noisy_byte)
            self.stats.total_bits_processed += 8
        
        # Update metadata
        ber = self.stats.total_errors_introduced / max(1, self.stats.total_bits_processed)
        
        metadata = packet.metadata.copy()
        metadata["applied_operations"] = metadata["applied_operations"] + ["bsc_channel"]
        if error_bitmask != 0:
            metadata["error_flags"] = metadata["error_flags"] + ["bsc_corrupted"]
        metadata["ber"] = ber
        
        output = DataPacket(
            id=packet.id,
            payload=bytes(noisy_payload),
            data_type=DataType.NOISY,
            metadata=metadata
        )
        
        return output
    
    def _get_last_operation_name(self) -> str:
        return f"bsc(p={self.config['error_prob']})"

class AWGNChannelNode(AbstractInfoNode):
    """Additive White Gaussian Noise channel."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "AWGN Channel")
        self.add_input_port("in")
        self.add_output_port("out")
        self.config["snr_db"] = 20.0
    
    def process(self, packet: DataPacket, tick_delta: float) -> DataPacket:
        snr_db = self.config["snr_db"]
        
        # Convert to signal
        import numpy as np
        signal = np.frombuffer(packet.payload, dtype=np.uint8).astype(np.float64)
        signal = (signal - 128) / 128.0  # Normalize to [-1, 1]
        
        # Add AWGN
        snr_linear = 10 ** (snr_db / 10.0)
        signal_power = np.mean(signal ** 2)
        noise_power = signal_power / snr_linear
        noise = np.sqrt(noise_power) * np.random.randn(len(signal))
        
        noisy_signal = signal + noise
        noisy_signal = np.clip(noisy_signal * 128 + 128, 0, 255).astype(np.uint8)
        
        output = DataPacket(
            id=packet.id,
            payload=noisy_signal.tobytes(),
            data_type=DataType.NOISY,
            metadata={
                **packet.metadata,
                "applied_operations": packet.metadata["applied_operations"] + ["awgn_channel"],
                "snr_db": snr_db
            }
        )
        
        return output
```

### 4.5 Receivers / Decoders

```python
class SyndromeCalculatorNode(AbstractInfoNode):
    """
    Calculates error syndromes for Hamming codes.
    
    Syndrome s = p · H^T
    If s = 0: No error
    If s ≠ 0: Error at position indicated by syndrome
    """
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "Syndrome Calculator")
        self.add_input_port("in")
        self.add_output_port("out")
    
    def process(self, packet: DataPacket, tick_delta: float) -> DataPacket:
        # Extract parity bits and calculate syndrome
        bits = self._bytes_to_bits(packet.payload)
        
        syndromes = []
        for i in range(0, len(bits), 7):
            chunk = bits[i:i+7]
            syndrome = self._calculate_syndrome(chunk)
            syndromes.append(syndrome)
        
        # Add syndrome to metadata
        metadata = packet.metadata.copy()
        metadata["syndromes"] = syndromes
        metadata["applied_operations"] = metadata["applied_operations"] + ["syndrome_calc"]
        
        output = DataPacket(
            id=packet.id,
            payload=packet.payload,
            data_type=packet.data_type,
            metadata=metadata
        )
        
        return output
    
    def _calculate_syndrome(self, bits_7: List[int]) -> int:
        """Calculate Hamming(7,4) syndrome."""
        # Hamming(7,4) parity-check matrix H
        # Syndrome = H · r^T
        p1 = bits_7[0] ^ bits_7[1] ^ bits_7[3] ^ bits_7[4] ^ bits_7[6]
        p2 = bits_7[0] ^ bits_7[2] ^ bits_7[3] ^ bits_7[5] ^ bits_7[6]
        p3 = bits_7[1] ^ bits_7[2] ^ bits_7[3]
        p4 = bits_7[4] ^ bits_7[5] ^ bits_7[6]
        
        syndrome = (p1 << 3) | (p2 << 2) | (p3 << 1) | p4
        return syndrome

class BERAnalyzerNode(AbstractInfoNode):
    """Analyzes Bit Error Rate and packet loss."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "BER Analyzer")
        self.add_input_port("in")
        self.add_output_port("out")
        self.stats.total_bits = 0
        self.stats.error_bits = 0
        self.stats.packets_analyzed = 0
    
    def process(self, packet: DataPacket, tick_delta: float) -> DataPacket:
        self.stats.packets_analyzed += 1
        self.stats.total_bits += packet.size_bits
        self.stats.error_bits += packet.error_count
        
        ber = self.stats.error_bits / max(1, self.stats.total_bits)
        
        # Update state for UI
        self._state.ber = ber
        self._state.total_errors = self.stats.error_bits
        self._state.total_bits = self.stats.total_bits
        
        # Add analysis to metadata
        metadata = packet.metadata.copy()
        metadata["ber"] = ber
        metadata["applied_operations"] = metadata["applied_operations"] + ["ber_analysis"]
        
        output = DataPacket(
            id=packet.id,
            payload=packet.payload,
            data_type=packet.data_type,
            metadata=metadata
        )
        
        return output
```

---

## 5. State Management & Real-Time Analytics

### Async State Emission System
```python
class AsyncStateEmitter:
    """
    Non-blocking state emission to UI.
    Uses a queue to batch updates and emit at UI frame rate.
    """
    
    def __init__(self, update_interval_ms: int = 100):
        self.update_interval_ms = update_interval_ms
        self.state_queue: deque = deque(maxlen=100)
        self.last_emit_time = 0
    
    def emit_async(self, node_id: str, state: NodeState):
        """Queue state update (non-blocking)."""
        self.state_queue.append((node_id, state))
        
        # Throttle emissions to UI frame rate
        current_time = time.time() * 1000
        if current_time - self.last_emit_time >= self.update_interval_ms:
            self._flush_to_ui()
    
    def _flush_to_ui(self):
        """Send all queued states to UI thread."""
        states = dict(self.state_queue)
        self.state_queue.clear()
        self.last_emit_time = time.time() * 1000
        
        # Emit to UI (Qt signal or similar)
        self.ui_update_signal.emit(states)

class NodeStats:
    """Statistics tracking for each node."""
    
    def __init__(self):
        self.packets_received = 0
        self.packets_sent = 0
        self.packets_processed = 0
        self.packets_dropped_buffer_full = 0
        self.packets_dropped_error = 0
        self.total_processing_time_ms = 0.0
        self.total_bits_processed = 0
        self.total_errors_introduced = 0
    
    def get_summary(self) -> Dict[str, Any]:
        return {
            "received": self.packets_received,
            "sent": self.packets_sent,
            "processed": self.packets_processed,
            "dropped_buffer": self.packets_dropped_buffer_full,
            "dropped_error": self.packets_dropped_error,
            "avg_processing_ms": self.total_processing_time_ms / max(1, self.packets_processed),
            "total_bits": self.total_bits_processed,
            "errors": self.total_errors_introduced
        }
```

---

## 6. Data Flow Example: Complete Pipeline

### Scenario: Text → Huffman → BSC → Hamming Decode → BER Analysis

```
┌──────────────┐
│ Text Source   │ DataPacket: payload="HELLO", data_type=RAW_TEXT
└──────┬───────┘ metadata: {original_size: 5, entropy: 2.32, hops: 0}
       │
       ▼
┌──────────────────┐
│ Huffman Compress │ DataPacket: payload="compressed_bin", data_type=COMPRESSED
└──────┬───────────┘ metadata: {compression_ratio: 0.6, entropy: 2.32, hops: 1,
       │                            applied_operations: ["huffman_compress"]}
       ▼
┌──────────────────┐
│ BSC Channel      │ DataPacket: payload="noisy_bin", data_type=NOISY
└──────┬───────────┘ metadata: {error_flags: ["bsc_corrupted"], ber: 0.05, hops: 2,
       │                            applied_operations: ["huffman_compress", "bsc_channel"]}
       ▼
┌──────────────────┐
│ Hamming Decode   │ DataPacket: payload="decoded_bin", data_type=DECODED
└──────┬───────────┘ metadata: {error_flags: ["bsc_corrupted", "hamming_fixed_2"],
       │                            hops: 3, applied_operations: ["huffman_compress",
       │                            "bsc_channel", "hamming_decode"]}
       ▼
┌──────────────────┐
│ BER Analyzer     │ Final state: BER = 0.048, Total bits = 40, Errors = 2
└──────────────────┘
```

### Transformation Rules Summary

| Node | Input Type | Output Type | Transformation |
|------|-----------|-------------|-----------------|
| TextSource | None | RAW_TEXT | Generate text payload |
| RandomSource | None | BINARY | Generate random bytes |
| HuffmanCompress | RAW_TEXT/BINARY | COMPRESSED | Apply Huffman coding |
| LZ77Compress | BINARY | COMPRESSED | Apply LZ77 compression |
| HammingEncode | BINARY | ENCODED | Add redundancy (4/7 rate) |
| BSCChannel | ANY | NOISY | Flip bits with prob p |
| AWGNChannel | ANY | NOISY | Add Gaussian noise |
| HammingDecode | ENCODED | DECODED | Correct single-bit errors |
| BERAnalyzer | ANY | ANY | Calculate error statistics |

---

## 7. Multi-Connection Broadcasting Logic

### Scenario: One Output → Multiple Targets

```
                    ┌─────────────┐
                    │   Node A    │
                    │  Output "out"│
                    └──────┬──────┘
                           │
                    Packet P (original)
                           │
            ┌──────────────┼──────────────┐
            │              │              │
            ▼              ▼              ▼
       ┌─────────┐   ┌─────────┐   ┌─────────┐
       │ Node B  │   │ Node C  │   │ Node D  │
       │ Input   │   │ Input   │   │ Input   │
       └─────────┘   └─────────┘   └─────────┘

Broadcast creates 3 independent copies:
- P_bc_0 → Node B
- P_bc_1 → Node C  
- P_bc_2 → Node D

Each copy has:
- Unique broadcast_id
- Independent metadata (can be modified separately)
- Shared payload reference (read-only optimization)
```

### Implementation
```python
def broadcast_packet(self, packet: DataPacket, port_name: str):
    connections = self.get_connections(port_name)
    
    for i, target in enumerate(connections):
        # Clone for this specific target
        cloned = DataPacket(
            id=f"{packet.id}_bc_{i}",
            payload=packet.payload,  # Shared reference (immutable)
            data_type=packet.data_type,
            metadata=packet.metadata.copy()
        )
        
        # Add routing metadata
        cloned.metadata["broadcast_id"] = i
        cloned.metadata["target_node"] = target.node_id
        
        # Send to output buffer
        self.output_buffers[port_name].enqueue(cloned)
```

---

## 8. Buffer Bloat Simulation

### Behavior
```
Input Rate: 100 packets/sec
Processing Rate: 50 packets/sec
Buffer Size: 10 packets

Timeline:
t=0ms:  Buffer=[], Processing starts
t=10ms: Buffer=[P1], Processing P1
t=20ms: Buffer=[P2, P1], Processing P2
t=30ms: Buffer=[P3, P2, P1], Processing P3
...
t=100ms: Buffer=[P10, P9, P8, P7, P6, P5, P4, P3, P2, P1] (FULL)
t=110ms: Buffer=[P11, P10, P9, P8, P7, P6, P5, P4, P3, P2] (P1 DROPPED)
t=120ms: Buffer=[P12, P11, P10, P9, P8, P7, P6, P5, P4, P3] (P2 DROPPED)

Result: 20% packet loss due to buffer overflow
```

### Implementation
```python
class InputBuffer:
    def __init__(self, max_size: int = 10):
        self.max_size = max_size
        self.queue: deque = deque(maxlen=max_size)
    
    def enqueue(self, packet: DataPacket):
        """Add packet. If full, drop oldest (FIFO overflow)."""
        if len(self.queue) >= self.max_size:
            dropped = self.queue[0]  # Oldest packet
            self.queue.popleft()     # Remove it
            self._on_drop(dropped)   # Notify stats
        
        self.queue.append(packet)
```

---

## 9. Complete Class Hierarchy

```
AbstractInfoNode (ABC)
├── Sources
│   ├── TextSourceNode
│   ├── RandomSourceNode
│   ├── NumberInputNode
│   ├── AudioSourceNode
│   └── ImageSourceNode
│
├── Compressors
│   ├── HuffmanCompressorNode
│   ├── LZ77CompressorNode
│   ├── LZ78CompressorNode
│   └── RLECompressorNode
│
├── ChannelCoders
│   ├── HammingEncoderNode
│   ├── HammingDecoderNode
│   ├── CRCEncoderNode
│   └── ParityEncoderNode
│
├── Channels
│   ├── BinarySymmetricChannelNode
│   ├── AWGNChannelNode
│   ├── GilbertElliottChannelNode
│   └── IdealChannelNode
│
├── Decoders
│   ├── HammingDecoderNode
│   ├── SyndromeCalculatorNode
│   └── ErrorCorrectorNode
│
└── Analyzers
    ├── EntropyMeterNode
    ├── BERAnalyzerNode
    ├── CompressionRatioNode
    └── LatencyMeterNode
```

---

## 10. Key Design Principles

### 1. Separation of Concerns
- **Simulation Engine**: Tick management, routing, timing
- **Nodes**: Processing logic, buffer management
- **DataPacket**: Data carrier with full history
- **UI**: Rendering only (receives state updates asynchronously)

### 2. Immutability Where Possible
- Payload is shared by reference (read-only)
- Metadata is copied on broadcast (allows independent tracking)
- Packet ID is immutable after creation

### 3. Non-Blocking UI
- State updates queued and batched
- Emitted at UI frame rate (not simulation tick rate)
- Simulation thread never waits for UI

### 4. Extensibility
- New nodes inherit from AbstractInfoNode
- Override only `process()` method
- Parameter schema auto-generates UI
- No UI code in node classes

---

## Summary

This architecture provides:
1. ✅ Universal DataPacket with full metadata tracking
2. ✅ Tick-based simulation engine (60 Hz)
3. ✅ Abstract base class with buffer management
4. ✅ Multi-connection broadcasting
5. ✅ Buffer bloat simulation
6. ✅ Async state emission to UI
7. ✅ Complete node implementations
8. ✅ Clear data flow documentation

The system is ready for implementation in Python with Qt for UI.