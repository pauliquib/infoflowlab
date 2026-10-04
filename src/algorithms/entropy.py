"""
Výpočet Shannonovy entropie a souvisejících metrik.
"""

import math
from typing import Dict, List, Tuple, Union
from collections import Counter


def shannon_entropy(data: Union[str, bytes]) -> float:
    """
    Vypočítá Shannonovu entropii dat (string nebo bytes).
    H(X) = -Σ p(x) * log₂(p(x))
    """
    if not data:
        return 0.0
    
    # Počet výskytů jednotlivých symbolů
    counts = Counter(data)
    total = len(data)
    
    entropy = 0.0
    for count in counts.values():
        probability = count / total
        entropy -= probability * math.log2(probability)
    
    return entropy


def shannon_entropy_from_pmf(pmf: Dict[str, float]) -> float:
    """
    Vypočítá entropii z pravděpodobnostního rozdělení.
    pmf = {symbol: probability}
    """
    entropy = 0.0
    for prob in pmf.values():
        if prob > 0:
            entropy -= prob * math.log2(prob)
    return entropy


def max_entropy(alphabet_size: int) -> float:
    """
    Maximální entropie pro abecedu dané velikosti.
    Hmax = log₂(|Σ|)
    """
    if alphabet_size <= 0:
        return 0.0
    return math.log2(alphabet_size)


def redundancy(data: Union[str, bytes]) -> Tuple[float, float, float]:
    """
    Vrátí entropii, maximální entropii a redundanci.
    R = Hmax - H(X)
    """
    h = shannon_entropy(data)
    h_max = max_entropy(len(set(data)))
    r = h_max - h
    return h, h_max, r


def efficiency(h: float, h_max: float) -> float:
    """
    Efektivita kódování: μ = H(X) / Hmax
    
    Args:
        h: Naměřená entropie
        h_max: Maximální možná entropie pro danou abecedu
    """
    if h_max <= 0:
        return 0.0
    return h / h_max


def efficiency_from_data(data: Union[str, bytes]) -> float:
    """
    Efektivita kódování z dat: μ = H(X) / Hmax
    """
    h, h_max, _ = redundancy(data)
    if h_max == 0:
        return 0.0
    return h / h_max


def symbol_probabilities(data: Union[str, bytes]) -> Dict[str, float]:
    """Vrátí pravděpodobnosti symbolů."""
    if not data:
        return {}
    
    counts = Counter(data)
    total = len(data)
    return {str(symbol): count / total for symbol, count in counts.items()}


def information_content(symbol: str, data: Union[str, bytes]) -> float:
    """
    Informační hodnota symbolu: I(x) = -log₂(p(x))
    """
    probs = symbol_probabilities(data)
    prob = probs.get(symbol, 0)
    if prob == 0:
        return float('inf')
    return -math.log2(prob)


def joint_entropy(data_x: Union[str, bytes], data_y: Union[str, bytes]) -> float:
    """
    Společná entropie H(X,Y).
    Pro jednoduchost předpokládáme stejnou délku.
    """
    if len(data_x) != len(data_y) or len(data_x) == 0:
        return 0.0
    
    pairs = list(zip(data_x, data_y))
    counts = Counter(pairs)
    total = len(pairs)
    
    entropy = 0.0
    for count in counts.values():
        prob = count / total
        entropy -= prob * math.log2(prob)
    
    return entropy


def conditional_entropy(data_x: Union[str, bytes], data_y: Union[str, bytes]) -> float:
    """
    Podmíněná entropie H(X|Y) = H(X,Y) - H(Y)
    """
    h_xy = joint_entropy(data_x, data_y)
    h_y = shannon_entropy(data_y)
    return h_xy - h_y


def mutual_information(data_x: Union[str, bytes], data_y: Union[str, bytes]) -> float:
    """
    Vzájemná informace I(X;Y) = H(X) + H(Y) - H(X,Y)
    """
    h_x = shannon_entropy(data_x)
    h_y = shannon_entropy(data_y)
    h_xy = joint_entropy(data_x, data_y)
    return h_x + h_y - h_xy


def entropy_rate(data: Union[str, bytes], block_size: int = 1) -> float:
    """
    Entropická rychlost: H(X) / block_size
    """
    if block_size <= 0 or not data:
        return 0.0
    return shannon_entropy(data) / block_size


def demo():
    """Demo výpočtů entropie."""
    print("=== Shannonova entropie ===\n")
    
    # Příklad 1: Rovnoměrné rozdělení
    text1 = "ABCD"
    h = shannon_entropy(text1)
    h_max = max_entropy(len(set(text1)))
    print(f"Text: '{text1}'")
    print(f"  H(X) = {h:.4f} bitů")
    print(f"  Hmax = {h_max:.4f} bitů")
    print(f"  R = {h_max - h:.4f} bitů")
    print(f"  Efektivita = {efficiency(h, h_max)*100:.1f}%")
    
    # Příklad 2: Nerovnoměrné rozdělení
    text2 = "AAAABBC"
    h2 = shannon_entropy(text2)
    probs = symbol_probabilities(text2)
    print(f"\nText: '{text2}'")
    print(f"  Pravděpodobnosti: {probs}")
    print(f"  H(X) = {h2:.4f} bitů")
    print(f"  Hmax = {max_entropy(len(set(text2))):.4f} bitů")
    
    # Příklad 3: Informační hodnota
    print(f"\nInformační hodnota 'A' v '{text2}': "
          f"{information_content('A', text2):.4f} bitů")
    print(f"Informační hodnota 'C' v '{text2}': "
          f"{information_content('C', text2):.4f} bitů")
    
    # Příklad 4: Český text (přibližné pravděpodobnosti)
    czech_pmf = {
        ' ': 0.15, 'e': 0.10, 'o': 0.08, 'a': 0.07,
        'n': 0.06, 't': 0.05, 's': 0.05, 'i': 0.04,
        'r': 0.04, 'v': 0.03, 'l': 0.03, 'd': 0.03,
    }
    h_cz = shannon_entropy_from_pmf(czech_pmf)
    print(f"\nČeština (odhad):")
    print(f"  H(X) ≈ {h_cz:.4f} bitů/znak")
    print(f"  Hmax = {max_entropy(len(czech_pmf)):.4f} bitů/znak")
    
    # Příklad 5: Bytes data
    print(f"\nBytes data:")
    data_bytes = b"Hello World!"
    h_b = shannon_entropy(data_bytes)
    h_max_b = max_entropy(len(set(data_bytes)))
    print(f"  H(bytes) = {h_b:.4f} bitů")
    print(f"  Hmax = {h_max_b:.4f} bitů")
    print(f"  μ = {efficiency(h_b, h_max_b)*100:.1f}%")


if __name__ == "__main__":
    demo()