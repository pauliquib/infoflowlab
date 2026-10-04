# Komprese & Komunikace: Interaktivní Simulátor

> **Verze:** 1.0  
> **Autor:** [Student]  
> **Datum:** 23. 6. 2026  
> **Cílová skupina:** Studenti předmětu "Základy informačních systémů" / "Informační teorie"  
> **Licence:** MIT (open-source pro vzdělávací účely)

---

## 1. Úvod a Motivace

### 1.1 Proč tento projekt?

Tradiční výuka komprese dat, číselných soustav, entropie a kódování je často abstraktní a studenti mají problém si představit:
- Jak se mění informace při přechodu mezi formáty
- Proč některé komprese jsou ztrátové a jiné bezeztrátové
- Jak funguje skutečná komunikace v síti
- Jak se vyvíjely komunikační kanály v historii

### 1.2 Cíl projektu

Vytvořit **interaktivní simulátor** (inspirovaný Cisco Packet Tracer), kde studenti mohou:
1. **Sestavovat komunikační řetězce** z historických i moderních prvků
2. **Pozorovat transformaci dat** v reálném čase s vizualizací
3. **Experimentovat s parametry** (šum, ztráta paketů, kompresní poměr)
4. **Srovnat efektivitu** různých kombinací komprese a kódování
5. **Procvičit všechny typy úloh** z testu (převody soustav, entropie, Hamming, kontrolní číslice, ...)

---

## 2. Funkční požadavky (Requirements)

### 2.1 Core Features (MVP)

| ID | Funkce | Popis | Priorita |
|----|--------|-------|----------|
| F1 | **Drag-and-Drop editor** | Přetahování prvků na plátno, propojování linkami | 🔴 Kritické |
| F2 | **Simulace toku dat** | Animované "pakety" procházející řetězcem prvků | 🔴 Kritické |
| F3 | **Reálný čas parametrů** | Zobrazení bitrate, latency, kompresního poměru, entropie | 🔴 Kritické |
| F4 | **Víceúrovňová komprese** | Podpora bezeztrátové i ztrátové komprese v řetězci | 🔴 Kritické |
| F5 | **Historické komunikační prvky** | Řeč, morseovka, dopis, telegraf, rádio | 🟡 Důležité |
| F6 | **Číselné soustavy** | Interaktivní převodník s vizualizací bitů | 🔴 Kritické |
| F7 | **Entropie kalkulátor** | Výpočet Shannonovy entropie pro zadaný text/zdroj | 🔴 Kritické |
| F8 | **Hammingovy kódy** | Vizualizace kódování, detekce a korekce chyb | 🟡 Důležité |
| F9 | **Kontrolní číslice** | Simulátor EAN/ISBN/ISSN/IČ s výpočtem | 🟡 Důležité |
| F10 | **Kanálové šumy** | Nastavitelný BSK (binární symetrický kanál) | 🟡 Důležité |
| F11 | **Vzorkovací teorém** | Demonstrace Nyquistova kritéria s audio signálem | 🟢 Dobré znát |
| F12 | **Export scénářů** | Uložení/načtení simulačních scénářů (JSON) | 🟢 Dobré znát |

### 2.2 Advanced Features (Post-MVP)

| ID | Funkce | Popis |
|----|--------|-------|
| AF1 | **Multiplayer mód** | Sdílení scénářů mezi studenty, řešení úloh |
| AF2 | **Quiz engine** | Automatické generování testových otázek ze simulace |
| AF3 | **3D vizualizace** | Prostorové zobrazení sítě (volitelné) |
| AF4 | **Web export** | Export simulace jako embeddable widget |
| AF5 | **AI asistent** | Vysvětlení konceptů pomocí LLM integrace |

---

## 3. Architektura systému

### 3.1 High-Level Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    UI Layer (Frontend)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │ Canvas   │  │ Sidebar  │  │ Inspector│  │ Timeline   │  │
│  │ (2D)     │  │ (Tools)  │  │ (Params) │  │ (Playback) │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │ IPC / WebSocket
┌────────────────────▼────────────────────────────────────────┐
│              Simulation Engine (Core)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Node Graph   │  │ Data Pipeline│  │ Physics/Animation│  │
│  │ (Topology)   │  │ (Transform)  │  │ (Particles)      │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│              Algorithm Modules (Backend)                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐  │
│  │ Encoding │ │ Compress │ │ Channel  │ │ Checksum/ECC   │  │
│  │ (Base-N) │ │ (LZ/Huff)│ │ (BSK)    │ │ (Hamming/CRC)  │  │
│  └──────────┘ └──────────┘ └──────────┘ └────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Komponenty detailně

