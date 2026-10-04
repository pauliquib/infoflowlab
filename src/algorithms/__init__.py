"""
Algorithm implementations - number systems, entropy, huffman, hamming, checksums,
compression, signal processing.
"""

from .number_systems import NumberConverter
from .entropy import (
    shannon_entropy,
    shannon_entropy_from_pmf,
    max_entropy,
    redundancy,
    efficiency,
    symbol_probabilities,
    information_content,
    joint_entropy,
    conditional_entropy,
    mutual_information,
    entropy_rate,
)
from .huffman import HuffmanCoder, huffman_encode, huffman_decode
from .hamming import HammingCode, encode_hamming_74, decode_hamming_74, apply_bsc_noise
from .checksums import ChecksumCalculator
from .compression import (
    CompressionResult,
    rle_compress, rle_decompress,
    lz77_compress, lz77_decompress,
    lzw_compress, lzw_decompress,
    lz78_compress, lz78_decompress,
    deflate_compress, deflate_decompress,
    analyze_compression,
)

try:
    from .signal_processing import (
        SampledSignal, Spectrum,
        sample_signal,
        quantize_signal,
        compute_fft,
        compute_waterfall,
        modulate_am, demodulate_am,
        modulate_fm, demodulate_fm,
        generate_test_signal,
    )
    _HAS_SIGNAL_PROCESSING = True
except ImportError:
    _HAS_SIGNAL_PROCESSING = False

__all__ = [
    "NumberConverter",
    "shannon_entropy", "shannon_entropy_from_pmf", "max_entropy",
    "redundancy", "efficiency", "symbol_probabilities", "information_content",
    "joint_entropy", "conditional_entropy", "mutual_information", "entropy_rate",
    "HuffmanCoder", "huffman_encode", "huffman_decode",
    "HammingCode", "encode_hamming_74", "decode_hamming_74", "apply_bsc_noise",
    "ChecksumCalculator",
    "CompressionResult",
    "rle_compress", "rle_decompress",
    "lz77_compress", "lz77_decompress",
    "lzw_compress", "lzw_decompress",
    "lz78_compress", "lz78_decompress",
    "deflate_compress", "deflate_decompress",
    "analyze_compression",
]

if _HAS_SIGNAL_PROCESSING:
    __all__.extend([
        "SampledSignal", "Spectrum",
        "sample_signal", "quantize_signal",
        "compute_fft", "compute_waterfall",
        "modulate_am", "demodulate_am",
        "modulate_fm", "demodulate_fm",
        "generate_test_signal",
    ])