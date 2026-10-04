"""
Encoder and Decoder nodes - Base conversion, UTF-8, Morse, Huffman, Base64, Hex.
All nodes use the enhanced NodeBase with category, param schema, and proper data types.
"""

from src.core.node_base import NodeBase, ParamType
from src.core.packet import DataPacket
from src.core.port import DataType
from src.algorithms.number_systems import NumberConverter
from src.algorithms.huffman import HuffmanCoder
from src.algorithms.huffman import huffman_encode as hf_enc, huffman_decode as hf_dec
import json
import base64


# ============================================================
# ENCODERS
# ============================================================

class BaseConverterNode(NodeBase):
    """Convert between number bases (2-36)."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "encoder", "🔀 BaseConv", category="encoders")
        self.add_input("in", DataType.NUMERIC)
        self.add_output("out", DataType.TEXT)
        self.set_param("from_base", 10)
        self.set_param("to_base", 2)
        self.set_param("signed", False)
        self.set_param("word_size", 8)
    
    def get_param_schema(self) -> dict:
        schema = super().get_param_schema()
        schema.update({
            "from_base": {
                "type": ParamType.INT, "label": "From Base", "default": 10,
                "min": 2, "max": 36, "description": "Source number base",
                "category": "basic"
            },
            "to_base": {
                "type": ParamType.INT, "label": "To Base", "default": 2,
                "min": 2, "max": 36, "description": "Target number base",
                "category": "basic"
            },
            "signed": {
                "type": ParamType.BOOL, "label": "Signed", "default": False,
                "description": "Use signed number representation",
                "category": "advanced"
            },
            "word_size": {
                "type": ParamType.INT, "label": "Word Size", "default": 8,
                "min": 4, "max": 64, "description": "Bit width for signed numbers",
                "category": "advanced"
            }
        })
        return schema
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        text = packet.as_text
        parts = text.split("_")
        val = parts[0]
        from_b = int(parts[1]) if len(parts) > 1 else self.get_param("from_base", 10)
        to_b = self.get_param("to_base", 2)
        
        try:
            result = NumberConverter.convert(val, from_b, to_b)
        except Exception as e:
            result = f"ERROR: {e}"
        
        data = result.encode("utf-8")
        new_pkt = DataPacket(id=packet.id, payload=data, source_format="text",
                             encoding="utf-8", size_bits=len(data)*8)
        new_pkt.add_step(self.name, "BaseConvert", len(packet.payload), len(data),
                         f"{from_b}→{to_b}")
        return new_pkt


class Utf8EncoderNode(NodeBase):
    """Encode text to UTF-8 bytes."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "encoder", "🔤 UTF-8", category="encoders")
        self.add_input("in", DataType.TEXT)
        self.add_output("out", DataType.BINARY)
    
    def get_param_schema(self) -> dict:
        return super().get_param_schema()
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        packet.encoding = "utf-8"
        packet.add_step(self.name, "UTF-8", len(packet.payload), len(packet.payload), "encoded")
        return packet


class MorseEncoderNode(NodeBase):
    """Encode text to Morse code."""
    
    MORSE = {
        'A': ".-", 'B': "-...", 'C': "-.-.", 'D': "-..", 'E': ".", 'F': "..-.",
        'G': "--.", 'H': "....", 'I': "..", 'J': ".---", 'K': "-.-", 'L': ".-..",
        'M': "--", 'N': "-.", 'O': "---", 'P': ".--.", 'Q': "--.-", 'R': ".-.",
        'S': "...", 'T': "-", 'U': "..-", 'V': "...-", 'W': ".--", 'X': "-..-",
        'Y': "-.--", 'Z': "--..", '1': ".----", '2': "..---", '3': "...--",
        '4': "....-", '5': ".....", '6': "-....", '7': "--...", '8': "---..",
        '9': "----.", '0': "-----", ' ': "/"
    }
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "encoder", "📻 Morse", category="encoders")
        self.add_input("in", DataType.TEXT)
        self.add_output("out", DataType.MORSE)
        self.set_param("wpm", 20)
    
    def get_param_schema(self) -> dict:
        schema = super().get_param_schema()
        schema["wpm"] = {
            "type": ParamType.INT, "label": "Speed (WPM)", "default": 20,
            "min": 5, "max": 100, "description": "Words per minute",
            "category": "basic"
        }
        return schema
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        text = packet.as_text.upper()
        result = " ".join(self.MORSE.get(c, "?") for c in text)
        data = result.encode("utf-8")
        new_pkt = DataPacket(id=packet.id, payload=data, source_format="morse",
                             size_bits=len(data)*8)
        new_pkt.add_step(self.name, "Morse", len(packet.payload), len(data), "encoded")
        return new_pkt