#### 3.2.1 Node System (Prvky simulace)

Každý prvek má:
- **Vstupní porty** (konektory)
- **Výstupní porty** (konektory)
- **Interní stav** (buffer, parametry)
- **Vizualizaci** (ikona, animace)
- **Konfiguraci** (nastavitelné parametry)

#### 3.2.2 Data Packet

```typescript
interface DataPacket {
  id: string;
  payload: Uint8Array;        // Binární data
  metadata: {
    sourceFormat: string;     // "text", "audio", "image"
    encoding: string;         // "utf-8", "base64", "binary"
    compressionRatio: number; // 1.0 = bezeztrátové
    entropy: number;          // Shannonova entropie
    size: number;             // Velikost v bitech
    history: TransformStep[]; // Historie transformací
    errors: ErrorInfo[];      // Detekované chyby
  };
}
```

---

## 4. Katalog prvků (Node Catalog)

### 4.1 Zdroje dat (Sources)

| Ikona | Název | Popis | Parametry |
|-------|-------|-------|-----------|
| 📝 | **Textový editor** | Zadání vlastního textu | Znaková sada, délka |
| 🎲 | **Náhodný generátor** | Generování dat s danou entropií | Entropie, délka, abeceda |
| 🎵 | **Audio nahrávka** | Nahrání/výběr audio souboru | Vzorkovací frekvence |
| 🖼️ | **Obrázek** | Načtení obrázku pro kompresi | Rozlišení, barevný prostor |
| 📊 | **Statistický zdroj** | Zdroj s definovanou PMF | Pravděpodobnosti symbolů |

### 4.2 Komunikační kanály (Channels)

| Kategorie | Prvky | Vlastnosti |
|-----------|-------|------------|
| **Historické** | Řeč (face-to-face), Dopis, Morseovka, Telegraf, Kouřové signály | Vysoká latence, nízká šířka pásma, kulturní kontext |
| **Analogové** | Telefon (POTS), Rádio AM/FM, Televize | Šum, interference, modulace |
| **Digitální** | Ethernet, WiFi, Bluetooth, Optika | Pakety, ARQ, šířka pásma |
| **Mobilní** | 2G/3G/4G/5G | Handover, QoS, omezení |

### 4.3 Kódování (Encoders)

| Prvek | Algoritmus | Vstup | Výstup | Parametry |
|-------|-----------|-------|--------|-----------|
| **Číselný převodník** | Base-N konverze | Číslo v soustavě Z₁ | Číslo v soustavě Z₂ | Základ zdrojový, cílový, doplňkový kód |
| **ASCII/UTF-8** | Znakové kódování | Text | Byty | Délka (7/8/16/32 bit) |
| **Morseovka** | Morseův kód | Text | Tečka/čárka | Rychlost (WPM) |
| **Base64** | Base64 encoding | Binární data | Text | Padding, URL-safe |
| **Huffman** | Huffmanovo kódování | Symboly s frekvencí | Prefixový kód | Statický/adaptivní |
| **Aritmetické** | Aritmetické kódování | Symboly | Frakce [0,1) | Přesnost |

### 4.4 Komprese (Compressors)

#### 4.4.1 Bezeztrátová komprese

| Prvek | Algoritmus | Princip | Typický poměr |
|-------|-----------|---------|---------------|
| **RLE** | Run-Length Encoding | Opakující se sekvence | 2:1 pro repetitivní data |
| **LZ77/LZ78** | Lempel-Ziv | Slovník referencí | 3:1 pro text |
| **LZW** | Lempel-Ziv-Welch | Dynamický slovník | GIF, TIFF |
| **Huffman** | Huffmanovo strom | Frekvenční analýza | 20-50% úspora |
| **Deflate** | LZ77 + Huffman | Kombinace | ZIP, PNG |
| **Bzip2** | BWT + MTF + RLE + Huffman | Blokové třídění | Lepší než Deflate |
| **Arithmetic** | Aritmetické kódování | Intervalová reprezentace | Blízké entropii |

