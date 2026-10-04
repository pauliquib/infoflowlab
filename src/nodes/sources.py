"""
Enhanced source nodes with param schemas and data types.
"""

import random
import uuid
from src.core.node_base import NodeBase, ParamType
from src.core.packet import DataPacket
from src.core.port import DataType
from src.algorithms.entropy import shannon_entropy


class TextSourceNode(NodeBase):
    """Text source with configurable text and encoding."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "source", "📝 Text", category="sources")
        self.add_output("out", DataType.TEXT)
        self.set_param("text", "Hello World! InfoFlowLab v1.0")
        self.set_param("encoding", "utf-8")
    
    def get_param_schema(self) -> dict:
        schema = super().get_param_schema()
        schema.update({
            "text": {
                "type": ParamType.TEXT, "label": "Source Text", "default": "Hello World!",
                "description": "Text data to send through the simulation",
                "category": "basic"
            },
            "encoding": {
                "type": ParamType.CHOICE, "label": "Encoding", "default": "utf-8",
                "choices": ["utf-8", "ascii", "utf-16", "iso-8859-2"],
                "description": "Character encoding",
                "category": "advanced"
            }
        })
        return schema
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        text = self.get_param("text", "Hello")
        encoding = self.get_param("encoding", "utf-8")
        data = text.encode(encoding)
        
        new_pkt = DataPacket(id=packet.id, payload=data,
                             source_format="text", encoding=encoding,
                             size_bits=len(data) * 8)
        new_pkt.entropy = shannon_entropy(data)
        new_pkt.add_step(self.name, "TextSource", 0, len(data),
                         f"text='{text[:30]}', H={new_pkt.entropy:.2f}")
        return new_pkt


class RandomSourceNode(NodeBase):
    """Random byte generator with configurable entropy."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "source", "🎲 Random", category="sources")
        self.add_output("out", DataType.BINARY)
        self.set_param("length", 100)
        self.set_param("entropy_target", 4.0)
        self.set_param("seed", 0)
    
    def get_param_schema(self) -> dict:
        schema = super().get_param_schema()
        schema.update({
            "length": {
                "type": ParamType.INT, "label": "Length", "default": 100,
                "min": 1, "max": 10000, "description": "Number of bytes to generate",
                "category": "basic"
            },
            "entropy_target": {
                "type": ParamType.FLOAT, "label": "Entropy Target", "default": 4.0,
                "min": 0.0, "max": 8.0, "step": 0.5,
                "description": "Target entropy in bits/byte (0=constant, 8=random)",
                "category": "basic"
            },
            "seed": {
                "type": ParamType.INT, "label": "Random Seed", "default": 0,
                "min": 0, "max": 999999, "description": "0 = no seed (random)",
                "category": "advanced"
            }
        })
        return schema
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        length = self.get_param("length", 100)
        target = self.get_param("entropy_target", 4.0)
        seed = self.get_param("seed", 0)
        
        if seed > 0:
            random.seed(seed)
        
        # Generate bytes with approximate entropy level
        if target >= 7.5:
            data = bytes(random.randint(0, 255) for _ in range(length))
        elif target >= 6.0:
            data = bytes(random.randint(32, 127) for _ in range(length))
        elif target >= 4.0:
            alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 "
            data = "".join(random.choice(alphabet) for _ in range(length)).encode("utf-8")
        elif target >= 2.0:
            alphabet = "ABCDEFGH"
            data = "".join(random.choice(alphabet) for _ in range(length)).encode("utf-8")
        else:
            alphabet = "AB"
            data = "".join(random.choice(alphabet) for _ in range(length)).encode("utf-8")
        
        new_pkt = DataPacket(id=packet.id, payload=data, source_format="binary",
                             size_bits=len(data)*8)
        new_pkt.entropy = shannon_entropy(data)
        new_pkt.add_step(self.name, "RandomSource", 0, len(data),
                         f"len={length}, H={new_pkt.entropy:.2f}")
        return new_pkt


