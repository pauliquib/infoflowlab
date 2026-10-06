# InfoFlowLab

**InfoFlowLab** is an interactive compression and communication simulator for visually designing and testing data flows. You build graphs from nodes, connect them, and simulate data transfer in real time.

![InfoFlowLab — simulace toku Text → UTF-8 → UTF-8Dec](docs/screenshot.png)

![CI](https://github.com/pauliquib/infoflowlab/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![PySide6](https://img.shields.io/badge/PySide6-6.5%2B-green)
![License](https://img.shields.io/badge/license-MIT-orange)

*Public snapshot — development happens in a private repository; the commit history is squashed here.*

## Open web book

**InfoFlowLab is the canonical depth** for information theory and exercises. The web book does **not** rewrite the algorithms; it only provides a signpost:

*InfoFlowLab — a signpost, not a textbook* — the related web book is maintained as a separate project.

## 🎯 Purpose

InfoFlowLab is designed for:
- **Education** - Students of information systems and information transmission theory
- **Visualising data flows** - Interactive design of communication chains
- **Testing algorithms** - Compression, encoding, ECC, checksums
- **Simulating communication** - Channels with noise, delay and loss

## ✨ Main features

### 🎨 Visual editor
- **Drag & drop** - Drag nodes from the sidebar onto the canvas
- **Connecting ports** - Click a port and drag it to another port
- **Zoom and pan** - Ctrl+Scroll to zoom, middle mouse button to pan
- **Deleting** - Delete/Backspace removes the selected element

### 🔧 Simulation
- **Simulation modes:**
  - ▶️ **Real-time** - Run in real time
  - ⏸️ **Pause/Resume** - Pause and continue
  - ⏭️ **Step** - Step by step, for teaching
- **Adjustable speed** - 0.1x to 5.0x
- **Tick interval** - 10 ms to 1000 ms
- **Injecting packets** - Insert test data by hand

### 📦 Node categories (30+ types)

#### 📝 Sources
- **TextSource** - Text input
- **RandomSource** - Random data with adjustable entropy
- **NumberInput** - Numeric values in different bases

#### 🔀 Encoders
- **Base64** - Base64 encoding and decoding
- **Hex** - Hexadecimal conversion
- **BaseConverter** - Conversion between number bases
- **UTF-8** - UTF-8 encoding
- **Morse** - Morse code
- **Huffman** - Huffman coding

#### 🗜️ Compressors
- **Huffman** - Huffman compression
- **RLE** - Run-length encoding

#### 📡 Channels
- **BSK** - Binary symmetric channel with noise
- **Ideal** - Ideal channel with delay

#### 🔴 ECC (error correction)
- **Hamming(7,4)** - Hamming code for correcting 1-bit errors
- **CRC32** - CRC checksum

#### ✅ Checksums
- **EAN-13** - EAN-13 barcode validation
- **ISBN** - ISBN-10/13 validation
- **ISSN** - ISSN validation
- **Luhn** - Luhn algorithm (payment cards)
- **Verhoeff** - Verhoeff algorithm

#### 📊 Analysers
- **EntropyMeter** - Shannon entropy calculation
- **Histogram** - Character frequency analysis

#### 💾 Sinks
- **Console** - Output to the console
- **File** - Save to a file
- **HexDump** - Hexadecimal dump
- **TextOutput** - Text output

### 🎛️ Tools
- **Console** - Coloured log output with timestamps
- **Inspector** - Properties panel for the selected node
- **Profiling** - Performance profiling
- **Save/Load** - Save and load scenarios (JSON)

## 🚀 Quick start

### Requirements

- Python 3.8 or newer
- PySide6 6.5.0 or newer

### Installation

```bash
# Clone the repository
git clone https://github.com/pauliquib/infoflowlab.git
cd infoflowlab

# Install the dependencies
pip install -e .

# or with the development dependencies
pip install -e ".[dev]"

# or with all dependencies
pip install -e ".[full]"
```

### Running

```bash
# Run directly
python main.py

# or with the Makefile
make run
```

## 🧪 Testing

```bash
# Run all tests
make test

# or directly with pytest
pytest tests/ -v

# With code coverage
make test-cov

# Unit tests only
make test-unit
```

## 📚 Usage

### Basic use

1. **Create a node**: drag an element from the sidebar onto the canvas
2. **Connect**: click the output port (right) and drag to an input port (left)
3. **Configure**: click a node to show its properties in the Inspector
4. **Simulate**: click ▶️ Play to start the simulation
5. **Stepping**: use ⏭️ Step to go one step at a time

### Keyboard shortcuts

| Key | Action |
|---------|------|
| `Delete` / `Backspace` | Delete the selected element |
| `Escape` | Cancel connecting |
| `Ctrl + Scroll` | Zoom in/out |
| `Middle Mouse` | Pan the canvas |

### Saving and loading

```python
from src.utils.serialization import export_scenario, import_scenario

# Save a scenario
export_scenario(engine, "my_scenario.json", "My scenario")

# Load a scenario
engine = import_scenario("moj_scenar.json")
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│  GUI vrstva (src/gui/)                  │
│  - MainWindow, Canvas, Sidebar, Inspector│
├─────────────────────────────────────────┤
│  Node vrstva (src/nodes/)               │
│  - Concrete node implementations          │
├─────────────────────────────────────────┤
│  Algoritmy (src/algorithms/)            │
│  - Entropie, Huffman, Hamming, CRC...   │
├─────────────────────────────────────────┤
│  Core vrstva (src/core/)                │
│  - Graph, Engine, NodeBase, Port, Packet │
├─────────────────────────────────────────┤
│  Utils (src/utils/)                     │
│  - Serializace, Logging                  │
└─────────────────────────────────────────┘
```

### Key components

- **Graph** - Central store of the graph; manages nodes and connections
- **SimulationEngine** - Drives the data-flow simulation
- **NodeBase** - Base class for all nodes
- **DataPacket** - Data structure for transferring information
- **Canvas** - Visual canvas for editing the graph

## 🛠️ Development

### Project structure

```
infoflowlab/
├── src/
│   ├── core/           # Core system
│   │   ├── graph.py
│   │   ├── engine.py
│   │   ├── node_base.py
│   │   ├── port.py
│   │   └── packet.py
│   ├── nodes/          # Node implementations
│   │   ├── sources.py
│   │   ├── encoders.py
│   │   ├── compressors.py
│   │   ├── channels.py
│   │   ├── ecc.py
│   │   ├── checksums.py
│   │   ├── analyzers.py
│   │   └── sinks.py
│   ├── algorithms/     # Algoritmy
│   │   ├── entropy.py
│   │   ├── huffman.py
│   │   ├── hamming.py
│   │   ├── checksums.py
│   │   └── ...
│   ├── gui/            # GUI komponenty
│   │   ├── main_window.py
│   │   ├── canvas.py
│   │   ├── sidebar.py
│   │   └── inspector.py
│   └── utils/          # Helper tools
│       ├── serialization.py
│       └── logger.py
├── tests/              # Test suite
├── docs/               # Dokumentace
├── logs/               # Logy
└── assets/             # Icons and images
```

### Adding a new node

1. Create a class in `src/nodes/<category>.py`:
```python
class MyNode(NodeBase):
    def __init__(self, node_id: str):
        super().__init__(node_id, "category", "Name")
        self.add_input("in")
        self.add_output("out")
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        # Implementace
        return new_packet
```

2. Add it to `src/nodes/__init__.py`

3. Add it to `Canvas.add_node_at()` in `src/gui/canvas.py`

### Available commands

```bash
make help          # Show all available commands
make install       # Install the package
make install-dev   # Install with development dependencies
make test          # Run the tests
make lint          # Check the code (flake8)
make format        # Format the code (black)
make typecheck     # Check types (mypy)
make clean         # Clean the project
```

## 📖 Documentation

- [Project overview](docs/actualni_rozpracovanost.md) (Czech)
- [Connection architecture](docs/CONNECTION_SYSTEM_ARCHITECTURE.md) (Czech)
- [Simulation engine](docs/SIMULATION_ENGINE_ARCHITECTURE.md) (Czech)
- [Connecting help](docs/NAPOVEDA_PROPOJENI.md) (Czech)
- [Logging and profiling](docs/logging_profiling.md) (Czech)

## 🐛 Known issues

- Ports are small (16 px), so they can be hard to hit
- Packet animation is linear (not along a Bézier curve)
- No undo/redo
- No PDF export

## 🔮 Planned improvements

### Short term (1–2 weeks)
- [ ] Undo/redo for canvas actions
- [ ] Better port detection (larger hit area)
- [ ] Export the graph as an image
- [ ] Zoom to fit

### Medium term (1–2 months)
- [ ] More node types
- [ ] Plugin system for user-defined nodes
- [ ] Batch simulation
- [ ] Statistics and reports

### Long term (3+ months)
- [ ] Web version (WebAssembly)
- [ ] Sharing graphs (cloud)
- [ ] Advanced visualisations

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT licence — see [LICENSE](LICENSE) for details.

## 👥 Authors

- **pauliquib** - *first version*

## 📞 Contact

If you have questions or suggestions, please open an issue on GitHub.

---

**InfoFlowLab v1.0** — made with ❤️ for education