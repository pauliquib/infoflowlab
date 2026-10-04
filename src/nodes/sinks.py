"""
Sink/output nodes - text display, file, console, hex dump, comparison.
"""

from src.core.node_base import NodeBase, ParamType
from src.core.packet import DataPacket
from src.core.port import DataType


class TextOutputNode(NodeBase):
    """Text display output."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "sink", "📄 TextOut", category="sinks")
        self.add_input("in", DataType.TEXT)
        self.last_text = ""
        self.last_metrics = {}
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        self.last_text = packet.as_text[:200]
        self.last_metrics = {
            "size_bits": packet.size_bits,
            "entropy": f"{packet.entropy:.3f}" if packet.entropy else "N/A",
            "compression_ratio": f"{packet.compression_ratio:.2f}",
            "errors": packet.error_count,
            "latency_ms": f"{packet.latency_accrued:.2f}"
        }
        packet.add_step(self.name, "TextOutput", len(packet.payload), len(packet.payload), "displayed")
        return packet


class FileSinkNode(NodeBase):
    """File output sink."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "sink", "💾 Soubor", category="sinks")
        self.add_input("in", DataType.ANY)
        self.set_param("filename", "output.bin")
    
    def get_param_schema(self) -> dict:
        schema = super().get_param_schema()
        schema["filename"] = {
            "type": ParamType.STR, "label": "Filename", "default": "output.bin",
            "description": "Path to output file",
            "category": "basic"
        }
        return schema
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        filename = self.get_param("filename", "output.bin")
        try:
            with open(filename, "wb") as f:
                f.write(packet.payload)
            packet.add_step(self.name, "FileSink", len(packet.payload), len(packet.payload),
                            f"saved to {filename}")
        except Exception as e:
            packet.add_step(self.name, "FileSink", len(packet.payload), len(packet.payload),
                            f"error: {e}")
        return packet


class ConsoleSinkNode(NodeBase):
    """Console output sink."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "sink", "🖥️ Konzole", category="sinks")
        self.add_input("in", DataType.ANY)
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        text = packet.as_text[:100]
        print(f"[ConsoleSink] {text}")
        packet.add_step(self.name, "ConsoleSink", len(packet.payload), len(packet.payload), "printed")
        return packet


class HexDumpSinkNode(NodeBase):
    """Hex dump output."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "sink", "🔢 HexDump", category="sinks")
        self.add_input("in", DataType.ANY)
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        hex_str = packet.as_hex
        formatted = ' '.join([hex_str[i:i+2] for i in range(0, min(len(hex_str), 100), 2)])
        print(f"[HexDump] {formatted}")
        packet.add_step(self.name, "HexDump", len(packet.payload), len(packet.payload), "dumped")
        return packet


class ComparisonSinkNode(NodeBase):
    """A/B comparison sink."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "sink", "⚖️ Compare", category="sinks")
        self.add_input("in_a", DataType.ANY)
        self.add_input("in_b", DataType.ANY)
        self.add_output("out", DataType.ANY)
        self.last_a = b""
        self.last_b = b""
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        if input_port == "in_a":
            self.last_a = packet.payload
        elif input_port == "in_b":
            self.last_b = packet.payload
        
        if self.last_a and self.last_b:
            equal = self.last_a == self.last_b
            diff_count = sum(1 for a, b in zip(self.last_a, self.last_b) if a != b) if not equal else 0
            packet.add_step(self.name, "Compare", len(packet.payload), len(packet.payload),
                            f"equal={equal}, diff_bytes={diff_count}")
        
        return packet


class ImageOutputNode(NodeBase):
    """Image output sink - displays image data with preview."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "sink", "🖼️ ImageOut", category="sinks")
        self.add_input("in", DataType.IMAGE)
        self.last_image_size = ""
        self.last_image_format = ""
        self.last_image_bytes = None  # Store for preview
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        if not packet.payload:
            self.last_image_size = "No data"
            self.last_image_bytes = None
            packet.add_step(self.name, "ImageOutput", 0, 0, "No image data")
            return packet
        
        try:
            from PIL import Image
            import io
            
            # Load image from packet payload
            img = Image.open(io.BytesIO(packet.payload))
            
            # Store metadata for display
            self.last_image_size = f"{img.width}x{img.height}"
            self.last_image_format = img.format or "Unknown"
            self.last_image_bytes = packet.payload  # Store for preview
            
            packet.add_step(self.name, "ImageOutput", len(packet.payload), len(packet.payload),
                          f"{img.width}x{img.height} {img.mode}")
            return packet
            
        except Exception as e:
            self.last_image_size = f"Error: {str(e)}"
            self.last_image_bytes = None
            packet.add_step(self.name, "ImageOutput", len(packet.payload), len(packet.payload),
                          f"Error: {str(e)}")
            return packet