#### 4.4.2 Ztrátová komprese

| Prvek | Algoritmus | Oblast | Princip | Parametr kvality |
|-------|-----------|--------|---------|-----------------|
| **JPEG** | DCT + Kvantizace | Obrázky | Diskrétní kosinová transformace | Kvalita (0-100) |
| **MP3/AAC** | Psychoakustický model | Audio | Maskování, MDCT | Bitrate (kbps) |
| **H.264/HEVC** | Predikce + DCT | Video | Intra/inter predikce | CRF, bitrate |
| **WebP** | VP8 keyframe | Obrázky | Predikce + entropy | Kvalita |
| **JPEG XL** | Modular + VarDCT | Obrázky | Nový standard | Distance |

### 4.5 Kanálové kódování (Error Correction)

| Prvek | Algoritmus | Detekce | Korekce | Parametry |
|-------|-----------|---------|---------|-----------|
| **Parita** | Sudá/lichá parita | 1 bit | 0 | Typ (sudá/lichá) |
| **Hamming(7,4)** | Hammingův kód | 2 bity | 1 bit | Standard/extended |
| **Hamming(15,11)** | Extended Hamming | 3 bity | 1 bit | - |
| **Reed-Solomon** | RS kódy | t symbolů | t/2 symbolů | n, k, t |
| **CRC** | Cyclic Redundancy Check | Burst chyby | 0 | Polynom (CRC-8/16/32) |
| **Turbo kódy** | Iterativní dekódování | Vysoká | Vysoká | Iterace |
| **LDPC** | Low-Density Parity Check | Vysoká | Vysoká | Matice H |

### 4.6 Kontrolní mechanismy (Checksums)

| Prvek | Standard | Použití | Parametry |
|-------|----------|---------|-----------|
| **EAN-13** | GS1 | Produkty | 13 číslic |
| **EAN-8** | GS1 | Malé produkty | 8 číslic |
| **ISBN-10** | ISO 2108 | Knihy | 10 znaků |
| **ISBN-13** | ISO 2108 | Knihy | 13 číslic |
| **ISSN** | ISO 3297 | Periodika | 8 číslic |
| **IČ** | ČSÚ | Firmy ČR | 8 číslic |
| **Rodné číslo** | ČR | Obyvatelé | 9-10 číslic |
| **Luhn** | ISO/IEC 7812 | Kreditní karty | Mod 10 |
| **Verhoeff** | - | SIM karty | Mod 10 |

### 4.7 Zpracování signálu (Signal Processing)

| Prvek | Funkce | Parametry |
|-------|--------|-----------|
| **Vzorkovač** | A/D převod | fs (vzorkovací frekvence), bitová hloubka |
| **Kvantizátor** | Kvantizace | Počet úrovní (n), rozsah (R) |
| **Filtr** | Dolní/horní propust | Mezní frekvence, řád |
| **Modulátor** | AM/FM/PM | Nosná frekvence, index modulace |
| **Demodulátor** | AM/FM/PM detekce | Typ demodulace |

### 4.8 Analýza (Analyzers)

| Prvek | Metrika | Vizualizace |
|-------|---------|-------------|
| **Entropie metr** | H(X), Hmax, R, μ | Graf, číselná hodnota |
| **Histogram** | Frekvence symbolů | Sloupcový graf |
| **Spektrum** | FFT | Frekvenční spektrum |
| **Kompresní poměr** | Vstup/výstup | Procento, graf |
| **BER/PER** | Bit/Packet Error Rate | Časový průběh |
| **Latency** | Zpoždění | Timeline, histogram |

---

## 5. Scénáře výuky (Learning Scenarios)

### 5.1 Scénář A: Základy číselných soustav

**Cíl:** Procvičit převody mezi soustavami

```
[Textový editor: "124"] 
    → [Číselný převodník: 10→2] 
    → [Zobrazení: 1111100₂]
    → [Číselný převodník: 2→8] 
    → [Zobrazení: 174₈]
    → [Číselný převodník: 2→16] 
    → [Zobrazení: 7C₁₆]
```

**Interaktivní prvky:**
- Kliknutím na bit přepnout hodnotu, okamžitý přepočet
- Vizualizace váhy pozic (128, 64, 32, 16, 8, 4, 2, 1)
- Zobrazení doplňkového a inverzního kódu
- Animace postupného dělení při převodu

