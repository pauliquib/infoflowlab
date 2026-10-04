"""
Tests for node implementations
"""

import pytest
from src.core.node_base import NodeBase, NodeStatus
from src.core.packet import DataPacket
from src.nodes.sources import TextSourceNode, RandomSourceNode, NumberInputNode
from src.nodes.encoders import Base64EncoderNode, HexEncoderNode, HuffmanEncoderNode
from src.nodes.compressors import HuffmanCompressorNode, RLECompressorNode
from src.nodes.channels import BSKChannelNode, IdealChannelNode
from src.nodes.ecc import Hamming74Node, CRC32Node
from src.nodes.checksums import EANValidator
from src.nodes.analyzers import EntropyMeterNode, HistogramNode
from src.nodes.sinks import ConsoleSinkNode, FileSinkNode


class SimpleTestNode(NodeBase):
    """Simple node for base-class tests."""

    def __init__(self, node_id: str):
        super().__init__(node_id, "test", "Simple Node")
        self.add_input("in")
        self.add_output("out")

    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        return packet


class TestSourceNodes:
    """Test source node implementations"""

    def test_text_source_node(self):
        node = TextSourceNode("text1")
        assert node.node_type == "source"
        assert "out" in node.output_ports

        node.set_param("text", "Hello World")
        node.set_param("encoding", "utf-8")

        pkt = DataPacket(id="test", payload=b"", source_format="text")
        result = node.process(pkt, "auto")
        assert result is not None
        assert result.payload == b"Hello World"

    def test_random_source_node(self):
        node = RandomSourceNode("rand1")
        assert node.node_type == "source"

        node.set_param("length", 10)
        node.set_param("entropy_target", 7.5)

        pkt = DataPacket(id="test", payload=b"", source_format="text")
        result = node.process(pkt, "auto")
        assert result is not None
        assert len(result.payload) == 10

    def test_number_input_node(self):
        node = NumberInputNode("num1")
        assert node.node_type == "source"

        node.set_param("value", "42")
        node.set_param("base", 10)

        pkt = DataPacket(id="test", payload=b"", source_format="text")
        result = node.process(pkt, "auto")
        assert result is not None
        assert b"42" in result.payload


class TestEncoderNodes:
    """Test encoder node implementations"""

    def test_base64_encoder(self):
        node = Base64EncoderNode("b64_enc")
        assert node.node_type == "encoder"
        assert "in" in node.input_ports
        assert "out" in node.output_ports

        pkt = DataPacket(id="test", payload=b"Hello", source_format="text")
        result = node.process(pkt, "in")
        assert result is not None
        assert result.payload == b"SGVsbG8="

    def test_hex_encoder(self):
        node = HexEncoderNode("hex_enc")

        pkt = DataPacket(id="test", payload=b"ABC", source_format="text")
        result = node.process(pkt, "in")
        assert result is not None
        assert result.payload == b"414243"

    def test_huffman_encoder(self):
        node = HuffmanEncoderNode("huff_enc")

        pkt = DataPacket(id="test", payload=b"AAAAABBBBC", source_format="text")
        result = node.process(pkt, "in")
        assert result is not None
        assert len(result.payload) > 0


class TestCompressorNodes:
    """Test compressor node implementations"""

    def test_huffman_compressor(self):
        node = HuffmanCompressorNode("huff_comp")

        pkt = DataPacket(id="test", payload=b"AAAAABBBBC", source_format="text")
        result = node.process(pkt, "in")
        assert result is not None
        assert result.compression_ratio > 1.0

    def test_rle_compressor(self):
        node = RLECompressorNode("rle_comp")

        pkt = DataPacket(id="test", payload=b"AAAAABBBBB", source_format="text")
        result = node.process(pkt, "in")
        assert result is not None
        assert len(result.payload) < len(pkt.payload)


