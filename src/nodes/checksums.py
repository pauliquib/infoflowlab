"""
Checksum validation nodes - EAN, ISBN, ISSN, ICO, Luhn, Verhoeff with param schemas.
"""

from src.core.node_base import NodeBase, ParamType
from src.core.packet import DataPacket
from src.core.port import DataType


class EANValidator(NodeBase):
    """EAN-13/EAN-8 barcode validator."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "checksums", "EAN Validator", category="checksums")
        self.add_input("in", DataType.TEXT)
        self.add_output("out", DataType.TEXT)
        self.set_param("ean_type", "EAN-13")
    
    def get_param_schema(self) -> dict:
        schema = super().get_param_schema()
        schema["ean_type"] = {
            "type": ParamType.CHOICE, "label": "EAN Type", "default": "EAN-13",
            "choices": ["EAN-13", "EAN-8"],
            "description": "EAN barcode type",
            "category": "basic"
        }
        return schema
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        text = packet.as_text.strip().replace('-', '').replace(' ', '')
        ean_type = self.get_param("ean_type", "EAN-13")
        
        if ean_type == "EAN-13":
            valid = self._validate_ean13(text)
            result = f"EAN-13: {text} - {'Valid' if valid else 'Invalid'}"
            if not valid:
                correct = self._calc_ean(text[:12]) if len(text) > 12 else "?"
                result += f" (correct: {correct})"
        else:
            valid = self._validate_ean8(text)
            result = f"EAN-8: {text} - {'Valid' if valid else 'Invalid'}"
            if not valid:
                correct = self._calc_ean(text[:7]) if len(text) > 7 else "?"
                result += f" (correct: {correct})"
        
        data = result.encode("utf-8")
        new_pkt = DataPacket(id=packet.id, payload=data, source_format="text", size_bits=len(data)*8)
        new_pkt.add_step(self.name, "EAN", len(packet.payload), len(data), result[:30])
        return new_pkt
    
    def _calc_ean(self, code: str) -> str:
        if not code.isdigit():
            return "?"
        weights = [1, 3] * ((len(code) + 1) // 2)
        weights = weights[:len(code)]
        total = sum(int(code[i]) * weights[i] for i in range(len(code)))
        return str((10 - (total % 10)) % 10)
    
    def _validate_ean13(self, code: str) -> bool:
        return len(code) == 13 and code.isdigit() and self._calc_ean(code[:12]) == code[12]
    
    def _validate_ean8(self, code: str) -> bool:
        return len(code) == 8 and code.isdigit() and self._calc_ean(code[:7]) == code[7]


class ISBNValidator(NodeBase):
    """ISBN-10/ISBN-13 validator."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "checksums", "ISBN Validator", category="checksums")
        self.add_input("in", DataType.TEXT)
        self.add_output("out", DataType.TEXT)
        self.set_param("isbn_type", "ISBN-13")
    
    def get_param_schema(self) -> dict:
        schema = super().get_param_schema()
        schema["isbn_type"] = {
            "type": ParamType.CHOICE, "label": "ISBN Type", "default": "ISBN-13",
            "choices": ["ISBN-13", "ISBN-10"],
            "description": "ISBN standard",
            "category": "basic"
        }
        return schema
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        text = packet.as_text.strip().replace('-', '').replace(' ', '')
        isbn_type = self.get_param("isbn_type", "ISBN-13")
        
        if isbn_type == "ISBN-13":
            valid = self._validate_isbn13(text)
            result = f"ISBN-13: {text} - {'Valid' if valid else 'Invalid'}"
        else:
            valid = self._validate_isbn10(text)
            result = f"ISBN-10: {text} - {'Valid' if valid else 'Invalid'}"
        
        data = result.encode("utf-8")
        new_pkt = DataPacket(id=packet.id, payload=data, source_format="text", size_bits=len(data)*8)
        new_pkt.add_step(self.name, "ISBN", len(packet.payload), len(data), result[:30])
        return new_pkt
    
    def _validate_isbn13(self, isbn: str) -> bool:
        if len(isbn) != 13 or not isbn.isdigit():
            return False
        weights = [1, 3] * 6
        total = sum(int(isbn[i]) * weights[i] for i in range(12))
        return (10 - (total % 10)) % 10 == int(isbn[12])
    
    def _validate_isbn10(self, isbn: str) -> bool:
        if len(isbn) != 10:
            return False
        check_char = isbn[9].upper()
        check_value = 10 if check_char == 'X' else (int(check_char) if check_char.isdigit() else -1)
        if check_value < 0:
            return False
        total = sum(int(isbn[i]) * (10 - i) for i in range(9))
        expected = (11 - (total % 11)) % 11
        return expected == check_value