### 5.2 Scénář B: Entropie a informační hodnota

**Cíl:** Pochopit Shannonovu entropii

```
[Statistický zdroj: p(A)=0.5, p(B)=0.25, p(C)=0.125, p(D)=0.125]
    → [Entropie metr]
    → [Huffman encoder]
    → [Entropie metr (po kompresi)]
    → [Komparátor: H vs Hpo]
```

**Interaktivní prvky:**
- Posuvníky pro změnu pravděpodobností
- Živý graf entropie při změnách
- Vizualizace Huffmanova stromu
- Zobrazení redundance R = Hmax - H

### 5.3 Scénář C: Komunikační řetězec

**Cíl:** Simulovat kompletní přenos

```
[Textový editor: "Hello World"]
    → [UTF-8 Encoder]
    → [Huffman Compressor]
    → [Hamming(7,4) Encoder]
    → [BSK Channel: p=0.95]
    → [Hamming Decoder]
    → [Huffman Decompressor]
    → [UTF-8 Decoder]
    → [Textový výstup]
```

**Interaktivní prvky:**
- Nastavení pravděpodobnosti chyby kanálu
- Vizualizace chyb (červené bity)
- Korekce chyb Hammingovým kódem
- Srovnání: s/bez ECC

### 5.4 Scénář D: Historická komunikace

**Cíl:** Porovnat efektivitu historických kanálů

```
[Textový editor: "SOS"]
    → [Rozdělovač do 3 kanálů]
    ├─→ [Řeč: latence=0, šířka=~39kbps]
    ├─→ [Morseovka: latence=ruční, šířka=~10bps]
    └─→ [Optika: latence=ms, šířka=~10Tbps]
    → [Komparátor všech kanálů]
```

**Interaktivní prvky:**
- Zobrazení "paketu" jako zvukové vlny (řeč), teček/čárek (Morse), fotonů (optika)
- Časová osa doručení
- Porovnání: informace za jednotku času

### 5.5 Scénář E: Ztrátová vs bezeztrátová komprese

**Cíl:** Demonstrovat rozdíl mezi typy komprese

```
[Obrázek: fotografie]
    → [Rozdělovač]
    ├─→ [PNG (bezeztrátová)] → [Soubor A]
    └─→ [JPEG (ztrátová, q=90)] → [Soubor B]
    └─→ [JPEG (ztrátová, q=10)] → [Soubor C]
    → [Komparátor: velikost, PSNR, SSIM]
```

**Interaktivní prvky:**
- Posuvník kvality JPEG
- Zobrazení artefaktů při nízké kvalitě
- Graf: kompresní poměr vs kvalita

### 5.6 Scénář F: Kontrolní číslice

**Cíl:** Procvičit výpočet kontrolních číslic

```
[EAN-13 vstup: 357159465852?]
    → [EAN-13 validátor]
    → [Výpočet krok za krokem]
    → [Výsledek: 8]
    → [Simulace chyby: změna jedné číslice]
    → [Detekce chyby]
```

**Interaktivní prvky:**
- Krok za krokem výpočet s vysvětlením
- Simulace překlepu (1 chyba, transpozice)
- Porovnání: které chyby detekují různé algoritmy

---

## 6. Technická specifikace

### 6.1 Doporučené technologie

#### 6.1.1 Varianty hodnocení

| Kritérium | Python + PyQt/PySide | JavaScript + Electron | C# + WPF | Rust + egui |
|-----------|---------------------|----------------------|----------|-------------|
| **Rychlost vývoje** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Výkon animací** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Multiplatformní** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Matematické knihovny** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Velikost distribuce** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Komunita/vzdělávání** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Web deployment** | ⭐⭐ (Pyodide) | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐ (WASM) |

#### 6.1.2 Doporučená volba: **Python + PySide6 + PyQtGraph**

**Proč:**
- ✅ Nejrychlejší vývoj pro prototyp
- ✅ Výborné matematické knihovny (NumPy, SciPy)
- ✅ PyQtGraph pro vysokovýkonné grafy
- ✅ Qt Graphics Framework pro 2D animace
- ✅ Snadná distribuce přes PyInstaller
- ✅ Studenti znají Python z přednášek

