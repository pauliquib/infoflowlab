#!/usr/bin/env python3
"""
Test script for logging and profiling system.
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_basic_logging():
    """Test basic logging functionality."""
    print("=" * 60)
    print("TEST 1: Basic Logging")
    print("=" * 60)
    
    from src.utils.logger import get_logger, log_manager
    
    # Test different log levels
    logger = get_logger("TestModule")
    logger.debug("This is a DEBUG message")
    logger.info("This is an INFO message")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")
    
    # Test log manager
    log_manager.info("Direct log_manager call")
    log_manager.warning("Warning via log_manager")
    
    print("\n✓ Basic logging test completed")
    print(f"  Log files created in: {log_manager._log_dir.absolute()}")
    

def test_profiling():
    """Test profiling functionality."""
    print("\n" + "=" * 60)
    print("TEST 2: Performance Profiling")
    print("=" * 60)
    
    from src.utils.logger import log_manager
    import time
    
    # Start profiling
    log_manager.start_profiling()
    print("Profiling started...")
    
    # Simulate some work
    for i in range(1000):
        _ = sum(range(100))
    
    time.sleep(0.1)  # Simulate I/O
    
    for i in range(500):
        _ = [x**2 for x in range(50)]
    
    # Stop profiling and get report
    report = log_manager.stop_profiling(sort_by='cumulative', lines=20)
    
    print("\nProfiling Report:")
    print("-" * 60)
    print(report)
    print("-" * 60)
    print("\n✓ Profiling test completed")
    print(f"  Profile data saved to: logs/profile_*.prof")


def test_performance_monitor():
    """Test performance monitor."""
    print("\n" + "=" * 60)
    print("TEST 3: Performance Monitor")
    print("=" * 60)
    
    from src.utils.logger import perf_monitor
    import time
    
    # Measure some operations
    with perf_monitor.measure("test_operation_1"):
        time.sleep(0.05)
    
    with perf_monitor.measure("test_operation_2"):
        time.sleep(0.03)
    
    with perf_monitor.measure("test_operation_1"):
        time.sleep(0.04)
    
    # Get statistics
    stats = perf_monitor.get_stats()
    
    print("\nPerformance Statistics:")
    print("-" * 60)
    for op_name, op_stats in stats.items():
        print(f"\nOperation: {op_name}")
        print(f"  Count: {op_stats['count']}")
        print(f"  Total: {op_stats['total']:.4f}s")
        print(f"  Average: {op_stats['average']:.4f}s")
        print(f"  Min: {op_stats['min']:.4f}s")
        print(f"  Max: {op_stats['max']:.4f}s")
    print("-" * 60)
    
    print("\n✓ Performance monitor test completed")


def test_log_files():
    """Test log file operations."""
    print("\n" + "=" * 60)
    print("TEST 4: Log File Operations")
    print("=" * 60)
    
    from src.utils.logger import log_manager
    
    # Get log file paths
    files = log_manager.get_log_files()
    print("\nLog file paths:")
    for name, path in files.items():
        print(f"  {name}: {path}")
        if path.exists():
            size = path.stat().st_size
            print(f"    Size: {size} bytes")
    
    # Get recent logs
    recent = log_manager.get_recent_logs(lines=10)
    print("\nRecent log entries (last 10 lines):")
    print("-" * 60)
    print(recent)
    print("-" * 60)
    
    print("\n✓ Log file operations test completed")


def test_decorator():
    """Test execution time decorator."""
    print("\n" + "=" * 60)
    print("TEST 5: Execution Time Decorator")
    print("=" * 60)
    
    from src.utils.logger import log_execution_time
    import time
    
    @log_execution_time
    def slow_function():
        time.sleep(0.1)
        return "Done"
    
    @log_execution_time
    def fast_function():
        return sum(range(100))
    
    print("\nCalling slow_function...")
    result = slow_function()
    print(f"Result: {result}")
    
    print("\nCalling fast_function...")
    result = fast_function()
    print(f"Result: {result}")
    
    print("\n✓ Decorator test completed (check logs for timing info)")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("InfoFlowLab Logging & Profiling System Tests")
    print("=" * 60)
    
    try:
        test_basic_logging()
        test_profiling()
        test_performance_monitor()
        test_log_files()
        test_decorator()
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        print("\nCheck the logs/ directory for output files:")
        print("  - logs/infoflowlab.log")
        print("  - logs/errors.log")
        print("  - logs/profile_*.prof")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()