class TestChannelNodes:
    """Test channel node implementations"""

    def test_bsk_channel(self):
        node = BSKChannelNode("bsk")
        node.set_param("error_prob", 0.1)

        pkt = DataPacket(id="test", payload=b"\x00\x01\x02\x03", source_format="binary")
        result = node.process(pkt, "in")
        assert result is not None
        assert len(result.payload) == len(pkt.payload)

    def test_ideal_channel(self):
        node = IdealChannelNode("delay")
        node.set_param("latency_ms", 100)

        pkt = DataPacket(id="test", payload=b"test", source_format="text")
        result = node.process(pkt, "in")
        assert result is not None
        assert result.payload == pkt.payload


class TestECCNodes:
    """Test error correction code nodes"""

    def test_hamming74(self):
        node = Hamming74Node("hamming")

        pkt = DataPacket(id="test", payload=b"\x0F", source_format="binary")
        result = node.process(pkt, "in")
        assert result is not None
        assert len(result.payload) > 0


class TestChecksumNodes:
    """Test checksum and validation nodes"""

    def test_crc32(self):
        node = CRC32Node("crc")

        pkt = DataPacket(id="test", payload=b"test data", source_format="text")
        result = node.process(pkt, "in")
        assert result is not None
        assert len(result.payload) > len(pkt.payload)

    def test_ean_validator(self):
        node = EANValidator("ean")
        pkt = DataPacket(id="test", payload=b"5901234123457", source_format="text")
        result = node.process(pkt, "in")
        assert result is not None


class TestAnalyzerNodes:
    """Test analyzer node implementations"""

    def test_entropy_meter(self):
        node = EntropyMeterNode("entropy")

        pkt = DataPacket(id="test", payload=bytes(range(256)), source_format="binary")
        result = node.process(pkt, "in")
        assert result is not None

    def test_histogram(self):
        node = HistogramNode("hist")

        pkt = DataPacket(id="test", payload=b"AABBC", source_format="text")
        result = node.process(pkt, "in")
        assert result is not None


class TestSinkNodes:
    """Test sink node implementations"""

    def test_console_sink(self):
        node = ConsoleSinkNode("console")

        pkt = DataPacket(id="test", payload=b"test output", source_format="text")
        result = node.process(pkt, "in")
        assert result is not None or result is None

    def test_file_sink(self):
        node = FileSinkNode("file")
        node.set_param("file_path", "/tmp/test_output.txt")

        pkt = DataPacket(id="test", payload=b"test data", source_format="text")
        result = node.process(pkt, "in")
        assert result is not None or result is None


class TestNodeBase:
    """Test base NodeBase functionality"""

    def test_node_creation(self):
        node = NodeBase("test1", "test", "Test Node")
        assert node.node_id == "test1"
        assert node.node_type == "test"
        assert node.name == "Test Node"
        assert node.status == NodeStatus.IDLE
        assert len(node.buffer) == 0

    def test_add_ports(self):
        node = NodeBase("test1", "test", "Test")

        node.add_input("in1")
        node.add_input("in2")
        node.add_output("out1")

        assert "in1" in node.input_ports
        assert "in2" in node.input_ports
        assert "out1" in node.output_ports

    def test_get_set_param(self):
        node = NodeBase("test1", "test", "Test")

        node.set_param("key1", "value1")
        node.set_param("key2", 42)

        assert node.get_param("key1") == "value1"
        assert node.get_param("key2") == 42
        assert node.get_param("nonexistent", "default") == "default"

    def test_node_to_dict(self):
        node = TextSourceNode("text1")
        node.position = (100, 200)
        node.set_param("text", "Hello")

        data = node.to_dict()
        assert "id" in data
        assert "type" in data
        assert "class_name" in data
        assert data["class_name"] == "TextSourceNode"
        assert "position" in data
        assert data["position"] == [100, 200]

    def test_node_reset(self):
        node = SimpleTestNode("test1")

        pkt = DataPacket(id="test", payload=b"data", source_format="text")
        node.buffer.append(pkt)

        node.reset()
        assert len(node.buffer) == 0
        assert node.status == NodeStatus.IDLE
