"""
Central node registry – single source of truth for node type resolution.

Used by Canvas (add node), Graph (deserialize), MainWindow (load scenario),
and serialization utilities.
"""

from typing import Dict, Optional, Type

from src.core.node_base import NodeBase

from .sources import (
    TextSourceNode, RandomSourceNode, NumberInputNode,
    AudioSourceNode, ImageSourceNode,
)
from .encoders import (
    BaseConverterNode, Utf8EncoderNode, MorseEncoderNode, HuffmanEncoderNode,
    Base64EncoderNode, HexEncoderNode,
    MorseDecoderNode, Utf8DecoderNode, Base64DecoderNode, HuffmanDecoderNode,
)
from .channels import (
    BSKChannelNode, IdealChannelNode, GilbertElliottChannelNode, AWGNChannelNode,
)
from .compressors import (
    RLECompressorNode, HuffmanCompressorNode, LZ77CompressorNode, LZWCompressorNode,
)
from .ecc import (
    Hamming74Node, Hamming1511Node, CRC8Node, CRC16Node, CRC32Node,
    ReedSolomonEncoderNode, ReedSolomonDecoderNode,
    ParityEncoderNode, ParityDecoderNode,
)
from .analyzers import (
    EntropyMeterNode, HistogramNode, CompressionRatioNode,
    BERMeterNode, LatencyMeterNode,
)
from .sinks import (
    TextOutputNode, FileSinkNode, ConsoleSinkNode, HexDumpSinkNode,
    ComparisonSinkNode, ImageOutputNode,
)
from .image_nodes import ImageBlockLossNode, ImageTransformNode, ImageComparatorNode
from .checksums import (
    EANValidator, ISBNValidator, ISSNValidator,
    LuhnValidator, VerhoeffValidator, ICOValidator, RCCalculator,
)


# Sidebar / canvas display key -> node class
SIDEBAR_NODE_MAP: Dict[str, Type[NodeBase]] = {
    # Sources
    "Text": TextSourceNode,
    "Random": RandomSourceNode,
    "Číslo": NumberInputNode,
    "AudioSrc": AudioSourceNode,
    "ImageSrc": ImageSourceNode,
    # Encoders
    "Base64": Base64EncoderNode,
    "Hex": HexEncoderNode,
    "BaseConv": BaseConverterNode,
    "UTF-8": Utf8EncoderNode,
    "Morse": MorseEncoderNode,
    "HuffmanEnc": HuffmanEncoderNode,
    # Decoders
    "MorseDec": MorseDecoderNode,
    "UTF-8Dec": Utf8DecoderNode,
    "Base64Dec": Base64DecoderNode,
    "HuffmanDec": HuffmanDecoderNode,
    # Compressors
    "RLE": RLECompressorNode,
    "Huffman": HuffmanCompressorNode,
    "LZ77": LZ77CompressorNode,
    "LZW": LZWCompressorNode,
    # Channels
    "BSK": BSKChannelNode,
    "Ideal": IdealChannelNode,
    "GilbertElliott": GilbertElliottChannelNode,
    "AWGN": AWGNChannelNode,
    # ECC
    "Hamming74": Hamming74Node,
    "Hamming1511": Hamming1511Node,
    "CRC8": CRC8Node,
    "CRC16": CRC16Node,
    "CRC32": CRC32Node,
    "ReedSolomon": ReedSolomonEncoderNode,
    "ReedSolomonDec": ReedSolomonDecoderNode,
    "ParityEnc": ParityEncoderNode,
    "ParityDec": ParityDecoderNode,
    # Checksums
    "EAN": EANValidator,
    "ISBN": ISBNValidator,
    "ISSN": ISSNValidator,
    "Luhn": LuhnValidator,
    "Verhoeff": VerhoeffValidator,
    "ICO": ICOValidator,
    "RC": RCCalculator,
    # Analyzers
    "Entropie": EntropyMeterNode,
    "Frekvence": HistogramNode,
    "CompRatio": CompressionRatioNode,
    "BER Meter": BERMeterNode,
    "LatencyMeter": LatencyMeterNode,
    # Sinks
    "Soubor": FileSinkNode,
    "Konzole": ConsoleSinkNode,
    "HexDump": HexDumpSinkNode,
    "TextOut": TextOutputNode,
    "Compare": ComparisonSinkNode,
    "ImageOut": ImageOutputNode,
    # Image processing
    "BlockLoss": ImageBlockLossNode,
    "Transform": ImageTransformNode,
    "ImageCompare": ImageComparatorNode,
}

