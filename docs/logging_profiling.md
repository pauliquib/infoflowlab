# Logování a Profilování v InfoFlowLab

## Přehled

InfoFlowLab obsahuje komplexní systém logování a profilování pro monitorování chodu aplikace a výkonu.

## Soubory s logy

Všechny logy jsou ukládány do adresáře `logs/`:

- **`infoflowlab.log`** - Hlavní log soubor (rotuje při 10MB, max 5 záloh)
- **`errors.log`** - Samostatný log pouze pro chyby (rotuje při 5MB, max 3 zálohy)
- **`profile_YYYYMMDD_HHMMSS.prof`** - Profiling data (binární soubory pro podrobnou analýzu)

## Použití v kódu

### Základní logování

```python
from src.utils.logger import get_logger

# Získání loggeru pro váš modul
logger = get_logger("NazevModulu")

# Různé úrovně logování
logger.debug("Detailní informace pro debugging")
logger.info("Obecné informační zpráva")
logger.warning("Varování - něco se nemusí dařit správně")
logger.error("Chyba - něco se pokazilo")
logger.critical("Kritická chyba - aplikace může být nestabilní")

# Logování výjimek s traceback
try:
    něco_riskantního()
except Exception as e:
    logger.exception("Operace selhala")
```

### Integrace s GUI konzolí

LogManager automaticky přenáší INFO, WARNING a ERROR zprávy do GUI konzole:

```python
from src.utils.logger import log_manager

# Tyto zprávy se objeví jak v souboru, tak v GUI konzoli
log_manager.info("Informace pro uživatele")
log_manager.warning("Upozornění uživatele")
log_manager.error("Chyba viditelná uživateli")
```

### Profilování výkonu

#### 1. Profilování celé aplikace (přes GUI)

V hlavním okně klikněte na:
- **⏱ Start Profiling** - Zahájí sběr dat o výkonu
- **⏹ Stop Profiling** - Zastaví sběr a zobrazí report

#### 2. Profilování programově

```python
from src.utils.logger import log_manager

# Spuštění profilování
log_manager.start_profiling()

# ... váš kód ...

# Zastavení a získání reportu
report = log_manager.stop_profiling(sort_by='cumulative', lines=30)
print(report)
```

#### 3. Měření výkonu konkrétních operací

```python
from src.utils.logger import perf_monitor

# Použití context manageru
with perf_monitor.measure("operace_komprese"):
    # Váš kód
    compress_data(data)

# Získání statistik
stats = perf_monitor.get_stats()
print(stats)
# Výstup:
# {
#     'operace_komprese': {
#         'count': 5,
#         'total': 0.1234,
#         'average': 0.0247,
#         'min': 0.0200,
#         'max': 0.0350
#     }
# }
```

#### 4. Decorator pro měření času funkcí

```python
from src.utils.logger import log_execution_time

@log_execution_time
def moje_funkce():
    # Nějaká práce
    pass
```

## Úrovně logování

Úroveň logování lze změnit za běhu:

```python
from src.utils.logger import log_manager
import logging

# Nastavení úrovně
log_manager.set_level(logging.DEBUG)   # Všechny zprávy
log_manager.set_level(logging.INFO)    # INFO a vyšší
log_manager.set_level(logging.WARNING) # Varování a chyby
log_manager.set_level(logging.ERROR)   # Pouze chyby
```

## Čtení logů

### Z příkazového řádku

```bash
# Posledních 50 řádků hlavního logu
tail -n 50 logs/infoflowlab.log

# Sledování logů v reálném čase
tail -f logs/infoflowlab.log

# Pouze chyby
tail -f logs/errors.log

# Vyhledávání v logu
grep "ERROR" logs/infoflowlab.log
grep "packet.*dropped" logs/infoflowlab.log
```

### Z Pythonu

```python
from src.utils.logger import log_manager

# Posledních N řádků
recent = log_manager.get_recent_logs(lines=100)
print(recent)

# Cesty k log souborům
files = log_manager.get_log_files()
print(files['main_log'])  # logs/infoflowlab.log
print(files['error_log']) # logs/errors.log

# Vymazání všech logů
log_manager.clear_logs()
```

## Analýza profiling dat

Profiling data jsou uložena v binárním formátu `.prof`. Pro analýzu:

