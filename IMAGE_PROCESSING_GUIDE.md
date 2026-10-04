# Pokročilé Zpracování Obrázků - Uživatelský Průvodce

## Přehled

InfoFlowLab nyní podporuje pokročilé zpracování obrázků s simulací chyb. Můžete načítat obrázky z PC, aplikovat různé typy chyb a analyzovat výsledky.

## Dostupné Nody

### 1. **Obrázek** (ImageSourceNode) - Zdroj obrázku
- **Kategorie:** Sources
- **Funkce:** Načte obrázek z vašeho počítače
- **Podporované formáty:** PNG, JPG, BMP, GIF, TIFF, WebP, atd.
- **Parametry:**
  - `Soubor obrázku` - cesta k souboru (s tlačítkem "..." pro prohlížení)

### 2. **ImageOut** (ImageOutputNode) - Výstup obrázku
- **Kategorie:** Sinks
- **Funkce:** Zobrazí metadata a náhled obrázku
- **Zobrazuje:**
  - Rozměry obrázku (šířka × výška)
  - Formát obrázku
  - **Náhled obrázku** v Inspectoru

### 3. **BlockLoss** (ImageBlockLossNode) - Ztráta bloků
- **Kategorie:** Channels
- **Funkce:** Simuluje ztrátu celých bloků pixelů (jako JPEG artefakty)
- **Parametry:**
  - `Block Size` (8-64px) - velikost bloků
  - `Loss Prob` (0-1) - pravděpodobnost ztráty bloku
  - `Replace With` - co nahradit ztracené bloky:
    - `black` - černá
    - `white` - bílá
    - `gray` - šedá
    - `noise` - náhodný šum

### 4. **Transform** (ImageTransformNode) - Transformace
- **Kategorie:** Signal
- **Funkce:** Aplikuje transformace a poškození
- **Parametry:**
  - `Rotation` (0, 90, 180, 270) - rotace
  - `Flip Horizontal` - převrácení vodorovně
  - `Flip Vertical` - převrácení svisle
  - `Crop %` (0-50%) - ořazení z každé strany
  - `Noise` (0-100) - přidání náhodného šumu

### 5. **Compare** (ImageComparatorNode) - Porovnání
- **Kategorie:** Analyzers
- **Funkce:** Porovná dva obrázky a vypočítá rozdíly
- **Parametry:**
  - `Show Diff` - zobrazit rozdílový obrázek
- **Výstupní metriky:**
  - MSE (Mean Squared Error)
  - PSNR (Peak Signal-to-Noise Ratio) v dB
  - Procentuální rozdíl

## Jak Používat - Příklady Flow

### Příklad 1: Základní načtení a zobrazení

```
Obrázek (source) → ImageOut (sink)
```

**Postup:**
1. Přetáhněte "Obrázek" z Sources na plátno
2. Přetáhněte "ImageOut" z Sinks na plátno
3. Propojte výstup "Obrázek" → vstup "ImageOut"
4. Klikněte na "Obrázek" uzél
5. V Inspectoru klikněte "..." u "Soubor obrázku"
6. Vyberte obrázek z PC
7. Spusťte simulaci
8. V ImageOut uvidíte náhled obrázku

### Příklad 2: Simulace bitových chyb (pomocí BSK kanálu)

```
Obrázek (source) → BSK kanál (p=0.05) → ImageOut (sink)
```

**Postup:**
1. Přetáhněte "Obrázek" a vyberte soubor
2. Přetáhněte "BSK" z Channels
3. Přetáhněte "ImageOut"
4. Propojte: Obrázek → BSK → ImageOut
5. Klikněte na BSK:
   - `Error Prob`: 0.05 (5% chybovost)
   - `Latency`: 10ms
6. Spusťte simulaci
7. ImageOut zobrazí poškozený obrázek

### Příklad 3: Simulace blokových chyb (JPEG-like artefakty)

```
Obrázek (source) → BlockLoss (block_size=16, loss_prob=0.2) → ImageOut
```

**Postup:**
1. Přetáhněte "Obrázek" a vyberte soubor
2. Přetáhněte "BlockLoss" z Channels
3. Přetáhněte "ImageOut"
4. Propojte: Obrázek → BlockLoss → ImageOut
5. Klikněte na BlockLoss:
   - `Block Size`: 16 (velikost bloků 16×16 px)
   - `Loss Prob`: 0.2 (20% pravděpodobnost ztráty)
   - `Replace With`: "black" nebo "noise"
6. Spusťte simulaci
7. ImageOut zobrazí obrázek s čtverečkovými artefakty

### Příklad 4: Komplexní poškození (transformace + šum)

```
Obrázek (source) → Transform (rotace + šum) → ImageOut
```

