"""
Checksum calculation algorithms - EAN, ISBN, ISSN, Luhn, Verhoeff
"""

from typing import Optional


class ChecksumCalculator:
    """Calculate and validate various checksums"""
    
    @staticmethod
    def ean13_check_digit(code: str) -> str:
        """Calculate EAN-13 check digit"""
        if len(code) != 12 or not code.isdigit():
            return "?"
        
        # Weights: 1,3,1,3,... from right to left
        weights = [1, 3] * 6
        total = sum(int(code[i]) * weights[i] for i in range(12))
        check = (10 - (total % 10)) % 10
        
        return str(check)
    
    @staticmethod
    def validate_ean13(code: str) -> bool:
        """Validate EAN-13 code"""
        code = code.strip().replace('-', '').replace(' ', '')
        if len(code) != 13 or not code.isdigit():
            return False
        
        check = ChecksumCalculator.ean13_check_digit(code[:12])
        return check == code[12]
    
    @staticmethod
    def ean8_check_digit(code: str) -> str:
        """Calculate EAN-8 check digit"""
        if len(code) != 7 or not code.isdigit():
            return "?"
        
        weights = [1, 3] * 3
        weights = weights[:7]
        total = sum(int(code[i]) * weights[i] for i in range(7))
        check = (10 - (total % 10)) % 10
        
        return str(check)
    
    @staticmethod
    def validate_ean8(code: str) -> bool:
        """Validate EAN-8 code"""
        code = code.strip().replace('-', '').replace(' ', '')
        if len(code) != 8 or not code.isdigit():
            return False
        
        check = ChecksumCalculator.ean8_check_digit(code[:7])
        return check == code[7]
    
    @staticmethod
    def isbn10_check_digit(isbn: str) -> str:
        """Calculate ISBN-10 check digit"""
        if len(isbn) != 9 or not isbn.isdigit():
            return "?"
        
        total = sum(int(isbn[i]) * (10 - i) for i in range(9))
        check = (11 - (total % 11)) % 11
        
        return 'X' if check == 10 else str(check)
    
    @staticmethod
    def validate_isbn10(isbn: str) -> bool:
        """Validate ISBN-10"""
        isbn = isbn.strip().replace('-', '').replace(' ', '')
        if len(isbn) != 10:
            return False
        
        check_char = isbn[9].upper()
        if check_char == 'X':
            check_value = 10
        elif check_char.isdigit():
            check_value = int(check_char)
        else:
            return False
        
        total = sum(int(isbn[i]) * (10 - i) for i in range(9))
        expected = (11 - (total % 11)) % 11
        
        return expected == check_value
    
    @staticmethod
    def isbn13_check_digit(isbn: str) -> str:
        """Calculate ISBN-13 check digit"""
        if len(isbn) != 12 or not isbn.isdigit():
            return "?"
        
        weights = [1, 3] * 6
        total = sum(int(isbn[i]) * weights[i] for i in range(12))
        check = (10 - (total % 10)) % 10
        
        return str(check)
    
    @staticmethod
    def validate_isbn13(isbn: str) -> bool:
        """Validate ISBN-13"""
        isbn = isbn.strip().replace('-', '').replace(' ', '')
        if len(isbn) != 13 or not isbn.isdigit():
            return False
        
        weights = [1, 3] * 6
        total = sum(int(isbn[i]) * weights[i] for i in range(12))
        check = (10 - (total % 10)) % 10
        
        return check == int(isbn[12])
    
    @staticmethod
    def issn_check_digit(issn: str) -> str:
        """Calculate ISSN check digit"""
        if len(issn) != 7 or not issn.isdigit():
            return "?"
        
        weights = [8, 7, 6, 5, 4, 3, 2]
        total = sum(int(issn[i]) * weights[i] for i in range(7))
        check = (11 - (total % 11)) % 11
        
        return 'X' if check == 10 else str(check)
    
    @staticmethod
    def validate_issn(issn: str) -> bool:
        """Validate ISSN"""
        issn = issn.strip().replace('-', '').replace(' ', '')
        if len(issn) != 8 or not issn[:7].isdigit():
            return False
        
        check_char = ChecksumCalculator.issn_check_digit(issn[:7])
        return check_char == issn[7].upper()
    
    @staticmethod
    def luhn_check_digit(number: str) -> str:
        """Calculate Luhn check digit"""
        if not number.isdigit():
            return "?"
        
        # Try all digits
        for i in range(10):
            if ChecksumCalculator.validate_luhn(number + str(i)):
                return str(i)
        
        return "?"
    
    @staticmethod
    def validate_luhn(number: str) -> bool:
        """Validate using Luhn algorithm"""
        number = number.strip().replace(' ', '')
        if not number.isdigit():
            return False
        
        total = 0
        for i, digit in enumerate(reversed(number)):
            d = int(digit)
            
            # Double every second digit from right
            if i % 2 == 1:
                d *= 2
                if d > 9:
                    d -= 9
            
            total += d
        
        return total % 10 == 0
    
    @staticmethod
    def verhoeff_check(number: str) -> bool:
        """Validate using Verhoeff algorithm"""
        if not number.isdigit():
            return False
        
        # Verhoeff tables
        d = [
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
            [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
            [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
            [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
            [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
            [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
            [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
            [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
            [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
        ]
        
        p = [
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
            [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
            [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
            [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
            [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
            [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
            [7, 0, 4, 6, 9, 1, 3, 2, 5, 8]
        ]
        
        inv = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]
        
        c = 0
        for i, digit in enumerate(reversed(number)):
            c = d[i % 8][(c + int(digit)) % 10]
        
        return c == 0
    
    @staticmethod
    def validate_ic(ic: str) -> bool:
        """Validate Czech IČ (company ID)"""
        ic = ic.strip().replace('-', '').replace(' ', '')
        if len(ic) != 8 or not ic.isdigit():
            return False
        
        # IČ uses same algorithm as ISSN but with different weights
        weights = [8, 7, 6, 5, 4, 3, 2]
        total = sum(int(ic[i]) * weights[i] for i in range(7))
        check = (11 - (total % 11)) % 11
        
        return check == int(ic[7])
    
    @staticmethod
    def validate_rodne_cislo(rc: str) -> bool:
        """Validate Czech birth number (rodné číslo)"""
        rc = rc.strip().replace('/', '').replace(' ', '')
        
        # Can be 9 or 10 digits
        if len(rc) not in [9, 10] or not rc.isdigit():
            return False
        
        # For 9-digit numbers, append 0 for century
        if len(rc) == 9:
            rc = '0' + rc
        
        # Extract year, month, day, sequence
        year = int(rc[0:2])
        month = int(rc[2:4])
        day = int(rc[4:6])
        
        # Adjust month for women (50+)
        if month > 50:
            month -= 50
        elif month > 12:
            month -= 20
        
        # Validate date
        if month < 1 or month > 12:
            return False
        if day < 1 or day > 31:
            return False
        
        # Validate check digit (mod 11)
        total = sum(int(rc[i]) * (10 - i) for i in range(9))
        check = total % 11
        
        # Special case: if check is 10, the number is valid without check digit
        if check == 10:
            return len(rc) == 9  # Old format without check digit
        
        return check == int(rc[9])
    
    @staticmethod
    def crc32(data: bytes) -> int:
        """Calculate CRC-32"""
        crc = 0xFFFFFFFF
        
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0xEDB88320
                else:
                    crc >>= 1
        
        return crc ^ 0xFFFFFFFF
    
    @staticmethod
    def crc16(data: bytes) -> int:
        """Calculate CRC-16 (IBM)"""
        crc = 0x0000
        
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        
        return crc
    
    @staticmethod
    def crc8(data: bytes) -> int:
        """Calculate CRC-8"""
        crc = 0x00
        
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x07
                else:
                    crc <<= 1
                crc &= 0xFF
        
        return crc