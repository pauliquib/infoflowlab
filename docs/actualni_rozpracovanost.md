# InfoFlowLab - Projektová dokumentace

> **Aktualizováno: červenec 2026 — verze 1.0.0**

## Stav projektu (v1.0)

| Oblast | Stav |
|--------|------|
| GUI (MainWindow, Canvas, Sidebar, Inspector) | ✅ Hotovo |
| 53 typů simulačních uzlů | ✅ Hotovo |
| Centrální registr uzlů (`src/nodes/registry.py`) | ✅ Hotovo |
| Ukládání/načítání scénářů (JSON, class_name + type_key) | ✅ Hotovo |
| Undo/Redo (Ctrl+Z / Ctrl+Y) | ✅ Hotovo |
| Wire Cutter (Alt+klik na port/spojení) | ✅ Integrováno z advanced_connection_system |
| Reroute body (dvojklik na spojení) | ✅ Hotovo |
| Unit testy (98 testů) | ✅ Hotovo |
| CI pipeline (GitHub Actions) | ✅ Hotovo |
| Pokročilý connection systém (reroute nodes, smart snapping) | ⚠️ Částečně — WireCutter integrován, zbytek v `advanced_connection_system.py` |

## Přehled projektu

**InfoFlowLab** je interaktivní simulátor komprese a komunikace pro vizuální návrh a testování datových toků. Aplikace umožňuje uživatelům vytvářet grafy z uzlů (nodes), propojovat je a simulovat přenos dat v reálném čase.

- **Verze**: 1.0.0
- **Framework**: PySide6 (Qt for Python)
- **Architektura**: Model-View-Controller s grafovým modelem
- **Stav**: Produkční v1.0 s kompletní testovací sadou a CI

---

## Nové funkce v1.0

### Undo/Redo (`src/core/undo_stack.py`)
- Příkazy: přidání/odebrání uzlu, přesun, přidání/odebrání spojení
- Makra pro hromadné operace (Delete, Alt+řez portu)
- Toolbar: ↶ Undo / ↷ Redo + Ctrl+Z / Ctrl+Y

### Node Registry (`src/nodes/registry.py`)
- Jediný zdroj pravdy pro 53 uzlů
- Serializace přes `class_name` + `type_key`
- Zpětná kompatibilita se starými scénáři (heuristiky podle názvu)

### Connection Enhancements
- **Alt+klik na port** — ořízne všechna spojení portu (WireCutter)
- **Alt+klik na drát** — ořízne jedno spojení
- **Dvojklik na drát** — přidá reroute bod (metadata `reroute_points`)
- **Dvojklik na port** — smaže spojení portu (s undo)

### Testování a CI
- `tests/` — 98 unit a GUI smoke testů
- `.github/workflows/ci.yml` — Python 3.11/3.12, pytest, flake8
- Headless Qt: `QT_QPA_PLATFORM=offscreen`

---

## Architektura systému

### Vrstvená struktura

```
┌─────────────────────────────────────────┐
│  GUI vrstva (src/gui/)                  │
│  - MainWindow, Canvas, Sidebar, Inspector│
├─────────────────────────────────────────┤
│  Node vrstva (src/nodes/)               │
│  - Konkrétní implementace uzlů          │
├─────────────────────────────────────────┤
│  Algoritmy (src/algorithms/)            │
│  - Entropie, Huffman, Hamming, CRC...   │
├─────────────────────────────────────────┤
│  Core vrstva (src/core/)                │
│  - Graph, Engine, NodeBase, Port, Packet │
├─────────────────────────────────────────┤
│  Utils (src/utils/)                     │
│  - Serializace                          │
└─────────────────────────────────────────┘
```

---

## Core moduly (src/core/)

### 1. Graph (`graph.py`)

**Účel**: Centrální úložiště grafu - spravuje uzly a spojení.

**Hlavní třída**: `Graph`

**Struktura dat**:
```python
self.nodes: Dict[str, NodeBase] = {}           # Mapování node_id -> NodeBase
self.connections: List[tuple] = []             # (from_node_id, from_port, to_node_id, to_port)
```