**Alternativa pro web:** JavaScript + React + D3.js + Canvas API

### 6.2 Architektura Python implementace

```
project/
├── main.py                    # Entry point
├── requirements.txt
├── assets/
│   ├── icons/                 # Ikony prvků (SVG)
│   ├── sounds/                # Audio efekty
│   └── themes/                # CSS-like styly
├── src/
│   ├── core/
│   │   ├── engine.py          # Hlavní simulační smyčka
│   │   ├── node.py            # Základní třída prvku
│   │   ├── packet.py          # Datový paket
│   │   └── graph.py           # Topologie grafu
│   ├── nodes/
│   │   ├── sources/           # Zdroje dat
│   │   ├── encoders/          # Kódovače
│   │   ├── compressors/       # Komprese
│   │   ├── channels/          # Kanály
│   │   ├── ecc/               # Error correction
│   │   ├── checksums/         # Kontrolní číslice
│   │   ├── analyzers/         # Analýza
│   │   └── sinks/             # Výstupy
│   ├── algorithms/
│   │   ├── number_systems.py  # Převody soustav
│   │   ├── entropy.py         # Entropie výpočty
│   │   ├── huffman.py         # Huffmanovo kódování
│   │   ├── hamming.py         # Hammingovy kódy
│   │   ├── checksums.py       # EAN, ISBN, ISSN, IČ
│   │   ├── channel.py         # BSK simulace
│   │   └── compression/       # RLE, LZ, Deflate
│   ├── gui/
│   │   ├── main_window.py     # Hlavní okno
│   │   ├── canvas.py          # Simulační plátno
│   │   ├── sidebar.py         # Panel nástrojů
│   │   ├── inspector.py       # Panel vlastností
│   │   ├── timeline.py        # Časová osa
│   │   └── widgets/           # Vlastní widgety
│   ├── visualization/
│   │   ├── packet_renderer.py # Vykreslení paketů
│   │   ├── node_renderer.py   # Vykreslení prvků
│   │   ├── animations.py      # Animace
│   │   └── charts.py          # Grafy (PyQtGraph)
│   └── utils/
│       ├── config.py          # Konfigurace
│       └── serialization.py   # Ukládání/načítání
└── tests/
    ├── test_algorithms.py
    └── test_simulation.py
```

### 6.3 Klíčové knihovny

```txt
# requirements.txt
PySide6>=6.5.0          # GUI framework
PyQtGraph>=0.13.0       # Vysokovýkonné grafy
NumPy>=1.24.0           # Numerické výpočty
Pillow>=10.0.0          # Zpracování obrázků
SoundFile>=0.12.0       # Audio I/O
pyaudio>=0.2.13         # Audio playback (volitelné)
```

### 6.4 Grafické prostředí detailně

#### 6.4.1 Layout aplikace

```
┌─────────────────────────────────────────────────────────────────┐
│  Menu Bar  │  Toolbar (Play/Pause/Stop/Step)                  │
├──────────┬──────────────────────────────────────┬─────────────┤
│          │                                      │             │
│  SIDEBAR │           CANVAS (2D)                │  INSPECTOR  │
│  (Tools) │                                      │  (Params)   │
│          │   ┌────┐      ┌────┐      ┌────┐   │             │
│  [Sources]│   │Node│─────→│Node│─────→│Node│   │  [Properties]│
│  [Encod] │   └────┘      └────┘      └────┘   │  [Metrics]  │
│  [Chann] │        ↗ Packet animation ↗         │  [History]  │
│  [Comp]  │                                      │             │
│  [ECC]   │                                      │             │
│  [Anal]  │                                      │             │
│          │                                      │             │
├──────────┴──────────────────────────────────────┴─────────────┤
│  TIMELINE / CONSOLE / LOG                                      │
└─────────────────────────────────────────────────────────────────┘
```

#### 6.4.2 Vizuální styl

- **Téma:** Dark mode (vývojářský/editor styl)
- **Barvy prvků podle kategorie:**
  - Zdroje: 🟢 Zelená
  - Kódování: 🔵 Modrá
  - Komprese: 🟡 Žlutá
  - Kanály: 🟠 Oranžová
  - ECC: 🔴 Červená
  - Analýza: 🟣 Fialová
- **Animace paketů:** Plynulý pohyb po linkách, pulzující efekt
- **Efekty:** Glow při aktivitě, červené blikání při chybě

