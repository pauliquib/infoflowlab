# Rychlý Start - Logování s logger_config.py

## Přehled

Systém `logger_config.py` poskytuje **neblokující** logovací architekturu založenou na Python `QueueHandler` + `QueueListener`. Logovací volání na hlavním vlákně trvají **< 1 µs** — zaručují, že 60 FPS simulační smyčka není nikdy zablokována I/O operacemi.

## Formát výstupu

Každá zpráva je zobrazena v přesném formátu:

```
[14:02:33.105] [LEVEL] [COMPONENT] - Message
```

Příklad:
- `[14:02:33.105] [INFO] [UI] - Node placed: 'HuffmanEncoder' at (320, 240)`
- `[14:02:33.106] [DEBUG] [ENGINE] - Tick #42 started`
- `[14:02:33.107] [WARNING] [NETWORK] - Cyclic graph detected`
- `[14:02:33.108] [ERROR] [COMPRESSOR] - Encoding failed`

## 1. Instalace a import

Do `main.py` přidejte inicializaci logování hned na začátek:

```python
# main.py — application bootstrap
import sys
sys.path.insert(0, '.')

def main():
    # Inicializace logování (pouze jednou, na začátku)
    from src.utils.logger_config import logger_config
    logger_config.setup(log_file_path="logs/infoflowlab.log")

    # Zbytek aplikace...
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    # ...

if __name__ == "__main__":
    main()
```

Po inicializaci stačí v libovolném modulu zavolat:

```python
from src.utils.logger_config import get_logger
# OR: from src.utils import get_logger (přes __init__.py)

logger = get_logger("UI")     # tag [UI]
logger.info("Uživatel kliknul na tlačítko Start")
```

## 2. Log úrovně a jejich použití

| Úroveň | Kdy použít | Příklad |
|--------|-----------|---------|
| `DEBUG` | Sledování packetů, matematické výpočty, detailní stavy | `logger.debug(f"Packet {id}: entropy=3.2 bits/symbol")` |
| `INFO` | Události uživatele (umístění uzlu, vytvoření spoje) | `logger.info("Node placed at (320, 240)")` |
| `WARNING` | Potenciální problémy (neplatné spoje, cyklické grafy) | `logger.warning("Connection rejected: would create a cycle")` |
| `ERROR` | Systémové chyby, selhání zpracování | `logger.error("Encoding failed: invalid symbol 0xFF")` |

## 3. Komponentní tagování

Každý logger je označen svým komponentem. Tag se automaticky objeví v hranatých závorkách:

```python
ui_log     = get_logger("UI")          # [UI]
engine_log = get_logger("ENGINE")      # [ENGINE]
net_log    = get_logger("NETWORK")     # [NETWORK]
comp_log   = get_logger("COMPRESSOR")  # [COMPRESSOR]
node_log   = get_logger("HuffmanEncoder")  # [HuffmanEncoder]
insp_log   = get_logger("Inspector")   # [Inspector]
```

## 4. Použití uvnitř NodeBase.process()

Přidejte logování přímo do metody `process()` vašeho uzlu:

```python
# src/nodes/compressors.py
from src.utils.logger_config import get_logger

class HuffmanEncoder(NodeBase):
    def __init__(self, node_id: str):
        super().__init__(node_id, "huffman_encoder", "Huffman Encoder", "compressors")
        self.log = get_logger("HuffmanEncoder")  # JEDEN logger po celý životnost

    def process(self, packet, input_port):
        self.log.info(f"Encoding packet {packet.id}: size={len(packet.payload)} bytes")

        # DEBUG: detailní výpočty (pouze ve verbose režimu)
        self.log.debug(f"Building Huffman tree from {len(frequencies)} symbols")
        self.log.debug(f"Compression ratio: {ratio:.2f}, saved: {saved} bytes")

        if compression_ratio < 0.5:
            self.log.warning(f"Low compression ratio ({ratio:.2f})")

        try:
            result = self._encode(packet.payload)
            return DataPacket(result)
        except ValueError as e:
            self.log.error(f"Encoding failed: {e}")
            raise
```

## 5. Použití v UI event handlerech

```python
# src/gui/canvas.py
from src.utils.logger_config import get_logger

class SimulationCanvas(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.log = get_logger("UI")

    def on_node_placed(self, node_type, pos):
        self.log.info(f"Node placed: '{node_type}' at position ({pos.x()}, {pos.y()})")

    def on_connection_created(self, src, dst):
        self.log.info(f"Connection created: {src}.output -> {dst}.input")

    def on_connection_rejected(self, reason):
        self.log.warning(f"Connection rejected: {reason}")
```