**Klíčové metody**:
- `add_node(node)` – Přidá uzel do grafu, vrací node_id
- `remove_node(node_id)` – Odstraní uzel a všechny jeho spojení
- `connect(from_id, from_port, to_id, to_port)` – Vytvoří spojení mezi porty, vrací bool
- `disconnect(from_id, from_port, to_id, to_port)` – Zruší spojení
- `get_node(node_id)` – Vrátí uzel podle ID
- `to_dict()` – Serializace grafu do slovníku

**Logika spojení**:
- Kontrola existence obou uzlů
- Validace názvů portů
- Volání `can_connect()` na portech (kontrola typu, stejného rodiče)
- Přidání do seznamu connections pouze při úspěchu

---

### 2. Engine (`engine.py`)

**Účel**: Řídí simulaci datového toku grafem.

**Hlavní třída**: `SimulationEngine(QObject)`

**Signály**:
- `simulation_started` – Spuštění simulace
- `simulation_stopped` – Zastavení simulace
- `packet_moved(packet_id, from_node, to_node)` – Pohyb paketu mezi uzly

**Stav**:
```python
self.running: bool = False
self.speed: float = 1.0                    # Násobič rychlosti (0.1 - 5.0)
self.active_packets: List[DataPacket] = []
```

**Klíčové metody**:
- `start()` – Spustí simulaci (nastaví `running = True`)
- `stop()` – Zastaví simulaci
- `step()` – Jeden krok simulace:
  1. Projde všechny uzly
  2. Odebere paket z bufferu prvního uzlu s daty
  3. Najde výstupní port s connections
  4. Odešle paket do připojených vstupních portů
  5. Emituje signál `packet_moved`
- `inject_packet(node_id, packet)` – Vloží paket do zdrojového uzlu
- `set_speed(speed)` – Nastaví rychlost simulace

**Zpracování paketu**:
```
Buffer uzlu → send_output() → receive_input() → process() → data_processed signal
```

---

### 3. NodeBase (`node_base.py`)

**Účel**: Základní třída pro všechny uzly v systému.

**Hlavní třída**: `NodeBase(QObject)`

**Atributy**:
```python
node_id: str                    # Unikátní identifikátor
node_type: str                  # Kategorie (source, encoder, sink, atd.)
name: str                       # Zobrazovaný název
position: Tuple[float, float]   # Pozice na canvasu (x, y)
input_ports: Dict[str, Port]    # Vstupní porty
output_ports: Dict[str, Port]   # Výstupní porty
params: Dict[str, Any]          # Parametry uzlu
status: str                     # "idle", "processing", "error"
buffer: List[DataPacket]        # Buffer pro čekající pakety
```

**Signály**:
- `data_processed(DataPacket)` – Emitováno po zpracování paketu
- `status_changed(str)` – Emitováno při změně stavu

**Klíčové metody**:
- `add_input(name)` / `add_output(name)` – Vytvoření portu
- `process(packet, input_port)` – Abstraktní metoda, přepisuje se v potomcích
- `send_output(packet, output_port)` – Odešle paket do všech připojených portů
- `receive_input(packet, input_port)` – Přijme paket, zpracuje ho, emituje signály
- `get_param(key, default)` / `set_param(key, value)` – Práce s parametry

**Zpracování toku**:
1. `receive_input()` je volána z `send_output()` jiného uzlu
2. Nastaví status na "processing"
3. Zavolá `process()` – v potomkovi vrací nový DataPacket
4. Emituje `data_processed` s výsledkem
5. Nastaví status zpět na "idle"

---

### 4. Port (`port.py`)

**Účel**: Reprezentace připojovacího bodu uzlu.

**Třídy**:
- `PortType(Enum)` – `INPUT` nebo `OUTPUT`
- `Port` – Instance portu

**Atributy**:
```python
name: str                        # Název portu (např. "out", "in")
type: PortType                   # INPUT nebo OUTPUT
parent_node: NodeBase            # Rodičovský uzel
connections: List['Port']        # Seznam připojených portů
position: QPointF                # Relativní pozice v uzlu
```