class HuffmanEncoderNode(NodeBase):
    """Huffman encoding with code table visualization."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "encoder", "🌳 HuffmanEnc", category="encoders")
        self.add_input("in", DataType.TEXT)
        self.add_output("out", DataType.HUFFMAN)
        self.last_codes = {}
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        data_str = packet.as_text
        coder = HuffmanCoder()
        encoded, metadata = coder.encode(data_str)
        self.last_codes = metadata.get("codes", {})
        
        result = json.dumps({"encoded": encoded, "codes": self.last_codes})
        data = result.encode("utf-8")
        encoded_len = len(encoded)
        original_bits = len(packet.payload) * 8
        ratio = original_bits / max(1, encoded_len)
        
        new_pkt = DataPacket(id=packet.id, payload=data, source_format="huffman",
                             size_bits=encoded_len)
        new_pkt.add_step(self.name, "Huffman", original_bits, encoded_len, f"ratio={ratio:.2f}")
        new_pkt.compression_ratio = ratio
        return new_pkt


class Base64EncoderNode(NodeBase):
    """Base64 encoding."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "encoder", "🔐 Base64", category="encoders")
        self.add_input("in", DataType.BINARY)
        self.add_output("out", DataType.BASE64)
        self.set_param("url_safe", False)
    
    def get_param_schema(self) -> dict:
        schema = super().get_param_schema()
        schema["url_safe"] = {
            "type": ParamType.BOOL, "label": "URL Safe", "default": False,
            "description": "Use URL-safe base64 variant",
            "category": "basic"
        }
        return schema
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        if self.get_param("url_safe"):
            encoded = base64.urlsafe_b64encode(packet.payload)
        else:
            encoded = base64.b64encode(packet.payload)
        new_pkt = DataPacket(id=packet.id, payload=encoded, source_format="base64",
                             size_bits=len(encoded)*8)
        new_pkt.add_step(self.name, "Base64", len(packet.payload), len(encoded), "encoded")
        return new_pkt


class HexEncoderNode(NodeBase):
    """Hex encoding."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "encoder", "🔢 Hex", category="encoders")
        self.add_input("in", DataType.BINARY)
        self.add_output("out", DataType.HEX)
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        encoded = packet.payload.hex().encode("ascii")
        new_pkt = DataPacket(id=packet.id, payload=encoded, source_format="hex",
                             size_bits=len(encoded)*8)
        new_pkt.add_step(self.name, "Hex", len(packet.payload), len(encoded), "encoded")
        return new_pkt


# ============================================================
# DECODERS
# ============================================================

class MorseDecoderNode(NodeBase):
    """Decode Morse code back to text."""
    
    REVERSE_MORSE = {v: k for k, v in MorseEncoderNode.MORSE.items()}
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "decoder", "📻 MorseDec", category="decoders")
        self.add_input("in", DataType.MORSE)
        self.add_output("out", DataType.TEXT)
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        text = packet.as_text
        result = ""
        for code in text.split(" "):
            result += self.REVERSE_MORSE.get(code, "?")
        data = result.encode("utf-8")
        new_pkt = DataPacket(id=packet.id, payload=data, source_format="text",
                             size_bits=len(data)*8)
        new_pkt.add_step(self.name, "MorseDec", len(packet.payload), len(data), "decoded")
        return new_pkt


class Utf8DecoderNode(NodeBase):
    """Decode UTF-8 bytes to text."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "decoder", "🔤 UTF-8Dec", category="decoders")
        self.add_input("in", DataType.BINARY)
        self.add_output("out", DataType.TEXT)
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        try:
            text = packet.payload.decode("utf-8")
            data = text.encode("utf-8")
            new_pkt = DataPacket(id=packet.id, payload=data, source_format="text",
                                 encoding="utf-8", size_bits=len(data)*8)
            new_pkt.add_step(self.name, "UTF-8Dec", len(packet.payload), len(data), "decoded")
            return new_pkt
        except UnicodeDecodeError as e:
            new_pkt = DataPacket(id=packet.id, payload=packet.payload,
                                 source_format="text", size_bits=len(packet.payload)*8)
            new_pkt.add_step(self.name, "UTF-8Dec", len(packet.payload), len(packet.payload),
                             f"ERROR: {e}")
            return new_pkt


class Base64DecoderNode(NodeBase):
    """Base64 decoding."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "decoder", "🔐 Base64Dec", category="decoders")
        self.add_input("in", DataType.BASE64)
        self.add_output("out", DataType.BINARY)
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        try:
            text = packet.as_text.strip()
            decoded = base64.b64decode(text)
            new_pkt = DataPacket(id=packet.id, payload=decoded, source_format="binary",
                                 size_bits=len(decoded)*8)
            new_pkt.add_step(self.name, "Base64Dec", len(packet.payload), len(decoded), "decoded")
            return new_pkt
        except Exception as e:
            new_pkt = DataPacket(id=packet.id, payload=packet.payload,
                                 size_bits=len(packet.payload)*8)
            new_pkt.add_step(self.name, "Base64Dec", len(packet.payload), len(packet.payload),
                             f"ERROR: {e}")
            return new_pkt


class HuffmanDecoderNode(NodeBase):
    """Huffman decoding."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "decoder", "🌳 HuffmanDec", category="decoders")
        self.add_input("in", DataType.HUFFMAN)
        self.add_output("out", DataType.TEXT)
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        try:
            data = json.loads(packet.as_text)
            encoded = data.get("encoded", "")
            codes = data.get("codes", {})
            
            # Reverse codes: code_str -> byte
            reverse = {v: chr(int(k)) if k.isdigit() else k for k, v in codes.items()}
            
            # Decode
            current = ""
            result = ""
            for bit in encoded:
                current += bit
                if current in reverse:
                    result += reverse[current]
                    current = ""
            
            data_bytes = result.encode("utf-8")
            new_pkt = DataPacket(id=packet.id, payload=data_bytes, source_format="text",
                                 size_bits=len(data_bytes)*8)
            new_pkt.add_step(self.name, "HuffmanDec", len(packet.payload), len(data_bytes), "decoded")
            return new_pkt
        except Exception as e:
            new_pkt = DataPacket(id=packet.id, payload=packet.payload,
                                 size_bits=len(packet.payload)*8)
            new_pkt.add_step(self.name, "HuffmanDec", len(packet.payload), len(packet.payload),
                             f"ERROR: {e}")
            return new_pkt