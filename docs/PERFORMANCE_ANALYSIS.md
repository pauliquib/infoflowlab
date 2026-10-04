# Analýza Výkonu a Optimalizace InfoFlowLab

## Problém: Aplikace "seká" (lag)

Tento dokument pomůže identifikovat a vyřešit příčiny pomalosti.

## Identifikované problémy v kódu

### 1. **KRITICKÉ: Více než 250 000 teček v gridu** 🚨

**Soubor:** `src/gui/canvas.py`, řádek 166-176

```python
def _draw_grid_dots(self):
    """Draw dot grid pattern on background."""
    scene_rect = self.scene.sceneRect()
    # Scene je 10000x10000 pixelů!
    # S gridem 20px = 500x500 = 250 000 teček!
    for x in range(int(scene_rect.left()), int(scene_rect.right()), self._grid_size):
        for y in range(int(scene_rect.top()), int(scene_rect.bottom()), self._grid_size):
            dot = self.scene.addEllipse(x - 1, y - 1, 2, 2, pen, QBrush(grid_color))
            dot.setZValue(-100)
```

**Problém:** 
- Scéna je 10 000 × 10 000 pixelů
- Grid spacing 20px = 500 × 500 = **250 000 QGraphicsEllipseItem objektů**
- Každý objekt spotřebovává paměť a CPU při překreslování

**Řešení:** Viz níže v sekci "Optimalizace"

### 2. **FullViewportUpdate - překresluje vše při každém pohybu**

**Soubor:** `src/gui/canvas.py`, řádek 129

```python
self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
```

**Problém:**
- Při každém pohybu/zoomu se překresluje celá scéna
- S 250 000 tečkami to extrémně zpomaluje

**Řešení:** 
```python
self.setViewportUpdateMode(QGraphicsView.MinimalViewportUpdate)
```

### 3. **Antialiasing všude**

**Soubor:** `src/gui/canvas.py`, řádky 121-123

```python
self.setRenderHint(QPainter.Antialiasing)
self.setRenderHint(QPainter.TextAntialiasing)
self.setRenderHint(QPainter.SmoothPixmapTransform)
```

**Problém:**
- Antialiasing zpomaluje rendering o 2-3x
- Zvláště problémové při zoomu/panu

### 4. **Animace packetů - neefektivní vyhledávání**

**Soubor:** `src/gui/canvas.py`, řádek 641-665

```python
def _animate_packets(self):
    # Pro každý packet prochází všechny uzly a porty
    for packet in list(self.engine.active_packets)[:10]:
        for node in self.graph.nodes.values():  # O(n)
            for port_name, port in node.output_ports.items():  # O(m)
                for conn in port.connections:  # O(k)
                    # ... hledáme connection
```

**Problém:**
- O(n × m × k) složitost při každém animačním ticku (20x za sekundu)
- Měl by být O(1) pomocí mapy

### 5. **Minimap se aktualizuje příliš často**

**Soubor:** `src/gui/canvas.py`, `_update_minimap()`

**Problém:**
- Minimap se aktualizuje při každém zoomu/panu
- `fitInView()` je poměrně náročná operace

## Okamžitá oprava - Rychlé řešení

Vytvořím opravenou verzi `canvas.py` s optimalizacemi:

### Optimalizace 1: Snížení počtu grid teček

```python
def _draw_grid_dots(self):
    """Draw dot grid pattern on background - OPTIMIZED."""
    # Použít menší grid nebo vykreslovat pouze viditelné tečky
    self._grid_size = 40  # Zvětšit z 20 na 40 = 4x méně teček
    
    # NEBO: Vykreslovat pouze tečky v aktuálním viewportu
    # (pokročilejší řešení)
```

### Optimalizace 2: Změna režimu překreslování

```python
# Místo:
self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

# Použít:
self.setViewportUpdateMode(QGraphicsView.MinimalViewportUpdate)
```

### Optimalizace 3: Vypnutí antialiasing pro grid

```python
# Grid tečky nemusí být antialiased
grid_color = QColor("#606060")
pen = QPen(grid_color, 1)
pen.setCosmetic(True)  # Neměnit šířku při zoomu
```

### Optimalizace 4: Cache pro animace packetů

```python
def _animate_packets(self):
    """OPTIMIZED: Use packet-to-connection mapping."""
    # Místo procházení všech uzlů, udržovat mapu: packet_id -> connection
    if not hasattr(self, '_packet_connection_map'):
        self._packet_connection_map = {}
    
    # Aktualizovat pouze aktivní animace
    for anim in self._animations:
        anim.update_position()
```

## Nástroje pro diagnostiku

### 1. Profiler (již implementován)