**Klíčové metody**:
- `can_connect(other)` – Kontrola možnosti spojení:
  - Různé typy (input ≠ output)
  - Různé rodiče (nelze propojit stejný uzel)
- `connect(other)` – Vytvoření spojení (obousměrné přidání do connections)
- `disconnect(other)` – Zrušení spojení

---

### 5. Packet (`packet.py`)

**Účel**: Datová struktura pro přenos informací mezi uzly.

**Hlavní třída**: `DataPacket`

**Atributy**:
```python
id: str                          # Unikátní ID paketu
payload: bytes                   # Samotná data
source_format: str               # "text", "number", "binary"
encoding: str                    # Použité kódování
size_bits: int                   # Velikost v bitech
history: List[dict]              # Historie zpracování
```

**Metody**:
- `add_step(node_name, input_size, output_size, description)` – Přidá záznam do historie
- `get_history()` – Vrátí kompletní historii zpracování

---

## GUI moduly (src/gui/)

### 1. Canvas (`canvas.py`)

**Účel**: Hlavní plátno pro vizuální úpravu grafu (QGraphicsView).

**Hlavní třída**: `Canvas(QGraphicsView)`

**Komponenty**:
```python
self.scene: QGraphicsScene                    # Scéna pro vykreslování
self._node_items: Dict[str, NodeItem]         # Mapování node_id -> NodeItem
self._connection_items: Dict[tuple, ConnectionItem]  # Mapování spojení
self._connecting_from: Optional[tuple]        # (node_id, port_name, port_type) při propojování
self._temp_line: Optional[QGraphicsPathItem]  # Dočasná čára při propojování
```

**Funkcionalita**:

#### Přidání uzlu
- `add_node_at(node_type, pos)` – Vytvoří uzel, přidá do grafu a scény
- Podporuje Drag & Drop z Sidebaru
- Automaticky překreslí spojení

#### Propojování portů
**Stavový automat**:
1. `mousePressEvent` – Kliknutí na port → nastavení `_connecting_from`
2. `mouseMoveEvent` – Vykreslení Bézierovy křivky (temp line)
3. `mouseReleaseEvent` – Kliknutí na cílový port → volání `graph.connect()`

**Opravené chyby**:
- `RubberBandDrag` → `NoDrag` (blokovalo kliknutí na porty)
- `itemAt()` → `items()` (hledá port i pod překrývajícím se uzlem)

#### Pohyb uzlů
- Uzly jsou `ItemIsMovable`
- `itemChange()` v NodeItem detekuje změnu pozice
- Automatická aktualizace všech připojených spojení

#### Animace paketů
- `start_animation()` / `stop_animation()` – Řízení QTimeru
- `_animate_step()` – Volá `engine.step()` a překresluje pakety
- `_draw_packets()` – Vykreslí žluté elipsy na spojeních (animace pohybu)

#### Ostatní
- `wheelEvent` – Zoom (scale)
- `keyPressEvent` – ESC pro zrušení propojování
- `clear_scene()` – Vyčištění celé scény

---

### 2. NodeItem (`node_item.py`)

**Účel**: Vizuální reprezentace uzlu na canvasu.

**Hlavní třída**: `NodeItem(QGraphicsRectItem)`

**Vzhled**:
- Rozměry: 160×80 px
- Hlavička (28px) s barvou podle kategorie
- Tělo s tmavším odstínem
- Stín (QGraphicsDropShadowEffect)
- Text: název (tučně) a typ

**Kategorie a barvy**:
```python
COLORS = {
    "sources": "#4CAF50",      # Zelená
    "encoders": "#2196F3",     # Modrá
    "compressors": "#FFC107",  # Žlutá
    "channels": "#FF9800",     # Oranžová
    "ecc": "#F44336",          # Červená
    "checksums": "#9C27B0",    # Fialová
    "analyzers": "#9C27B0",    # Fialová
    "general": "#607D8B",      # Šedá
    "default": "#757575"
}
```

