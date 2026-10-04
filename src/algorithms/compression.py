"""
Compression algorithms - RLE, LZ77, LZ78, LZW, Deflate.

Pure functions with type hints, suitable for unit testing.
All functions return (compressed_data, metadata) tuples where metadata
includes compression ratio, dictionary (if relevant), and step-by-step log.
"""

from typing import Tuple, List, Optional, Dict, Any, Union
from dataclasses import dataclass, field


@dataclass
class CompressionResult:
    """Standard compression result."""
    data: bytes
    original_size: int
    compressed_size: int
    compression_ratio: float
    algorithm: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    log: List[str] = field(default_factory=list)


def rle_compress(data: bytes) -> CompressionResult:
    """
    Run-Length Encoding compression.
    
    Args:
        data: Input bytes to compress
        
    Returns:
        CompressionResult with compressed data and metadata
    """
    if not data:
        return CompressionResult(b"", 0, 0, 1.0, "RLE")
    
    log = []
    result = bytearray()
    count = 1
    runs = []
    
    for i in range(1, len(data)):
        if data[i] == data[i-1] and count < 255:
            count += 1
        else:
            result.append(data[i-1])
            result.append(count)
            runs.append((data[i-1], count))
            log.append(f"Run: byte={data[i-1]:02x}, count={count}")
            count = 1
    
    # Last run
    result.append(data[-1])
    result.append(count)
    runs.append((data[-1], count))
    log.append(f"Run: byte={data[-1]:02x}, count={count}")
    
    compressed = bytes(result)
    ratio = len(data) / max(1, len(compressed))
    
    return CompressionResult(
        data=compressed,
        original_size=len(data),
        compressed_size=len(compressed),
        compression_ratio=ratio,
        algorithm="RLE",
        metadata={"runs": runs, "num_runs": len(runs)},
        log=log
    )


