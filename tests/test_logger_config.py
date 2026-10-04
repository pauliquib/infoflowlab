#!/usr/bin/env python3
"""
test_logger_config.py — Comprehensive demonstration of the non-blocking logging system.

Shows:
1. Logger configuration and basic usage
2. Component tagging (UI, ENGINE, NETWORK, COMPRESSOR, etc.)
3. Log level use cases (DEBUG for packet tracking, INFO for placement, etc.)
4. Usage from inside a NodeBase.process() method
5. Usage from simulated UI event handlers
6. Toggling between DEBUG (verbose) and PRODUCTION (WARNING+ only) modes
7. Performance: demonstrating the non-blocking QueueHandler
"""

import sys
import os
import time
import threading

# Ensure the project root is on the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# 1. SETUP: Initialize the logging system once at application startup
# =============================================================================

def setup_application_logging():
    """
    Call this once when your application boots (e.g. in main.py).
    After this, any module can simply call get_logger("COMPONENT").
    """
    from src.utils.logger_config import logger_config
    # Optional: pass a custom log file path
    logger_config.setup(log_file_path="logs/infoflowlab.log")
    return logger_config


# =============================================================================
# 2. EXAMPLE: Using logging inside a NodeBase.process() method
# =============================================================================

def simulate_node_process():
    """
    Demonstrates how a simulation node would use logging in its process() method.
    This simulates what you'd write inside any NodeBase subclass.
    """
    from src.utils.logger_config import get_logger

    # Each node gets its own logger tagged with its component + node name
    log = get_logger("HuffmanEncoder")

    # --- INFO: Normal processing lifecycle ---
    log.info("Packet received for encoding")
    log.info("Input size: 1024 bytes, expecting ~40%% compression")

    # --- DEBUG: Detailed packet tracking & math ---
    # (only printed in DEV/verbose mode)
    log.debug("Building Huffman tree from frequency table")
    log.debug("Symbol frequencies: A=45, B=13, C=12, D=16, E=9, F=5")
    log.debug("Tree constructed: root weight=100, depth=4")
    log.debug("Encoded output: 01010110 00111001... (truncated)")
    log.debug("Compression ratio: 0.42, space saved: 593 bytes")

    # --- WARNING: Potential issues that don't crash the system ---
    log.warning("Compression ratio below threshold (0.42 < 0.50) — data may be incompressible")
    log.warning("Symbol entropy suggests theoretical min is 0.38, achieved 0.42")

    # --- ERROR: Something went wrong ---
    # Simulate a failed encoding attempt
    try:
        raise ValueError("Invalid symbol encountered during encoding: 0xFF")
    except ValueError as e:
        log.error(f"Encoding failed: {e}")


def simulate_packet_tracking():
    """
    Shows DEBUG-level packet tracking that one would use for
    tracing individual packets through the simulation graph.
    """
    from src.utils.logger_config import get_logger

    log = get_logger("PacketRouter")

    # Simulate a packet traversing the network
    packet_id = "PKT-0042"
    log.debug(f"[{packet_id}] Injected at SOURCE node 'TextGenerator'")
    log.debug(f"[{packet_id}] Buffer occupancy: 42/100 slots used")
    log.debug(f"[{packet_id}] Routing decision: port 'output' -> connection #3")
    log.debug(f"[{packet_id}] Arrived at CHANNEL node 'NoisyChannel'")
    log.debug(f"[{packet_id}] BER simulation: 3 bits flipped out of 1024")
    log.debug(f"[{packet_id}] Forwarded to SINK node 'HexDisplay'")


# =============================================================================
# 3. EXAMPLE: Using logging in UI event handlers
# =============================================================================

def simulate_ui_events():
    """
    Demonstrates how UI components (canvas, sidebar, dialogs) would log events.
    These would typically be triggered by user interactions.
    """
    from src.utils.logger_config import get_logger

    ui_log = get_logger("UI")

    # --- INFO: User actions (node placement, connections) ---
    ui_log.info("Node placed: 'HuffmanEncoder' at position (320, 240)")
    ui_log.info("Node placed: 'BinarySink' at position (640, 480)")
    ui_log.info("Connection created: HuffmanEncoder.output -> BinarySink.input")
    ui_log.info("Selection box created: rect(100, 100, 800, 600)")

    # --- DEBUG: Fine-grained UI state ---
    ui_log.debug("Canvas zoom level set to 1.5x")
    ui_log.debug("Grid snapping enabled, step=20px")
    ui_log.debug("Node 'HuffmanEncoder' dragged from (300,200) to (320,240)")

    # --- WARNING: Invalid user operations ---
    ui_log.warning("Connection rejected: HuffmanEncoder.output -> HuffmanEncoder.input would create a cycle")
    ui_log.warning("Connection rejected: incompatible data types (STRING <-> FLOAT)")
    ui_log.warning("Node placement rejected: position (1500, 900) outside canvas bounds")

    # --- ERROR: UI system failures ---
    ui_log.error("Failed to render node 'HuffmanEncoder': invalid paint device")
    ui_log.error("Serialization failed: node graph contains 3 cycles, maximum allowed is 0")


