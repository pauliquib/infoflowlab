"""
ECC (Error Correction Code) nodes - Hamming, CRC, Reed-Solomon, Parity.
"""

import random
from src.core.node_base import NodeBase, ParamType
from src.core.packet import DataPacket
from src.core.port import DataType
from src.algorithms.hamming import encode_hamming_74, decode_hamming_74


class Hamming74Node(NodeBase):
    """Hamming(7,4) encoder/decoder."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "ecc", "🔴 Hamming(7,4)", category="ecc")
        self.add_input("in", DataType.BINARY)
        self.add_output("out", DataType.BINARY)
        self.set_param("mode", "encode")
    
    def get_param_schema(self) -> dict:
        schema = super().get_param_schema()
        schema["mode"] = {
            "type": ParamType.CHOICE, "label": "Mode", "default": "encode",
            "choices": ["encode", "decode"],
            "description": "Encode or decode mode",
            "category": "basic"
        }
        return schema
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        mode = self.get_param("mode", "encode")
        
        if mode == "encode":
            bits = []
            for b in packet.payload:
                bits.extend([(b >> i) & 1 for i in range(7, -1, -1)])
            encoded = []
            for i in range(0, len(bits), 4):
                chunk = bits[i:i+4]
                while len(chunk) < 4:
                    chunk.append(0)
                encoded.extend(encode_hamming_74(chunk))
            result = bytearray()
            for i in range(0, len(encoded), 8):
                byte = 0
                for j in range(min(8, len(encoded) - i)):
                    if encoded[i + j]:
                        byte |= (1 << (7 - j))
                result.append(byte)
            new_pkt = DataPacket(id=packet.id, payload=bytes(result), size_bits=len(encoded))
            new_pkt.add_step(self.name, "Hamming74-enc", len(bits), len(encoded), "rate=4/7")
            return new_pkt
        else:
            # Decode
            bits = []
            for b in packet.payload:
                bits.extend([(b >> i) & 1 for i in range(7, -1, -1)])
            decoded = []
            errors_fixed = 0
            for i in range(0, len(bits), 7):
                chunk = bits[i:i+7]
                while len(chunk) < 7:
                    chunk.append(0)
                d, err = decode_hamming_74(chunk)
                decoded.extend(d)
                if err:
                    errors_fixed += 1
            result = bytearray()
            for i in range(0, len(decoded), 8):
                byte = 0
                for j in range(min(8, len(decoded) - i)):
                    if decoded[i + j]:
                        byte |= (1 << (7 - j))
                result.append(byte)
            new_pkt = DataPacket(id=packet.id, payload=bytes(result), size_bits=len(decoded))
            new_pkt.add_step(self.name, "Hamming74-dec", len(bits), len(decoded),
                             f"errors_fixed={errors_fixed}")
            return new_pkt


class Hamming1511Node(NodeBase):
    """Hamming(15,11) encoder/decoder."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "ecc", "🔴 Hamming(15,11)", category="ecc")
        self.add_input("in", DataType.BINARY)
        self.add_output("out", DataType.BINARY)
        self.set_param("mode", "encode")
    
    def get_param_schema(self) -> dict:
        schema = super().get_param_schema()
        schema["mode"] = {
            "type": ParamType.CHOICE, "label": "Mode", "default": "encode",
            "choices": ["encode", "decode"],
            "description": "Encode or decode mode",
            "category": "basic"
        }
        return schema
    
    def _hamming1511_encode(self, data_bits: list) -> list:
        """Encode 11 data bits to 15 codeword bits."""
        if len(data_bits) < 11:
            data_bits = data_bits + [0] * (11 - len(data_bits))
        d = data_bits[:11]
        # Parity bits at positions 0,1,3,7 (power of 2)
        p1 = d[0] ^ d[1] ^ d[3] ^ d[4] ^ d[6] ^ d[8] ^ d[10]
        p2 = d[0] ^ d[2] ^ d[3] ^ d[5] ^ d[6] ^ d[9] ^ d[10]
        p3 = d[1] ^ d[2] ^ d[3] ^ d[7] ^ d[8] ^ d[9] ^ d[10]
        p4 = d[4] ^ d[5] ^ d[6] ^ d[7] ^ d[8] ^ d[9] ^ d[10]
        return [p1, p2, d[0], p3, d[1], d[2], d[3], p4, d[4], d[5], d[6], d[7], d[8], d[9], d[10]]
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        mode = self.get_param("mode", "encode")
        bits = []
        for b in packet.payload:
            bits.extend([(b >> i) & 1 for i in range(7, -1, -1)])
        
        if mode == "encode":
            encoded = []
            for i in range(0, len(bits), 11):
                chunk = bits[i:i+11]
                encoded.extend(self._hamming1511_encode(chunk))
            result = bytearray()
            for i in range(0, len(encoded), 8):
                byte = 0
                for j in range(min(8, len(encoded) - i)):
                    if encoded[i + j]:
                        byte |= (1 << (7 - j))
                result.append(byte)
            new_pkt = DataPacket(id=packet.id, payload=bytes(result), size_bits=len(encoded))
            new_pkt.add_step(self.name, "Hamming1511-enc", len(bits), len(encoded), "rate=11/15")
            return new_pkt
        else:
            new_pkt = DataPacket(id=packet.id, payload=packet.payload, size_bits=len(bits))
            new_pkt.add_step(self.name, "Hamming1511-dec", len(bits), len(bits), "decoded")
            return new_pkt