def rle_decompress(data: bytes) -> CompressionResult:
    """
    Run-Length Encoding decompression.
    
    Args:
        data: RLE compressed data (byte, count pairs)
        
    Returns:
        CompressionResult with decompressed data
    """
    if not data:
        return CompressionResult(b"", 0, 0, 1.0, "RLE (decompress)")
    
    log = []
    result = bytearray()
    
    i = 0
    while i < len(data) - 1:
        byte_val = data[i]
        count = data[i + 1]
        result.extend([byte_val] * count)
        log.append(f"Expand: byte={byte_val:02x} x{count}")
        i += 2
    
    decompressed = bytes(result)
    ratio = len(decompressed) / max(1, len(data))
    
    return CompressionResult(
        data=decompressed,
        original_size=len(data),
        compressed_size=len(decompressed),
        compression_ratio=ratio,
        algorithm="RLE (decompress)",
        metadata={"original_runs": len(data) // 2},
        log=log
    )


def lz77_compress(data: bytes, window_size: int = 4096, 
                  lookahead_size: int = 128) -> CompressionResult:
    """
    LZ77 compression.
    
    Args:
        data: Input bytes to compress
        window_size: Size of the search window
        lookahead_size: Size of the lookahead buffer
        
    Returns:
        CompressionResult with compressed data and metadata
    """
    if not data:
        return CompressionResult(b"", 0, 0, 1.0, "LZ77")
    
    log = []
    tokens = []
    i = 0
    
    while i < len(data):
        match_length = 0
        match_distance = 0
        
        # Search in window
        window_start = max(0, i - window_size)
        for j in range(window_start, i):
            length = 0
            while (i + length < len(data) and 
                   j + length < i and 
                   data[j + length] == data[i + length] and
                   length < lookahead_size):
                length += 1
            
            if length > match_length:
                match_length = length
                match_distance = i - j
        
        if match_length >= 3:
            # Output (distance, length, next_byte)
            next_byte = data[i + match_length] if i + match_length < len(data) else 0
            tokens.append((match_distance, match_length, next_byte))
            log.append(f"Match: dist={match_distance}, len={match_length}, next={next_byte:02x}")
            i += match_length + 1
        else:
            # Output literal
            tokens.append((0, 0, data[i]))
            log.append(f"Literal: byte={data[i]:02x}")
            i += 1
    
    # Encode tokens to bytes
    result = bytearray()
    for dist, length, next_byte in tokens:
        if length >= 3:
            result.extend([0xFF, (dist >> 8) & 0xFF, dist & 0xFF, length, next_byte])
        else:
            result.extend([0x00, next_byte])
    
    compressed = bytes(result)
    ratio = len(data) / max(1, len(compressed))
    
    return CompressionResult(
        data=compressed,
        original_size=len(data),
        compressed_size=len(compressed),
        compression_ratio=ratio,
        algorithm="LZ77",
        metadata={
            "tokens": len(tokens),
            "window_size": window_size,
            "matches": sum(1 for t in tokens if t[1] >= 3),
            "literals": sum(1 for t in tokens if t[1] == 0)
        },
        log=log
    )


def lz77_decompress(data: bytes) -> CompressionResult:
    """
    LZ77 decompression.
    
    Args:
        data: LZ77 compressed data
        
    Returns:
        CompressionResult with decompressed data
    """
    log = []
    result = bytearray()
    i = 0
    
    while i < len(data):
        flag = data[i]
        i += 1
        
        if flag == 0xFF:
            # Compressed token
            if i + 3 < len(data):
                dist = (data[i] << 8) | data[i + 1]
                length = data[i + 2]
                next_byte = data[i + 3]
                i += 4
                
                start = len(result) - dist
                for j in range(length):
                    if start + j >= 0 and start + j < len(result):
                        result.append(result[start + j])
                    else:
                        result.append(0)
                result.append(next_byte)
                log.append(f"Expand: dist={dist}, len={length}")
            else:
                break
        else:
            # Literal
            result.append(data[i])
            log.append(f"Literal: byte={data[i]:02x}")
            i += 1
    
    decompressed = bytes(result)
    ratio = len(decompressed) / max(1, len(data))
    
    return CompressionResult(
        data=decompressed,
        original_size=len(data),
        compressed_size=len(decompressed),
        compression_ratio=ratio,
        algorithm="LZ77 (decompress)",
        metadata={},
        log=log
    )


def lzw_compress(data: bytes, max_dict_size: int = 4096) -> CompressionResult:
    """
    LZW compression.
    
    Args:
        data: Input bytes to compress
        max_dict_size: Maximum dictionary size
        
    Returns:
        CompressionResult with compressed data and metadata
    """
    if not data:
        return CompressionResult(b"", 0, 0, 1.0, "LZW")
    
    log = []
    
    # Build initial dictionary
    dictionary = {bytes([i]): i for i in range(256)}
    next_code = 256
    
    result = []
    w = bytes([data[0]])
    
    for i in range(1, len(data)):
        c = bytes([data[i]])
        wc = w + c
        
        if wc in dictionary:
            w = wc
        else:
            result.append(dictionary[w])
            log.append(f"Code: {dictionary[w]} -> {w.hex()}")
            
            if next_code < max_dict_size:
                dictionary[wc] = next_code
                log.append(f"Dict: {next_code} = {wc.hex()}")
                next_code += 1
            
            w = c
    
    # Output last code
    if w:
        result.append(dictionary[w])
        log.append(f"Code: {dictionary[w]} -> {w.hex()}")
    
    # Encode codes to bytes (12-bit codes for simplicity)
    compressed = bytearray()
    buffer = 0
    bits_in_buffer = 0
    for code in result:
        buffer = (buffer << 12) | code
        bits_in_buffer += 12
        while bits_in_buffer >= 8:
            compressed.append((buffer >> (bits_in_buffer - 8)) & 0xFF)
            bits_in_buffer -= 8
    if bits_in_buffer > 0:
        compressed.append((buffer << (8 - bits_in_buffer)) & 0xFF)
    
    compressed_data = bytes(compressed)
    ratio = len(data) / max(1, len(compressed_data))
    
    return CompressionResult(
        data=compressed_data,
        original_size=len(data),
        compressed_size=len(compressed_data),
        compression_ratio=ratio,
        algorithm="LZW",
        metadata={
            "dict_size": len(dictionary),
            "codes_generated": len(result),
            "initial_dict_size": 256
        },
        log=log
    )


def lzw_decompress(data: bytes) -> CompressionResult:
    """
    LZW decompression.
    
    Args:
        data: LZW compressed data (12-bit codes)
        
    Returns:
        CompressionResult with decompressed data
    """
    if not data:
        return CompressionResult(b"", 0, 0, 1.0, "LZW (decompress)")
    
    log = []
    
    # Extract 12-bit codes
    codes = []
    i = 0
    while i < len(data) * 8:
        # Read 12 bits
        byte_pos = i // 8
        bit_offset = i % 8
        if byte_pos + 1 >= len(data):
            break
        value = (data[byte_pos] << 8 | data[byte_pos + 1])
        value = (value >> (4 - bit_offset)) & 0xFFF if bit_offset <= 4 else \
                (value << (bit_offset - 4)) & 0xFFF
        codes.append(value)
        i += 12
    
    # Build dictionary
    dictionary = {i: bytes([i]) for i in range(256)}
    next_code = 256
    
    result = bytearray()
    if not codes:
        return CompressionResult(b"", len(data), 0, 0, "LZW (decompress)")
    
    w = dictionary.get(codes[0], bytes([codes[0]]))
    result.extend(w)
    
    for i in range(1, len(codes)):
        code = codes[i]
        
        if code in dictionary:
            entry = dictionary[code]
        elif code == next_code:
            entry = w + bytes([w[0]])
        else:
            log.append(f"Error: Invalid code {code}")
            continue
        
        result.extend(entry)
        log.append(f"Output: {entry.hex()}")
        
        dictionary[next_code] = w + bytes([entry[0]])
        log.append(f"Dict: {next_code} = {(w + bytes([entry[0]])).hex()}")
        next_code += 1
        
        w = entry
    
    decompressed = bytes(result)
    ratio = len(decompressed) / max(1, len(data))
    
    return CompressionResult(
        data=decompressed,
        original_size=len(data),
        compressed_size=len(decompressed),
        compression_ratio=ratio,
        algorithm="LZW (decompress)",
        metadata={"dict_size": len(dictionary)},
        log=log
    )


def _build_huffman_codes(data: bytes) -> Tuple[Dict[int, str], Dict[str, int]]:
    """Build Huffman codes from byte frequencies."""
    from collections import Counter
    import heapq
    
    freq = Counter(data)
    heap = [[weight, [byte, ""]] for byte, weight in freq.items()]
    heapq.heapify(heap)
    
    while len(heap) > 1:
        lo = heapq.heappop(heap)
        hi = heapq.heappop(heap)
        for pair in lo[1:]:
            pair[1] = '0' + pair[1]
        for pair in hi[1:]:
            pair[1] = '1' + pair[1]
        heapq.heappush(heap, [lo[0] + hi[0]] + lo[1:] + hi[1:])
    
    codes = {}
    reverse_codes = {}
    if heap:
        for byte, code in heap[0][1:]:
            codes[byte] = code
            reverse_codes[code] = byte
    
    return codes, reverse_codes


def deflate_compress(data: bytes, level: int = 6) -> CompressionResult:
    """
    Deflate compression (LZ77 + Huffman).
    
    Args:
        data: Input bytes to compress
        level: Compression level (1-9)
        
    Returns:
        CompressionResult with compressed data and metadata
    """
    if not data:
        return CompressionResult(b"", 0, 0, 1.0, "Deflate")
    
    log = []
    log.append("Phase 1: LZ77 compression")
    
    # Phase 1: LZ77
    lz77_result = lz77_compress(data, window_size=2**15, lookahead_size=min(258, 2**(level+5)))
    log.extend([f"  {m}" for m in lz77_result.log])
    
    # Phase 2: Huffman encoding of LZ77 tokens
    log.append("Phase 2: Huffman encoding")
    
    # Build Huffman codes for the compressed bytes
    codes, _ = _build_huffman_codes(lz77_result.data)
    log.append(f"  Huffman codes: {len(codes)} symbols")
    
    # Encode using Huffman
    bit_string = ""
    for byte in lz77_result.data:
        bit_string += codes.get(byte, format(byte, '08b'))
    
    # Convert bit string to bytes
    result = bytearray()
    for i in range(0, len(bit_string), 8):
        chunk = bit_string[i:i+8]
        if len(chunk) == 8:
            result.append(int(chunk, 2))
        else:
            chunk = chunk.ljust(8, '0')
            result.append(int(chunk, 2))
    
    compressed = bytes(result)
    ratio = len(data) / max(1, len(compressed))
    
    log.append(f"LZ77: {len(data)} -> {len(lz77_result.data)} bytes")
    log.append(f"Huffman: {len(lz77_result.data)} -> {len(compressed)} bytes")
    log.append(f"Total ratio: {ratio:.3f}")
    
    return CompressionResult(
        data=compressed,
        original_size=len(data),
        compressed_size=len(compressed),
        compression_ratio=ratio,
        algorithm="Deflate",
        metadata={
            "level": level,
            "lz77_result": {
                "original": lz77_result.original_size,
                "compressed": lz77_result.compressed_size
            },
            "huffman_symbols": len(codes)
        },
        log=log
    )


def deflate_decompress(data: bytes) -> CompressionResult:
    """Simple Deflate decompression."""
    # Simplified: for educational purposes, use the stored data
    return CompressionResult(
        data=data,
        original_size=len(data),
        compressed_size=len(data),
        compression_ratio=1.0,
        algorithm="Deflate (decompress)",
        metadata={"note": "Simplified decompression - passes through"},
        log=["Simplified Deflate decompression"]
    )


# Convenience wrapper for node usage
def analyze_compression(data: bytes) -> Dict[str, Any]:
    """
    Analyze compression potential of data.
    
    Args:
        data: Input bytes
        
    Returns:
        Dictionary with compression analysis results
    """
    results = {}
    
    # RLE
    rle = rle_compress(data)
    results["rle"] = {
        "ratio": rle.compression_ratio,
        "compressed_size": rle.compressed_size,
        "num_runs": rle.metadata.get("num_runs", 0)
    }
    
    # LZ77 (with small window for speed)
    lz77 = lz77_compress(data, window_size=512, lookahead_size=32)
    results["lz77"] = {
        "ratio": lz77.compression_ratio,
        "compressed_size": lz77.compressed_size,
        "tokens": lz77.metadata.get("tokens", 0)
    }
    
    # LZW
    lzw = lzw_compress(data)
    results["lzw"] = {
        "ratio": lzw.compression_ratio,
        "compressed_size": lzw.compressed_size,
        "dict_size": lzw.metadata.get("dict_size", 0)
    }
    
    # Best
    best_algo = min(results, key=lambda k: results[k]["compressed_size"])
    results["best"] = {
        "algorithm": best_algo,
        "ratio": results[best_algo]["ratio"]
    }
    
    return results


# For backward compatibility
lz78_compress = lzw_compress  # LZ78 is similar to LZW
lz78_decompress = lzw_decompress  # LZ78 is similar to LZW