def simulate_sidebar_events():
    """
    Shows logging from the sidebar/panel components.
    """
    from src.utils.logger_config import get_logger

    sidebar_log = get_logger("Sidebar")
    sidebar_log.info("Accordion panel 'Compression' expanded")
    sidebar_log.debug("Rendering 12 node buttons in category 'Compression'")
    sidebar_log.info("Node filter text: 'Huffman' matched 2 nodes")


def simulate_inspector_events():
    """
    Shows logging from the property inspector.
    """
    from src.utils.logger_config import get_logger

    insp_log = get_logger("Inspector")
    insp_log.info("Inspecting node: 'HuffmanEncoder'")
    insp_log.debug("Parameter schema loaded: 8 parameters in 3 categories")
    insp_log.info("Parameter 'CompressionLevel' changed from 'Fast' to 'Maximum'")


# =============================================================================
# 4. ENGINE COMPONENT LOGGING
# =============================================================================

def simulate_engine_tick():
    """
    Simulates what the SimulationEngine would log each tick.
    DEBUG messages here are high-frequency and would flood the console,
    so they only appear in verbose mode.
    """
    from src.utils.logger_config import get_logger

    engine_log = get_logger("ENGINE")

    # --- INFO: Major lifecycle events ---
    engine_log.info("Simulation started — mode=REALTIME, interval=16ms (target 60 FPS)")
    engine_log.info("3 nodes active: TextGenerator -> HuffmanEncoder -> BinarySink")

    # --- DEBUG: Per-tick details (suppressed in production mode) ---
    engine_log.debug("Tick #1 started — processing queue depth: 2")
    engine_log.debug("  -> TextGenerator: generating 64 bytes of Lorem Ipsum...")
    engine_log.debug("  -> Packet PKT-0042 injected, routing to HuffmanEncoder")
    engine_log.debug("  -> HuffmanEncoder: encoding 1024 bits -> 430 bits (42%%)")
    engine_log.debug("  -> BinarySink: packet received, appending to output buffer")
    engine_log.debug("Tick #1 completed — 1 packet processed, 0 dropped, elapsed: 4.2ms")

    engine_log.debug("Tick #2 started — processing queue depth: 1")
    engine_log.debug("  -> TextGenerator: idle (awaiting trigger)")
    engine_log.debug("Tick #2 completed — 0 packets processed, 0 dropped, elapsed: 0.3ms")

    engine_log.info("Simulation paused after 100 ticks — avg FPS: 58.3, total packets: 95")
    engine_log.info("Simulation stopped — total elapsed: 1.72s, processed: 95, dropped: 5")


def simulate_network_events():
    """
    Shows logging from the connection/network system.
    """
    from src.utils.logger_config import get_logger

    net_log = get_logger("NETWORK")

    # --- INFO ---
    net_log.info("Connection established: TextGenerator.output -> HuffmanEncoder.input (DataRate: 1Mbps)")

    # --- DEBUG ---
    net_log.debug("Connection #3: BER=0.001, latency=2ms, jitter=0.5ms")
    net_log.debug("Packet PKT-0042: 1024 bytes transmitted in 8.2ms")
    net_log.debug("Connection throughput: 845 Kbps (84.5%% utilization)")

    # --- WARNING ---
    net_log.warning("Connection #3: packet loss detected (1/1000 packets dropped)")
    net_log.warning("Connection buffer at 95% capacity — backpressure applied")

    # --- ERROR ---
    net_log.error("Connection #4: link down — no response from HuffmanEncoder")


def simulate_compressor_events():
    """
    Shows logging from compression algorithm nodes with math calculations.
    """
    from src.utils.logger_config import get_logger

    comp_log = get_logger("COMPRESSOR")

    # --- INFO ---
    comp_log.info("Compression started: input_size=4096, algorithm=LZ77")

    # --- DEBUG: Math calculations (only in verbose mode) ---
    comp_log.debug("Sliding window size: 4096 bytes, lookahead: 128 bytes")
    comp_log.debug("Match found at offset=142, length=12 — encoding as (142, 12, 'n')")
    comp_log.debug("Match found at offset=2048, length=42 — encoding as (2048, 42, ' ')")
    comp_log.debug("Literal emitted: character 'X' at position 3072")
    comp_log.debug("Entropy before: 7.2 bits/symbol, after: 3.1 bits/symbol")

    # --- WARNING ---
    comp_log.warning("Compression ratio: 0.95 — minimal gain, consider using different algorithm")
    comp_log.warning("Dictionary exhausted: resetting at position 2048")

    # --- ERROR ---
    comp_log.error("Compression failed: input data is empty")


# =============================================================================
# 5. DEMONSTRATION: Non-blocking performance
# =============================================================================

