"""
Hamming error correction codes
"""

from typing import List, Tuple


class HammingCode:
    """Hamming error correction code implementation"""
    
    @staticmethod
    def encode(data: bytes, n: int = 7, k: int = 4) -> bytes:
        """
        Encode data using Hamming code.
        
        Args:
            data: Input data
            n: Total bits in codeword (7 or 15)
            k: Data bits (4 or 11)
            
        Returns:
            Encoded data
        """
        r = n - k  # Number of parity bits
        
        # Convert bytes to bits
        bits = []
        for byte in data:
            for i in range(8):
                bits.append((byte >> i) & 1)
        
        # Pad to multiple of k
        while len(bits) % k != 0:
            bits.append(0)
        
        # Encode each k-bit block
        encoded = []
        for i in range(0, len(bits), k):
            block = bits[i:i + k]
            encoded_bits = HammingCode._encode_block(block, n, k)
            encoded.extend(encoded_bits)
        
        # Convert back to bytes
        result = bytearray()
        for i in range(0, len(encoded), 8):
            byte = 0
            for j in range(min(8, len(encoded) - i)):
                byte |= encoded[i + j] << j
            result.append(byte)
        
        return bytes(result)
    
    @staticmethod
    def _encode_block(data_bits: List[int], n: int, k: int) -> List[int]:
        """Encode k data bits into n-bit Hamming code"""
        r = n - k
        
        # Create codeword
        codeword = [0] * n
        
        # Parity bit positions: 2^0, 2^1, 2^2, ...
        parity_positions = [2 ** i - 1 for i in range(r)]
        
        # Place data bits
        data_idx = 0
        for i in range(n):
            if i not in parity_positions:
                codeword[i] = data_bits[data_idx]
                data_idx += 1
        
        # Calculate parity bits
        for p in parity_positions:
            parity = 0
            for i in range(p, n, p + 1):
                parity ^= codeword[i]
            codeword[p] = parity
        
        return codeword
    
    @staticmethod
    def decode(data: bytes, n: int = 7, k: int = 4) -> Tuple[bytes, List[int]]:
        """
        Decode Hamming code and correct errors.
        
        Args:
            data: Encoded data
            n: Total bits in codeword
            k: Data bits
            
        Returns:
            Tuple of (decoded_data, list_of_corrected_positions)
        """
        r = n - k
        parity_positions = [2 ** i - 1 for i in range(r)]
        
        # Convert to bits (LSB first per byte)
        bits = []
        for byte in data:
            for i in range(8):
                bits.append((byte >> i) & 1)
        
        decoded = []
        errors = []
        
        # Process and correct each n-bit block in place
        for block_start in range(0, len(bits), n):
            block = bits[block_start:block_start + n]
            if len(block) < n:
                break
            
            syndrome = HammingCode._calculate_syndrome(block, n, k)
            if syndrome != 0:
                error_pos = syndrome - 1
                if error_pos < n:
                    bits[block_start + error_pos] ^= 1
                    errors.append(block_start + error_pos)
            
            for i in range(n):
                if i not in parity_positions:
                    decoded.append(bits[block_start + i])
        
        # Convert back to bytes
        result = bytearray()
        for i in range(0, len(decoded), 8):
            byte = 0
            for j in range(min(8, len(decoded) - i)):
                byte |= decoded[i + j] << j
            result.append(byte)
        
        return bytes(result), errors
    
    @staticmethod
    def _calculate_syndrome(block: List[int], n: int, k: int) -> int:
        """Calculate syndrome (error position)"""
        r = n - k
        parity_positions = [2 ** i - 1 for i in range(r)]
        
        syndrome = 0
        for p in parity_positions:
            parity = 0
            for i in range(p, n, p + 1):
                parity ^= block[i]
            if parity:
                syndrome |= (1 << parity_positions.index(p))
        
        return syndrome
    
    @staticmethod
    def detect_errors(data: bytes, n: int = 7, k: int = 4) -> List[int]:
        """
        Detect errors without correction.
        
        Returns:
            List of block indices with errors
        """
        r = n - k
        
        bits = []
        for byte in data:
            for i in range(8):
                bits.append((byte >> i) & 1)
        
        error_blocks = []
        
        for i in range(0, len(bits), n):
            block = bits[i:i + n]
            if len(block) < n:
                break
            
            syndrome = HammingCode._calculate_syndrome(block, n, k)
            if syndrome != 0:
                error_blocks.append(i // n)
        
        return error_blocks
    
    @staticmethod
    def get_code_info(n: int, k: int) -> dict:
        """Get information about Hamming code"""
        r = n - k
        
        return {
            "n": n,
            "k": k,
            "r": r,
            "rate": k / n,
            "min_distance": 3,  # Hamming codes have d_min = 3
            "error_detection": r,
            "error_correction": 1,
            "description": f"Hamming({n},{k}): {k} data bits, {r} parity bits"
        }
    
    @staticmethod
    def extended_hamming(data: bytes) -> bytes:
        """
        Extended Hamming code (detects 2 errors, corrects 1).
        
        Uses Hamming(8,4) which adds overall parity bit.
        """
        # First encode with Hamming(7,4)
        encoded = HammingCode.encode(data, n=7, k=4)
        
        # Add overall parity bit for each byte
        result = bytearray()
        for byte in encoded:
            parity = bin(byte).count('1') % 2
            result.append((byte << 1) | parity)
        
        return bytes(result)
    
    @staticmethod
    def decode_extended(data: bytes) -> Tuple[bytes, List[int]]:
        """Decode extended Hamming code"""
        decoded_bits = []
        errors = []
        
        for i, byte in enumerate(data):
            # Extract data byte and parity
            data_byte = byte >> 1
            parity_bit = byte & 1
            
            # Check overall parity
            actual_parity = bin(data_byte).count('1') % 2
            
            if actual_parity != parity_bit:
                # Parity error - either single error in data or error in parity bit
                # Try to decode with Hamming(7,4)
                decoded_block, block_errors = HammingCode.decode(
                    bytes([data_byte]), n=7, k=4
                )
                
                if block_errors:
                    # Single error corrected
                    errors.append(i * 8 + block_errors[0])
                else:
                    # Error in parity bit only
                    errors.append(i * 8 + 7)
            
            # Extract 7 bits
            for j in range(7):
                decoded_bits.append((data_byte >> j) & 1)
        
        # Convert back to bytes (4 bits per original byte)
        result = bytearray()
        for i in range(0, len(decoded_bits), 4):
            if i + 4 <= len(decoded_bits):
                byte = 0
                for j in range(4):
                    byte |= decoded_bits[i + j] << j
                result.append(byte)
        
        return bytes(result), errors


# === Standalone helper functions for node-based API ===

def encode_hamming_74(data_bits: List[int]) -> List[int]:
    """
    Encode 4 data bits into 7 Hamming(7,4) codeword bits.
    
    Args:
        data_bits: List of 4 bits (will be padded to 4 if shorter)
        
    Returns:
        List of 7 encoded bits
    """
    bits = list(data_bits)
    while len(bits) < 4:
        bits.append(0)
    return HammingCode._encode_block(bits, 7, 4)


def decode_hamming_74(block_bits: List[int]) -> Tuple[List[int], List[int]]:
    """
    Decode 7 Hamming(7,4) codeword bits into corrected 4 data bits.
    
    Args:
        block_bits: List of 7 encoded bits
        
    Returns:
        Tuple of (corrected_4_data_bits, list_of_error_positions)
    """
    r = 7 - 4  # 3 parity bits
    parity_positions = [2 ** i - 1 for i in range(r)]  # 0, 1, 3
    
    block = list(block_bits)
    errors = []
    
    # Calculate syndrome
    syndrome = 0
    for p_idx, p in enumerate(parity_positions):
        parity = 0
        for i in range(p, 7, p + 1):
            parity ^= block[i]
        if parity:
            syndrome |= (1 << p_idx)
    
    if syndrome != 0:
        error_pos = syndrome - 1
        if error_pos < 7:
            block[error_pos] ^= 1
            errors.append(error_pos)
    
    # Extract data bits (skip parity positions)
    decoded = []
    for i in range(7):
        if i not in parity_positions:
            decoded.append(block[i])
    
    return decoded, errors


def apply_bsc_noise(bits: List[int], error_prob: float = 0.05) -> List[int]:
    """
    Apply Binary Symmetric Channel noise to bits.
    Each bit is flipped with probability error_prob.
    
    Args:
        bits: Input bit list
        error_prob: Probability of each bit being flipped (0.0 to 1.0)
        
    Returns:
        Noisy bit list
    """
    import random
    return [1 - b if random.random() < error_prob else b for b in bits]