class ISSNValidator(NodeBase):
    """ISSN validator."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "checksums", "ISSN Validator", category="checksums")
        self.add_input("in", DataType.TEXT)
        self.add_output("out", DataType.TEXT)
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        text = packet.as_text.strip().replace('-', '').replace(' ', '')
        
        if len(text) != 8 or not text[:7].isdigit():
            result = f"ISSN: {text} - Invalid format"
        else:
            weights = [8, 7, 6, 5, 4, 3, 2]
            total = sum(int(text[i]) * weights[i] for i in range(7))
            check = (11 - (total % 11)) % 11
            check_char = 'X' if check == 10 else str(check)
            valid = check_char == text[7].upper()
            result = f"ISSN: {text} - {'Valid' if valid else 'Invalid'}"
        
        data = result.encode("utf-8")
        new_pkt = DataPacket(id=packet.id, payload=data, source_format="text", size_bits=len(data)*8)
        new_pkt.add_step(self.name, "ISSN", len(packet.payload), len(data), result[:30])
        return new_pkt


class LuhnValidator(NodeBase):
    """Luhn algorithm validator."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "checksums", "Luhn Validator", category="checksums")
        self.add_input("in", DataType.TEXT)
        self.add_output("out", DataType.TEXT)
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        text = packet.as_text.strip().replace(' ', '')
        
        if not text.isdigit():
            result = f"Luhn: {text} - Invalid format"
        else:
            valid = self._luhn_check(text)
            result = f"Luhn: {text} - {'Valid' if valid else 'Invalid'}"
            if not valid:
                for i in range(10):
                    if self._luhn_check(text[:-1] + str(i)):
                        result += f" (correct: {i})"
                        break
        
        data = result.encode("utf-8")
        new_pkt = DataPacket(id=packet.id, payload=data, source_format="text", size_bits=len(data)*8)
        new_pkt.add_step(self.name, "Luhn", len(packet.payload), len(data), result[:30])
        return new_pkt
    
    def _luhn_check(self, number: str) -> bool:
        if not number.isdigit():
            return False
        total = 0
        for i, digit in enumerate(reversed(number)):
            d = int(digit)
            if i % 2 == 1:
                d *= 2
                if d > 9:
                    d -= 9
            total += d
        return total % 10 == 0


class VerhoeffValidator(NodeBase):
    """Verhoeff algorithm validator."""
    
    _D = [[0,1,2,3,4,5,6,7,8,9],[1,2,3,4,0,6,7,8,9,5],[2,3,4,0,1,7,8,9,5,6],
          [3,4,0,1,2,8,9,5,6,7],[4,0,1,2,3,9,5,6,7,8],[5,9,8,7,6,0,4,3,2,1],
          [6,5,9,8,7,1,0,4,3,2],[7,6,5,9,8,2,1,0,4,3],[8,7,6,5,9,3,2,1,0,4],
          [9,8,7,6,5,4,3,2,1,0]]
    _INV = [0,4,3,2,1,5,6,7,8,9]
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "checksums", "Verhoeff Validator", category="checksums")
        self.add_input("in", DataType.TEXT)
        self.add_output("out", DataType.TEXT)
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        text = packet.as_text.strip().replace(' ', '')
        
        if not text.isdigit():
            result = f"Verhoeff: {text} - Invalid format"
        else:
            c = 0
            for i, digit in enumerate(reversed(text)):
                c = self._D[(i + 1) % 8][(c + int(digit)) % 10]
            valid = c == 0
            result = f"Verhoeff: {text} - {'Valid' if valid else 'Invalid'}"
        
        data = result.encode("utf-8")
        new_pkt = DataPacket(id=packet.id, payload=data, source_format="text", size_bits=len(data)*8)
        new_pkt.add_step(self.name, "Verhoeff", len(packet.payload), len(data), result[:30])
        return new_pkt


class ICOValidator(NodeBase):
    """IČO (Czech business ID) validator."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "checksums", "ICO Validator", category="checksums")
        self.add_input("in", DataType.TEXT)
        self.add_output("out", DataType.TEXT)
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        text = packet.as_text.strip()
        weights = [8, 7, 6, 5, 4, 3, 2]
        
        if len(text) != 8 or not text.isdigit():
            result = f"IČO: {text} - Invalid format (must be 8 digits)"
        else:
            total = sum(int(text[i]) * weights[i] for i in range(7))
            check = (11 - (total % 11)) % 11
            if check == 10:
                check = 1  # Special case for IČO
            valid = check == int(text[7])
            result = f"IČO: {text} - {'Valid' if valid else 'Invalid'}"
        
        data = result.encode("utf-8")
        new_pkt = DataPacket(id=packet.id, payload=data, source_format="text", size_bits=len(data)*8)
        new_pkt.add_step(self.name, "IČO", len(packet.payload), len(data), result[:30])
        return new_pkt


class RCCalculator(NodeBase):
    """Rodné číslo (Czech birth ID) validator."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "checksums", "RC Validator", category="checksums")
        self.add_input("in", DataType.TEXT)
        self.add_output("out", DataType.TEXT)
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        text = packet.as_text.strip().replace('/', '')
        
        if len(text) not in (9, 10) or not text.isdigit():
            result = f"RC: {text} - Invalid format"
        else:
            if len(text) == 9:
                # Old format (before 1954)
                result = f"RC: {text} - Old format (9 digits)"
            else:
                # Standard format: divisible by 11
                num = int(text)
                valid = num % 11 == 0
                result = f"RC: {text} - {'Valid' if valid else 'Invalid'}"
        
        data = result.encode("utf-8")
        new_pkt = DataPacket(id=packet.id, payload=data, source_format="text", size_bits=len(data)*8)
        new_pkt.add_step(self.name, "RC", len(packet.payload), len(data), result[:30])
        return new_pkt