def demonstrate_non_blocking():
    """
    Shows that the QueueHandler-based logging does NOT block the calling thread.
    Even if the file system is slow, the main thread is never stalled.
    """
    from src.utils.logger_config import logger_config, get_logger

    log = get_logger("PERF_TEST")

    print("\n" + "=" * 70)
    print("  PERFORMANCE DEMONSTRATION: Non-blocking QueueHandler")
    print("=" * 70)
    print("\n  The main thread logs 1,000 messages to the queue (microseconds each).")
    print("  A separate listener thread writes them to disk in the background.")
    print("  This ensures the 60 FPS simulation loop is NEVER blocked by I/O.\n")

    # Warm up
    for _ in range(100):
        log.debug("Warmup message")

    # Benchmark logging speed
    num_messages = 10_000
    start = time.perf_counter()

    for i in range(num_messages):
        log.debug(f"Performance test message #{i}: x={i*0.042:.4f}, y={(i*17)%256}")

    elapsed = time.perf_counter() - start
    msgs_per_sec = num_messages / elapsed

    print(f"  Logged {num_messages} messages in {elapsed:.4f} seconds")
    print(f"  Throughput: {msgs_per_sec:,.0f} messages/second")
    print(f"  Time per call: {(elapsed / num_messages) * 1_000_000:.1f} µs")
    print(f"\n  → At 60 FPS, one tick = 16.67 ms.")
    print(f"  → Each log call takes < 1 µs — completely negligible.\n")


# =============================================================================
# 6. DEMONSTRATION: Toggling verbose / production mode
# =============================================================================

def demonstrate_mode_toggle():
    """
    Shows how to switch between DEBUG (verbose) and WARNING+ (production) modes.
    In production mode, only WARNING and ERROR messages appear on the console.
    """
    from src.utils.logger_config import logger_config, get_logger

    log = get_logger("ModeDemo")

    print("\n" + "=" * 70)
    print("  MODE TOGGLE DEMONSTRATION")
    print("=" * 70)

    # --- PRODUCTION MODE: Only WARNING and above ---
    print("\n  [PRODUCTION MODE] — set_verbose(False)")
    print("  Only WARNING and ERROR messages will appear:\n")

    logger_config.set_verbose(False)
    log.debug("   (this DEBUG should NOT appear in console)")
    log.info("   (this INFO should NOT appear in console)")
    log.warning("   ✓ WARNING: Low compression ratio detected")
    log.error("   ✓ ERROR: Encoding failed — invalid symbol")

    # --- DEBUG MODE: Everything ---
    print("\n  [DEBUG MODE] — set_verbose(True)")
    print("  All messages (DEBUG, INFO, WARNING, ERROR) will appear:\n")

    logger_config.set_verbose(True)
    log.debug("   ✓ DEBUG: Huffman tree depth = 4, symbols = 6")
    log.info("   ✓ INFO: Node placed at (320, 240)")
    log.warning("   ✓ WARNING: Cyclic graph detected")
    log.error("   ✓ ERROR: Connection lost")


# =============================================================================
# 7. DEMONSTRATION: Component tagging output format
# =============================================================================

def demonstrate_component_tagging():
    """
    Shows that each log message is tagged with its origin component,
    using the exact format: [TIMESTAMP] [LEVEL] [COMPONENT] - Message
    """
    from src.utils.logger_config import get_logger

    print("\n" + "=" * 70)
    print("  COMPONENT TAGGING — Each message shows its origin in [COMPONENT]")
    print("=" * 70)
    print("  Expected format: [14:02:33.105] [LEVEL] [COMPONENT] - Message\n")

    get_logger("UI").info("User clicked 'Start Simulation'")
    get_logger("ENGINE").info("Tick #1 started")
    get_logger("NETWORK").warning("Connection #3: packet loss detected")
    get_logger("COMPRESSOR").debug("Entropy before: 7.2, after: 3.1 bits/symbol")
    get_logger("TextGenerator").error("Failed to generate text: no seed data")
    get_logger("Inspector").info("Parameter 'bitrate' changed from 1000 to 2000")


# =============================================================================
# MAIN: Run all demonstrations
# =============================================================================

def main():
    print("=" * 70)
    print("  InfoFlowLab — Non-blocking Logging System Demonstration")
    print("  logger_config.py with QueueHandler + QueueListener")
    print("=" * 70)

    # 1. Setup logging once (simulate application boot)
    logger_config = setup_application_logging()

    # 2. Run demonstrations
    print("\n>>> SECTION 1: NodeBase.process() logging inside simulation nodes")
    print("-" * 70)
    simulate_node_process()

    print("\n>>> SECTION 2: Packet tracking (DEBUG-level)")
    print("-" * 70)
    simulate_packet_tracking()

    print("\n>>> SECTION 3: UI Event Handler logging")
    print("-" * 70)
    simulate_ui_events()
    simulate_sidebar_events()
    simulate_inspector_events()

    print("\n>>> SECTION 4: Engine and network logging")
    print("-" * 70)
    simulate_engine_tick()
    simulate_network_events()
    simulate_compressor_events()

    # 3. Performance demonstration
    demonstrate_non_blocking()

    # 4. Mode toggle demonstration
    demonstrate_mode_toggle()

    # 5. Component tagging
    demonstrate_component_tagging()

    # 6. Cleanup
    logger_config.shutdown()

    print("\n" + "=" * 70)
    print("  ALL DEMONSTRATIONS COMPLETE")
    print("  Check logs/infoflowlab.log for the full output")
    print("=" * 70)


if __name__ == "__main__":
    main()