**Porty**:
- `input_ports` / `output_ports` – Dict[str, PortItem]
- Vstupní: levá strana (x = -PORT_RADIUS)
- Výstupní: pravá strana (x = NODE_WIDTH - PORT_RADIUS)
- Rozestup: 24px, začátek: HEADER_HEIGHT + 20
- Z-index: 10 (nad uzlem)

**Interakce**:
- `ItemIsMovable` – Přesun myší
- `ItemIsSelectable` – Výběr (modrý okraj)
- `hoverEnterEvent` / `hoverLeaveEvent` – Glow efekt
- `contextMenuEvent` – Kontextové menu (Odstranit/Duplikovat)
- `itemChange` – Automatická aktualizace spojení při pohybu

**Metody**:
- `get_port_scene_pos(port_name, port_type)` – Vrátí světové souřadnice portu
- `_update_connected_connections()` – Aktualizuje všechny spojení pro tento uzel

---

### 3. PortItem (`node_item.py`)

**Účel**: Vizuální port uzlu (QGraphicsEllipseItem).

**Vlastnosti**:
- Rozměr: 16×16 px (PORT_RADIUS = 8)
- Barva: #E0E0E0 (výchozí), #4CAF50 (hover)
- Z-index: 10
- Nese data: `data(0)="port"`, `data(1)="input"/"output"`, `data(2)=name`

**Události**:
- `hoverEnterEvent` / `hoverLeaveEvent` – Zvýraznění
- `mousePressEvent` – Zahájení propojování (přepošle na Canvas)

---

### 4. ConnectionItem (`node_item.py`)

**Účel**: Vizuální spojení mezi uzly (Bézierova křivka).

**Hlavní třída**: `ConnectionItem(QGraphicsPathItem)`

**Vlastnosti**:
- Barva: #B0BEC5 (výchozí), #4CAF50 (aktivní)
- Šířka: 2px (výchozí), 3px (aktivní)
- Z-index: -1 (pod uzly)

**Metody**:
- `update_path()` – Přepočítá Bézierovu křivku:
  - Start: výstupní port (vpravo)
  - End: vstupní port (vlevo)
  - Kontrolní body: dx = max(|x2-x1|*0.5, 50)
- `set_active(active)` – Nastaví aktivní stav (pro animaci)
- `update_positions()` – Alias pro `update_path()` (voláno při pohybu uzlu)

---

### 5. MainWindow (`main_window.py`)

**Účel**: Hlavní okno aplikace.

**Layout**:
```
┌──────────────────────────────────────────────┐
│ Toolbar: Play | Pause | Step | Stop | Reset │
├──────────┬───────────────────┬───────────────┤
│ Sidebar  │     Canvas        │  Inspector    │
│ (20%)    │     (60%)        │  (20%)        │
│          │                   │               │
└──────────┴───────────────────┴───────────────┘
```

**Komponenty**:
- `Graph` – Datový model
- `SimulationEngine` – Simulační jádro
- `Canvas` – Vykreslovací plátno
- `Sidebar` – Panel s dostupnými uzly
- `Inspector` – Panel vlastností vybraného uzlu

**Toolbar akce**:
- `on_play()` – Spustí simulaci + animaci
- `on_pause()` – Zastaví simulaci
- `on_step()` – Jeden krok simulace
- `on_stop()` – Zastaví + smaže animace
- `on_reset()` – Smazání všech prvků
- `on_inject()` – Vloží testovací paket do prvního zdroje
- `on_help()` – Zobrazí dialog s nápovědou

**Signální propojení**:
```python
canvas.node_selected → inspector.set_node
sidebar.node_requested → canvas.add_node_at
engine.simulation_started → lbl_status.setText("Running")
engine.simulation_stopped → lbl_status.setText("Stopped")
```

---

## Node implementace (src/nodes/)

### Struktura

Všechny uzly dědí z `NodeBase` a implementují metodu `process()`.

