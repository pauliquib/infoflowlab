"""
Modul pro převody mezi číselnými soustavami.
Podporuje: binární, oktalovou, dekadickou, hexadecimální.
Plus doplňkové kódy.
"""

from typing import Tuple, Optional
import math


class NumberConverter:
    """Převodník mezi číselnými soustavami."""
    
    DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    
    @classmethod
    def to_decimal(cls, number_str: str, base: int) -> int:
        """Převede číslo z libovolné soustavy do dekadické."""
        number_str = number_str.strip().upper()
        if not number_str:
            return 0
        
        result = 0
        is_negative = number_str.startswith('-')
        if is_negative:
            number_str = number_str[1:]
        
        for char in number_str:
            if char not in cls.DIGITS[:base]:
                raise ValueError(f"Neplatný znak '{char}' pro základ {base}")
            result = result * base + cls.DIGITS.index(char)
        
        return -result if is_negative else result
    
    @classmethod
    def from_decimal(cls, number: int, base: int) -> str:
        """Převede dekadické číslo do libovolné soustavy."""
        if number == 0:
            return "0"
        
        is_negative = number < 0
        number = abs(number)
        result = ""
        
        while number > 0:
            result = cls.DIGITS[number % base] + result
            number //= base
        
        return "-" + result if is_negative else result
    
    @classmethod
    def convert(cls, number_str: str, from_base: int, to_base: int) -> str:
        """Převede číslo mezi dvěma soustavami."""
        decimal = cls.to_decimal(number_str, from_base)
        return cls.from_decimal(decimal, to_base)
    
    @classmethod
    def to_binary_string(cls, number: int, bits: int = 8) -> str:
        """Převede číslo na binární řetězec s pevnou délkou."""
        if number < 0:
            # Doplňkový kód pro záporná čísla
            number = (1 << bits) + number
        
        binary = bin(number)[2:]
        return binary.zfill(bits)[-bits:]
    
    @classmethod
    def from_binary_string(cls, binary_str: str, signed: bool = False) -> int:
        """Převede binární řetězec na číslo."""
        if not binary_str:
            return 0
        
        if signed and binary_str[0] == '1':
            # Záporné číslo v doplňkovém kódu
            inverted = ''.join('1' if b == '0' else '0' for b in binary_str)
            return -(int(inverted, 2) + 1)
        
        return int(binary_str, 2)
    
    @classmethod
    def to_complement(cls, number: int, bits: int = 8) -> str:
        """Vrátí doplňkový kód (two's complement) čísla."""
        return cls.to_binary_string(number, bits)
    
    @classmethod
    def get_place_values(cls, number_str: str, base: int) -> list:
        """Vrátí váhy pozic pro vizualizaci."""
        number_str = number_str.strip().upper()
        if number_str.startswith('-'):
            number_str = number_str[1:]
        
        values = []
        length = len(number_str)
        for i, char in enumerate(number_str):
            digit_value = cls.DIGITS.index(char)
            place_value = base ** (length - 1 - i)
            values.append({
                'digit': char,
                'value': digit_value,
                'place': length - 1 - i,
                'place_value': place_value,
                'total': digit_value * place_value
            })
        return values
    
    @classmethod
    def fractional_convert(cls, number: float, to_base: int, precision: int = 10) -> str:
        """Převede desetinnou část do jiné soustavy."""
        if number == 0:
            return "0"
        
        result = ""
        frac = abs(number) - int(abs(number))
        
        for _ in range(precision):
            frac *= to_base
            digit = int(frac)
            result += cls.DIGITS[digit]
            frac -= digit
            if frac == 0:
                break
        
        return result


def demo():
    """Demo převodů."""
    print("=== Převody číselných soustav ===")
    
    # 255₁₀ → různé soustavy
    num = 255
    print(f"{num}₁₀ = {NumberConverter.from_decimal(num, 2)}₂")
    print(f"{num}₁₀ = {NumberConverter.from_decimal(num, 8)}₈")
    print(f"{num}₁₀ = {NumberConverter.from_decimal(num, 16)}₁₆")
    
    # Zpětný převod
    hex_num = "FF"
    dec = NumberConverter.to_decimal(hex_num, 16)
    print(f"{hex_num}₁₆ = {dec}₁₀")
    
    # Doplňkový kód
    print(f"\n-5 v 8-bit doplňkovém kódu: {NumberConverter.to_complement(-5, 8)}")
    
    # Váhy pozic
    print("\nVáhy pozic pro 174₈:")
    for v in NumberConverter.get_place_values("174", 8):
        print(f"  {v['digit']} × {8}^{v['place']} = {v['total']}")


if __name__ == "__main__":
    demo()