# Class name -> node class (for serialization)
CLASS_NAME_MAP: Dict[str, Type[NodeBase]] = {
    cls.__name__: cls for cls in SIDEBAR_NODE_MAP.values()
}

# Legacy factory keys (old save format) -> class
LEGACY_TYPE_MAP: Dict[str, Type[NodeBase]] = {
    "source": TextSourceNode,
    "random_source": RandomSourceNode,
    "number_source": NumberInputNode,
    "audio_source": AudioSourceNode,
    "image_source": ImageSourceNode,
    "encoder": Base64EncoderNode,
    "hex_encoder": HexEncoderNode,
    "base_converter": BaseConverterNode,
    "utf8_encoder": Utf8EncoderNode,
    "morse_encoder": MorseEncoderNode,
    "huffman_encoder": HuffmanEncoderNode,
    "huffman_decoder": HuffmanDecoderNode,
    "utf8_decoder": Utf8DecoderNode,
    "base64_decoder": Base64DecoderNode,
    "morse_decoder": MorseDecoderNode,
    "compressor": HuffmanCompressorNode,
    "rle_compressor": RLECompressorNode,
    "lz77_compressor": LZ77CompressorNode,
    "lzw_compressor": LZWCompressorNode,
    "channel": BSKChannelNode,
    "ideal_channel": IdealChannelNode,
    "gilbert_elliott": GilbertElliottChannelNode,
    "awgn_channel": AWGNChannelNode,
    "ecc": Hamming74Node,
    "hamming74": Hamming74Node,
    "hamming1511": Hamming1511Node,
    "crc8": CRC8Node,
    "crc16": CRC16Node,
    "crc32": CRC32Node,
    "reed_solomon_encoder": ReedSolomonEncoderNode,
    "reed_solomon_decoder": ReedSolomonDecoderNode,
    "parity_encoder": ParityEncoderNode,
    "parity_decoder": ParityDecoderNode,
    "ean": EANValidator,
    "isbn": ISBNValidator,
    "issn": ISSNValidator,
    "luhn": LuhnValidator,
    "verhoeff": VerhoeffValidator,
    "ico": ICOValidator,
    "analyzer": EntropyMeterNode,
    "histogram": HistogramNode,
    "compression_ratio": CompressionRatioNode,
    "ber_meter": BERMeterNode,
    "latency_meter": LatencyMeterNode,
    "sink": TextOutputNode,
    "file_sink": FileSinkNode,
    "console_sink": ConsoleSinkNode,
    "hexdump_sink": HexDumpSinkNode,
    "comparison_sink": ComparisonSinkNode,
    "image_output": ImageOutputNode,
    "image_block_loss": ImageBlockLossNode,
    "image_transform": ImageTransformNode,
    "image_comparator": ImageComparatorNode,
}

