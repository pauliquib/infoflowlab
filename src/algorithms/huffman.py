"""
Huffmanovo kódování - bezeztrátová komprese.
"""

import heapq
from typing import Dict, Tuple, Optional, List
from collections import Counter, defaultdict


class HuffmanNode:
    def __init__(self, symbol: str = None, frequency: int = 0):
        self.symbol = symbol
        self.frequency = frequency
        self.left = None
        self.right = None
        self.code = ""
    
    def __lt__(self, other):
        return self.frequency < other.frequency
    
    def __repr__(self):
        return f"HuffmanNode({self.symbol}, {self.frequency})"


class HuffmanCoder:
    """Huffmanův kódovač/dekódovač."""
    
    def __init__(self):
        self.root: Optional[HuffmanNode] = None
        self.codes: Dict[str, str] = {}
        self.reverse_codes: Dict[str, str] = {}
        self.frequencies: Dict[str, int] = {}
    
    def build_tree(self, data: str) -> HuffmanNode:
        """Vybuduje Huffmanův strom z dat."""
        if not data:
            return None
        
        # Spočítat frekvence
        self.frequencies = dict(Counter(data))
        
        # Vytvořit min-heap
        heap = []
        for symbol, freq in self.frequencies.items():
            node = HuffmanNode(symbol, freq)
            heapq.heappush(heap, node)
        
        if len(heap) == 1:
            # Speciální případ - jen jeden symbol
            node = heapq.heappop(heap)
            self.root = HuffmanNode(None, node.frequency)
            self.root.left = node
            return self.root
        
        # Stavět strom
        while len(heap) > 1:
            left = heapq.heappop(heap)
            right = heapq.heappop(heap)
            
            merged = HuffmanNode(None, left.frequency + right.frequency)
            merged.left = left
            merged.right = right
            
            heapq.heappush(heap, merged)
        
        self.root = heapq.heappop(heap)
        return self.root
    
    def _generate_codes(self, node: HuffmanNode, current_code: str = ""):
        """Rekurzivně vygeneruje kódy."""
        if node is None:
            return
        
        if node.symbol is not None:
            # List - přiřadit kód
            code = current_code if current_code else "0"
            self.codes[node.symbol] = code
            self.reverse_codes[code] = node.symbol
            return
        
        self._generate_codes(node.left, current_code + "0")
        self._generate_codes(node.right, current_code + "1")
    
    def encode(self, data: str) -> Tuple[str, Dict]:
        """
        Zakóduje data Huffmanovým kódováním.
        Vrátí: (zakódovaný řetězec, metadata pro dekódování)
        """
        if not data:
            return "", {}
        
        self.build_tree(data)
        self.codes = {}
        self.reverse_codes = {}
        self._generate_codes(self.root)
        
        encoded = "".join(self.codes[char] for char in data)
        
        metadata = {
            'codes': self.codes.copy(),
            'frequencies': self.frequencies.copy(),
            'original_length': len(data),
            'encoded_length': len(encoded),
            'compression_ratio': len(encoded) / (len(data) * 8)
        }
        
        return encoded, metadata
    
    def decode(self, encoded: str, metadata: Dict) -> str:
        """Dekóduje Huffmanem zakódovaná data."""
        if not encoded:
            return ""
        
        # Obnovit kódy
        self.codes = metadata.get('codes', {})
        self.reverse_codes = {v: k for k, v in self.codes.items()}
        
        result = []
        current = ""
        
        for bit in encoded:
            current += bit
            if current in self.reverse_codes:
                result.append(self.reverse_codes[current])
                current = ""
        
        return "".join(result)
    
    def get_tree_structure(self) -> List[Dict]:
        """Vrátí strukturu stromu pro vizualizaci."""
        if not self.root:
            return []
        
        result = []
        
        def traverse(node, depth=0, path=""):
            if node is None:
                return
            
            entry = {
                'symbol': node.symbol,
                'frequency': node.frequency,
                'depth': depth,
                'path': path,
                'is_leaf': node.symbol is not None
            }
            result.append(entry)
            
            traverse(node.left, depth + 1, path + "0")
            traverse(node.right, depth + 1, path + "1")
        
        traverse(self.root)
        return result
    
    def get_average_code_length(self) -> float:
        """Vrátí průměrnou délku kódu."""
        if not self.codes or not self.frequencies:
            return 0.0
        
        total_symbols = sum(self.frequencies.values())
        total_length = sum(
            len(self.codes[sym]) * freq 
            for sym, freq in self.frequencies.items()
        )
        
        return total_length / total_symbols
    
    def get_efficiency(self) -> float:
        """Vrátí efektivitu kódování."""
        from .entropy import shannon_entropy
        
        if not self.frequencies:
            return 0.0
        
        # Vytvořit řetězec z frekvencí pro výpočet entropie
        data = ""
        for sym, freq in self.frequencies.items():
            data += sym * freq
        
        h = shannon_entropy(data)
        avg_length = self.get_average_code_length()
        
        if avg_length == 0:
            return 0.0
        
        return h / avg_length


