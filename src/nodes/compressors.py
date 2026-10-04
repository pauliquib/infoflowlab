"""
Compressor nodes with enhanced base class and param schemas.
"""

from src.core.node_base import NodeBase, ParamType
from src.core.packet import DataPacket
from src.core.port import DataType
from src.algorithms.compression import (
    rle_compress, rle_decompress,
    lz77_compress,
    lzw_compress,
)
import json


class RLECompressorNode(NodeBase):
    """Run-Length Encoding compress/decompress."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "compressor", "📏 RLE", category="compressors")
        self.add_input("in", DataType.BINARY)
        self.add_output("out", DataType.BINARY)
        self.set_param("mode", "compress")
    
    def get_param_schema(self) -> dict:
        schema = super().get_param_schema()
        schema["mode"] = {
            "type": ParamType.CHOICE, "label": "Mode", "default": "compress",
            "choices": ["compress", "decompress"],
            "description": "Compress or decompress mode",
            "category": "basic"
        }
        return schema
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        mode = self.get_param("mode", "compress")
        if mode == "compress":
            result = rle_compress(packet.payload)
        else:
            result = rle_decompress(packet.payload)
        
        new_pkt = DataPacket(id=packet.id, payload=result.data,
                             size_bits=len(result.data)*8)
        new_pkt.compression_ratio = result.compression_ratio
        new_pkt.add_step(self.name, f"RLE-{mode}", result.original_size, result.compressed_size,
                         f"ratio={result.compression_ratio:.2f}")
        return new_pkt


class HuffmanCompressorNode(NodeBase):
    """Huffman compression."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "compressor", "🌳 Huffman", category="compressors")
        self.add_input("in", DataType.BINARY)
        self.add_output("out", DataType.BINARY)
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        from src.algorithms.huffman import huffman_encode, huffman_decode
        encoded, codes = huffman_encode(packet.payload)
        # Store codes as metadata in payload
        meta = json.dumps({"codes": {str(k): v for k, v in codes.items()}}).encode()
        full = meta + b"|||" + encoded.encode()
        
        new_pkt = DataPacket(id=packet.id, payload=full, size_bits=len(encoded))
        new_pkt.compression_ratio = (len(packet.payload) * 8) / max(1, len(encoded))
        new_pkt.add_step(self.name, "Huffman", len(packet.payload)*8, len(encoded),
                         f"ratio={new_pkt.compression_ratio:.2f}")
        return new_pkt


class LZ77CompressorNode(NodeBase):
    """LZ77 sliding window compression."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "compressor", "🗜️ LZ77", category="compressors")
        self.add_input("in", DataType.BINARY)
        self.add_output("out", DataType.BINARY)
        self.set_param("window_size", 4096)
    
    def get_param_schema(self) -> dict:
        schema = super().get_param_schema()
        schema["window_size"] = {
            "type": ParamType.INT, "label": "Window Size", "default": 4096,
            "min": 128, "max": 32768, "step": 128,
            "description": "Search window size for LZ77",
            "category": "basic"
        }
        return schema
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        ws = self.get_param("window_size", 4096)
        result = lz77_compress(packet.payload, window_size=ws)
        new_pkt = DataPacket(id=packet.id, payload=result.data,
                             size_bits=len(result.data)*8)
        new_pkt.compression_ratio = result.compression_ratio
        new_pkt.add_step(self.name, "LZ77", result.original_size, result.compressed_size,
                         f"ratio={result.compression_ratio:.2f}, window={ws}")
        return new_pkt


class LZWCompressorNode(NodeBase):
    """LZW dictionary compression."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "compressor", "🗜️ LZW", category="compressors")
        self.add_input("in", DataType.BINARY)
        self.add_output("out", DataType.BINARY)
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        result = lzw_compress(packet.payload)
        new_pkt = DataPacket(id=packet.id, payload=result.data,
                             size_bits=len(result.data)*8)
        new_pkt.compression_ratio = result.compression_ratio
        new_pkt.add_step(self.name, "LZW", result.original_size, result.compressed_size,
                         f"ratio={result.compression_ratio:.2f}")
        return new_pkt