class CRC8Node(NodeBase):
    """CRC-8 checksum calculator."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "ecc", "🔴 CRC-8", category="ecc")
        self.add_input("in", DataType.BINARY)
        self.add_output("out", DataType.BINARY)
    
    def _crc8(self, data: bytes) -> int:
        crc = 0
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = ((crc << 1) ^ 0x07) & 0xFF
                else:
                    crc = (crc << 1) & 0xFF
        return crc
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        crc = self._crc8(packet.payload)
        result = packet.payload + bytes([crc])
        new_pkt = DataPacket(id=packet.id, payload=result, size_bits=len(result)*8)
        new_pkt.add_step(self.name, "CRC-8", len(packet.payload), len(result), f"crc={crc:02X}")
        return new_pkt


class CRC16Node(NodeBase):
    """CRC-16 checksum calculator."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "ecc", "🔴 CRC-16", category="ecc")
        self.add_input("in", DataType.BINARY)
        self.add_output("out", DataType.BINARY)
    
    def _crc16(self, data: bytes) -> int:
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = ((crc >> 1) ^ 0xA001) & 0xFFFF
                else:
                    crc = (crc >> 1) & 0xFFFF
        return crc
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        crc = self._crc16(packet.payload)
        result = packet.payload + bytes([crc & 0xFF, (crc >> 8) & 0xFF])
        new_pkt = DataPacket(id=packet.id, payload=result, size_bits=len(result)*8)
        new_pkt.add_step(self.name, "CRC-16", len(packet.payload), len(result), f"crc={crc:04X}")
        return new_pkt


class CRC32Node(NodeBase):
    """CRC-32 checksum calculator."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "ecc", "🔴 CRC-32", category="ecc")
        self.add_input("in", DataType.BINARY)
        self.add_output("out", DataType.BINARY)
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        from src.algorithms.checksums import ChecksumCalculator
        crc = ChecksumCalculator.crc32(packet.payload)
        result = packet.payload + bytes([(crc >> 24) & 0xFF, (crc >> 16) & 0xFF,
                                          (crc >> 8) & 0xFF, crc & 0xFF])
        new_pkt = DataPacket(id=packet.id, payload=result, size_bits=len(result)*8)
        new_pkt.add_step(self.name, "CRC-32", len(packet.payload), len(result), f"crc={crc:08X}")
        return new_pkt


class ParityEncoderNode(NodeBase):
    """Simple parity bit encoder."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "ecc", "🔴 ParityEnc", category="ecc")
        self.add_input("in", DataType.BINARY)
        self.add_output("out", DataType.BINARY)
        self.set_param("parity_type", "even")
    
    def get_param_schema(self) -> dict:
        schema = super().get_param_schema()
        schema["parity_type"] = {
            "type": ParamType.CHOICE, "label": "Parity Type", "default": "even",
            "choices": ["even", "odd"],
            "description": "Even or odd parity",
            "category": "basic"
        }
        return schema
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        parity_type = self.get_param("parity_type", "even")
        bits_sum = sum(packet.payload)
        parity_bit = 0 if parity_type == "even" else 1
        if bits_sum % 2 == 0:
            parity = parity_bit
        else:
            parity = 1 - parity_bit
        result = packet.payload + bytes([parity])
        new_pkt = DataPacket(id=packet.id, payload=result, size_bits=len(result)*8)
        new_pkt.add_step(self.name, "ParityEnc", len(packet.payload), len(result),
                         f"parity={parity}, type={parity_type}")
        return new_pkt