**Vzorová implementace**:
```python
class MyNode(NodeBase):
    def __init__(self, node_id: str):
        super().__init__(node_id, "category", "Název")
        self.add_input("in")      # Vstupní port
        self.add_output("out")    # Výstupní port
        self.set_param("key", default_value)  # Parametry
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        # Zpracování paketu
        result = ...
        return DataPacket(...)
```

---

### Kategorie uzlů

#### 1. Zdroje (Sources) – `sources.py`

**TextSourceNode** (`"📝 Text"`)
- Vstup: žádný
- Výstup: `out`
- Parametry: `text` (string), `encoding` (utf-8)
- Funkce: Vytvoří paket z textu

**RandomSourceNode** (`"🎲 Random"`)
- Vstup: žádný
- Výstup: `out`
- Parametry: `length` (int), `entropy_target` (0-8)
- Funkce: Generuje náhodná data s nastavitelnou entropií

**NumberInputNode** (`"🔢 Číslo"`)
- Vstup: žádný
- Výstup: `out`
- Parametry: `value` (string), `base` (int)
- Funkce: Vytvoří paket z číselné hodnoty

---

#### 2. Kódování (Encoders) – `encoders.py`

**Base64EncoderNode** (`"Base64"`)
- Vstup: `in`
- Výstup: `out`
- Funkce: Kódování/dekódování Base64

**HexEncoderNode** (`"Hex"`)
- Vstup: `in`
- Výstup: `out`
- Funkce: Převod na hexadecimální řetězec

**Další dostupné** (v `__init__.py`):
- `BaseConverterNode` – Převod mezi číslenými soustavami
- `Utf8EncoderNode` – UTF-8 kódování
- `MorseEncoderNode` – Morseovka
- `HuffmanEncoderNode` – Huffmanovo kódování

---

#### 3. Komprese (Compressors) – `compressors.py`

**HuffmanCompressorNode** (`"Huffman"`)
- Vstup: `in`
- Výstup: `out`
- Funkce: Huffmanova komprese

**RLECompressorNode** (`"RLE"`)
- Vstup: `in`
- Výstup: `out`
- Funkce: Run-Length Encoding

---

#### 4. Kanály (Channels) – `channels.py`

**BSKChannelNode** (`"Šum"`)
- Vstup: `in`
- Výstup: `out`
- Parametry: `noise_level` (float)
- Funkce: Simuluje šum (bitové flipy)

**IdealChannelNode** (`"Zpoždění"`)
- Vstup: `in`
- Výstup: `out`
- Parametry: `delay` (int)
- Funkce: Zpožďuje přenos dat

---

#### 5. ECC (Error Correction) – `ecc.py`

**Hamming74Node** (`"Hamming"`)
- Vstup: `in`
- Výstup: `out`
- Funkce: Hammingův kód (7,4) pro opravu chyb

---

#### 6. Kontrolní součty (Checksums) – `checksums.py`

**CRC32Node** – CRC32 kontrolní součet
**MD5HashNode** – MD5 hash
**EANValidator** – EAN-13 validace
**ISBNValidator** – ISBN-10/13 validace
**ISSNValidator** – ISSN validace
**LuhnValidator** – Luhnův algoritmus (karty)
**VerhoeffValidator** – Verhoeffův algoritmus

---

#### 7. Analyzátory (Analyzers) – `analyzers.py`

**EntropyMeterNode** (`"Entropie"`)
- Vstup: `in`
- Výstup: žádný (nebo `out` pro přepočet)
- Funkce: Výpočet Shannonovy entropie

**HistogramNode** (`"Frekvence"`)
- Vstup: `in`
- Výstup: žádný
- Funkce: Analýza frekvence znaků

---

#### 8. Výstupy (Sinks) – `sinks.py`

**FileSinkNode** (`"Soubor"`)
- Vstup: `in`
- Výstup: žádný
- Funkce: Uložení do souboru

**ConsoleSinkNode** (`"Konzole"`)
- Vstup: `in`
- Výstup: žádný
- Funkce: Výstup do konzole

**HexDumpSinkNode** (`"HexDump"`)
- Vstup: `in`
- Výstup: žádný
- Funkce: Hexadecimální výpis

