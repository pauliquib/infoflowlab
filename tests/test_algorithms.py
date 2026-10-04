"""
Tests for algorithm implementations
"""

import pytest
from src.algorithms.entropy import shannon_entropy
from src.algorithms.hamming import HammingCode
from src.algorithms.huffman import huffman_encode, huffman_decode
from src.algorithms.checksums import ChecksumCalculator
from src.algorithms.number_systems import NumberConverter
from src.algorithms.compression import rle_compress, rle_decompress


class TestEntropy:
    """Test entropy calculations"""

    def test_entropy_zero(self):
        """Test entropy of uniform data (all same bytes)"""
        data = b"AAAAA"
        entropy = shannon_entropy(data)
        assert entropy == 0.0

    def test_entropy_max(self):
        """Test entropy of random data"""
        data = bytes(range(256))
        entropy = shannon_entropy(data)
        assert entropy > 7.9

    def test_entropy_partial(self):
        """Test entropy of mixed data"""
        data = b"AABBC"
        entropy = shannon_entropy(data)
        assert 0 < entropy < 8

    def test_entropy_empty(self):
        """Test entropy of empty data"""
        entropy = shannon_entropy(b"")
        assert entropy == 0.0


class TestHamming:
    """Test Hamming error correction"""

    def test_hamming_encode(self):
        data = b"\x00"
        encoded = HammingCode.encode(data)
        assert len(encoded) > 0

    def test_hamming_decode(self):
        original = b"\x0F"
        encoded = HammingCode.encode(original)
        decoded, _ = HammingCode.decode(encoded)
        assert decoded == original

    def test_hamming_single_error_correction(self):
        original = b"\xAB"
        encoded = HammingCode.encode(original)

        encoded_list = bytearray(encoded)
        encoded_list[0] ^= 0x01
        encoded_corrupted = bytes(encoded_list)

        decoded, errors = HammingCode.decode(encoded_corrupted)
        assert decoded == original
        assert len(errors) > 0


class TestHuffman:
    """Test Huffman compression"""

    def test_huffman_compress_decompress(self):
        original = b"AAAAABBBCC"
        encoded, codes = huffman_encode(original)
        decompressed = huffman_decode(encoded, codes)
        assert decompressed == original
        assert len(encoded) < len(original) * 8

    def test_huffman_random_data(self):
        original = bytes(range(256))
        encoded, codes = huffman_encode(original)
        decompressed = huffman_decode(encoded, codes)
        assert decompressed == original

    def test_huffman_empty(self):
        encoded, codes = huffman_encode(b"")
        decompressed = huffman_decode(encoded, codes)
        assert decompressed == b""


class TestChecksums:
    """Test checksum and validation algorithms"""

    def test_crc32(self):
        data = b"test data"
        checksum = ChecksumCalculator.crc32(data)
        assert isinstance(checksum, int)
        assert checksum >= 0

    def test_crc32_consistency(self):
        data = b"test data"
        assert ChecksumCalculator.crc32(data) == ChecksumCalculator.crc32(data)

    def test_ean13_valid(self):
        valid_codes = [
            "5901234123457",
            "9780201379624",
        ]
        for code in valid_codes:
            assert ChecksumCalculator.validate_ean13(code) is True

    def test_ean13_invalid(self):
        invalid_codes = [
            "1234567890123",
            "12345",
            "abcdefghijklm",
        ]
        for code in invalid_codes:
            assert ChecksumCalculator.validate_ean13(code) is False

    def test_isbn10_valid(self):
        valid_codes = [
            "0306406152",
            "0201633612",
        ]
        for code in valid_codes:
            assert ChecksumCalculator.validate_isbn10(code) is True

    def test_isbn13_valid(self):
        assert ChecksumCalculator.validate_isbn13("9780306406157") is True

    def test_luhn_valid(self):
        valid_numbers = [
            "4532015112830366",
            "5425233430109903",
        ]
        for number in valid_numbers:
            assert ChecksumCalculator.validate_luhn(number) is True

    def test_luhn_invalid(self):
        invalid_numbers = [
            "1234567890123456",
            "1111111111111111",
        ]
        for number in invalid_numbers:
            assert ChecksumCalculator.validate_luhn(number) is False


class TestNumberSystems:
    """Test number system conversions"""

    def test_binary_to_decimal(self):
        assert NumberConverter.convert("1010", 2, 10) == "10"
        assert NumberConverter.convert("11111111", 2, 10) == "255"

    def test_decimal_to_hex(self):
        assert NumberConverter.convert("255", 10, 16).upper() == "FF"
        assert NumberConverter.convert("16", 10, 16).upper() == "10"

    def test_hex_to_binary(self):
        assert NumberConverter.convert("FF", 16, 2) == "11111111"
        assert NumberConverter.convert("A0", 16, 2) == "10100000"

    def test_octal_to_decimal(self):
        assert NumberConverter.convert("77", 8, 10) == "63"
        assert NumberConverter.convert("10", 8, 10) == "8"


class TestCompression:
    """Test compression algorithms"""

    def test_rle_encode_decode(self):
        original = b"AAAAABBBCCDDDD"
        encoded = rle_compress(original)
        decoded = rle_decompress(encoded.data)
        assert decoded.data == original
        assert len(encoded.data) < len(original)

    def test_rle_no_compression(self):
        original = b"ABCDEFGHIJ"
        encoded = rle_compress(original)
        decoded = rle_decompress(encoded.data)
        assert decoded.data == original

    def test_rle_empty(self):
        encoded = rle_compress(b"")
        decoded = rle_decompress(encoded.data)
        assert decoded.data == b""

    def test_rle_single_byte(self):
        original = b"AAAAA"
        encoded = rle_compress(original)
        decoded = rle_decompress(encoded.data)
        assert decoded.data == original
        assert len(encoded.data) < len(original)