class NumberInputNode(NodeBase):
    """Numeric input with base selection."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "source", "🔢 Číslo", category="sources")
        self.add_output("out", DataType.NUMERIC)
        self.set_param("value", "255")
        self.set_param("base", 10)
        self.set_param("label", "")
    
    def get_param_schema(self) -> dict:
        schema = super().get_param_schema()
        schema.update({
            "value": {
                "type": ParamType.STR, "label": "Value", "default": "255",
                "description": "Numeric value as string",
                "category": "basic"
            },
            "base": {
                "type": ParamType.INT, "label": "Base", "default": 10,
                "min": 2, "max": 36, "description": "Input number base",
                "category": "basic"
            },
            "label": {
                "type": ParamType.STR, "label": "Label", "default": "",
                "description": "Optional label for display",
                "category": "basic"
            }
        })
        return schema
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        val = self.get_param("value", "0")
        base = self.get_param("base", 10)
        data = f"{val}_{base}".encode("utf-8")
        new_pkt = DataPacket(id=packet.id, payload=data, source_format="number",
                             size_bits=len(data)*8)
        new_pkt.add_step(self.name, "NumberInput", 0, len(data), f"val={val}, base={base}")
        return new_pkt


class AudioSourceNode(NodeBase):
    """Audio source placeholder (for loading WAV files)."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "source", "🎵 AudioSrc", category="sources")
        self.add_output("out", DataType.AUDIO)
        self.set_param("file_path", "")
        self.set_param("sample_rate", 44100)
    
    def get_param_schema(self) -> dict:
        schema = super().get_param_schema()
        schema.update({
            "file_path": {
                "type": ParamType.STR, "label": "File Path", "default": "",
                "description": "Path to WAV/MP3 file",
                "category": "basic"
            },
            "sample_rate": {
                "type": ParamType.INT, "label": "Sample Rate", "default": 44100,
                "min": 8000, "max": 192000, "description": "Sampling rate in Hz",
                "category": "basic"
            }
        })
        return schema
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        # Generate test tone as placeholder
        import numpy as np
        duration = 0.1  # 100ms
        sr = self.get_param("sample_rate", 44100)
        t = np.linspace(0, duration, int(sr * duration))
        tone = np.sin(2 * np.pi * 440 * t) * 0.5
        audio_bytes = (tone * 127 + 128).astype(np.uint8).tobytes()
        
        new_pkt = DataPacket(id=packet.id, payload=audio_bytes, source_format="audio",
                             size_bits=len(audio_bytes)*8)
        new_pkt.add_step(self.name, "AudioSource", 0, len(audio_bytes),
                         f"440Hz tone, {sr}Hz")
        return new_pkt


class ImageSourceNode(NodeBase):
    """Image source - loads images from PC."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "source", "🖼️ Obrázek", category="sources")
        self.add_output("out", DataType.IMAGE)
        self.set_param("file_path", "")
        self._last_image_data = None
    
    def get_param_schema(self) -> dict:
        schema = super().get_param_schema()
        schema.update({
            "file_path": {
                "type": ParamType.FILE, "label": "Soubor obrázku", "default": "",
                "description": "Cesta k souboru obrázku (PNG, JPG, BMP, GIF, atd.)",
                "category": "basic"
            }
        })
        return schema
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        file_path = self.get_param("file_path", "")
        
        if not file_path:
            # No file selected - return empty packet
            new_pkt = DataPacket(id=packet.id, payload=b"", source_format="image",
                                 size_bits=0)
            new_pkt.add_step(self.name, "ImageSource", 0, 0, "No file selected")
            return new_pkt
        
        try:
            from PIL import Image
            import io
            
            # Load image using Pillow
            img = Image.open(file_path)
            
            # Convert to RGB if necessary (handle RGBA, grayscale, etc.)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save to bytes in PNG format
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            image_bytes = buffer.getvalue()
            
            # Store metadata
            self._last_image_data = {
                'width': img.width,
                'height': img.height,
                'mode': img.mode,
                'format': img.format
            }
            
            new_pkt = DataPacket(id=packet.id, payload=image_bytes, 
                                 source_format="image",
                                 size_bits=len(image_bytes)*8)
            new_pkt.add_step(self.name, "ImageSource", 0, len(image_bytes),
                           f"{img.width}x{img.height} {img.mode}")
            return new_pkt
            
        except Exception as e:
            # Error loading image
            error_msg = f"Error: {str(e)}"
            new_pkt = DataPacket(id=packet.id, payload=b"", source_format="image",
                                 size_bits=0)
            new_pkt.add_step(self.name, "ImageSource", 0, 0, error_msg)
            return new_pkt