```bash
# Zobrazení reportu přímo z terminálu
python -m pstats logs/profile_20260627_080000.prof

# Nebo v Pythonu:
python -c "
import pstats
stats = pstats.Stats('logs/profile_20260627_080000.prof')
stats.sort_stats('cumulative')
stats.print_stats(30)
"
```

### Užitečné příkazy pro pstats

```
stats.sort_stats('cumulative')   # Seřadit podle kumulativního času
stats.sort_stats('total')        # Seřadit podle celkového času
stats.sort_stats('calls')        # Seřadit podle počtu volání
stats.print_stats(20)            # Zobrazit top 20 funkcí
stats.print_callers('function')  # Zobrazit volající konkrétní funkce
```

## Příklad: Kompletní workflow

```python
from src.utils.logger import get_logger, perf_monitor
import logging

# 1. Získání loggeru
logger = get_logger("MojeKomponenta")
logger.setLevel(logging.DEBUG)

# 2. Logování běhu
logger.info("Zahajuji operaci")

# 3. Měření výkonu
with perf_monitor.measure("toto_je_dulezita_operace"):
    # Nějaká práce
    process_data()

# 4. Logging výsledků
stats = perf_monitor.get_stats()
logger.info(f"Výkonnostní statistiky: {stats}")

# 5. Profilování celé sekvence
from src.utils.logger import log_manager
log_manager.start_profiling()

# ... mnoho práce ...

report = log_manager.stop_profiling()
logger.info(f"Profiling dokončen:\n{report}")
```

## Tipy a triky

1. **Debugování problémů s packety:**
   ```python
   logger.debug(f"Packet {packet.id} status: {packet.status}, size: {len(packet.payload)}")
   ```

2. **Sledování výkonu smyček:**
   ```python
   for i, node in enumerate(nodes):
       with perf_monitor.measure(f"node_{i}_process"):
           node.process()
   ```

3. **Logování stavu simulace:**
   ```python
   logger.info(f"Tick {tick}: active={len(active)}, processed={processed}, dropped={dropped}")
   ```

4. **Conditional logging:**
   ```python
   if logger.isEnabledFor(logging.DEBUG):
       # Expensive debug computation
       debug_info = expensive_calculation()
       logger.debug(f"Debug info: {debug_info}")
   ```

## Architektura systému

```
src/utils/logger.py
├── LogManager (singleton)
│   ├── File Handler (rotating)
│   ├── Error Handler (rotating)
│   ├── Console Handler (stdout)
│   ├── GUI Signal (log_message)
│   └── Profiler (cProfile)
├── PerformanceMonitor
│   └── Context manager for timing
└── Utility functions
    ├── get_logger()
    └── log_execution_time() decorator
```

## Konfigurace

Výchozí konfigurace (v `src/utils/logger.py`):

- **Log adresář:** `logs/`
- **Max velikost hlavního logu:** 10 MB
- **Max velikost error logu:** 5 MB
- **Počet záloh:** 5 (hlavní), 3 (errors)
- **Výchozí úroveň:** DEBUG (soubory), INFO (konzole)

Pro změnu konfigurace upravte příslušné hodnoty v `_setup_logging()` metodě.

## Troubleshooting

### Logy se nezapisují
- Zkontrolujte, zda existuje adresář `logs/`
- Zkontrolujte oprávnění k zápisu
- Zkontrolujte, zda není log soubor zamčen jiným procesem

### Profiling nefunguje
- Ujistěte se, že jste stisknuli "Stop Profiling" pro ukončení
- Profiling může zpomalit aplikaci - používejte pouze při potřebě
- Pro analýzu potřebujete nainstalovaný Python s modulem `pstats`

### GUI konzole je pomalá
- LogManager používá bufferování (5 zpráv před flush)
- Pro velmi intenzivní logging zvažte zvýšení bufferu
- V `main_window.py` upravte `if len(self._console_buffer) >= 5:`

## Budoucí vylepšení

- [ ] Logování do JSON formátu pro lepší parsování
- [ ] Webové rozhraní pro prohlížení logů
- [ ] Automatické odesílání chyb na server
- [ ] Grafické zobrazení výkonnostních metrik
- [ ] Export profiling dat do flame graph
- [ ] Integrace s external tools (Sentry, ELK stack)