```bash
# Spusťte aplikaci
python main.py

# V GUI:
# 1. Klikněte ⏱ Start Profiling
# 2. Proveďte problematickou operaci (např. zoom, pan)
# 3. Klikněte ⏹ Stop Profiling
# 4. Analyzujte report - hledejte:
#    - _draw_grid_dots
#    - _animate_packets
#    - paintEvent
#    - update_viewport
```

### 2. Performance Monitor

```python
# Přidat do canvas.py:
from src.utils.logger import perf_monitor

def _animate_packets(self):
    with perf_monitor.measure("canvas_animate_packets"):
        # ... stávající kód
```

### 3. Debug výpis

```python
# Přidat do canvas.py:
import logging
logger = logging.getLogger("Canvas")

def _draw_grid_dots(self):
    logger.info(f"Drawing grid: {self._grid_size}px spacing")
    start = time.time()
    # ... kreslení
    elapsed = (time.time() - start) * 1000
    logger.info(f"Grid drawn in {elapsed:.2f}ms ({count} dots)")
```

## Doporučená oprava

### Krátkodobá (rychlé, ale ne optimální):

1. **Zvětšit grid spacing z 20 na 40px**
2. **Změnit FullViewportUpdate na MinimalViewportUpdate**
3. **Vypnout antialiasing při zoomu/panu**

### Dlouhodobá (správné řešení):

1. **Použít QGraphicsItemGroup pro grid** - všechny tečky jako jeden objekt
2. **Nakreslit grid do pixmapy** - static background image
3. **Vykreslovat grid pomocí QPainter** - v paintEvent místo QGraphicsItem
4. **Optimalizovat animace packetů** - použít mapu packet → connection

## Testování výkonu

### Test 1: Měření grid renderingu

```python
import time
from src.utils.logger import perf_monitor

# V canvas.py:
def _draw_grid_dots(self):
    with perf_monitor.measure("grid_drawing"):
        # ... existující kód
```

### Test 2: Měření animací

```python
def _animate_packets(self):
    with perf_monitor.measure("packet_animation"):
        # ... existující kód
```

### Test 3: Měření překreslování

```python
def paintEvent(self, event):
    with perf_monitor.measure("canvas_paint"):
        # ... existující kód
```

## Očekávané výsledky

### Před optimalizací:
- Grid: ~250 000 objektů, ~500ms při inicializaci
- Zoom/Pan: 100-500ms (závisí na zoom levelu)
- Animace: 20-50ms per frame (při 10 packetech)

### Po optimalizaci:
- Grid: 1 QPixmap objekt, ~10ms
- Zoom/Pan: 10-30ms
- Animace: 2-5ms per frame

## Implementace oprav

Chcete, abych:

1. **Okamžitě opravil kritické problémy** (grid, viewport update)?
2. **Vytvořil diagnostický nástroj** pro měření výkonu?
3. **Implementoval plnou optimalizaci** (grid jako pixmapa)?

## Kontaktní informace pro debugging

Pokud aplikace stále seká po základních opravách:

```bash
# 1. Spusťte s profilingem
python -m cProfile -o profile_output.prof main.py

# 2. Po chvíli (nechte aplikaci běžet) stiskněte Ctrl+C

# 3. Analyzujte
python -c "
import pstats
p = pstats.Stats('profile_output.prof')
p.sort_stats('cumulative')
p.print_stats(50)
"
```

## Časté příčiny lagů

| Příčina | Symptom | Řešení |
|---------|---------|--------|
| 250k grid teček | Pomalý zoom/pan | Zvětšit grid spacing na 40px |
| FullViewportUpdate | Pomalé při pohybu | Změnit na MinimalViewportUpdate |
| Antialiasing | Pomalé rendering | Vypnout při zoomu |
| Animace packetů | CPU 100% | Optimalizovat vyhledávání |
| Mnoho uzlů (>50) | Pomalá simulace | Omezit tick processing |

## Monitoring během běhu

Přidejte do `main_window.py` status bar indikátory:

```python
# FPS counter
self._fps_counter = 0
self._fps_timer = QTimer()
self._fps_timer.timeout.connect(self._update_fps)
self._fps_timer.start(1000)  # Každou sekundu

def _update_fps(self):
    self.lbl_fps.setText(f"FPS: {self._fps_counter}")
    self._fps_counter = 0

# V canvas._animate_packets:
self._fps_counter += 1
```

## Další kroky

1. **Okamžitě**: Zvětšit grid spacing na 40px
2. **Dnes**: Změnit ViewportUpdateMode
3. **Tento týden**: Implementovat grid jako pixmapu
4. **Příště**: Optimalizovat animace packetů

---

**Potřebujete, abych implementoval tyto opravy hned?**