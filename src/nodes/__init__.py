"""
Simulation nodes - complete catalog for v1.0.
"""

from .sources import TextSourceNode, RandomSourceNode, NumberInputNode, AudioSourceNode, ImageSourceNode
from .encoders import (
    BaseConverterNode, Utf8EncoderNode, MorseEncoderNode, HuffmanEncoderNode,
    Base64EncoderNode, HexEncoderNode,
    MorseDecoderNode, Utf8DecoderNode, Base64DecoderNode, HuffmanDecoderNode
)
from .channels import BSKChannelNode, IdealChannelNode, GilbertElliottChannelNode, AWGNChannelNode
from .compressors import RLECompressorNode, HuffmanCompressorNode, LZ77CompressorNode, LZWCompressorNode
from .ecc import (
    Hamming74Node, Hamming1511Node, CRC8Node, CRC16Node, CRC32Node,
    ReedSolomonEncoderNode, ReedSolomonDecoderNode,
    ParityEncoderNode, ParityDecoderNode
)
from .analyzers import EntropyMeterNode, HistogramNode, CompressionRatioNode, BERMeterNode, LatencyMeterNode
from .sinks import TextOutputNode, FileSinkNode, ConsoleSinkNode, HexDumpSinkNode, ComparisonSinkNode, ImageOutputNode
from .image_nodes import ImageBlockLossNode, ImageTransformNode, ImageComparatorNode
from .checksums import (
    EANValidator, ISBNValidator, ISSNValidator,
    LuhnValidator, VerhoeffValidator, ICOValidator, RCCalculator
)

__all__ = [
    # Sources
    "TextSourceNode", "RandomSourceNode", "NumberInputNode", "AudioSourceNode", "ImageSourceNode",
    # Encoders
    "BaseConverterNode", "Utf8EncoderNode", "MorseEncoderNode", "HuffmanEncoderNode",
    "Base64EncoderNode", "HexEncoderNode",
    # Decoders
    "MorseDecoderNode", "Utf8DecoderNode", "Base64DecoderNode", "HuffmanDecoderNode",
    # Channels
    "BSKChannelNode", "IdealChannelNode", "GilbertElliottChannelNode", "AWGNChannelNode",
    # Compressors
    "RLECompressorNode", "HuffmanCompressorNode", "LZ77CompressorNode", "LZWCompressorNode",
    # ECC
    "Hamming74Node", "Hamming1511Node", "CRC8Node", "CRC16Node", "CRC32Node",
    "ReedSolomonEncoderNode", "ReedSolomonDecoderNode",
    "ParityEncoderNode", "ParityDecoderNode",
    # Analyzers
    "EntropyMeterNode", "HistogramNode", "CompressionRatioNode", "BERMeterNode", "LatencyMeterNode",
    # Sinks
    "TextOutputNode", "FileSinkNode", "ConsoleSinkNode", "HexDumpSinkNode", "ComparisonSinkNode", "ImageOutputNode",
    # Image processing
    "ImageBlockLossNode", "ImageTransformNode", "ImageComparatorNode",
    # Checksums
    "EANValidator", "ISBNValidator", "ISSNValidator",
    "LuhnValidator", "VerhoeffValidator", "ICOValidator", "RCCalculator",
]