---

## 7. Implementační roadmap

### Fáze 1: Základ (Týden 1-2)
- [ ] Setup projektu, GUI skeleton (PySide6)
- [ ] Canvas s drag-and-drop
- [ ] Základní Node třída a porty
- [ ] Spojování prvků linkami
- [ ] Ukládání/načítání grafu (JSON)

### Fáze 2: Algoritmy (Týden 3-4)
- [ ] Převody číselných soustav
- [ ] Entropie kalkulátor
- [ ] Huffmanovo kódování
- [ ] Hammingovy kódy
- [ ] Kontrolní číslice (EAN, ISBN, ISSN, IČ)

### Fáze 3: Simulace (Týden 5-6)
- [ ] DataPacket a pipeline
- [ ] Tok dat mezi prvky
- [ ] Animace paketů
- [ ] BSK kanál se šumem
- [ ] Základní komprese (RLE, Huffman)

### Fáze 4: Vizualizace (Týden 7-8)
- [ ] PyQtGraph integrace
- [ ] Histogramy a spektra
- [ ] Timeline přehrávání
- [ ] Metriky v reálném čase
- [ ] Tematické ikony a styly

### Fáze 5: Rozšíření (Týden 9-10)
- [ ] Ztrátová komprese (JPEG, MP3)
- [ ] Historické komunikační prvky
- [ ] Víceúrovňové řetězce
- [ ] Export scénářů
- [ ] Dokumentace a tutoriály

### Fáze 6: Polish (Týden 11-12)
- [ ] Bug fixing
- [ ] Optimalizace výkonu
- [ ] Uživatelské testování
- [ ] Finální balíček

---

## 8. Příklady interakce

### 8.1 Přidání prvku na plátno

1. Student klikne na "Sources" v sidebaru
2. Rozbalí se seznam: Textový editor, Audio, Obrázek, ...
3. Přetáhne "Textový editor" na canvas
4. Dvakrát klikne → otevře se dialog s textem
5. Zadá: "ABCD" → okno se zavře, node zobrazí náhled

### 8.2 Propojení a simulace

1. Student přetáhne "Huffman Compressor" vedle zdroje
2. Klikne na výstupní port zdroje, táhne na vstupní port kompresoru
3. Vznikne spojovací čára (linka)
4. Klikne "Play" v toolbaru
5. Animace: paket s "ABCD" se pohybuje po lince ke kompresoru
6. V kompresoru se zobrazí: vstup=32 bitů, výstup=?
7. V inspectoru se aktualizují metriky

### 8.3 Analýza výsledků

1. Student přidá "Entropie metr" za kompresor
2. Propojí výstup kompresoru s metrem
3. V inspectoru metru vidí:
   - H(X) = 2.0 bitů
   - Hmax = 2.0 bitů (pro 4 symboly)
   - R = 0 bitů (optimální komprese)
   - μ = 100% (efektivita)
4. Histogram zobrazí frekvence symbolů

---

## 9. Mapování na testové otázky

| Téma z testu | Prvky v simulátoru | Scénář |
|--------------|-------------------|--------|
| Převody soustav | Číselný převodník | Scénář A |
| Entropie | Entropie metr, Statistický zdroj | Scénář B |
| Kanálová kapacita | BSK kanál, Kapacita metr | Scénář C |
| Hammingova vzdálenost | Hamming kód, Chybový kanál | Scénář C |
| Kontrolní číslice | EAN/ISBN/ISSN validátor | Scénář F |
| Vzorkovací teorém | Vzorkovač, Spektrum | Custom |
| Kvantizace | Kvantizátor, Šum metr | Custom |
| Bayesova věta | Podmíněná pravděpodobnost node | Custom |
| Kombinatorika | Permutace/Variace/Kombinace kalkulátor | Custom |

---

## 10. Otevřené otázky a rozhodnutí

### 10.1 K diskusi

| Otázka | Možnosti | Doporučení |
|--------|----------|------------|
| Web vs Desktop? | Electron, PyQt, Web app | PyQt pro rychlost, Electron pro dostupnost |
| 3D vizualizace? | PyQt3D, Three.js, Unity | 2D pro MVP, 3D jako rozšíření |
| Ukládání scénářů? | JSON, SQLite, Cloud | JSON lokálně, Cloud pro sdílení |
| Lokalizace? | Čeština, Angličtina | Čeština primárně, EN rozšíření |
| Audio přehrávání? | PyAudio, Qt Multimedia | Qt Multimedia (integrované) |

