# 🧪 Kompletní Checklist pro Ověření Všech Funkcí InfoFlowLab v1.0

Tento dokument slouží jako **podrobný návod k otestování všech funkcí** programu InfoFlowLab v1.0.
Každá položka obsahuje **krok za krokem** postup ověření a očekávaný výsledek.
Postupujte **od nejdůležitějších funkcí k méně důležitým**.

---

## 📋 Obsah

1. [Základní spuštění a načtení aplikace](#1-základní-spuštění-a-načtení-aplikace)
2. [Hlavní toolbar a simulační ovládání](#2-hlavní-toolbar-a-simulační-ovládání)
3. [Canvas (plátno) - práce s prvky](#3-canvas-plátno---práce-s-prvky)
4. [Sidebar (levý panel) - kategorie a přidávání uzlů](#4-sidebar-levý-panel---kategorie-a-přidávání-uzlů)
5. [Inspector (pravý panel) - prohlížení a editace](#5-inspector-pravý-panel---prohlížení-a-editace)
6. [Propojování uzlů (connection system)](#6-propojování-uzlů-connection-system)
7. [Simulační engine](#7-simulační-engine)
8. [Packet animace](#8-packet-animace)
9. [Uzly - zdroje (Sources)](#9-uzly---zdroje-sources)
10. [Uzly - kódovače (Encoders)](#10-uzly---kódovače-encoders)
11. [Uzly - dekódovače (Decoders)](#11-uzly---dekódovače-decoders)
12. [Uzly - komprese (Compressors)](#12-uzly---komprese-compressors)
13. [Uzly - kanály (Channels)](#13-uzly---kanály-channels)
14. [Uzly - ECC (Error Correction Code)](#14-uzly---ecc-error-correction-code)
15. [Uzly - kontrolní součty (Checksums)](#15-uzly---kontrolní-součty-checksums)
16. [Uzly - analyzátory (Analyzers)](#16-uzly---analyzátory-analyzers)
17. [Uzly - výstupy (Sinks)](#17-uzly---výstupy-sinks)
18. [Konzole a logování](#18-konzole-a-logování)
19. [Profilování výkonu](#19-profilování-výkonu)
20. [Ukládání a načítání scénářů](#20-ukládání-a-načítání-scénářů)
21. [Export obrázku a Zoom to Fit](#21-export-obrázku-a-zoom-to-fit)
22. [Nápověda a dokumentace](#22-nápověda-a-dokumentace)
23. [Resetování aplikace](#23-resetování-aplikace)
24. [Marquee výběr a hromadné operace](#24-marquee-výběr-a-hromadné-operace)
25. [Minimapa](#25-minimapa)
26. [Komplexní end-to-end testy](#26-komplexní-end-to-end-testy)
27. [Testování hraničních situací](#27-testování-hraničních-situací)

---

## 1. Základní spuštění a načtení aplikace

### 1.1 Spuštění aplikace
- [X] **Postup**: Spusťte `python main.py` (nebo `make run` pokud je Makefile)
- [X] **Očekávaný výsledek**: 
  - Objeví se hlavní okno s názvem **"InfoFlowLab v1.0 - Simulátor komprese a komunikace"**
  - Velikost okna je cca 1600×950 px
  - Tmavé téma (dark theme) - pozadí #1e1e1e, text #d4d4d4
  - Aplikace používá Fusion styl pro konzistentní vzhled napříč platformami
- [X] **Ověření**: Podívejte se na horní lištu okna, zda obsahuje správný titulek

### 1.2 Ikona aplikace
- [X] **Postup**: Po spuštění zkontrolujte ikonu v hlavním panelu a v záhlaví okna
- [X] **Očekávaný výsledek**: Ikona je nastavena z `icon.ico` (nebo `icon.icns` na macOS)

### 1.3 Inicializace logovacího systému
- [X] **Postup**: Po spuštění zkontrolujte konzoli v dolní části okna
- [X] **Očekávaný výsledek**: 
  - V konzoli se zobrazí: `"InfoFlowLab v1.0 initialized"`
  - Následně: `"Ready for simulation. Drag nodes from the sidebar."`

### 1.4 Status bar
- [X] **Postup**: Podívejte se na stavový řádek (je-li implementován)
- [X] **Očekávaný výsledek**: Zobrazuje indikátor stavu připravenosti

---

## 2. Hlavní toolbar a simulační ovládání

### 2.1 Tlačítko Play (▶)
- [X] **Postup**: 
  1. Přidejte alespoň jeden zdrojový uzel (např. Text) na canvas
  2. Klikněte na tlačítko **▶ Play**
- [X] **Očekávaný výsledek**: [ano ale animace se přehraje jen jednou, místo opakovaně]
  - Status indikátor se změní na "● Running"
  - Engine přejde do režimu RUNNING
  - Začnou se generovat ticky (vidíte v labelu "Tick: 1", "Tick: 2", ...)
  - V konzoli se objeví: `"Simulation started (Real-time mode)"`

### 2.2 Tlačítko Pause (⏸)
- [x] **Postup**: Během běžící simulace klikněte na **⏸ Pause**
- [x] **Očekávaný výsledek**:
  - Status se změní na "● Paused"
  - Engine přejde do režimu PAUSED
  - Ticky se zastaví (label zůstává na aktuální hodnotě)
  - V konzoli: `"Simulation paused"`

### 2.3 Tlačítko Step (⏭)
- [x] **Postup**: Po pauze nebo i v idle stavu klikněte na **⏭ Step**
- [x] **Očekávaný výsledek**:
  - Provede se jeden simulační krok (tick)
  - Tick label se zvýší o 1
  - V konzoli: `"Step executed (tick X)"`
  - Uzly zpracují data (pokud jsou v bufferu)

### 2.4 Tlačítko Stop (⏹)
- [x] **Postup**: Klikněte na **⏹ Stop** (během simulace nebo po pauze)
- [x] **Očekávaný výsledek**:
  - Status se změní na "● Stopped"
  - Engine přejde do režimu IDLE
  - Tick label se vynuluje: "Tick: 0"
  - Všechny packet animace zmizí
  - V konzoli: `"Simulation stopped"`

### 2.5 Tlačítko Inject (💉) - Vložení testovacího packetu
- [ ] **Postup**: 
  1. Přidejte zdrojový uzel (např. Text) na canvas
  2. Klikněte na **💉 Inject**
- [ ] **Očekávaný výsledek**:
  - Do zdrojového uzlu je injikován packet s payloadem "Hello World!"
  - V konzoli: `"Injected packet pkt_XXXXXX into [node_name]"`
  - **Pokud není žádný source uzel**: v konzoli se zobrazí warning: `"No source node found to inject packet"`
  
  nefunguje, pouze vzdy vypíše ([12:30:12] Injected packet pkt_13ef43 into 📝 Text)
  
### 2.6 Speed slider (Rychlost simulace)
- [x] **Postup**: 
  1. Spusťte simulaci
  2. Posuňte slider Rychlost doprava/doleva
- [x] **Očekávaný výsledek**:
  - Label vedle slideru se mění (např. "0.5x", "1.0x", "3.5x")
  - Při vyšší rychlosti ticky přibývají rychleji
  - Rozsah: 0.1x až 5.0x

  ještě by bylo potřeba aby animace souhlasila s tím co se aktuálně děje

### 2.7 Tick interval (Tick (ms))
- [ ] **Postup**: 
  1. Změňte hodnotu v spinboxu "Tick (ms)" na např. 500 ms
  2. Spusťte simulaci
- [ ] **Očekávaný výsledek**:
  - Ticky přibývají pomaleji (každých 500 ms)
  - Rozsah: 10 ms až 1000 ms

  pokud je takovy rozsah, nemělo by pole uživateli dovolit zadávat hodnoty které jsou mimo meze 10-1000 ms

### 2.8 Snap-to-grid tlačítko
- [ ] **Postup**: 
  1. Klikněte na tlačítko **Snap-to-grid** (ON/OFF)
  2. Přetáhněte uzel na canvasu
- [ ] **Očekávaný výsledek**:
  - Když je **ON**: uzly přeskakují na nejbližší mřížku (grid 40px)
  - Když je **OFF**: uzly lze umístit libovolně
  - Tlačítko mění text mezi "ON" a "OFF"

  ikdyž je v režimu ON, tak se prvky nepřichytávají k mřížce
  funguje jen v moment uplne noveho vytvoreni prvku na platno, ale ne při posouvání s již existujícím prvkem po plátně
  
  
## 3. Canvas (plátno) - práce s prvky

### 3.1 Vyvolání canvasu a zobrazení gridu
- [x] **Postup**: Po spuštění se podívejte na střední část okna
- [x] **Očekávaný výsledek**:
  - Zobrazuje se tmavé plátno s tečkovaným gridem
  - Rozteč teček je 40px
  - Plátno je připraveno pro přidávání uzlů

### 3.2 Zoom (Ctrl+Scroll)
- [ ] **Postup**: 
  1. Podržte **Ctrl** a otáčejte kolečkem myši nahoru/dolů
  2. Sledujte změnu přiblížení
- [ ] **Očekávaný výsledek**:
  - Scroll nahoru: přiblížení (zoom in) - max 3.0x
  - Scroll dolů: oddálení (zoom out) - min 0.25x
  - Zoom se provádí pod kurzorem myši (AnchorUnderMouse)

### 3.3 Pan (posun plátna středním tlačítkem)
- [ ] **Postup**: 
  1. Podržte **střední tlačítko myši** (kolečko)
  2. Pohybujte myší
- [ ] **Očekávaný výsledek**:
  - Kurzor se změní na zavřenou ruku
  - Plátno se plynule posouvá
  - Po uvolnění se kurzor vrátí na šipku
  
  hrozně se seká při teto akci

### 3.4 Drag & Drop ze sidebaru na canvas
- [x] **Postup**: 
  1. V levém sidebaru najděte kategorii "1. Zdroje (Sources)"
  2. Klikněte na tlačítko "Text" a táhněte na plátno
- [x] **Očekávaný výsledek**:
  - Během tažení se zobrazuje "ghost" (průhledný obdélník s názvem)
  - Po puštění se uzel objeví na canvasu na pozici, kde byl upuštěn
  - Uzel se přichytí na grid (je-li snap-to-grid zapnutý)

### 3.5 Výběr uzlu kliknutím
- [x] **Postup**: Klikněte na libovolný uzel na canvasu
- [x] **Očekávaný výsledek**:
  - Uzel se zvýrazní (ohraničení)
  - V pravém Inspector panelu se zobrazí jeho vlastnosti

### 3.6 Smazání uzlu (Delete/Backspace)
- [x] **Postup**: 
  1. Vyberte uzel kliknutím
  2. Stiskněte **Delete** nebo **Backspace**
- [x] **Očekávaný výsledek**:
  - Uzel zmizí z canvasu
  - Všechna propojení k/od tohoto uzlu jsou odstraněna
  - Inspector se vyčistí (zobrazí "No node selected")

### 3.7 Zrušení výběru (Escape)
- [ ] **Postup**: 
  1. Vyberte uzel
  2. Stiskněte **Escape**
- [ ] **Očekávaný výsledek**: Výběr se zruší (pokud je tato funkce implementována)

  tato funkce nefunguje s klavesou escape, ale uzivatel mui kliknout do prazdneho prostoru na platne
  
  
### 3.8 Přesouvání uzlu
- [x] **Postup**: 
  1. Klikněte a podržte levé tlačítko na uzlu
  2. Přetáhněte uzel na nové místo
- [x] **Očekávaný výsledek**:
  - Uzel se pohybuje s myší
  - Propojení zůstávají (aktualizují se podle nové pozice)
  - Pokud je snap-to-grid zapnutý, uzel přeskakuje na grid

---

## 4. Sidebar (levý panel) - kategorie a přidávání uzlů

### 4.1 Zobrazení kategorií
- [x] **Postup**: Po spuštění se podívejte na levý panel
- [x] **Očekávaný výsledek**: Je vidět 7 kategorií:
  1. **Zdroje (Sources)** - 📝 zelená
  2. **Zpracování a Komprese (Source Coding)** - 🗜️ modrá
  3. **Zabezpečení proti chybám (Channel Coding)** - 🛡️ oranžová
  4. **Přenosové Kanály (Environment)** - 📡 fialová
  5. **Dekódování na příjmu (Receivers)** - 🔁 cyan
  6. **Kontrolní kódy (Checksums)** - ✅ světle zelená
  7. **Měření a Výstupy (Analytics)** - 📊 červeno-oranžová

### 4.2 Rozbalování a sbalování kategorií (Accordion)
- [ ] **Postup**: Klikněte na název kategorie (např. "1. Zdroje (Sources)")
- [ ] **Očekávaný výsledek**:
  - Kategorie se rozbalí/sbalí s plynulou animací (150 ms)
  - Při rozbalení se zobrazí tlačítka jednotlivých uzlů
  - V každé kategorii je subtitle (popis) pod názvem

   nefunguje, sice proběhne pokus o rozbalení, ale program stále drží okna rozbalené a neumí je sbalit. někdy náhodně jsou nabídky sbalené/minimilizovane, ale uplně nahodně a bez řádu. Prosím opravit.
   
### 4.3 Vyhledávání v sidebaru
- [x] **Postup**: 
  1. Napište text do vyhledávacího pole "🔍 Hledat" (např. "Hamming")
  2. Sledujte výsledky
- [x] **Očekávaný výsledek**:
  - Zobrazí se pouze kategorie obsahující hledaný text
  - Vyhovující kategorie se automaticky rozbalí
  - Ostatní kategorie se automaticky skryjí
  - Tlačítka, která neodpovídají hledání, se skryjí
  - Po smazání textu se obnoví původní stav

### 4.4 Drag & Drop ze sidebaru (ghost node)
- [ ] **Postup**: 
  1. Rozbalte kategorii "Zdroje"
  2. Klikněte na "Random" a táhněte
- [x] **Očekávaný výsledek**:
  - Objeví se průhledný ghost obdélník (180×32 px) s textem "Random"
  - Po puštění na canvasu se vytvoří RandomSourceNode na pozici kurzoru
  
  funguje, jen bych potřeboval přidat označovací podmínku v levem sidebaru pro prvky tak, aby mohl být označený jen jeden prvek.

### 4.5 Seznam všech uzlů v sidebaru
- [x] **Ověřte, že sidebar obsahuje všechny tyto uzly**:

| Kategorie | Uzly |
|-----------|------|
| **Zdroje** | Text, Random, Číslo, AudioSrc, ImageSrc |
| **Zpracování** | Base64, BaseConv, UTF-8, Morse, HuffmanEnc, Hex, RLE, Huffman, LZ77, LZW |
| **Zabezpečení** | Hamming74, Hamming1511, CRC8, CRC16, CRC32, ReedSolomon, ReedSolomonDec, ParityEnc, ParityDec |
| **Kanály** | Ideal, BSK, GilbertElliott, AWGN |
| **Dekódování** | Base64Dec, MorseDec, UTF-8Dec, HuffmanDec |
| **Kontrolní kódy** | EAN, ISBN, ISSN, Luhn, Verhoeff, ICO |
| **Měření** | Entropie, Frekvence, CompRatio, BER Meter, LatencyMeter, TextOut, Soubor, Konzole, HexDump, Compare |

### 4.6 Informační lišta v sidebaru
- [x] **Ověření**: Ve spodní části sidebaru je text "💡 Přetáhněte prvek na plátno" a "Klikněte na kategorii pro rozbalení"

Tady bych velice rád přidal možnost v nastavení aplikace pro vypnutí všech informačních prvků z aplikace jako rezim zen-pro

---

## 5. Inspector (pravý panel) - prohlížení a editace

### 5.1 Zobrazení Inspectoru bez výběru
- [x] **Postup**: Po spuštění se podívejte na pravý panel před výběrem uzlu
- [x] **Očekávaný výsledek**:
  - Nadpis: "Inspector"
  - Text: "No node selected\n\nSelect a node on the canvas\nto inspect its properties."

### 5.2 Sekce Basic Info
- [x] **Postup**: Vyberte uzel na canvasu
- [x] **Očekávaný výsledek**:
  - Nadpis se změní na název uzlu (např. "📝 Text")
  - **Basic Info** sekce obsahuje:
    - **ID**: zkrácené ID uzlu (prvních 12 znaků...)
    - **Type**: typ uzlu (např. "source")
    - **Category**: kategorie (např. "sources" - zeleně)
    - **Status**: aktuální stav (např. "idle" - žlutě)
    - **Position**: souřadnice (např. "(0, 0)")

### 5.3 Sekce Parameters - editace parametrů
- [ ] **Postup**: V Inspectoru najděte sekci "Parameters"
- [ ] **Očekávaný výsledek**:
  - Zobrazují se parametry podle typu uzlu (schema-driven UI)
  - Různé widgety podle typu parametru:
    - **INT**: SpinBox + Slider
    - **FLOAT**: DoubleSpinBox + Slider
    - **STR**: QLineEdit
    - **CHOICE**: QComboBox (dropdown)
    - **BOOL**: QCheckBox
    - **TEXT**: QTextEdit (víceřádkový)
  - Každý parametr má tooltip s popisem
  - Po změně hodnoty se parametr propíše do uzlu a do konzole: `"Param key=value set on node XXXXXXXX"`

  moc nerozumim tomuto kroku
  
### 5.4 Sekce Statistics
- [ ] **Postup**: Po spuštění simulace a zpracování dat vyberte uzel
- [ ] **Očekávaný výsledek**:
  - **Packets processed**: počet zpracovaných packetů
  - **Packets dropped**: počet ztracených packetů
  - **Avg latency**: průměrná latence v ms
  - **Buffer size**: aktuální velikost bufferu / max (např. "3/100")
  - U specifických uzlů další metriky (entropie, efficiency, output text atd.)

### 5.5 Sekce History
- [ ] **Postup**: Po simulaci vyberte uzel, který zpracoval packety
- [ ] **Očekávaný výsledek**:
  - Zobrazuje historii posledních 10 packetů
  - Formát: `[node_name] operation: input_size→output_size`
  - Pokud není historie: "No data"

### 5.6 Sekce Theory
- [ ] **Postup**: Vyberte libovolný uzel
- [ ] **Očekávaný výsledek**:
  - Zobrazuje se teoretický popis dané kategorie
  - Např. pro source: "Data source node. Generates or provides input data for the simulation pipeline."

### 5.7 Změna parametru a ověření propisu do uzlu
- [ ] **Postup**: 
  1. Vyberte TextSourceNode
  2. V Inspectoru změňte parametr "Source Text" na "Testovací data"
  3. Spusťte Inject
- [ ] **Očekávaný výsledek**: 
  - Nový text se použije při generování packetu
  - V konzoli se objeví zpráva o změně parametru

---

## 6. Propojování uzlů (connection system)

### 6.1 Vytvoření propojení (z portu na port)
- [ ] **Postup**: 
  1. Přidejte na canvas dva uzly (např. Text a Base64)
  2. Klikněte na výstupní port prvního uzlu (malý kroužek na pravé straně)
  3. Táhněte na vstupní port druhého uzlu (malý kroužek na levé straně)
  4. Pusťte myš
- [ ] **Očekávaný výsledek**:
  - Během tažení se zobrazuje **dočasná Bézierova křivka** z portu k kurzoru
  - Po puštění se vytvoří **trvalá spojovací čára** (Bézierova křivka)
  - V konzoli by se měla objevit zpráva o vytvoření spojení

### 6.2 Validace datových typů portů
- [ ] **Postup**: Zkuste propojit nekompatibilní porty (např. audio výstup s textovým vstupem)
- [ ] **Očekávaný výsledek**: 
  - Spojení se nevytvoří
  - V konzoli se objeví chybová zpráva (např. "Incompatible data types")
  - Porty jsou barevně odlišeny podle datového typu

### 6.3 Zrušení propojování (Escape)
- [ ] **Postup**: 
  1. Klikněte na port a začněte táhnout
  2. Stiskněte **Escape**
- [ ] **Očekávaný výsledek**: 
  - Dočasná čára zmizí
  - Port se vrátí do původního stavu

### 6.4 Odstranění propojení
- [ ] **Postup**: Klikněte na existující spojovací čáru a stiskněte Delete
- [ ] **Očekávaný výsledek**: 
  - Spojení se odstraní
  - Data již neprocházejí mezi uzly

### 6.5 Detekce cyklů v grafu
- [ ] **Postup**: 
  1. Vytvořte A → B → C
  2. Zkuste vytvořit C → A
- [ ] **Očekávaný výsledek**: 
  - Spojení se vytvoří (propojení je povoleno)
  - V konzoli nebo logu se objeví warning: "Warning: Connection would create a cycle in the graph"
  - Uživatel je upozorněn na cyklus

### 6.6 Aktualizace spojení při přesunu uzlu
- [ ] **Postup**: 
  1. Vytvořte propojení A → B
  2. Přesuňte uzel A na jiné místo
- [ ] **Očekávaný výsledek**: 
  - Spojovací čára se plynule aktualizuje podle nové pozice

---

## 7. Simulační engine

### 7.1 Režimy simulace
- [ ] **Ověřte všechny 4 režimy**:
  - **IDLE**: Po spuštění nebo po stop
  - **RUNNING**: Po kliknutí na Play
  - **PAUSED**: Po kliknutí na Pause
  - **STEP**: Po kliknutí na Step (jednorázově)

### 7.2 Tick counting
- [ ] **Postup**: Spusťte simulaci a sledujte label "Tick: X"
- [ ] **Očekávaný výsledek**: 
  - Tick se zvyšuje při každém cyklu enginu
  - V RUNNING režimu přibývá automaticky podle nastaveného intervalu

### 7.3 Zpracování zdrojových uzlů za tick
- [ ] **Postup**: 
  1. Přidejte TextSourceNode
  2. Spusťte Play
- [ ] **Očekávaný výsledek**: 
  - Každý tick engine generuje packety ze zdrojových uzlů
  - Číslo v "Packets processed" v Inspectoru roste

### 7.4 Propagace dat přes propojené uzly
- [ ] **Postup**: 
  1. Vytvořte řetězec: Text → Base64 → TextOut
  2. Spusťte Inject
- [ ] **Očekávaný výsledek**: 
  - Data procházejí celým řetězcem
  - Každý uzel provede svou transformaci
  - TextOut zobrazí výsledek (v Inspectoru v sekci Statistics)

### 7.5 Reset enginu
- [ ] **Postup**: 
  1. Spusťte simulaci (necháme pár ticků)
  2. Klikněte na **↺ Reset**
- [ ] **Očekávaný výsledek**: 
  - Všechny packety zmizí
  - Statistiky se vynulují
  - Všechny uzly se resetují (buffer, počítadla)
  - Status: "● Ready", Tick: "Tick: 0"

### 7.6 Záznam událostí (event log)
- [ ] **Postup**: Tato funkce se aktivuje voláním `start_recording()` na enginu (programaticky)
- [ ] **Očekávaný výsledek**: 
  - Engine ukládá události (inject, process, drop, tick) do `event_log`
  - Po zastavení nahrávání lze log exportovat

---

## 8. Packet animace

### 8.1 Animace packetů při Play
- [ ] **Postup**: 
  1. Vytvořte řetězec: Text → Base64 → TextOut
  2. Spusťte Play
- [ ] **Očekávaný výsledek**: 
  - Po spojích se pohybují animované tečky/kuličky představující packety
  - Animace běží 20 fps (50 ms interval)
  - Maximálně 5 současných animací (performance limit)

### 8.2 Zastavení animací při Stop
- [ ] **Postup**: Během běžící simulace klikněte na Stop
- [ ] **Očekávaný výsledek**: Všechny animace packetů okamžitě zmizí

### 8.3 Zastavení animací při Pause
- [ ] **Postup**: Během běžící simulace klikněte na Pause
- [ ] **Očekávaný výsledek**: Animace se zastaví (nezmizí)

---

## 9. Uzly - zdroje (Sources)

### 9.1 TextSourceNode (📝 Text)
- [ ] **Funkce**: Generuje textová data
- [ ] **Parametry**: Source Text (TEXT), Encoding (CHOICE: utf-8, ascii, utf-16, iso-8859-2)
- [ ] **Test**:
  1. Přidejte Text → TextOut
  2. Klikněte Inject
  3. **Očekávaný výsledek**: V TextOut v sekci Statistics se zobrazí "Hello World! InfoFlowLab v1.0" (nebo vlastní text)
  4. Změňte text v Inspectoru a opakujte Inject
  5. Změňte encoding na "ascii" a ověřte funkčnost

### 9.2 RandomSourceNode (🎲 Random)
- [ ] **Funkce**: Generuje náhodná data s nastavitelnou entropií
- [ ] **Parametry**: Length (INT), Entropy Target (FLOAT 0-8), Seed (INT)
- [ ] **Test**:
  1. Přidejte Random → TextOut
  2. Nastavte Length=50, Entropy=8.0
  3. Inject
  4. **Očekávaný výsledek**: Vygeneruje se 50 náhodných bytů (vysoká entropie)
  5. Nastavte Entropy=1.0, Seed=42
  6. Inject dvakrát - **očekávejte stejný výsledek** (seed fixuje generátor)

### 9.3 NumberInputNode (🔢 Číslo)
- [ ] **Funkce**: Generuje číselnou hodnotu v dané bázi
- [ ] **Parametry**: Value (STR), Base (INT 2-36), Label (STR)
- [ ] **Test**:
  1. Přidejte Číslo → BaseConv
  2. Nastavte Value="255", Base=10
  3. V BaseConv nastavte From Base=10, To Base=2
  4. Inject
  5. **Očekávaný výsledek**: Výstup "11111111" (255 v binární)

### 9.4 AudioSourceNode (🎵 AudioSrc)
- [ ] **Funkce**: Generuje testovací audio tón (440 Hz)
- [ ] **Parametry**: File Path (STR), Sample Rate (INT 8000-192000)
- [ ] **Test**:
  1. Přidejte AudioSrc → HexDump
  2. Inject
  3. **Očekávaný výsledek**: Vygeneruje se 440 Hz sinusový tón (100 ms)
  4. Zkuste změnit Sample Rate na 48000

### 9.5 ImageSourceNode (🖼️ ImageSrc)
- [ ] **Funkce**: Generuje testovací gradientní obrázek
- [ ] **Parametry**: Width (INT 8-512), Height (INT 8-512)
- [ ] **Test**:
  1. Přidejte ImageSrc → HexDump
  2. Nastavte Width=16, Height=16
  3. Inject
  4. **Očekávaný výsledek**: Vygeneruje se 16×16×3 = 768 bytů RGB dat

---

## 10. Uzly - kódovače (Encoders)

### 10.1 Base64EncoderNode (🔐 Base64)
- [ ] **Funkce**: Base64 kódování
- [ ] **Parametry**: URL Safe (BOOL)
- [ ] **Test**:
  1. Text → Base64 → TextOut
  2. V TextSource nastavte text "Hello"
  3. Inject
  4. **Očekávaný výsledek**: "Hello" → "SGVsbG8=" (Base64)
  5. Zapněte URL Safe → "SGVsbG8=" (stejné, liší se jen u znaků +/)

### 10.2 HexEncoderNode (🔢 Hex)
- [ ] **Funkce**: Hex kódování (binární data na hexadecimální řetězec)
- [ ] **Test**:
  1. Text → Hex → TextOut
  2. Text: "ABC"
  3. Inject
  4. **Očekávaný výsledek**: "ABC" → "414243" (hexadecimální reprezentace)

### 10.3 BaseConverterNode (🔀 BaseConv)
- [ ] **Funkce**: Převod mezi číselnými soustavami (2-36)
- [ ] **Parametry**: From Base (INT), To Base (INT), Signed (BOOL), Word Size (INT)
- [ ] **Test**:
  1. Číslo → BaseConv → TextOut
  2. Číslo: Value="255", Base=10
  3. BaseConv: From=10, To=16
  4. Inject → **Očekávaný výsledek**: "FF"
  5. Změňte To=2 → "11111111"

### 10.4 Utf8EncoderNode (🔤 UTF-8)
- [ ] **Funkce**: UTF-8 kódování textu
- [ ] **Test**:
  1. Text → UTF-8 → TextOut
  2. Text: "Čeština"
  3. Inject
  4. **Očekávaný výsledek**: Text je zakódován do UTF-8 bytů

### 10.5 MorseEncoderNode (📻 Morse)
- [ ] **Funkce**: Kódování textu do Morseovy abecedy
- [ ] **Parametry**: Speed (WPM) (INT 5-100)
- [ ] **Test**:
  1. Text → Morse → TextOut
  2. Text: "SOS"
  3. Inject
  4. **Očekávaný výsledek**: "SOS" → "... --- ..."

### 10.6 HuffmanEncoderNode (🌳 HuffmanEnc)
- [ ] **Funkce**: Huffmanovo kódování (komprese) s kódovou tabulkou
- [ ] **Test**:
  1. Text → HuffmanEnc → TextOut
  2. Text: "AAAAABBBCCD" (častější znaky = kratší kód)
  3. Inject
  4. **Očekávaný výsledek**: Vygeneruje se JSON s encoded string a codes dictionary
  5. Sledujte compression ratio v historii

---

## 11. Uzly - dekódovače (Decoders)

### 11.1 Base64DecoderNode (🔐 Base64Dec)
- [ ] **Funkce**: Base64 dekódování
- [ ] **Test**:
  1. Text → Base64 → Base64Dec → TextOut
  2. Text: "Hello"
  3. Inject
  4. **Očekávaný výsledek**: "Hello" → Base64 → zpět na "Hello" (round-trip)
  5. Také můžete otestovat samostatně: Inject Base64Enc → HexDump a ověřit dekódování

### 11.2 MorseDecoderNode (📻 MorseDec)
- [ ] **Funkce**: Dekódování Morseovy abecedy zpět na text
- [ ] **Test**:
  1. Text → Morse → MorseDec → TextOut
  2. Text: "HELLO"
  3. Inject
  4. **Očekávaný výsledek**: "HELLO" → Morse → zpět na "HELLO" (round-trip)

### 11.3 Utf8DecoderNode (🔤 UTF-8Dec)
- [ ] **Funkce**: UTF-8 dekódování
- [ ] **Test**:
  1. Text → UTF-8 → UTF-8Dec → TextOut
  2. Text s diakritikou
  3. Inject
  4. **Očekávaný výsledek**: Round-trip - text zůstane stejný

### 11.4 HuffmanDecoderNode (🌳 HuffmanDec)
- [ ] **Funkce**: Huffmanovo dekódování
- [ ] **Test**:
  1. Text → HuffmanEnc → HuffmanDec → TextOut
  2. Text: "Hello World!"
  3. Inject
  4. **Očekávaný výsledek**: Round-trip - původní text se obnoví

---

## 12. Uzly - komprese (Compressors)

### 12.1 RLECompressorNode (📏 RLE)
- [ ] **Funkce**: Run-Length Encoding komprese/dekomprese
- [ ] **Parametry**: Mode (CHOICE: compress/decompress)
- [ ] **Test**:
  1. Přidejte Text → RLE → TextOut
  2. Text: "AAAAABBBBCCCCDDDD" (vhodný pro RLE - opakující se znaky)
  3. Nastavte RLE mode=compress
  4. Inject
  5. **Očekávaný výsledek**: Data se zkomprimují, compression ratio < 1.0
  6. **Test dekomprese**: Text → RLE(mode=compress) → RLE(mode=decompress) → TextOut
  7. **Očekávaný výsledek**: Původní data se obnoví

### 12.2 HuffmanCompressorNode (🌳 Huffman)
- [ ] **Funkce**: Huffmanova komprese binárních dat
- [ ] **Test**:
  1. Text → HuffmanComp → TextOut
  2. Text s nerovnoměrným rozložením (např. "AAAAABBBCCD")
  3. Inject
  4. **Očekávaný výsledek**: Data se zkomprimují, compression ratio se zobrazí v historii
  5. *Poznámka: Výstup obsahuje metadata (kódovou tabulku) oddělenou `|||` od komprimovaných dat*

### 12.3 LZ77CompressorNode (🗜️ LZ77)
- [ ] **Funkce**: LZ77 sliding window komprese
- [ ] **Parametry**: Window Size (INT 128-32768)
- [ ] **Test**:
  1. Text → LZ77 → TextOut
  2. Text: "ABABABABABABABAB" (vhodný pro LZ77)
  3. Inject
  4. **Očekávaný výsledek**: Komprimovaná data s compression ratio
  5. Zkuste změnit Window Size (např. 256, 4096, 16384) a pozorujte změnu komprese

### 12.4 LZWCompressorNode (🗜️ LZW)
- [ ] **Funkce**: LZW dictionary komprese
- [ ] **Test**:
  1. Text → LZW → TextOut
  2. Text s opakujícími se vzory
  3. Inject
  4. **Očekávaný výsledek**: Komprimovaná data s compression ratio

---

## 13. Uzly - kanály (Channels)

### 13.1 IdealChannelNode (🔌 Ideal)
- [ ] **Funkce**: Ideální kanál s nastavitelnou latencí (bez chyb)
- [ ] **Parametry**: Latency (INT 0-10000 ms)
- [ ] **Test**:
  1. Text → Ideal → TextOut
  2. Nastavte latenci na 100 ms
  3. Inject
  4. **Očekávaný výsledek**: Data projdou beze změny, přidá se latence 100 ms

### 13.2 BSKChannelNode (📡 BSK)
- [ ] **Funkce**: Binary Symmetric Channel - binární symetrický kanál s bitovou chybovostí
- [ ] **Parametry**: Error Prob (FLOAT 0-1), Latency (INT 0-10000 ms)
- [ ] **Test**:
  1. Text → BSK → TextOut
  2. Nastavte Error Prob = 0.1 (10% chybovost)
  3. Inject několikrát
  4. **Očekávaný výsledek**: Někdy dojde k poškození dat (změna bitů)
  5. Sledujte BER (Bit Error Rate) v historii packetu
  6. **Test s nulovou chybovostí**: Error Prob = 0.0 → data projdou beze změny

### 13.3 GilbertElliottChannelNode (📡 Gilbert-Elliott)
- [ ] **Funkce**: Gilbert-Elliott model kanálu s burst chybami (shluky chyb)
- [ ] **Parametry**: P(good) (FLOAT), P(bad) (FLOAT), Burst Length (INT 1-100)
- [ ] **Test**:
  1. Text → GilbertElliott → TextOut
  2. P(good)=0.2, P(bad)=0.5, Burst Length=5
  3. Inject několikrát
  4. **Očekávaný výsledek**: Chyby se vyskytují ve shlucích (burstech), ne izolovaně

### 13.4 AWGNChannelNode (📡 AWGN)
- [ ] **Funkce**: Additive White Gaussian Noise - aditivní bílý gaussovský šum
- [ ] **Parametry**: SNR (dB) (FLOAT -10 až 50)
- [ ] **Test**:
  1. Text → AWGN → TextOut
  2. SNR = 0 dB (velmi špatný signál)
  3. Inject
  4. **Očekávaný výsledek**: Data jsou silně poškozena šumem
  5. SNR = 50 dB (výborný signál) → data projdou téměř beze změny

---

## 14. Uzly - ECC (Error Correction Code)

### 14.1 Hamming74Node (🔴 Hamming(7,4))
- [ ] **Funkce**: Hamming(7,4) kód - enkodér/dekodér s detekcí a opravou 1 bitu
- [ ] **Parametry**: Mode (CHOICE: encode/decode)
- [ ] **Test**:
  1. **Encode**: Text → Hamming74(mode=encode) → TextOut
  2. Inject → data jsou zakódována s redundancí (4→7 bitů)
  3. **Oprava chyb**: Text → Hamming74(encode) → BSK(p=0.05) → Hamming74(decode) → TextOut
  4. Inject několikrát
  5. **Očekávaný výsledek**: Chyby z BSK kanálu jsou opraveny (pokud je chyba max 1 bit na 7-bitový blok)
  6. Sledujte "errors_fixed" v historii

### 14.2 Hamming1511Node (🔴 Hamming(15,11))
- [ ] **Funkce**: Hamming(15,11) kód - lepší kódový poměr (11/15 vs 4/7)
- [ ] **Parametry**: Mode (CHOICE: encode/decode)
- [ ] **Test**:
  1. Text → Hamming1511(encode) → TextOut
  2. Inject → poměr 11/15 (účinnější než Hamming(7,4))
  3. *Dekódování je v současné implementaci základní (pouze předá data)*

### 14.3 CRC8Node (🔴 CRC-8)
- [ ] **Funkce**: CRC-8 kontrolní součet (1 byte)
- [ ] **Test**:
  1. Text → CRC8 → TextOut
  2. Inject
  3. **Očekávaný výsledek**: K datům je přidán 1 byte CRC (např. "crc=A5")
  4. *CRC poly = 0x07*

### 14.4 CRC16Node (🔴 CRC-16)
- [ ] **Funkce**: CRC-16 kontrolní součet (2 byty)
- [ ] **Test**:
  1. Text → CRC16 → TextOut
  2. Inject
  3. **Očekávaný výsledek**: K datům jsou přidány 2 byty CRC

### 14.5 CRC32Node (🔴 CRC-32)
- [ ] **Funkce**: CRC-32 kontrolní součet (4 byty)
- [ ] **Test**:
  1. Text → CRC32 → TextOut
  2. Inject
  3. **Očekávaný výsledek**: K datům jsou přidány 4 byty CRC

### 14.6 ParityEncoderNode (🔴 ParityEnc)
- [ ] **Funkce**: Parity bit enkodér (sudá/lichá parita)
- [ ] **Parametry**: Parity Type (CHOICE: even/odd)
- [ ] **Test**:
  1. Text → ParityEnc → TextOut
  2. Mode = even
  3. Inject
  4. **Očekávaný výsledek**: K datům je přidán 1 paritní byte
  5. Mode = odd → paritní bit se invertuje

### 14.7 ParityDecoderNode (🔴 ParityDec)
- [ ] **Funkce**: Parity bit dekodér/kontrolor
- [ ] **Parametry**: Parity Type (CHOICE: even/odd)
- [ ] **Test**:
  1. Text → ParityEnc → ParityDec → TextOut
  2. **Očekávaný výsledek**: Data projdou, parity se odstraní
  3. **S chybou**: Text → ParityEnc → BSK(p=0.1) → ParityDec → TextOut
  4. Inject → pokud BSK poškodí paritu, ParityDec ohlásí chybu

### 14.8 ReedSolomonEncoderNode (🔴 RS Enc)
- [ ] **Funkce**: Zjednodušený Reed-Solomon enkodér
- [ ] **Parametry**: Codeword Length (INT 3-255), Data Length (INT 1-253)
- [ ] **Test**:
  1. Text → RS Enc → TextOut
  2. n=15, k=11
  3. Inject
  4. **Očekávaný výsledek**: K datům je přidán 1 paritní byte (zjednodušená implementace)

### 14.9 ReedSolomonDecoderNode (🔴 RS Dec)
- [ ] **Funkce**: Zjednodušený Reed-Solomon dekodér
- [ ] **Parametry**: Data Length (INT 1-253)
- [ ] **Test**:
  1. Text → RS Enc → RS Dec → TextOut
  2. Inject
  3. **Očekávaný výsledek**: Data jsou oříznuta na prvních k bytů

---

## 15. Uzly - kontrolní součty (Checksums)

### 15.1 EANValidator (EAN)
- [ ] **Funkce**: Validace EAN-13/EAN-8 čárových kódů
- [ ] **Parametry**: EAN Type (CHOICE: EAN-13/EAN-8)
- [ ] **Test**:
  1. Text → EAN → TextOut
  2. Text: "5901234123457" (platné EAN-13)
  3. Inject
  4. **Očekávaný výsledek**: "EAN-13: 5901234123457 - Valid"
  5. Změňte poslední číslici: "5901234123450"
  6. Inject → "EAN-13: 5901234123450 - Invalid (correct: X)"
  7. **EAN-8 test**: Type=EAN-8, Text="96385074" → "Valid"

### 15.2 ISBNValidator (ISBN)
- [ ] **Funkce**: Validace ISBN-10/ISBN-13
- [ ] **Parametry**: ISBN Type (CHOICE: ISBN-13/ISBN-10)
- [ ] **Test**:
  1. Text → ISBN → TextOut
  2. Type=ISBN-13, Text="9780306406157" (platné)
  3. Inject → "ISBN-13: ... - Valid"
  4. Type=ISBN-10, Text="0306406152" (platné)
  5. Inject → "ISBN-10: ... - Valid"

### 15.3 ISSNValidator (ISSN)
- [ ] **Funkce**: Validace ISSN (seriálové publikace)
- [ ] **Test**:
  1. Text → ISSN → TextOut
  2. Text: "03178471" (platné ISSN)
  3. Inject
  4. **Očekávaný výsledek**: "ISSN: 03178471 - Valid"
  5. Špatné ISSN: "12345678" → "Invalid"

### 15.4 LuhnValidator (Luhn)
- [ ] **Funkce**: Luhnův algoritmus (používá se u kreditních karet)
- [ ] **Test**:
  1. Text → Luhn → TextOut
  2. Text: "4532015112830366" (platné číslo karty)
  3. Inject → "Luhn: ... - Valid"
  4. Špatné: "4532015112830367" → "Invalid (correct: X)"
  5. *Luhn se používá také pro česká rodná čísla (starší formát)*

### 15.5 VerhoeffValidator (Verhoeff)
- [ ] **Funkce**: Verhoeffův algoritmus (dihedral group D5)
- [ ] **Test**:
  1. Text → Verhoeff → TextOut
  2. Použijte předem vypočítané platné číslo (např. 1234567890 → vyzkoušejte)
  3. Inject → "Verhoeff: ... - Valid" nebo "Invalid"

### 15.6 ICOValidator (ICO)
- [ ] **Funkce**: Validace IČO (české identifikační číslo organizace)
- [ ] **Test**:
  1. Text → ICO → TextOut
  2. Text: "27082440" (platné IČO - např. Seznam.cz)
  3. Inject → "IČO: 27082440 - Valid"
  4. Špatné: "12345678" → "Invalid"
  5. *Speciální případ: pokud je kontrolní číslice 10, použije se 1*

### 15.7 RCCalculator (RC)
- [ ] **Funkce**: Validace rodného čísla (ČR)
- [ ] **Test**:
  1. Text → RC → TextOut
  2. Text: "780123/1234" (9 číslic) → "Old format (9 digits)"
  3. Text: "7801231234" (10 číslic dělitelných 11) → "Valid" nebo "Invalid"
  4. *Rodné číslo musí být dělitelné 11 (pro 10místná čísla od roku 1954)*

---

## 16. Uzly - analyzátory (Analyzers)

### 16.1 EntropyMeterNode (📊 Entropie)
- [ ] **Funkce**: Výpočet Shannonovy entropie dat
- [ ] **Test**:
  1. Text → Entropie → TextOut
  2. Text: "AAAA" (nízká entropie)
  3. Inject → v historii: "H=0.000, eff=0.0%" (všechny znaky stejné)
  4. Text: náhodný text (např. z Random s Entropy=8.0)
  5. Inject → entropie se blíží 8.0 bitů/byte
  6. **Očekávaný výsledek**: Entropie se zobrazí v Inspectoru v sekci Statistics

### 16.2 HistogramNode (📈 Frekvence)
- [ ] **Funkce**: Frekvenční analýza symbolů
- [ ] **Test**:
  1. Text → Frekvence → TextOut
  2. Text: "ABBCCCDDDD"
  3. Inject
  4. **Očekávaný výsledek**: V Inspectoru v "Unique symbols" se zobrazí počet unikátních symbolů
  5. *Pro podrobnější histogram je potřeba zkontrolovat atribut `frequencies` v kódu*

### 16.3 CompressionRatioNode (📊 CompRatio)
- [ ] **Funkce**: Měření kompresního poměru
- [ ] **Test**:
  1. Text → RLE → CompRatio → TextOut
  2. Text: "AAAAABBBBBCCCCCDDDDD"
  3. RLE mode=compress
  4. Inject
  5. **Očekávaný výsledek**: Compression ratio = input_size / output_size
  6. *Pokud je ratio > 1.0, data se zmenšila (dobrá komprese)*

### 16.4 BERMeterNode (📊 BER Meter)
- [ ] **Funkce**: Měření bitové chybovosti (Bit Error Rate)
- [ ] **Test**:
  1. Text → BSK → BER Meter → TextOut
  2. BSK Error Prob = 0.05
  3. Inject několikrát
  4. **Očekávaný výsledek**: BER = error_bits / total_bits (měl by se blížit 0.05)
  5. V historii: "BER=0.049234, errors=X/Y"

### 16.5 LatencyMeterNode (⏱️ LatencyMeter)
- [ ] **Funkce**: Měření latence (zpoždění) packetů
- [ ] **Test**:
  1. Text → Ideal(latency=50ms) → LatencyMeter → TextOut
  2. Inject
  3. **Očekávaný výsledek**: Latence by měla být ~50 ms (podle nastavení kanálu)
  4. V historii: "latency=52.34ms, avg=52.34ms"

---

## 17. Uzly - výstupy (Sinks)

### 17.1 TextOutputNode (📄 TextOut)
- [ ] **Funkce**: Zobrazení textového výstupu
- [ ] **Test**:
  1. Text → TextOut
  2. Inject
  3. **Očekávaný výsledek**: V Inspectoru v "Statistics" se zobrazí "Output: Hello World!..."
  4. Zkontrolujte také: size_bits, entropy, compression_ratio, errors, latency_ms

### 17.2 FileSinkNode (💾 Soubor)
- [ ] **Funkce**: Uložení dat do souboru
- [ ] **Parametry**: Filename (STR)
- [ ] **Test**:
  1. Text → Soubor
  2. Nastavte filename="test_output.bin"
  3. Inject
  4. **Očekávaný výsledek**: Soubor `test_output.bin` se vytvoří a obsahuje data
  5. Pomocí `cat test_output.bin` nebo hexdump zkontrolujte obsah

### 17.3 ConsoleSinkNode (🖥️ Konzole)
- [ ] **Funkce**: Výpis dat do systémové konzole (stdout)
- [ ] **Test**:
  1. Text → Konzole
  2. Inject
  3. **Očekávaný výsledek**: V terminálu, kde běží aplikace, se objeví "[ConsoleSink] Hello World!..."

### 17.4 HexDumpSinkNode (🔢 HexDump)
- [ ] **Funkce**: Hexadecimální výpis dat
- [ ] **Test**:
  1. Text → HexDump
  2. Text: "ABC"
  3. Inject
  4. **Očekávaný výsledek**: V terminálu se objeví "[HexDump] 41 42 43" (hex hodnoty bytů)

### 17.5 ComparisonSinkNode (⚖️ Compare)
- [ ] **Funkce**: Porovnání A/B dvou vstupů
- [ ] **Test**:
  1. Vytvořte dvě větve: Text1 → Compare(in_a) a Text2 → Compare(in_b)
  2. *Poznámka: Tento uzel má vstupy "in_a" a "in_b"*
  3. Inject do obou zdrojů
  4. **Očekávaný výsledek**: V historii: "equal=True, diff_bytes=0"
  5. Dejte různý text do zdrojů → "equal=False, diff_bytes=X"

---

## 18. Konzole a logování

### 18.1 Výpis zpráv do konzole
- [ ] **Postup**: Provádějte různé akce a sledujte konzoli v dolní části
- [ ] **Očekávaný výsledek**:
  - Zprávy se zobrazují s časovým razítkem `[HH:MM:SS]`
  - Různé barvy podle kategorie:
    - **info** - zelená
    - **warning** - žlutá
    - **error** - červená
    - **packet** - zelená
    - **debug** - šedá
  - Maximálně 1000 řádků (pak se starší mažou)

### 18.2 Dávkové zpracování logů
- [ ] **Ověření**: Logy se vyflusávají po 5 zprávách nebo každých 10 ticků (optimalizace výkonu)

### 18.3 Logger do souboru
- [ ] **Postup**: Zkontrolujte adresář `logs/` (pokud je implementováno)
- [ ] **Očekávaný výsledek**: Logy se ukládají do souboru pro pozdější analýzu

---

## 19. Profilování výkonu

### 19.1 Start profiling
- [ ] **Postup**: Klikněte na **⏱ Start Profiling** v toolbaru
- [ ] **Očekávaný výsledek**:
  - Tlačítko "Start Profiling" se zneaktivní
  - Tlačítko "Stop Profiling" se aktivuje
  - V konzoli: "Performance profiling STARTED"

### 19.2 Stop profiling a zobrazení reportu
- [ ] **Postup**: 
  1. Nechte profilování běžet alespoň pár sekund
  2. Klikněte na **⏹ Stop Profiling**
- [ ] **Očekávaný výsledek**:
  - Objeví se dialogové okno "Profiling Report" (900×600 px)
  - Report obsahuje naměřená data (časování jednotlivých operací)
  - Tlačítka se přepnou zpět
  - V konzoli: "Performance profiling STOPPED"

### 19.3 Obsah profiling reportu
- [ ] **Ověření**: Report obsahuje údaje jako:
  - Čas kreslení gridu
  - Čas animace packetů
  - Další měřené operace (perf_monitor)

---

## 20. Ukládání a načítání scénářů

### 20.1 Uložení scénáře (💾 Save)
- [ ] **Postup**: 
  1. Vytvořte na canvasu několik uzlů a propojení
  2. Klikněte na **💾 Save**
  3. Zadejte název souboru (např. `test_scenario.json`)
- [ ] **Očekávaný výsledek**:
  - Otevře se dialog pro uložení souboru
  - Po uložení: "Scenario saved to test_scenario.json"
  - Soubor obsahuje JSON s poli "nodes" a "connections"

### 20.2 Načtení scénáře (📂 Load)
- [ ] **Postup**: 
  1. Klikněte na **📂 Load**
  2. Vyberte dříve uložený soubor
- [ ] **Očekávaný výsledek**:
  - Otevře se dialog pro výběr souboru
  - Uzly a propojení se obnoví na canvasu
  - "Scenario loaded from test_scenario.json"

### 20.3 Formát JSON
- [ ] **Ověření**: Zkontrolujte uložený JSON soubor
- [ ] **Očekávaný výsledek**:
  ```json
  {
    "nodes": [
      {
        "id": "...",
        "type": "source",
        "name": "📝 Text",
        "category": "sources",
        "position": [0, 0],
        "params": {...},
        "config": {...},
        "input_ports": {...},
        "output_ports": {...}
      }
    ],
    "connections": [
      {
        "from_node": "...",
        "from_port": "out",
        "to_node": "...",
        "to_port": "in",
        "metadata": {...}
      }
    ]
  }
  ```

### 20.4 Robustnost načítání - neznámé typy uzlů
- [ ] **Test**: Záměrně vložte do JSON neexistující typ uzlu a zkuste načíst
- [ ] **Očekávaný výsledek**: Uzel se přeskočí s warningem, ostatní uzly se načtou

---

## 21. Export obrázku a Zoom to Fit

### 21.1 Zoom to Fit (🔍)
- [ ] **Postup**: 
  1. Přidejte několik uzlů na různé pozice
  2. Oddalte (Ctrl+scroll dolů)
  3. Klikněte na **🔍 Zoom to Fit**
- [ ] **Očekávaný výsledek**:
  - Viewport se přizpůsobí tak, aby byly vidět všechny uzly
  - S tolerancí ±50 px padding
  - Zoom je omezen mezi 0.25x a 3.0x
  - V konzoli: "Zoomed to fit all nodes"

### 21.2 Export obrázku (📷 Export)
- [ ] **Postup**: 
  1. Vytvořte scénu s uzly a propojeními
  2. Klikněte na **📷 Export**
  3. Vyberte umístění a formát (PNG nebo JPEG)
- [ ] **Očekávaný výsledek**:
  - Otevře se dialog pro uložení
  - Obrázek se uloží na zadanou cestu
  - "Canvas exported to ..."
  - Pokud se export nezdaří: "Failed to export canvas to ..."

---

## 22. Nápověda a dokumentace

### 22.1 Help dialog (❓ Help)
- [ ] **Postup**: Klikněte na **❓ Help**
- [ ] **Očekávaný výsledek**:
  - Otevře se dialog "InfoFlowLab v1.0 - Nápověda" (800×600 px)
  - Obsahuje sekce: O aplikaci, Ovládání, Práce s canvasem, Kategorie prvků, Klávesové zkratky

### 22.2 Tlačítko propojovací nápovědy v Help dialogu
- [ ] **Postup**: V Help dialogu klikněte na **📖 Nápověda k propojování prvků**
- [ ] **Očekávaný výsledek**:
  - Otevře se webový prohlížeč s `docs/NAPOVEDA_PROPOJENI.html`
  - Pokud soubor neexistuje: "Help file not found"

---

## 23. Resetování aplikace

### 23.1 Reset (↺)
- [ ] **Postup**: 
  1. Přidejte několik uzlů a propojení
  2. Spusťte simulaci
  3. Klikněte na **↺ Reset**
- [ ] **Očekávaný výsledek**:
  - Všechny uzly zmizí z canvasu
  - Všechna propojení zmizí
  - Inspector se vyčistí ("No node selected")
  - Status: "● Ready", Tick: "Tick: 0"
  - Engine se resetuje (statistiky vynulovány)
  - V konzoli: "Simulation reset - all nodes cleared"

---

## 24. Marquee výběr a hromadné operace

### 24.1 Marquee výběr (obdélníkový výběr)
- [ ] **Postup**: 
  1. Klikněte na prázdné místo na canvasu
  2. Táhněte myší (levé tlačítko) - vytvoří se modrý obdélník
- [ ] **Očekávaný výsledek**:
  - Zobrazí se modrý obdélník s průhlednou výplní (modrá #2196F3)
  - Uzly uvnitř obdélníku se zvýrazní (vyberou)

### 24.2 Shift+Marquee pro přidání k výběru
- [ ] **Postup**: 
  1. Vyberte první skupinu uzlů
  2. Podržte **Shift** a udělejte druhý marquee výběr
- [ ] **Očekávaný výsledek**: Nové uzly se přidají k již vybraným

---

## 25. Minimapa

### 25.1 Zobrazení minimapy
- [ ] **Postup**: Po spuštění zkontrolujte pravý dolní roh canvasu
- [ ] **Očekávaný výsledek**:
  - V pravém dolním rohu je malý náhled scény (150×100 px)
  - Zobrazuje všechny uzly na canvasu v miniatuře
  - Okraj minimapy je oranžový nebo šedý

### 25.2 Aktualizace minimapy
- [ ] **Postup**: 
  1. Přidejte nový uzel
  2. Zoom/posuňte canvas
- [ ] **Očekávaný výsledek**: Minimapa se aktualizuje podle aktuálního stavu

---

## 26. Komplexní end-to-end testy

### 26.1 Základní round-trip: Text → Base64 → Base64Dec → TextOut
- [ ] **Postup**: 
  1. Vytvořte: Text → Base64 → Base64Dec → TextOut
  2. Text: "Hello World!"
  3. Inject
- [ ] **Očekávaný výsledek**: 
  - Výstup v TextOut: "Hello World!" (původní text se obnovil)

### 26.2 Komprese + dekomprese: Text → RLE(compress) → RLE(decompress) → TextOut
- [ ] **Postup**:
  1. Vytvořte: Text → RLE(mode=compress) → RLE(mode=decompress) → TextOut
  2. Text: "AAAAABBBBBCCCCCDDDDD"
  3. Inject
- [ ] **Očekávaný výsledek**: Původní text se obnoví

### 26.3 Komunikace s šumem + ECC: Text → HammingEnc → BSK → HammingDec → TextOut
- [ ] **Postup**:
  1. Vytvořte: Text → Hamming74(encode) → BSK(p=0.05) → Hamming74(decode) → TextOut
  2. Inject několikrát
- [ ] **Očekávaný výsledek**: 
  - Hamming kód opraví většinu 1-bitových chyb
  - Výstup by měl být většinou shodný se vstupem
  - Sledujte "errors_fixed" v historii HammingDec

### 26.4 Výpočet entropie: Random → Entropie → TextOut
- [ ] **Postup**:
  1. Vytvořte: Random(Entropy=8.0) → Entropie → TextOut
  2. Inject
- [ ] **Očekávaný výsledek**: Entropie by měla být vysoká (~7.5-8.0 bitů/byte)

### 26.5 Přenos s různými BER: Text → BSK(p=0.01) → TextOut vs Text → BSK(p=0.3) → TextOut
- [ ] **Postup**: 
  1. Vytvořte dvě paralelní větve s různými chybovostmi
  2. Porovnejte výsledky
- [ ] **Očekávaný výsledek**: Vyšší chybovost → více poškozených dat

### 26.6 Uložit a načíst komplexní scénář
- [ ] **Postup**: 
  1. Vytvořte komplexní scénář s různými typy uzlů a propojení
  2. Uložte
  3. Resetujte
  4. Načtěte
- [ ] **Očekávaný výsledek**: Všechny uzly a propojení jsou obnoveny

---

## 27. Testování hraničních situací

### 27.1 Spuštění Play bez uzlů
- [ ] **Postup**: Klikněte na Play, aniž byste přidali jakýkoli uzel
- [ ] **Očekávaný výsledek**: Simulace běží, ale neděje se nic (není co zpracovávat)

### 27.2 Inject bez zdrojového uzlu
- [ ] **Postup**: Klikněte na Inject bez zdroje na canvasu
- [ ] **Očekávaný výsledek**: Warning v konzoli: "No source node found to inject packet"

### 27.3 Pause bez běžící simulace
- [ ] **Postup**: Klikněte na Pause v idle stavu
- [ ] **Očekávaný výsledek**: Warning v logu: "Pause called but simulation not running"

### 27.4 Příliš mnoho uzlů (stres test)
- [ ] **Postup**: Přidejte 20+ uzlů a propojení
- [ ] **Očekávaný výsledek**: Aplikace by měla zůstat responzivní, i když může být pomalejší

### 27.5 Velké množství dat (stres test)
- [ ] **Postup**: 
  1. Random(Length=10000) → TextOut
  2. Inject
- [ ] **Očekávaný výsledek**: Zpracuje se 10 KB dat bez pádu

### 27.6 Neplatný JSON při načítání
- [ ] **Postup**: Zkuste načíst nevalidní JSON soubor
- [ ] **Očekávaný výsledek**: Chybová zpráva v konzoli: "Failed to load: ..."

### 27.7 Rychlé klikání na Play/Pause/Stop
- [ ] **Postup**: Rychle za sebou klikněte Play → Pause → Play → Stop
- [ ] **Očekávaný výsledek**: Aplikace nespadne, stavy se správně přepínají

### 27.8 Smazání uzlu během simulace
- [ ] **Postup**: 
  1. Spusťte simulaci
  2. Během běhu smažte uzel
- [ ] **Očekávaný výsledek**: Uzel zmizí, simulace pokračuje s ostatními uzly

### 27.9 Propojení výstup → výstup
- [ ] **Postup**: Zkuste propojit dva výstupní porty
- [ ] **Očekávaný výsledek**: Spojení se nevytvoří, porty jsou kompatibilní jen INPUT↔OUTPUT

### 27.10 Propojení stejného uzlu
- [ ] **Postup**: Zkuste propojit výstup uzlu s jeho vlastním vstupem
- [ ] **Očekávaný výsledek**: Mělo by být možné (detekce cyklu by měla varovat)

---

## 📊 Shrnutí

| Kategorie | Počet testů | Status |
|-----------|-------------|--------|
| 1. Základní spuštění | 4 | ⬜ |
| 2. Toolbar a ovládání | 8 | ⬜ |
| 3. Canvas | 8 | ⬜ |
| 4. Sidebar | 6 | ⬜ |
| 5. Inspector | 7 | ⬜ |
| 6. Propojování | 6 | ⬜ |
| 7. Simulační engine | 6 | ⬜ |
| 8. Packet animace | 3 | ⬜ |
| 9. Zdroje (5 uzlů) | 5 | ⬜ |
| 10. Kódovače (6 uzlů) | 6 | ⬜ |
| 11. Dekódovače (4 uzly) | 4 | ⬜ |
| 12. Komprese (4 uzly) | 4 | ⬜ |
| 13. Kanály (4 uzly) | 4 | ⬜ |
| 14. ECC (9 uzlů) | 9 | ⬜ |
| 15. Kontrolní součty (7 uzlů) | 7 | ⬜ |
| 16. Analyzátory (5 uzlů) | 5 | ⬜ |
| 17. Výstupy (5 uzlů) | 5 | ⬜ |
| 18. Konzole a logování | 3 | ⬜ |
| 19. Profilování | 3 | ⬜ |
| 20. Ukládání/načítání | 4 | ⬜ |
| 21. Export/Zoom to Fit | 2 | ⬜ |
| 22. Nápověda | 2 | ⬜ |
| 23. Reset | 1 | ⬜ |
| 24. Marquee výběr | 2 | ⬜ |
| 25. Minimapa | 2 | ⬜ |
| 26. End-to-end testy | 6 | ⬜ |
| 27. Hraniční situace | 10 | ⬜ |
| **CELKEM** | **~130 testů** | **⬜** |

---

## 🔧 Jak používat tento checklist

1. **Pro každý checkbox** proveďte popsaný postup
2. **Označte**: `- [x]` pokud test proběhl úspěšně, `- [ ]` pokud ne
3. **V případě chyby**: Poznamenejte si detail chyby (např. "po kroku X se objevila chyba Y")
4. **Priorita**: Testujte od sekce 1 po sekci 27 (od nejdůležitějších k méně důležitým)
5. **Opakovatelnost**: Některé testy (zejména s kanály a šumem) mohou dávat pokaždé jiné výsledky - to je normální

> **Tip**: Pro rychlejší testování vytvořte předem připravené scénáře a uložte je přes Save/Load.
