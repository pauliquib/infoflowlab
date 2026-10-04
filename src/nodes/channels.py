"""
Channel nodes - communication channel models with noise simulation.
"""

import random
import math
from src.core.node_base import NodeBase, ParamType
from src.core.packet import DataPacket
from src.core.port import DataType


class IdealChannelNode(NodeBase):
    """Ideal channel with configurable latency."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "channel", "🔌 Ideal", category="channels")
        self.add_input("in", DataType.ANY)
        self.add_output("out", DataType.ANY)
        self.set_param("latency_ms", 10)
    
    def get_param_schema(self) -> dict:
        schema = super().get_param_schema()
        schema["latency_ms"] = {
            "type": ParamType.INT, "label": "Latency", "default": 10,
            "min": 0, "max": 10000,
            "description": "Channel latency in milliseconds",
            "unit": "ms", "category": "basic"
        }
        return schema
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        latency = self.get_param("latency_ms", 0)
        packet.record_latency(latency)
        packet.add_step(self.name, "IdealChannel", len(packet.payload), len(packet.payload),
                        f"latency={latency}ms")
        return packet


class BSKChannelNode(NodeBase):
    """Binary Symmetric Channel with configurable error probability."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "channel", "📡 BSK", category="channels")
        self.add_input("in", DataType.ANY)
        self.add_output("out", DataType.ANY)
        self.set_param("error_prob", 0.05)
        self.set_param("latency_ms", 5)
        self.total_bits = 0
        self.error_bits = 0
    
    def get_param_schema(self) -> dict:
        schema = super().get_param_schema()
        schema.update({
            "error_prob": {
                "type": ParamType.FLOAT, "label": "Error Prob", "default": 0.05,
                "min": 0.0, "max": 1.0, "step": 0.01,
                "description": "Bit error probability (0-1)",
                "category": "basic"
            },
            "latency_ms": {
                "type": ParamType.INT, "label": "Latency", "default": 5,
                "min": 0, "max": 10000,
                "description": "Channel latency in ms",
                "unit": "ms", "category": "basic"
            }
        })
        return schema
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        prob = self.get_param("error_prob", 0.05)
        latency = self.get_param("latency_ms", 5)
        
        bits = list(packet.payload)
        noisy = bytearray()
        error_bitmask = 0
        bit_pos = 0
        
        for b in bits:
            if random.random() < prob:
                error_byte = b ^ random.randint(1, 255)
                noisy.append(error_byte)
                error_bitmask |= (1 << (bit_pos % 64)) if bit_pos < 64 else 0
                self.error_bits += 1
            else:
                noisy.append(b)
            self.total_bits += 1
            bit_pos += 8
        
        noisy_data = bytes(noisy)
        new_pkt = DataPacket(id=packet.id, payload=noisy_data,
                             source_format=packet.source_format,
                             size_bits=len(noisy_data)*8)
        
        if error_bitmask:
            new_pkt.add_error("BSC", f"Bit errors with p={prob}", error_bitmask)
        
        new_pkt.record_latency(latency)
        ber = self.error_bits / max(1, self.total_bits)
        new_pkt.add_step(self.name, "BSK", len(bits), len(noisy_data),
                         f"errors={bin(error_bitmask).count('1')}, p={prob}, BER={ber:.4f}")
        return new_pkt


class GilbertElliottChannelNode(NodeBase):
    """Gilbert-Elliott burst error channel model."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "channel", "📡 Gilbert-Elliott", category="channels")
        self.add_input("in", DataType.ANY)
        self.add_output("out", DataType.ANY)
        self.set_param("p_good", 0.05)
        self.set_param("p_bad", 0.3)
        self.set_param("k_burst", 3)
        self._state = "good"
    
    def get_param_schema(self) -> dict:
        schema = super().get_param_schema()
        schema.update({
            "p_good": {
                "type": ParamType.FLOAT, "label": "P(good)", "default": 0.05,
                "min": 0.0, "max": 1.0, "step": 0.01,
                "description": "Error probability in good state",
                "category": "basic"
            },
            "p_bad": {
                "type": ParamType.FLOAT, "label": "P(bad)", "default": 0.3,
                "min": 0.0, "max": 1.0, "step": 0.01,
                "description": "Error probability in bad state",
                "category": "basic"
            },
            "k_burst": {
                "type": ParamType.INT, "label": "Burst Length", "default": 3,
                "min": 1, "max": 100,
                "description": "Average burst length in bytes",
                "category": "basic"
            }
        })
        return schema
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        p_good = self.get_param("p_good", 0.05)
        p_bad = self.get_param("p_bad", 0.3)
        k_burst = self.get_param("k_burst", 3)
        
        bits = list(packet.payload)
        noisy = bytearray()
        errors = 0
        
        i = 0
        while i < len(bits):
            if self._state == "good":
                if random.random() < p_good:
                    noisy.append(bits[i] ^ random.randint(1, 255))
                    errors += 1
                else:
                    noisy.append(bits[i])
                # Transition to bad state
                if random.random() < 0.1:
                    self._state = "bad"
            else:
                # Burst errors
                burst_len = random.randint(1, k_burst)
                for _ in range(burst_len):
                    if i < len(bits):
                        if random.random() < p_bad:
                            noisy.append(bits[i] ^ random.randint(1, 255))
                            errors += 1
                        else:
                            noisy.append(bits[i])
                        i += 1
                self._state = "good" if random.random() < 0.3 else "bad"
                continue
            i += 1
        
        new_pkt = DataPacket(id=packet.id, payload=bytes(noisy),
                             source_format=packet.source_format,
                             size_bits=len(noisy)*8)
        if errors > 0:
            new_pkt.add_error("GilbertElliott", f"Burst errors in state={self._state}", errors)
        new_pkt.add_step(self.name, "GilbertElliott", len(bits), len(noisy),
                         f"errors={errors}, state={self._state}")
        return new_pkt


class AWGNChannelNode(NodeBase):
    """Additive White Gaussian Noise channel."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "channel", "📡 AWGN", category="channels")
        self.add_input("in", DataType.ANY)
        self.add_output("out", DataType.ANY)
        self.set_param("snr_db", 20.0)
    
    def get_param_schema(self) -> dict:
        schema = super().get_param_schema()
        schema["snr_db"] = {
            "type": ParamType.FLOAT, "label": "SNR (dB)", "default": 20.0,
            "min": -10, "max": 50, "step": 1,
            "description": "Signal-to-noise ratio in dB",
            "category": "basic"
        }
        return schema
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        snr = self.get_param("snr_db", 20.0)
        import numpy as np
        
        # Convert bytes to signal
        data = np.frombuffer(packet.payload, dtype=np.uint8).astype(np.float64)
        data = (data - 128) / 128.0  # Normalize to [-1, 1]
        
        # Add AWGN noise
        signal_power = np.mean(data ** 2)
        snr_linear = 10 ** (snr / 10.0)
        noise_power = signal_power / max(snr_linear, 1e-10)
        noise = np.sqrt(noise_power) * np.random.randn(len(data))
        noisy = data + noise
        
        # Denormalize and convert back to bytes
        noisy = np.clip(noisy * 128 + 128, 0, 255).astype(np.uint8)
        noisy_data = bytes(noisy)
        
        new_pkt = DataPacket(id=packet.id, payload=noisy_data,
                             source_format=packet.source_format,
                             size_bits=len(noisy_data)*8)
        new_pkt.add_step(self.name, "AWGN", len(packet.payload), len(noisy_data),
                         f"SNR={snr}dB")
        return new_pkt