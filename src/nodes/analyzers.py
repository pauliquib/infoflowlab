"""
Analyzer nodes - entropy, histogram, BER, latency, compression ratio.
"""

from src.core.node_base import NodeBase, ParamType
from src.core.packet import DataPacket
from src.core.port import DataType
from src.algorithms.entropy import shannon_entropy, max_entropy, efficiency


class EntropyMeterNode(NodeBase):
    """Shannon entropy meter."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "analyzer", "📊 Entropie", category="analyzers")
        self.add_input("in", DataType.ANY)
        self.add_output("out", DataType.ANY)
        self.last_entropy = 0.0
        self.last_max = 0.0
        self.last_eff = 0.0
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        self.last_entropy = shannon_entropy(packet.payload)
        self.last_max = max_entropy(256)
        self.last_eff = efficiency(self.last_entropy, self.last_max)
        packet.entropy = self.last_entropy
        packet.add_step(self.name, "Entropy", len(packet.payload), len(packet.payload),
                        f"H={self.last_entropy:.3f}, eff={self.last_eff:.1f}%")
        return packet


class HistogramNode(NodeBase):
    """Symbol frequency histogram."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "analyzer", "📈 Histogram", category="analyzers")
        self.add_input("in", DataType.ANY)
        self.add_output("out", DataType.ANY)
        self.frequencies = {}
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        from collections import Counter
        self.frequencies = dict(Counter(packet.payload))
        packet.add_step(self.name, "Histogram", len(packet.payload), len(packet.payload),
                        f"unique={len(self.frequencies)}")
        return packet


class CompressionRatioNode(NodeBase):
    """Compression ratio analyzer."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "analyzer", "📊 CompRatio", category="analyzers")
        self.add_input("in", DataType.ANY)
        self.add_output("out", DataType.ANY)
        self.last_ratio = 1.0
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        ratio = packet.compression_ratio
        self.last_ratio = ratio
        if packet.history:
            last = packet.history[-1]
            in_size = last.input_size
            out_size = last.output_size
            detail = f"in={in_size}, out={out_size}, ratio={ratio:.3f}"
        else:
            detail = f"ratio={ratio:.3f}"
        packet.add_step(self.name, "CompRatio", len(packet.payload), len(packet.payload), detail)
        return packet


class BERMeterNode(NodeBase):
    """Bit Error Rate meter."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "analyzer", "📊 BER Meter", category="analyzers")
        self.add_input("in", DataType.ANY)
        self.add_output("out", DataType.ANY)
        self.total_bits = 0
        self.error_bits = 0
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        self.total_bits += packet.size_bits
        self.error_bits += packet.error_count
        ber = self.error_bits / max(1, self.total_bits)
        packet.add_step(self.name, "BER", len(packet.payload), len(packet.payload),
                        f"BER={ber:.6f}, errors={self.error_bits}/{self.total_bits}")
        return packet


class LatencyMeterNode(NodeBase):
    """Latency measurement analyzer."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "analyzer", "⏱️ LatencyMeter", category="analyzers")
        self.add_input("in", DataType.ANY)
        self.add_output("out", DataType.ANY)
        self.latencies = []
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        latency = packet.latency_accrued
        self.latencies.append(latency)
        if len(self.latencies) > 100:
            self.latencies.pop(0)
        avg = sum(self.latencies) / len(self.latencies) if self.latencies else 0
        packet.add_step(self.name, "Latency", len(packet.payload), len(packet.payload),
                        f"latency={latency:.2f}ms, avg={avg:.2f}ms")
        return packet