# === Standalone helper functions for node-based API ===

def _build_tree_from_bytes(data: bytes):
    """Build Huffman tree from bytes data and return (codes, reverse_codes)."""
    if not data:
        return {}, {}
    
    # Count frequencies
    frequencies = Counter(data)
    
    # Create min-heap
    heap = []
    for symbol, freq in frequencies.items():
        node = HuffmanNode(str(symbol), freq)
        heapq.heappush(heap, node)
    
    if len(heap) == 1:
        node = heapq.heappop(heap)
        root = HuffmanNode(None, node.frequency)
        root.left = node
    else:
        while len(heap) > 1:
            left = heapq.heappop(heap)
            right = heapq.heappop(heap)
            merged = HuffmanNode(None, left.frequency + right.frequency)
            merged.left = left
            merged.right = right
            heapq.heappush(heap, merged)
        root = heapq.heappop(heap)
    
    # Generate codes
    codes = {}
    reverse_codes = {}
    
    def generate(node, code=""):
        if node is None:
            return
        if node.symbol is not None:
            c = code if code else "0"
            codes[node.symbol] = c
            reverse_codes[c] = node.symbol
            return
        generate(node.left, code + "0")
        generate(node.right, code + "1")
    
    generate(root)
    return codes, reverse_codes


def huffman_encode(data: bytes) -> Tuple[str, Dict[str, str]]:
    """
    Encode bytes using Huffman coding.
    
    Args:
        data: Input bytes to encode
        
    Returns:
        Tuple of (bit_string, codes_dict)
    """
    codes, _ = _build_tree_from_bytes(data)
    if not codes:
        return "", {}
    
    encoded = "".join(codes[str(b)] for b in data)
    return encoded, codes


def huffman_decode(encoded: str, codes: Dict[str, str]) -> bytes:
    """
    Decode Huffman-encoded bit string back to bytes.
    
    Args:
        encoded: Bit string (e.g. "0101101...")
        codes: Huffman codes dictionary {symbol_str: code_str}
        
    Returns:
        Decoded bytes
    """
    if not encoded or not codes:
        return b""
    
    # Build reverse codes
    reverse = {v: int(k) for k, v in codes.items()}
    
    result = bytearray()
    current = ""
    for bit in encoded:
        current += bit
        if current in reverse:
            result.append(reverse[current])
            current = ""
    
    return bytes(result)


def demo():
    """Demo Huffmanova kódování."""
    print("=== Huffmanovo kódování ===\n")
    
    data = "AAAABBC"
    coder = HuffmanCoder()
    
    encoded, metadata = coder.encode(data)
    print(f"Původní data: '{data}'")
    print(f"Délka původní: {len(data) * 8} bitů")
    print(f"Zakódováno: {encoded}")
    print(f"Délka zakódovaná: {len(encoded)} bitů")
    print(f"Kompresní poměr: {metadata['compression_ratio']:.2%}")
    
    print(f"\nKódy:")
    for sym, code in sorted(coder.codes.items()):
        print(f"  '{sym}': {code}")
    
    print(f"\nPrůměrná délka kódu: {coder.get_average_code_length():.2f} bitů")
    print(f"Efektivita: {coder.get_efficiency()*100:.1f}%")
    
    decoded = coder.decode(encoded, metadata)
    print(f"\nDekódováno: '{decoded}'")
    print(f"Shoda: {data == decoded}")
    
    # Test bytes-based standalone functions
    print("\n=== Bytes-based Huffman ===")
    data_bytes = b"Hello World! This is a test."
    encoded_bits, codes = huffman_encode(data_bytes)
    decoded_bytes = huffman_decode(encoded_bits, codes)
    print(f"Original: {data_bytes}")
    print(f"Encoded length: {len(encoded_bits)} bits")
    print(f"Decoded: {decoded_bytes}")
    print(f"Match: {data_bytes == decoded_bytes}")


if __name__ == "__main__":
    demo()