**TextOutputNode** – Textový výstup

---

## Algoritmy (src/algorithms/)

### entropy.py
- Výpočet Shannonovy entropie
- `calculate_entropy(data: bytes) -> float`
- Výsledek: 0-8 bitů na byte

### hamming.py
- Hammingův kód (7,4)
- `encode(data: bytes) -> bytes`
- `decode(data: bytes) -> bytes`
- Oprava 1-bitových chyb

### huffman.py
- Huffmanova komprese
- `compress(data: bytes) -> bytes`
- `decompress(data: bytes) -> bytes`
- Vytvoření kódového stromu

### checksums.py
- CRC32, MD5
- EAN, ISBN, ISSN validace
- Luhn, Verhoeff algoritmy

### number_systems.py
- Převod mezi číslenými soustavami
- `convert(value: str, from_base: int, to_base: int) -> str`

---

## GUI komponenty (src/gui/)

### Sidebar (`sidebar.py`)

**Účel**: Levý panel s dostupnými uzly.

**Funkcionalita**:
- Zobrazení kategorií (Sources, Encoders, atd.)
- Tlačítka pro přidání uzlu
- Drag & Drop na canvas
- Signál `node_requested(node_type)` – Požadavek na vytvoření uzlu

---

### Inspector (`inspector.py`)

**Účel**: Pravý panel s vlastnostmi vybraného uzlu.

**Funkcionalita**:
- Zobrazení parametrů uzlu
- Editace hodnot (QLineEdit, QSpinBox, atd.)
- Zobrazení historie paketů
- Aktualizace při výběru uzlu (`set_node(node)`)

---

## Tok dat v aplikaci

### 1. Vytvoření spojení

```
Uživatel klikne na port (PortItem.mousePressEvent)
    ↓
Nastavení canvas._connecting_from
    ↓
Uživatel táhne myší → vykreslení temp čáry (Canvas.mouseMoveEvent)
    ↓
Uživatel pustí na cílovém portu (Canvas.mouseReleaseEvent)
    ↓
Hledání portu pomocí self.items() (všechny itemy na pozici)
    ↓
Validace směru: output → input
    ↓
Volání graph.connect()
    ↓
Kontrola: can_connect() na portech
    ↓
Přidání do graph.connections
    ↓
Překreslení spojení (_redraw_connections)
```

### 2. Simulace datového toku

```
User klikne Play
    ↓
engine.start() → running = True
canvas.start_animation() → QTimer (500ms)
    ↓
Každý krok: engine.step()
    ↓
Projde všechny uzly
    ↓
Najde uzel s buffered paketem
    ↓
Odešle přes send_output() → receive_input()
    ↓
Zpracování v process() → nový DataPacket
    ↓
Emituje data_processed signal
    ↓
canvas._draw_packets() → animace žlutých teček
```

### 3. Pohyb uzlu

```
Uživatel táhne uzel (NodeItem.mouseMoveEvent)
    ↓
Aktualizace node.position
    ↓
QGraphicsView automaticky přesune item
    ↓
itemChange() detekuje změnu pozice
    ↓
QTimer.singleShot(0, _update_connected_connections)
    ↓
Najde všechny ConnectionItem pro tento node
    ↓
Volá conn_item.update_positions()
    ↓
Přepočet Bézierovy křivky
```

---

## Klíčové vzory a principy

### 1. Signal-Slot (Qt)
- Všechny asynchronní operace používají signály
- `data_processed`, `status_changed`, `simulation_started`, atd.

### 2. Graph-based data model
- `Graph` uchovává logická data
- `Canvas` uchovává vizuální reprezentaci
- Synchronizace přes `_redraw_connections()`

### 3. Port-based connections
- Obousměrné spojení (přidává se do obou portů)
- Validace typu a rodiče před spojením

### 4. Buffer-based processing
- Uzly mají buffer pro čekající pakety
- `engine.step()` zpracovává jeden paket za krok