## 6. Přepínání DEBUG / PRODUCTION režimu

V produkčním režimu se na konzoli zobrazují pouze WARNING a ERROR zprávy.
DEBUG a INFO jsou potlačeny (stále se však ukládají do souboru).

```python
from src.utils.logger_config import logger_config

# Produkční režim: pouze varování a chyby na konzoli
logger_config.set_verbose(False)

# Debug režim: vše (výchozí)
logger_config.set_verbose(True)

# Zjištění aktuálního stavu
if logger_config.is_verbose():
    print("Debug režim je aktivní")
```

### Doporučené použití:

Přidejte přepínač do GUI nebo použijte environment proměnnou:

```python
import os
from src.utils.logger_config import logger_config

# Podle proměnné prostředí
if os.getenv("INFOFLOWLAB_LOG_LEVEL", "").upper() == "PRODUCTION":
    logger_config.set_verbose(False)
```

Nebo do menu v hlavním okně:

```python
def toggle_verbose_logging(self, enabled: bool):
    logger_config.set_verbose(enabled)
    status = "DEBUG" if enabled else "PRODUCTION"
    self.status_bar.showMessage(f"Log level: {status}", 3000)
```

## 7. Testování systému

```bash
# Spuštění komplexního demonstračního skriptu
python test_logger_config.py

# Otestování všech úrovní a komponent
python -c "
from src.utils.logger_config import logger_config, get_logger
logger_config.setup()
get_logger('TEST').debug('Debug test')
get_logger('TEST').info('Info test')
get_logger('TEST').warning('Warning test')
get_logger('TEST').error('Error test')
logger_config.shutdown()
"
```

## 8. Ukázka kompletního výstupu

```
[05:03:38.883] [INFO]    [InfoFlowLab]      - ============================================================
[05:03:38.883] [INFO]    [InfoFlowLab]      - Non-blocking logging system initialized
[05:03:38.883] [INFO]    [InfoFlowLab]      - Log file: logs/infoflowlab.log
[05:03:38.883] [INFO]    [InfoFlowLab]      - ============================================================
[05:03:38.883] [DEBUG]   [InfoFlowLab.TEST] - debug test
[05:03:38.883] [INFO]    [InfoFlowLab.TEST] - info test
[05:03:38.883] [WARNING] [InfoFlowLab.TEST] - warning test
[05:03:38.883] [ERROR]   [InfoFlowLab.TEST] - error test
[05:04:25.123] [INFO]    [UI]               - Node placed: 'HuffmanEncoder' at (320, 240)
[05:04:25.124] [WARNING] [NETWORK]          - Connection rejected: cyclic graph detected
[05:04:25.125] [ERROR]   [HuffmanEncoder]   - Encoding failed: invalid symbol 0xFF
```

## 9. Výkon

Non-blocking QueueHandler zajišťuje:
- **< 1 µs** na logovací volání na hlavním vlákně
- Samostatné vlákno zapisuje logy na disk na pozadí
- 10 000 zpráv je zalogováno za ~0.02 s (500 000 msg/s)
- Při 60 FPS je jeden tick = 16.67 ms → logování je **zcela zanedbatelné**

## 10. Struktura souborů

```
InfoFlowLab/
├── src/utils/
│   ├── logger_config.py        # Hlavní logovací systém (QueueHandler + QueueListener)
│   ├── logger.py               # Původní logovací systém (zpětná kompatibilita)
│   └── __init__.py             # Exportuje logger_config a get_logger
├── test_logger_config.py       # Komplexní demonstrační/testovací skript
└── docs/
    ├── QUICK_START_LOGGING.md  # Tento soubor
    └── logging_profiling.md    # Plná dokumentace (včetně profilování)
```

## API Reference

### `logger_config.setup(log_file_path="logs/infoflowlab.log", level=logging.DEBUG)`
Inicializuje logovací systém. Volá se jednou při startu aplikace.

### `get_logger(name: str) -> logging.Logger`
Vrátí logger s daným komponentním tagem. Lze volat kdykoliv po `setup()`.

### `logger_config.set_verbose(enabled: bool)`
- `True` → DEBUG režim (všechny zprávy na konzoli)
- `False` → PRODUCTION režim (pouze WARNING+)

### `logger_config.is_verbose() -> bool`
Zjištění aktuálního režimu.

### `logger_config.shutdown()`
Řádné ukončení (zastaví listener, uzavře handlery).