### 10.2 Rizika

| Riziko | Pravděpodobnost | Dopad | Mitigace |
|--------|----------------|-------|----------|
| Příliš velký scope | Vysoká | Vysoký | Striktní MVP, iterativní vývoj |
| Výkon animací | Střední | Střední | PyQtGraph, optimalizace draw calls |
| Komplexita algoritmů | Střední | Střední | Použít existující knihovny |
| UI/UX pro začátečníky | Střední | Vysoký | Tutoriály, tooltips, předpřipravené scénáře |

---

## 11. Závěr

Tento projekt má potenciál stát se **standardním výukovým nástrojem** pro předmět. Klíčové je:

1. **Začít jednoduše** – MVP s 5-10 základními prvky
2. **Iterovat** – přidávat scénáře podle zpětné vazby studentů
3. **Vizuálně přitažlivé** – animace a interaktivita jsou klíčové
4. **Propojené s testem** – každý scénář odpovídá konkrétní otázce
5. **Open-source** – umožnit dalším studentům přispívat

---

## Přílohy

### A. Seznam všech prvků (kompletní)

**Zdroje (8):**
Textový editor, Náhodný generátor, Audio nahrávka, Obrázek, Statistický zdroj, Číselný vstup, Soubor, QR kód

**Kódování (10):**
ASCII, UTF-8, UTF-16, Base64, Morseovka, Číselný převodník, Huffman, Aritmetické, Shannon-Fano, LZ77

**Komprese bezeztrátová (8):**
RLE, LZ77, LZ78, LZW, Huffman, Deflate, Bzip2, Aritmetická

**Komprese ztrátová (6):**
JPEG, PNG, MP3, AAC, H.264, WebP

**Kanály (12):**
Řeč, Dopis, Morseovka, Telegraf, Kouřové signály, Telefon, Rádio AM, Rádio FM, Ethernet, WiFi, Optika, 5G

**ECC (7):**
Parita, Hamming(7,4), Hamming(15,11), Reed-Solomon, CRC-8/16/32, Turbo kódy, LDPC

**Kontrolní číslice (9):**
EAN-13, EAN-8, ISBN-10, ISBN-13, ISSN, IČ, Rodné číslo, Luhn, Verhoeff

**Signál (5):**
Vzorkovač, Kvantizátor, Filtr, Modulátor, Demodulátor

**Analýza (6):**
Entropie metr, Histogram, Spektrum, Kompresní poměr, BER/PER, Latence

**Výstupy (4):**
Textový výstup, Soubor, Graf, Tabulka

**Celkem: 75+ prvků**

### B. Ukázka JSON scénáře

```json
{
  "version": "1.0",
  "name": "Scénář C: Komunikační řetězec",
  "nodes": [
    {
      "id": "source_1",
      "type": "TextSource",
      "position": {"x": 100, "y": 200},
      "params": {"text": "Hello World", "encoding": "utf-8"}
    },
    {
      "id": "huffman_1",
      "type": "HuffmanCompressor",
      "position": {"x": 300, "y": 200},
      "params": {"mode": "static"}
    },
    {
      "id": "hamming_1",
      "type": "HammingEncoder",
      "position": {"x": 500, "y": 200},
      "params": {"n": 7, "k": 4}
    },
    {
      "id": "bsk_1",
      "type": "BSKChannel",
      "position": {"x": 700, "y": 200},
      "params": {"p": 0.95, "q": 0.05}
    }
  ],
  "connections": [
    {"from": "source_1.out", "to": "huffman_1.in"},
    {"from": "huffman_1.out", "to": "hamming_1.in"},
    {"from": "hamming_1.out", "to": "bsk_1.in"}
  ]
}
```

### C. Reference

- Shannon, C.E. (1948). "A Mathematical Theory of Communication"
- Hamming, R.W. (1950). "Error Detecting and Error Correcting Codes"
- Cover, T.M. & Thomas, J.A. "Elements of Information Theory"
- Sayood, K. "Introduction to Data Compression"
- Cisco Packet Tracer – inspirace UI/UX