### 5. Item-based rendering
- Každý uzel = `NodeItem` (QGraphicsRectItem)
- Každé spojení = `ConnectionItem` (QGraphicsPathItem)
- Každý port = `PortItem` (QGraphicsEllipseItem)

---

## Známé problémy a omezení

### 1. Propojování portů
- **Opraveno**: `RubberBandDrag` blokoval kliknutí na porty
- **Opraveno**: `itemAt()` nenacházelo port pod uzlem
- **Stávající**: Porty jsou malé (16px), může být obtížné trefit

### 2. Animace paketů
- Používá `time.time()` pro interpolaci – nezávislé na FPS
- Žluté tečky se pohybují lineárně (ne po křivce)

### 3. Simulace
- `engine.step()` zpracovává pouze první paket v bufferu
- Nepodporuje paralelní zpracování
- Žádná priority ve frontě

### 4. Serializace
- `graph.to_dict()` existuje, ale chybí `from_dict()`
- Uzly se neukládají s parametry

### 5. GUI
- Chybí undo/redo
- Chybí zoom to fit
- Chybí export do obrázku/PDF
- Inspector je zjednodušený

---

## Rozšířitelnost

### Přidání nového uzlu

1. Vytvořte třídu v `src/nodes/kategorie.py`:
```python
class MyNewNode(NodeBase):
    def __init__(self, node_id: str):
        super().__init__(node_id, "category", "Název")
        self.add_input("in")
        self.add_output("out")
        self.set_param("param", default)
    
    def process(self, packet, input_port):
        # Implementace
        return new_packet
```

2. Přidejte do `src/nodes/__init__.py`:
```python
from .kategorie import MyNewNode
__all__ = [..., "MyNewNode"]
```

3. Přidejte do `Canvas.add_node_at()` v `src/gui/canvas.py`:
```python
node_classes = {
    ...
    "Název": MyNewNode,
}
```

### Přidání nového algoritmu

1. Vytvořte soubor v `src/algorithms/`
2. Implementujte čistou funkci (bez side-effectů)
3. Importujte v příslušném uzlu

---

## Závislosti

```
PySide6>=6.5.0      # Qt framework pro GUI
PyQtGraph>=0.13.0   # Grafy (momentálně nepoužito)
NumPy>=1.24.0       # Numerické operace (momentálně nepoužito)
Pillow>=10.0.0      # Obrázky (momentálně nepoužito)
```

**Poznámka**: PyQtGraph, NumPy a Pillow jsou v requirements, ale nejsou aktivně používány v aktuální verzi.

---

## Budoucí vylepšení

### Krátkodobá (1-2 týdny)
- [ ] Undo/Redo pro akce na canvasu
- [ ] Lepší detekce portů (zvětšit hit area)
- [ ] Export grafu do JSON
- [ ] Import grafu z JSON
- [ ] Lepší Inspector (dynamické widgety podle parametrů)

### Střednědobá (1-2 měsíce)
- [ ] Více typů uzlů (modulární systém)
- [ ] Plugin systém pro uživatelské uzly
- [ ] Batch simulace (více kroků najednou)
- [ ] Statistiky a reporty
- [ ] Uložení session

### Dlouhodobá (3+ měsíce)
- [ ] Webová verze (WebAssembly)
- [ ] Sdílení grafů (cloud)
- [ ] Pokročilé vizualizace (grafy, tabulky)
- [ ] Unit testy (pytest)
- [ ] CI/CD pipeline

---

## Závěr

InfoFlowLab je dobře strukturovaný projekt s čistým oddělením logiky (core) a prezentace (GUI). Architektura umožňuje snadné přidávání nových uzlů a algoritmů. Hlavní nedostatky jsou v oblasti serializace, testování a pokročilých GUI funkcí, ale základní funkcionalita (vytváření grafů, propojování, simulace) je plně operabilní.

**Doporučení pro další vývoj**:
1. Přidat comprehensive test suite
2. Vytvořit plugin systém pro uzly
3. Vylepšit dokumentaci kódu (docstrings)
4. Přidat type hints všude
5. Vytvořit CI/CD pro automatické testy