**Postup:**
1. Přetáhněte "Obrázek" a vyberte soubor
2. Přetáhněte "Transform" z Signal
3. Přetáhněte "ImageOut"
4. Propojte: Obrázek → Transform → ImageOut
5. Klikněte na Transform:
   - `Rotation`: 90 (otočení o 90°)
   - `Flip Horizontal`: zaškrtnout
   - `Noise`: 30 (přidat šum)
6. Spusťte simulaci
7. ImageOut zobrazí transformovaný obrázek

### Příklad 5: Kompletní research flow - Porovnání kanálů

```
                    ┌→ BSK (p=0.01) → BER Meter → Compare
Obrázek (source) →┤
                    └→ AWGN (SNR=20dB) → BER Meter → Compare
                                                      ↓
                                                ImageOut + TextOut
```

**Postup:**
1. Vytvořte flow podle diagramu
2. Spusťte simulaci
3. Porovnání ukáže rozdíly mezi kanály
4. ImageOut zobrazí výsledný obrázek
5. TextOut zobrazí metriky

### Příklad 6: Analýza kvality - PSNR měření

```
Obrázek (source) → [Transform/BlockLoss] → Compare → ImageOut
                      ↑
                Originál (druhý vstup)
```

**Postup:**
1. Přetáhněte dva "Obrázek" uzly
2. Oba vyberte stejný soubor (originál)
3. Přetáhněte "Transform" nebo "BlockLoss"
4. Přetáhněte "Compare"
5. Přetáhněte "ImageOut"
6. Propojte:
   - Obrázek 1 → Compare (in_a)
   - Obrázek 1 → Transform → Compare (in_b)
   - Compare → ImageOut
7. Spusťte simulaci
8. Compare vypočítá MSE, PSNR a rozdíly

## Tipy pro Simulaci Chyb

### 1. Postupné zhoršování
Otestujte různé úrovně chyb:
```
Obrázek → BSK (p=0.01) → ImageOut
Obrázek → BSK (p=0.05) → ImageOut
Obrázek → BSK (p=0.10) → ImageOut
Obrázek → BSK (p=0.20) → ImageOut
```

### 2. Porovnání typů chyb
```
Obrázek → BSK (random chyby) → Compare
Obrázek → BlockLoss (blokové chyby) → Compare
```

### 3. Scan SNR úrovní
```
Obrázek → AWGN (SNR=10dB) → ImageOut
Obrázek → AWGN (SNR=20dB) → ImageOut
Obrázek → AWGN (SNR=30dB) → ImageOut
Obrázek → AWGN (SNR=40dB) → ImageOut
```

### 4. Kombinace chyb
```
Obrázek → BlockLoss (p=0.1) → Transform (noise=20) → AWGN (SNR=25dB) → ImageOut
```

## Vysvětlení Metrik

### MSE (Mean Squared Error)
- **Co je:** Průměr kvadratické chyby mezi pixely
- **Rozsah:** 0 (žádná chyba) → ∞ (velká chyba)
- **Interpretace:** Nižší = lepší kvalita

### PSNR (Peak Signal-to-Noise Ratio)
- **Co je:** Poměr signálu k šumu v dB
- **Rozsah:** ∞ (perfektní) → 0 (katastrofa)
- **Interpretace:**
  - > 40 dB: Výborná kvalita
  - 30-40 dB: Dobrá kvalita
  - 20-30 dB: Střední kvalita
  - < 20 dB: Špatná kvalita

### BER (Bit Error Rate)
- **Co je:** Podíl chybných bitů
- **Rozsah:** 0% → 100%
- **Interpretace:** Nižší = lepší

## Omezení a Poznámky

1. **Velikost obrázků:** Pro velké obrázky (>4K) může být zpracování pomalé
2. **Paměť:** Všechny obrázky jsou ukládány jako PNG v paměti
3. **Kvalita:** Při kompresi může dojít ke ztrátě kvality
4. **Preview:** Náhled v Inspectoru je maximálně 250px

## Řešení Problémů

### Obrázek se nenačítá
- Zkontrolujte cestu k souboru
- Ujistěte se, že formát je podporován (PNG, JPG, BMP, GIF)
- Zkontrolujte, zda soubor není poškozený

### Náhled se nezobrazuje
- Ujistěte se, že ImageOut má vstupní data
- Zkontrolujte, zda obrázek není poškozený
- Zkuste obnovit Inspector (klikněte jinam a zpět)

### Chyby v simulaci
- Zkontrolujte konzoli pro detaily chyby
- Ujistěte se, že jsou všechny uzly správně propojeny
- Zkontrolujte parametry kanálů (např. error_prob < 1.0)

## Budoucí Vylepšení

- [ ] Podpora více formátů výstupu (JPEG, WebP)
- [ ] Histogram a analýza frekvencí
- [ ] Pokročilé filtry (Gaussian blur, edge detection)
- [ ] Batch processing pro více obrázků
- [ ] Uložení výsledků přímo z ImageOut
- [ ] Video podpora (frame-by-frame processing)