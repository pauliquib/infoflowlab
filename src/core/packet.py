"""
DataPacket - enhanced packet with full metadata for simulation.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import time
import uuid


@dataclass
class TransformStep:
    """Record of a single processing step in the packet's journey."""
    node_name: str
    operation: str
    input_size: int
    output_size: int
    processing_time_ms: float = 0.0
    details: str = ""


@dataclass
class DataPacket:
    """
    Enhanced data packet with full metadata for simulation.
    
    Supports lazy properties for different views (text, hex, bits),
    error tracking, latency measurement, and compression history.
    """
    id: str
    payload: bytes
    source_format: str = "text"
    encoding: str = "utf-8"
    compression_ratio: float = 1.0
    entropy: float = 0.0
    size_bits: int = 0
    history: List[TransformStep] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    timestamp_created: float = field(default_factory=time.time)
    timestamp_received: Optional[float] = None
    latency_accrued: float = 0.0
    bitrate: float = 0.0
    error_count: int = 0
    error_bitmask: int = 0
    compression_ratio_history: List[float] = field(default_factory=list)
    spectrum_data: Optional[Any] = None
    _as_text: Optional[str] = None
    _as_hex: Optional[str] = None
    _as_bits: Optional[str] = None
    
    def __post_init__(self):
        if self.size_bits == 0 and self.payload:
            self.size_bits = len(self.payload) * 8
    
    @property
    def as_text(self) -> str:
        """Lazy property: payload as text."""
        if self._as_text is None:
            try:
                self._as_text = self.payload.decode(self.encoding, errors="replace")
            except Exception:
                self._as_text = repr(self.payload)[:200]
        return self._as_text
    
    @property
    def as_hex(self) -> str:
        """Lazy property: payload as hex string."""
        if self._as_hex is None:
            self._as_hex = self.payload.hex()
        return self._as_hex
    
    @property
    def as_bits(self) -> str:
        """Lazy property: payload as bit string."""
        if self._as_bits is None:
            self._as_bits = ''.join(format(b, '08b') for b in self.payload)
        return self._as_bits
    
    def add_step(self, node_name: str, operation: str, in_size: int, out_size: int,
                 details: str = "", processing_time_ms: float = 0.0):
        """Add a processing step to the packet's history."""
        self.history.append(TransformStep(
            node_name=node_name,
            operation=operation,
            input_size=in_size,
            output_size=out_size,
            processing_time_ms=processing_time_ms,
            details=details
        ))
        self.size_bits = out_size * 8 if isinstance(out_size, int) else out_size
    
    def add_error(self, error_type: str, description: str, bitmask: int = 0):
        """Record an error that occurred during transmission."""
        self.errors.append({
            "type": error_type,
            "description": description,
            "bitmask": bitmask,
            "timestamp": time.time()
        })
        self.error_count += 1
        self.error_bitmask |= bitmask
    
    def record_latency(self, latency_ms: float):
        """Accrue latency from a processing step or channel."""
        self.latency_accrued += latency_ms
    
    def mark_received(self):
        """Mark the packet as received at its destination."""
        self.timestamp_received = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize packet to dictionary (excluding large payloads)."""
        return {
            "id": self.id,
            "source_format": self.source_format,
            "encoding": self.encoding,
            "compression_ratio": self.compression_ratio,
            "entropy": self.entropy,
            "size_bits": self.size_bits,
            "error_count": self.error_count,
            "latency_accrued": self.latency_accrued,
            "timestamp_created": self.timestamp_created,
            "history": [
                {
                    "node_name": h.node_name,
                    "operation": h.operation,
                    "input_size": h.input_size,
                    "output_size": h.output_size,
                    "details": h.details
                }
                for h in self.history
            ],
            "errors": self.errors
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any], payload: bytes = b"") -> 'DataPacket':
        """Deserialize packet from dictionary."""
        pkt = DataPacket(
            id=data.get("id", f"pkt_{uuid.uuid4().hex[:8]}"),
            payload=payload,
            source_format=data.get("source_format", "text"),
            encoding=data.get("encoding", "utf-8"),
            compression_ratio=data.get("compression_ratio", 1.0),
            entropy=data.get("entropy", 0.0),
            size_bits=data.get("size_bits", 0),
            error_count=data.get("error_count", 0),
            latency_accrued=data.get("latency_accrued", 0.0),
            timestamp_created=data.get("timestamp_created", time.time())
        )
        for h_data in data.get("history", []):
            pkt.history.append(TransformStep(
                node_name=h_data.get("node_name", ""),
                operation=h_data.get("operation", ""),
                input_size=h_data.get("input_size", 0),
                output_size=h_data.get("output_size", 0),
                details=h_data.get("details", "")
            ))
        pkt.errors = data.get("errors", [])
        return pkt