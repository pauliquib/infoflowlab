# Nápověda: Propojování prvků v InfoFlowLab

> **Kompletní návod** jak různě propojovat prvky a čeho při různých kombinacích můžete dosáhnout.

---

## Obsah

1. [Základy propojování](#základy-propojování)
2. [Typy dat a kompatibilita](#typy-dat-a-kompatibilita)
3. [Katalog prvků a jejich porty](#katalog-prvků-a-jejich-porty)
4. [Užitečné kombinace](#užitečné-kombinace)
5. [Příklady scénářů](#příklady-scénářů)
6. [Tipy a triky](#tipy-a-triky)
7. [Řešení problémů](#řešení-problémů)

---

## 1. Základy propojování

### 1.1 Jak propojit dva prvky

```
┌─────────────┐         ┌─────────────┐
│   Prvek A   │────────▶│   Prvek B   │
│  (výstup)   │  linka  │  (vstup)    │
└─────────────┘         └─────────────┘
     output    ───────▶    input
```

**Postup:**
1. **Klikněte na výstupní port** (kolečko na pravé straně prvku) - obarví se žlutě
2. **Táhněte myší** - vytvoří se přechodová křivka (Bézierova křivka)
3. **Uvolněte na vstupním portu** (kolečko na levé straně cílového prvku) - propojení je hotové
4. **Stiskněte Escape** nebo klikněte jinam pro zrušení

### 1.2 Pravidla propojování

| Pravidlo | Popis | Příklad |
|----------|-------|---------|
| **Směr** | Vždy `output → input` | Výstup zdroje → Vstup kompresoru |
| **Žádné smyčky** | Nemůžete propojit prvek sám se sebou | Node A → Node A ❌ |
| **Jeden vstup** | Vstupní port může mít jen jednu spojení | Node A → Node B (nelze Node A → Node B a zároveň Node C → Node B) |
| **Více výstupů** | Výstupní port může mít mnoho spojení | Node A → Node B, Node A → Node C ✓ |
| **Kompatibilita dat** | Porty musí být kompatibilní (viz sekce 2) | TEXT → BINARY ✓, AUDIO → TEXT ❌ |

### 1.3 Odpojení a přepojení

**Odpojení:**
- Vyberte spojení (klikněte na linku)
- Stiskněte **Delete** nebo **Backspace**
- Nebo použijte kontextové menu (pravý klik)

**Přepojení:**
- Klikněte na existující spojení
- Táhněte na nový cíl
- Staré spojení se automaticky odstraní

---

## 2. Typy dat a kompatibilita

### 2.1 Dostupné datové typy

| Typ | Zkratka | Popis | Příklady |
|-----|---------|-------|----------|
| **BINARY** | `BIN` | Čistá binární data (bytes) | Komprimovaná data, šifrový text |
| **TEXT** | `TXT` | Textová data (UTF-8/ASCII) | "Hello World", čísla v textové podobě |
| **AUDIO** | `AUD` | Zvuková data | WAV, MP3, sinusoida |
| **IMAGE** | `IMG` | Obrázková data | PNG, JPEG, pixely |
| **NUMERIC** | `NUM` | Číselná data | "255", "10110" (číslo v soustavě) |
| **MORSE** | `MOR` | Morseův kód | ".- -... -.-." |
| **HUFFMAN** | `HUF` | Huffmanovo kódování | Binární řetězec s kódovou tabulkou |
| **BASE64** | `B64` | Base64 kódování | "SGVsbG8=" |
| **HEX** | `HEX` | Hexadecimální kódování | "48656C6C6F" |
| **ANY** | `ANY` | Kompatibilní s čímkoli | Kanály, analyzátory |

### 2.2 Maticí kompatibility

```
         │ BIN │ TXT │ AUD │ IMG │ NUM │ MOR │ HUF │ B64 │ HEX │ ANY
─────────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────
BIN      │  ✓  │  ✓  │  ✗  │  ✗  │  ✓  │  ✗  │  ✗  │  ✓  │  ✓  │  ✓
TXT      │  ✓  │  ✓  │  ✗  │  ✗  │  ✓  │  ✓  │  ✓  │  ✗  │  ✗  │  ✓
AUD      │  ✗  │  ✗  │  ✓  │  ✗  │  ✗  │  ✗  │  ✗  │  ✗  │  ✗  │  ✓
IMG      │  ✗  │  ✗  │  ✗  │  ✓  │  ✗  │  ✗  │  ✗  │  ✗  │  ✗  │  ✓
NUM      │  ✓  │  ✓  │  ✗  │  ✗  │  ✓  │  ✗  │  ✗  │  ✗  │  ✗  │  ✓
MOR      │  ✗  │  ✓  │  ✗  │  ✗  │  ✗  │  ✓  │  ✗  │  ✗  │  ✗  │  ✓
HUF      │  ✗  │  ✓  │  ✗  │  ✗  │  ✗  │  ✗  │  ✓  │  ✗  │  ✗  │  ✓
B64      │  ✓  │  ✗  │  ✗  │  ✗  │  ✗  │  ✗  │  ✗  │  ✓  │  ✗  │  ✓
HEX      │  ✓  │  ✗  │  ✗  │  ✗  │  ✗  │  ✗  │  ✗  │  ✗  │  ✓  │  ✓
ANY      │  ✓  │  ✓  │  ✓  │  ✓  │  ✓  │  ✓  │  ✓  │  ✓  │  ✓  │  ✓
```

**Vysvětlení:**
- **TEXT ↔ BINARY**: Kompatibilní (UTF-8 kódování/dekódování)
- **NUMERIC ↔ TEXT/BINARY**: Čísla lze převést na text a zpět
- **Všechny → ANY**: Prvky s portem ANY přijímají cokoli
- **Ostatní**: Nejsou přímo kompatibilní (vyžadují konverzi)

---

## 3. Katalog prvků a jejich porty

### 3.1 Zdroje dat (Sources)

| Ikona | Název | Výstup | Popis |
|-------|-------|--------|-------|
| 📝 | **Textový editor** | `TEXT` | Zadejte libovolný text |
| 🎲 | **Náhodný generátor** | `BINARY` | Generuje data s nastavitelnou entropií |
| 🔢 | **Číslo** | `NUMERIC` | Číslo v libovolné soustavě (2-36) |
| 🎵 | **Audio** | `AUDIO` | Zvuková data (testovací tón) |
| 🖼️ | **Obrázek** | `IMAGE` | Testovací obrázek (gradient) |

**Vstupy:** Žádné (zdrojové prvky nemají vstupy)

### 3.2 Kódování (Encoders)

| Ikona | Název | Vstup | Výstup | Popis |
|-------|-------|-------|--------|-------|
| 🔀 | **BaseConv** | `NUMERIC` | `TEXT` | Převod mezi číslenými soustavami (2-36) |
| 🔤 | **UTF-8 Enc** | `TEXT` | `BINARY` | Zakóduje text do UTF-8 bytů |
| 📻 | **Morse** | `TEXT` | `MORSE` | Zakóduje text do Morseovy abecedy |
| 🌳 | **HuffmanEnc** | `TEXT` | `HUFFMAN` | Huffmanovo kódování s kompresí |
| 🔐 | **Base64** | `BINARY` | `BASE64` | Base64 kódování |
| 🔢 | **Hex** | `BINARY` | `HEX` | Hexadecimální kódování |

### 3.3 Dekódování (Decoders)

| Ikona | Název | Vstup | Výstup | Popis |
|-------|-------|-------|--------|-------|
| 📻 | **MorseDec** | `MORSE` | `TEXT` | Dekóduje Morseův kód |
| 🔤 | **UTF-8Dec** | `BINARY` | `TEXT` | Dekóduje UTF-8 byty |
| 🔐 | **Base64Dec** | `BASE64` | `BINARY` | Dekóduje Base64 |
| 🌳 | **HuffmanDec** | `HUFFMAN` | `TEXT` | Dekóduje Huffmanovo kódování |

### 3.4 Komprese (Compressors)

| Ikona | Název | Vstup | Výstup | Popis |
|-------|-------|-------|--------|-------|
| 📏 | **RLE** | `BINARY` | `BINARY` | Run-Length Encoding (komprese/dekomprese) |
| 🗜️ | **LZ77** | `BINARY` | `BINARY` | LZ77 s nastavitelným oknem |
| 🗜️ | **LZW** | `BINARY` | `BINARY` | LZW slovníková komprese |
| 🌳 | **Huffman** | `BINARY` | `BINARY` | Huffmanova komprese |

**Poznámka:** Kompresory mají parametr `mode` (compress/decompress) u RLE, u ostatních je vždy komprese.

### 3.5 Kanály (Channels)

| Ikona | Název | Vstup | Výstup | Popis |
|-------|-------|-------|--------|-------|
| 🔌 | **Ideal** | `ANY` | `ANY` | Ideální kanál (pouze latence) |
| 📡 | **BSK** | `ANY` | `ANY` | Binární symetrický kanál (šum) |
| 📡 | **Gilbert-Elliott** | `ANY` | `ANY` | Kanál s nárazy chyb |
| 📡 | **AWGN** | `ANY` | `ANY` | Kanál s Gaussovým šumem |

**Vlastnosti kanálů:**
- **Ideal**: Žádné chyby, nastavitelná latence
- **BSK**: Náhodné bitové chyby (parametr `error_prob`)
- **Gilbert-Elliott**: Nárazové chyby (dva stavy: dobrý/špatný)
- **AWGN**: Šum podle SNR (pouze pro float data)

### 3.6 Oprava chyb (ECC)

| Ikona | Název | Vstup | Výstup | Popis |
|-------|-------|-------|--------|-------|
| 🔴 | **Hamming(7,4)** | `BINARY` | `BINARY` | Kódování/dekódování Hamming(7,4) |
| 🔴 | **Hamming(15,11)** | `BINARY` | `BINARY` | Kódování/dekódování Hamming(15,11) |
| 🔴 | **CRC-8** | `BINARY` | `BINARY` | Kontrolní součet CRC-8 |
| 🔴 | **CRC-16** | `BINARY` | `BINARY` | Kontrolní součet CRC-16 |
| 🔴 | **CRC-32** | `BINARY` | `BINARY` | Kontrolní součet CRC-32 |
| 🔴 | **ParityEnc** | `BINARY` | `BINARY` | Parnostní bity (sudá/lichá) |
| 🔴 | **ParityDec** | `BINARY` | `BINARY` | Kontrola parnosti |
| 🔴 | **RS Enc** | `BINARY` | `BINARY` | Reed-Solomon kódování |
| 🔴 | **RS Dec** | `BINARY` | `BINARY` | Reed-Solomon dekódování |

### 3.7 Analyzátory (Analyzers)

| Ikona | Název | Vstup | Výstup | Popis |
|-------|-------|-------|--------|-------|
| 📊 | **Entropie** | `ANY` | `ANY` | Měření Shannonovy entropie |
| 📈 | **Histogram** | `ANY` | `ANY` | Frekvenční histogram symbolů |
| 📊 | **CompRatio** | `ANY` | `ANY` | Měření kompresního poměru |
| 📊 | **BER Meter** | `ANY` | `ANY` | Měření bitové chybovosti |
| ⏱️ | **LatencyMeter** | `ANY` | `ANY` | Měření zpoždění |

**Vlastnost:** Analyzátory nezmění data, pouze přidají metriky do historie paketu.

---

## 4. Užitečné kombinace

### 4.1 Základní toky dat

#### A) Text → Komprese → Kanál → Dekomprese → Text

```
📝 Text ──→ 🌳 HuffmanEnc ──→ 📡 BSK ──→ 🌳 HuffmanDec ──→ 📝 Text
   │              │                  │                │              │
   │              │                  │                │              │
   └──────────────┴──────────────────┴────────────────┴──────────────┘
                      Kompletní komunikační řetězec
```

**Co se stane:**
1. Text se zakóduje Huffmanovým kódem (komprese)
2. Data projdou BSK kanálem (náhodné chyby)
3. Huffmanovo kódování se dekóduje
4. Opět získáte původní text (možná s chybami)

**Co můžete pozorovat:**
- Kompresní poměr (např. 2.5:1)
- Počet chyb před a po opravě
- Entropii před/po kompresi

#### B) Číslo → Převod soustavy → Zobrazení

```
🔢 Číslo (255₁₀) ──→ 🔀 BaseConv (10→2) ──→ 📊 Analyzátor
   │                      │
   │                      └── Výstup: "11111111₂"
   │
   └── Parametry: value=255, base=10
```

**Co se stane:**
- Číslo 255 v desítkové soustavě se převede na binární
- Výstup: "11111111" (8 bitů)

**Možné varianty:**
- 10 → 2 (desítková → binární)
- 10 → 8 (desítková → osmičková)
- 10 → 16 (desítková → hexadecimální)
- 2 → 16 (binární → hexadecimální)

#### C) Text → Morseovka → Zpět na text

```
📝 "SOS" ──→ 📻 Morse ──→ 📻 MorseDec ──→ 📝 "SOS"
   │            │                │
   │            └── "... --- ..."│
   │                             │
   └── Parametry: text="SOS"     └── Výstup: "SOS"
```

**Co se stane:**
- Text se převede na Morseovy tečky a čárky
- Pak se znovu převede zpět na text
- Můžete pozorovat, jak se zvyšuje délka dat

### 4.2 Kompresní řetězce

#### D) Víceúrovňová komprese

```
📝 Text ──→ 📏 RLE ──→ 🗜️ LZ77 ──→ 🌳 Huffman ──→ 📊 CompRatio
   │           │            │              │
   │           │            │              └── Výstup: komprimovaná data
   │           │            └── Dále komprimuje
   │           └── První komprese
   │
   └── "AAAAABBBCCCC" (40 bytů)
```

**Co se stane:**
1. RLE: "A5B3C4" (8 bytů) - opakující se sekvence
2. LZ77: Další komprese pomocí slovníku
3. Huffman: Frekvenční komprese
4. Celkový poměr: ~10:1 nebo lepší

**Poznámka:** Každá komprese přidává overhead, pro malá data nemusí být výhodné.

#### E) Komprese + ECC (oprava chyb)

```
📝 Text ──→ 🌳 Huffman ──→ 🔴 Hamming(7,4) ──→ 📡 BSK ──→ 🔴 HammingDec ──→ 🌳 HuffmanDec ──→ 📝 Text
   │              │                  │                │                  │                │
   │              │                  │                │                  │                │
   └──────────────┴──────────────────┴────────────────┴──────────────────┴────────────────┘
                    Komprese + ochrana proti chybám + dekomprese
```

**Co se stane:**
1. Text se komprimuje (Huffman)
2. Přidá se ochrana proti chybám (Hamming)
3. Data projdou šumovým kanálem
4. Chyby se opraví (Hamming dokáže opravit 1 bit na 7)
5. Data se dekomprimují

**Výhoda:** Kombinace komprese + ECC je velmi účinná pro přenos přes šumové kanály.

### 4.3 Analýza a měření

#### F) Srovnání kompresních algoritmů

```
📝 Text ──┬─→ 📏 RLE ──→ 📊 CompRatio ──→ 📊 Entropie
          │
          ├─→ 🗜️ LZ77 ──→ 📊 CompRatio ──→ 📊 Entropie
          │
          └─→ 🌳 Huffman ──→ 📊 CompRatio ──→ 📊 Entropie
```

**Co se stane:**
- Stejný vstup projde třemi různými kompresory
- Každý z nich měří vlastní kompresní poměr
- Porovnáte efektivitu algoritmů

**Co pozorovat:**
- RLE: Dobré pro opakující se data (AAAAAA)
- LZ77: Dobré pro text s opakujícími se vzory
- Huffman: Dobré pro data s nerovnoměrnou frekvencí

#### G) Měření kvality kanálu

```
🎲 Random ──→ 📡 BSK ──→ 📊 BER Meter ──→ 📊 LatencyMeter
   │              │
   │              └── Parametry: error_prob=0.1
   │
   └── Parametry: entropy_target=4.0
```

**Co se stane:**
- Generují se náhodná data
- Projdou BSK kanálem s 10% chybovostí
- BER Meter počítá celkovou chybovost
- LatencyMeter měří zpoždění

**Použití:** Můžete experimentovat s různými hodnotami `error_prob` a sledovat, jak se mění BER.

### 4.4 Komplexní scénáře

#### H) Kompletní komunikační řetězec

```
📝 "Hello" ──→ 🔤 UTF-8Enc ──→ 🌳 Huffman ──→ 🔴 Hamming(7,4) ──→ 📡 BSK ──→ 🔴 HammingDec ──→ 🌳 HuffmanDec ──→ 🔤 UTF-8Dec ──→ 📝 Výstup
   │                │                │                  │                │                  │                │                │
   │                │                │                  │                │                  │                │                │
   └────────────────┴────────────────┴──────────────────┴────────────────┴──────────────────┴────────────────┴────────────────┘
                         Komprese + ECC + Kanál + Oprava + Dekomprese
```

**Postup transformace:**
1. **Text** → UTF-8 kódování → **BINARY** (40 bitů)
2. **BINARY** → Huffman komprese → **HUFFMAN** (25 bitů, poměr 1.6:1)
3. **HUFFMAN** → Hamming kódování → **BINARY** (35 bitů, přidáno 10 bitů ECC)
4. **BINARY** → BSK kanál (p=0.05) → **BINARY** (možná s chybami)
5. **BINARY** → Hamming dekódování → **BINARY** (opraveny chyby)
6. **BINARY** → Huffman dekomprese → **BINARY** (40 bitů)
7. **BINARY** → UTF-8 dekódování → **TEXT** ("Hello")

**Co můžete měřit:**
- Kompresní poměr na každé úrovni
- Počet detekovaných a opravených chyb
- Celkové zpoždění
- Úspěšnost přenosu (BER před/po ECC)

#### I) Historická komunikace

```
📝 "SOS" ──┬─→ 📻 Morse ──→ 📊 Entropie
           │
           ├─→ 🔤 UTF-8 ──→ 📡 Ideal ──→ 📊 LatencyMeter
           │
           └─→ 🔤 UTF-8 ──→ 📡 BSK ──→ 📊 BER Meter
```

**Co se stane:**
- Porovnání různých komunikačních kanálů
- Morseovka: vysoká entropie (mnoho symbolů)
- Ideální kanál: nulové chyby, nastavitelná latence
- BSK kanál: náhodné chyby

**Vzdělávací hodnota:** Studenté vidí, jak se liší efektivita historických vs. moderních kanálů.

---

## 5. Příklady scénářů

### 5.1 Scénář: Procvičení převodů soustav

**Cíl:** Naučit se převádět mezi číslenými soustavami.

```
🔢 Číslo ──→ 🔀 BaseConv ──→ 📊 Analyzátor
```

**Kroky:**
1. Přetáhněte **🔢 Číslo** na plátno
2. Nastavte: `value=255`, `base=10`
3. Přetáhněte **🔀 BaseConv**
4. Nastavte: `from_base=10`, `to_base=2`
5. Propojte je
6. Spusťte simulaci

**Výsledek:** Číslo 255 se převede na "11111111" (binární)

**Experimenty:**
- Zkuste 10 → 8 (255 → "377")
- Zkuste 2 → 16 ("11111111" → "FF")
- Zkuste 16 → 10 ("FF" → "255")

### 5.2 Scénář: Porozumění entropii

**Cíl:** Pochopit, co je Shannonova entropie.

```
🎲 Random ──┬─→ 📊 Entropie
            │
            └── Parametry: entropy_target=0.0 (nízká entropie)
```

**Kroky:**
1. Přetáhněte **🎲 Random**
2. Nastavte: `entropy_target=0.0` (všechna "A")
3. Přetáhněte **📊 Entropie**
4. Propojte a spusťte

**Výsledek:** H(X) ≈ 0.0 bitů (všechna data stejná)

**Experimenty:**
- `entropy_target=8.0` (náhodná data) → H(X) ≈ 8.0 bitů
- `entropy_target=4.0` (písmena a číslice) → H(X) ≈ 5.5 bitů

### 5.3 Scénář: Komprese vs. nekomprese

**Cíl:** Porovnat velikost před a po kompresi.

```
📝 Text ──┬─→ 📊 CompRatio (přímá cesta)
          │
          └─→ 🌳 Huffman ──→ 📊 CompRatio (komprese)
```

**Kroky:**
1. Vytvořte text: "AAAAABBBCCCCAAADD"
2. Propojte přímo na CompRatio → uvidíte původní velikost
3. Přidejte Huffman kompresor mezi
4. Porovnáte poměry

**Výsledek:**
- Původní: 17 bytů
- Komprimovaná: ~8 bytů (poměr ~2:1)

**Poznámka:** Čím více opakujících se sekvencí, tím lepší komprese.

### 5.4 Scénář: Chyby v komunikaci

**Cíl:** Pochopit, jak funguje oprava chyb.

```
📝 Text ──→ 🔤 UTF-8 ──→ 🔴 Hamming(7,4) ──→ 📡 BSK ──→ 🔴 HammingDec ──→ 📊 BER Meter
```

**Kroky:**
1. Vytvořte text: "Test"
2. Přidejte UTF-8 encoder
3. Přidejte Hamming(7,4) encoder
4. Přidejte BSK kanál s `error_prob=0.1` (10% chyb)
5. Přidejte Hamming(7,4) decoder
6. Přidejte BER Meter

**Výsledek:**
- Hamming kód přidá redundantní bity
- BSK způsobí ~10% chyb
- Hamming opraví většinu chyb (1 bit na 7)
- BER po opravě bude mnohem nižší

**Experimenty:**
- Zvyšte `error_prob` na 0.3 → Hamming už neopraví všechny chyby
- Použijte Hamming(15,11) → lepší oprava, více redundantních bitů

### 5.5 Scénář: Měření latence

**Cíl:** Porozumět zpoždění v komunikačních kanálech.

```
📝 Text ──┬─→ 🔌 Ideal ──→ ⏱️ LatencyMeter
          │     (latency=100ms)
          │
          └─→ 📡 BSK ──→ ⏱️ LatencyMeter
                (latency=50ms)
```

**Kroky:**
1. Vytvořte dva paralelní řetězce
2. První: Ideal kanál s `latency_ms=100`
3. Druhý: BSK kanál s `latency_ms=50`
4. Oba propojte na LatencyMeter

**Výsledek:**
- Ideal: ~100ms zpoždění
- BSK: ~50ms zpoždění + čas na zpracování šumu

**Poučení:** Latence není jen o fyzickém přenosu, ale i o zpracování.

---

## 6. Tipy a triky

### 6.1 Rychlé propojování

**Tip:** Můžete táhnout z výstupu na vstup i naopak. Systém automaticky rozpozná směr.

```
Výstup ──→ Vstup  (správně)
Vstup ◀── Výstup  (také správně, systém otočí)
```

### 6.2 Paralelní zpracování

```
📝 Text1 ──→ 🌳 Huffman ──→ 📊 CompRatio
📝 Text2 ──→ 🌳 Huffman ──→ 📊 CompRatio
📝 Text3 ──→ 🌳 Huffman ──→ 📊 CompRatio
```

**Výhoda:** Můžete porovnávat různé vstupy nebo algoritmy současně.

### 6.3 Zřetězení analyzátorů

```
📝 Text ──→ 🌳 Huffman ──→ 📊 CompRatio ──→ 📊 Entropie ──→ 📊 Histogram
```

**Výhoda:** Každý analyzátor přidá další metriky do historie paketu.

### 6.4 Použití parametrů

**Tip:** Mnoho prvků má nastavitelné parametry. Klikněte na prvek pro otevření panelu vlastností.

**Užitečné parametry:**
- **BSK kanál**: `error_prob` (0.0 - 1.0) - pravděpodobnost chyby
- **LZ77**: `window_size` (128 - 32768) - velikost vyhledávacího okna
- **Huffman**: Automaticky vypočítá optimální kódy
- **BaseConv**: `from_base`, `to_base` (2 - 36)

### 6.5 Znovupoužitelnost

**Tip:** Pokud máte složitý řetězec, který chcete použít vícekrát:
1. Uložte scénář (File → Save)
2. Načtěte ho znovu (File → Load)
3. Nebo zkopírujte skupinu prvků (Ctrl+C, Ctrl+V)

---

## 7. Řešení problémů

### 7.1 Nemůžu propojit dva prvky

**Příčiny:**
1. **Nekompatibilní datové typy** - zkontrolujte barvy portů
   - Šedý = ANY (kompatibilní s čímkoli)
   - Modrý = TEXT
   - Zelený = BINARY
   - atd.

2. **Už je spojení** - vstupní port může mít jen jedno spojení
   - Řešení: Odpojte staré spojení (Delete) nebo použijte jiný port

3. **Smyčka** - nemůžete propojit prvek sám se sebou

**Řešení:**
- Klikněte na port pro zobrazení tooltipu s důvodem
- Zkontrolujte typy dat v panelu vlastností

### 7.2 Spojení se neobjeví

**Příčiny:**
1. Oba prvky nejsou na plátně
2. Porty jsou skryté (přiblížili jste se příliš)
3. Chyba v validaci

**Řešení:**
- Přiblížte/oddalte pohled (scroll nebo Ctrl+scroll)
- Zkontrolujte konzoli pro chyby
- Zkuste obnovit spojení (odpojte a znovu propojte)

### 7.3 Simulace nefunguje

**Příčiny:**
1. Chybí vstupní zdroj
2. Prvky nejsou propojené
3. Chyba v algoritmu

**Řešení:**
- Zkontrolujte, že máte zdroj (📝, 🎲, atd.)
- Zkontrolujte spojení (červená = chyba, zelená = OK)
- Podívejte se do konzole na chybové hlášky

### 7.4 Výsledek je nečekaný

**Příčiny:**
1. Špatná konfigurace parametrů
2. Nekompatibilní kódování/dekódování
3. Chyby v kanálu

**Řešení:**
- Zkontrolujte parametry všech prvků
- Zkuste postupně přidávat analyzátory (Entropie, BER Meter)
- Sledujte historii paketu (Inspector panel)

### 7.5 Pomalá simulace

**Příčiny:**
1. Příliš mnoho prvků
2. Velká data (obrázky, audio)
3. Složité algoritmy (LZ77 s velkým oknem)

**Řešení:**
- Zjednodušte řetězec
- Použijte menší data pro testování
- Snižte `window_size` u LZ77

---

## 8. Shrnutí: Nejčastější kombinace

### 8.1 Pro začátečníky

```
📝 Text ──→ 📊 Entropie
```
**Účel:** Pochopit, co je entropie

```
🔢 Číslo ──→ 🔀 BaseConv ──→ 📊 Analyzátor
```
**Účel:** Procvičit převody soustav

### 8.2 Pro středně pokročilé

```
📝 Text ──→ 🌳 Huffman ──→ 📊 CompRatio
```
**Účel:** Porozumět kompresi

```
📝 Text ──→ 🔤 UTF-8 ──→ 🔴 Hamming ──→ 📡 BSK ──→ 🔴 HammingDec ──→ 🔤 UTF-8Dec ──→ 📝 Text
```
**Účel:** Komunikační řetězec s opravou chyb

### 8.3 Pro pokročilé

```
📝 Text ──→ 📏 RLE ──→ 🗜️ LZ77 ──→ 🌳 Huffman ──→ 🔴 Hamming ──→ 📡 Gilbert-Elliott ──→ 🔴 HammingDec ──→ 🌳 HuffmanDec ──→ 🗜️ LZ77Dec ──→ 📏 RLEDec ──→ 📝 Text
```
**Účel:** Víceúrovňová komprese + ECC + nárazové chyby

```
🎲 Random ──┬─→ 📏 RLE ──→ 📊 CompRatio
            ├─→ 🗜️ LZ77 ──→ 📊 CompRatio
            └─→ 🌳 Huffman ──→ 📊 CompRatio
```
**Účel:** Srovnání kompresních algoritmů

---

## 9. Zdroje a další informace

### 9.1 Související dokumentace

- **[CONNECTION_SYSTEM_ARCHITECTURE.md](CONNECTION_SYSTEM_ARCHITECTURE.md)** - Technické detaily propojovacího systému
- **[ADVANCED_CONNECTION_SYSTEM.md](ADVANCED_CONNECTION_SYSTEM.md)** - Pokročilé funkce
- **[default_doc.md](default_doc.md)** - Hlavní dokumentace projektu
- **[COMPLETE_SYSTEM_EXAMPLE.md](COMPLETE_SYSTEM_EXAMPLE.md)** - Kompletní příklady

### 9.2 Klávesové zkratky

| Klávesa | Akce |
|---------|------|
| **Delete/Backspace** | Smazat vybrané spojení |
| **Escape** | Zrušit propojování |
| **Ctrl+S** | Uložit scénář |
| **Ctrl+O** | Otevřít scénář |
| **Space** | Spustit/pozastavit simulaci |
| **Ctrl+Z** | Zpět |
| **Ctrl+Y** | Znovu |

### 9.3 Kontaktní informace

- **Projekt:** InfoFlowLab
- **Účel:** Výuka komprese dat a komunikace
- **Cílová skupina:** Studenti informačních systémů

---

## 10. Závěr

Tato nápověda vás seznámila se základy propojování prvků v InfoFlowLab. Nyní víte:

✅ **Jak propojit** dva prvky (output → input)  
✅ **Jaké typy dat** existují a co je kompatibilní  
✅ **Co každý prvek** dělá a jaké porty má  
✅ **Jaké kombinace** jsou užitečné pro různé účely  
✅ **Jak řešit** běžné problémy  

**Doporučení:**
1. Začněte s jednoduchými scénáři (sekce 5)
2. Experimentujte s parametry
3. Pozorujte metriky v analyzátorech
4. Postupně přidávejte složitější řetězce

**Vzdělávací cíle:**
- Pochopit transformaci dat v komunikačních řetězcích
- Experimentovat s kompresí a kódováním
- Porozumět vlivu šumu na přenos
- Srovnávat efektivitu různých algoritmů

 Hodně štěstí při experimentování! 🚀

---

*Poslední aktualizace: 28. 6. 2026*