# Resolve ambiguous legacy types using node display name substrings
_LEGACY_NAME_HINTS: Dict[str, list] = {
    "source": [
        ("Obrázek", ImageSourceNode),
        ("Image", ImageSourceNode),
        ("Audio", AudioSourceNode),
        ("Zvuk", AudioSourceNode),
        ("Random", RandomSourceNode),
        ("Náhod", RandomSourceNode),
        ("Číslo", NumberInputNode),
        ("Number", NumberInputNode),
        ("Text", TextSourceNode),
    ],
    "channel": [
        ("Gilbert", GilbertElliottChannelNode),
        ("AWGN", AWGNChannelNode),
        ("Ideal", IdealChannelNode),
        ("BSK", BSKChannelNode),
    ],
    "ecc": [
        ("RS Enc", ReedSolomonEncoderNode),
        ("RS Dec", ReedSolomonDecoderNode),
        ("Reed", ReedSolomonEncoderNode),
        ("Hamming(15", Hamming1511Node),
        ("Hamming", Hamming74Node),
        ("CRC-8", CRC8Node),
        ("CRC8", CRC8Node),
        ("CRC-16", CRC16Node),
        ("CRC16", CRC16Node),
        ("CRC-32", CRC32Node),
        ("CRC32", CRC32Node),
        ("Parity Enc", ParityEncoderNode),
        ("Parity Dec", ParityDecoderNode),
    ],
    "encoder": [
        ("Hex", HexEncoderNode),
        ("Base64", Base64EncoderNode),
        ("UTF-8", Utf8EncoderNode),
        ("Morse", MorseEncoderNode),
        ("Huffman", HuffmanEncoderNode),
        ("BaseConv", BaseConverterNode),
        ("Base", BaseConverterNode),
    ],
    "compressor": [
        ("RLE", RLECompressorNode),
        ("LZ77", LZ77CompressorNode),
        ("LZW", LZWCompressorNode),
        ("Huffman", HuffmanCompressorNode),
    ],
    "analyzer": [
        ("Entropie", EntropyMeterNode),
        ("Entropy", EntropyMeterNode),
        ("Frekvence", HistogramNode),
        ("Histogram", HistogramNode),
        ("CompRatio", CompressionRatioNode),
        ("BER", BERMeterNode),
        ("Latency", LatencyMeterNode),
    ],
    "checksums": [
        ("EAN", EANValidator),
        ("ISBN", ISBNValidator),
        ("ISSN", ISSNValidator),
        ("Luhn", LuhnValidator),
        ("Verhoeff", VerhoeffValidator),
        ("ICO", ICOValidator),
        ("IČO", ICOValidator),
    ],
    "sink": [
        ("Soubor", FileSinkNode),
        ("File", FileSinkNode),
        ("Konzole", ConsoleSinkNode),
        ("Console", ConsoleSinkNode),
        ("HexDump", HexDumpSinkNode),
        ("Compare", ComparisonSinkNode),
        ("ImageOut", ImageOutputNode),
        ("Obrázek", ImageOutputNode),
    ],
}


def get_sidebar_key(node_class: Type[NodeBase]) -> Optional[str]:
    """Return sidebar key for a node class, or None."""
    for key, cls in SIDEBAR_NODE_MAP.items():
        if cls is node_class:
            return key
    return None


def get_node_class(sidebar_key: str) -> Optional[Type[NodeBase]]:
    """Get node class from sidebar/canvas key."""
    return SIDEBAR_NODE_MAP.get(sidebar_key)


def build_node_factory() -> Dict[str, Type[NodeBase]]:
    """Build complete factory dict for Graph.from_dict()."""
    factory: Dict[str, Type[NodeBase]] = {}
    factory.update(CLASS_NAME_MAP)
    factory.update(SIDEBAR_NODE_MAP)
    factory.update(LEGACY_TYPE_MAP)
    return factory


def resolve_node_class(node_data: dict) -> Optional[Type[NodeBase]]:
    """
    Resolve node class from serialized node data.

    Resolution order:
    1. class_name field (new format)
    2. type_key field (sidebar key)
    3. type field (legacy generic type + name hints)
    """
    class_name = node_data.get("class_name")
    if class_name and class_name in CLASS_NAME_MAP:
        return CLASS_NAME_MAP[class_name]

    type_key = node_data.get("type_key")
    if type_key and type_key in SIDEBAR_NODE_MAP:
        return SIDEBAR_NODE_MAP[type_key]

    node_type = node_data.get("type", "")
    if node_type in SIDEBAR_NODE_MAP:
        return SIDEBAR_NODE_MAP[node_type]
    if node_type in CLASS_NAME_MAP:
        return CLASS_NAME_MAP[node_type]
    if node_type in LEGACY_TYPE_MAP:
        name = node_data.get("name", "")
        hints = _LEGACY_NAME_HINTS.get(node_type, [])
        for hint, cls in hints:
            if hint in name:
                return cls
        return LEGACY_TYPE_MAP[node_type]

    return None
