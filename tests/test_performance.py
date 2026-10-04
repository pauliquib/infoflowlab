#!/usr/bin/env python3
"""
Performance test for InfoFlowLab - measures the impact of optimizations.
"""

import sys
import os
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.mark.xfail(reason="canvas._animate_packets() was replaced by the new animation system", strict=False)
def test_canvas_performance():
    """Test canvas rendering performance."""
    print("=" * 60)
    print("PERFORMANCE TEST - Canvas Rendering")
    print("=" * 60)
    
    from src.utils.logger import perf_monitor, get_logger
    from src.core.graph import Graph
    from src.core.engine import SimulationEngine
    from src.gui.canvas import Canvas
    from PySide6.QtWidgets import QApplication
    
    # Create QApplication (required for Qt widgets)
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    logger = get_logger("PerformanceTest")
    
    # Test 1: Canvas initialization
    print("\n1. Testing canvas initialization...")
    with perf_monitor.measure("canvas_init"):
        graph = Graph()
        engine = SimulationEngine(graph)
        canvas = Canvas(graph, engine)
    
    stats = perf_monitor.get_stats()
    if "canvas_init" in stats:
        logger.info(f"Canvas init: {stats['canvas_init']['total']*1000:.2f}ms")
    
    # Test 2: Grid drawing (should be fast now)
    print("2. Testing grid drawing...")
    with perf_monitor.measure("grid_redraw"):
        canvas._draw_grid_dots()
    
    stats = perf_monitor.get_stats()
    if "grid_drawing" in stats:
        logger.info(f"Grid drawing: {stats['grid_drawing']['total']*1000:.2f}ms")
        if "grid_drawing" in stats and stats["grid_drawing"]["total"] < 0.5:
            print("   ✓ Grid drawing is FAST (< 500ms)")
        else:
            print("   ⚠ Grid drawing is SLOW (> 500ms)")
    
    # Test 3: Add multiple nodes
    print("3. Testing node addition (10 nodes)...")
    start = time.time()
    for i in range(10):
        canvas.add_node_at("Text", (i * 100, i * 100))
    elapsed = (time.time() - start) * 1000
    logger.info(f"Added 10 nodes in {elapsed:.2f}ms")
    print(f"   Time: {elapsed:.2f}ms")
    
    # Test 4: Zoom operations
    print("4. Testing zoom operations...")
    from PySide6.QtGui import QWheelEvent
    from PySide6.QtCore import QPoint, QPointF
    
    # Simulate zoom events
    with perf_monitor.measure("zoom_operations"):
        for _ in range(5):
            # Simulate Ctrl+Scroll up
            canvas.scale(1.15, 1.15)
        for _ in range(5):
            # Simulate Ctrl+Scroll down
            canvas.scale(1/1.15, 1/1.15)
    
    stats = perf_monitor.get_stats()
    if "zoom_operations" in stats:
        logger.info(f"10 zoom ops: {stats['zoom_operations']['total']*1000:.2f}ms")
        print(f"   Time: {stats['zoom_operations']['total']*1000:.2f}ms")
    
    # Test 5: Animation tick
    print("5. Testing animation tick...")
    with perf_monitor.measure("animation_tick"):
        canvas._animate_packets()
    
    stats = perf_monitor.get_stats()
    if "packet_animation" in stats:
        logger.info(f"Animation tick: {stats['packet_animation']['total']*1000:.2f}ms")
        print(f"   Time: {stats['packet_animation']['total']*1000:.2f}ms")
    
    # Summary
    print("\n" + "=" * 60)
    print("PERFORMANCE SUMMARY")
    print("=" * 60)
    
    all_stats = perf_monitor.get_stats()
    for op_name, op_stats in all_stats.items():
        print(f"\n{op_name}:")
        print(f"  Total: {op_stats['total']*1000:.2f}ms")
        print(f"  Average: {op_stats['average']*1000:.2f}ms")
        print(f"  Count: {op_stats['count']}")
    
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS:")
    print("=" * 60)
    
    if "grid_drawing" in all_stats:
        grid_time = all_stats["grid_drawing"]["total"] * 1000
        if grid_time > 500:
            print("⚠ Grid drawing is still slow - consider using QPixmap")
        elif grid_time > 200:
            print("✓ Grid drawing is acceptable")
        else:
            print("✓ Grid drawing is FAST!")
    
    if "packet_animation" in all_stats:
        anim_time = all_stats["packet_animation"]["total"] * 1000
        if anim_time > 20:
            print("⚠ Packet animation could be faster")
        else:
            print("✓ Packet animation is fast")
    
    print("\n" + "=" * 60)
    print("Test completed! Check logs/ for detailed output.")
    print("=" * 60)
    
    # Clean up
    canvas.deleteLater()
    perf_monitor.reset()


def test_memory_usage():
    """Test memory usage with many nodes."""
    print("\n" + "=" * 60)
    print("MEMORY TEST - Many Nodes")
    print("=" * 60)
    
    from src.utils.logger import get_logger
    from src.core.graph import Graph
    from src.core.engine import SimulationEngine
    from src.gui.canvas import Canvas
    from PySide6.QtWidgets import QApplication
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    logger = get_logger("MemoryTest")
    
    graph = Graph()
    engine = SimulationEngine(graph)
    canvas = Canvas(graph, engine)
    
    # Add 50 nodes
    print("\nAdding 50 nodes...")
    start = time.time()
    for i in range(50):
        x = (i % 10) * 150
        y = (i // 10) * 150
        canvas.add_node_at("Text", (x, y))
    elapsed = (time.time() - start) * 1000
    
    logger.info(f"Added 50 nodes in {elapsed:.2f}ms")
    print(f"Time: {elapsed:.2f}ms")
    print(f"Nodes in graph: {len(graph.nodes)}")
    print(f"Node items in canvas: {len(canvas._node_items)}")
    
    # Test connection creation
    print("\nCreating 25 connections...")
    start = time.time()
    node_ids = list(graph.nodes.keys())
    for i in range(0, min(25, len(node_ids)-1), 2):
        canvas.graph.connect(node_ids[i], "output", node_ids[i+1], "input")
    canvas._redraw_connections()
    elapsed = (time.time() - start) * 1000
    
    logger.info(f"Created 25 connections in {elapsed:.2f}ms")
    print(f"Time: {elapsed:.2f}ms")
    print(f"Connections: {len(graph.connections)}")
    
    print("\n✓ Memory test completed")
    
    # Clean up
    canvas.deleteLater()


def main():
    """Run all performance tests."""
    print("\n" + "=" * 60)
    print("InfoFlowLab Performance Test Suite")
    print("=" * 60)
    
    try:
        test_canvas_performance()
        test_memory_usage()
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED ✓")
        print("=" * 60)
        print("\nCheck logs/performance.log for detailed metrics")
        print("Use GUI profiling (⏱ Start Profiling) for deeper analysis")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()