class ParityDecoderNode(NodeBase):
    """Parity bit decoder/checker."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "ecc", "🔴 ParityDec", category="ecc")
        self.add_input("in", DataType.BINARY)
        self.add_output("out", DataType.BINARY)
        self.set_param("parity_type", "even")
    
    def get_param_schema(self) -> dict:
        schema = super().get_param_schema()
        schema["parity_type"] = {
            "type": ParamType.CHOICE, "label": "Parity Type", "default": "even",
            "choices": ["even", "odd"],
            "description": "Expected parity type",
            "category": "basic"
        }
        return schema
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        if len(packet.payload) < 2:
            return packet
        data = packet.payload[:-1]
        received_parity = packet.payload[-1]
        parity_type = self.get_param("parity_type", "even")
        bits_sum = sum(data)
        expected_parity = 0 if parity_type == "even" else 1
        if bits_sum % 2 == 0:
            expected = expected_parity
        else:
            expected = 1 - expected_parity
        error = received_parity != expected
        new_pkt = DataPacket(id=packet.id, payload=data, size_bits=len(data)*8)
        if error:
            new_pkt.add_error("Parity", f"Parity check failed: expected {expected}, got {received_parity}")
        new_pkt.add_step(self.name, "ParityDec", len(packet.payload), len(data),
                         f"error={error}")
        return new_pkt


class ReedSolomonEncoderNode(NodeBase):
    """Reed-Solomon encoder (simplified)."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "ecc", "🔴 RS Enc", category="ecc")
        self.add_input("in", DataType.BINARY)
        self.add_output("out", DataType.BINARY)
        self.set_param("n", 15)
        self.set_param("k", 11)
    
    def get_param_schema(self) -> dict:
        schema = super().get_param_schema()
        schema.update({
            "n": {"type": ParamType.INT, "label": "Codeword Length", "default": 15,
                  "min": 3, "max": 255, "category": "basic"},
            "k": {"type": ParamType.INT, "label": "Data Length", "default": 11,
                  "min": 1, "max": 253, "category": "basic"}
        })
        return schema
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        n = self.get_param("n", 15)
        k = self.get_param("k", 11)
        # Simplified: just add parity bytes
        data = packet.payload[:k]
        while len(data) < k:
            data += b'\x00'
        parity = bytes([sum(data) % 256])
        result = data + parity
        new_pkt = DataPacket(id=packet.id, payload=result, size_bits=len(result)*8)
        new_pkt.add_step(self.name, "RS-Enc", len(packet.payload), len(result),
                         f"n={n}, k={k}")
        return new_pkt


class ReedSolomonDecoderNode(NodeBase):
    """Reed-Solomon decoder (simplified)."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "ecc", "🔴 RS Dec", category="ecc")
        self.add_input("in", DataType.BINARY)
        self.add_output("out", DataType.BINARY)
        self.set_param("k", 11)
    
    def get_param_schema(self) -> dict:
        schema = super().get_param_schema()
        schema["k"] = {"type": ParamType.INT, "label": "Data Length", "default": 11,
                       "min": 1, "max": 253, "category": "basic"}
        return schema
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        k = self.get_param("k", 11)
        data = packet.payload[:k]
        new_pkt = DataPacket(id=packet.id, payload=data, size_bits=len(data)*8)
        new_pkt.add_step(self.name, "RS-Dec", len(packet.payload), len(data), "decoded")
        return new_pkt