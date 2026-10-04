"""
Logging configuration and utilities for InfoFlowLab.

Provides:
- File-based logging with rotation
- Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Integration with GUI console
- Performance profiling utilities
"""

import logging
import logging.handlers
import sys
import time
import cProfile
import pstats
import io
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from PySide6.QtCore import QObject, Signal


class LogManager(QObject):
    """
    Centralized logging manager that bridges Python logging with GUI console.
    
    Features:
    - File logging with automatic rotation (10MB max, 5 backups)
    - Console output with color coding
    - Performance profiling support
    - Runtime log level adjustment
    """
    
    # Signal for GUI integration
    log_message = Signal(str, str)  # category, message
    
    # Log levels
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
    
    _instance: Optional['LogManager'] = None
    
    def __new__(cls) -> 'LogManager':
        """Singleton pattern to ensure single logging configuration."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize logging system."""
        if self._initialized:
            return
        
        super().__init__()
        self._initialized = True
        self._log_dir = Path("logs")
        self._log_dir.mkdir(exist_ok=True)
        self._profiler: Optional[cProfile.Profile] = None
        self._profiling_enabled = False
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure Python logging with file and console handlers."""
        # Create logger
        self.logger = logging.getLogger("InfoFlowLab")
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate logs
        self.logger.propagate = False
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # File handler with rotation (10MB max, 5 backup files)
        log_file = self._log_dir / "infoflowlab.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Detailed format for file
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Error-only separate file for quick debugging
        error_file = self._log_dir / "errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s\n'
            'Exception: %(exc_info)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        error_handler.setFormatter(error_formatter)
        self.logger.addHandler(error_handler)
        
        # Console handler (for terminal output)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        self.logger.info("=" * 60)
        self.logger.info("InfoFlowLab Logging System Initialized")
        self.logger.info(f"Log directory: {self._log_dir.absolute()}")
        self.logger.info("=" * 60)
    
    def get_logger(self, name: str = "InfoFlowLab") -> logging.Logger:
        """
        Get a logger instance.
        
        Args:
            name: Logger name (default: "InfoFlowLab")
            
        Returns:
            Logger instance
        """
        return logging.getLogger(name)
    
    def set_level(self, level: int):
        """
        Set logging level at runtime.
        
        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.logger.setLevel(level)
        for handler in self.logger.handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                # Keep file handler at DEBUG to capture everything
                continue
            handler.setLevel(level)
        
        self.info(f"Log level changed to {logging.getLevelName(level)}")
    
    def debug(self, message: str, *args, **kwargs):
        """Log debug message."""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Log info message."""
        self.logger.info(message, *args, **kwargs)
        # Also emit to GUI console
        self.log_message.emit("info", message)
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning message."""
        self.logger.warning(message, *args, **kwargs)
        self.log_message.emit("warning", message)
    
    def error(self, message: str, *args, **kwargs):
        """Log error message."""
        self.logger.error(message, *args, **kwargs, exc_info=True)
        self.log_message.emit("error", message)
    
    def critical(self, message: str, *args, **kwargs):
        """Log critical message."""
        self.logger.critical(message, *args, **kwargs, exc_info=True)
        self.log_message.emit("error", f"CRITICAL: {message}")
    
    def exception(self, message: str, *args, **kwargs):
        """Log exception with traceback."""
        self.logger.exception(message, *args, **kwargs)
        self.log_message.emit("error", f"EXCEPTION: {message}")
    
    def log_function_call(self, func_name: str, args: tuple, kwargs: dict):
        """Log function call for debugging."""
        args_str = ", ".join([str(arg) for arg in args])
        kwargs_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
        all_args = ", ".join(filter(None, [args_str, kwargs_str]))
        self.debug(f"CALL: {func_name}({all_args})")
    
    # ==================== PROFILING ====================
    
    def start_profiling(self):
        """Start performance profiling."""
        if self._profiling_enabled:
            self.warning("Profiling already active")
            return
        
        self._profiler = cProfile.Profile()
        self._profiler.enable()
        self._profiling_enabled = True
        self.info("Performance profiling STARTED")
    
    def stop_profiling(self, sort_by: str = 'cumulative', lines: int = 30) -> str:
        """
        Stop profiling and return report.
        
        Args:
            sort_by: Sort key ('cumulative', 'total', 'calls', etc.)
            lines: Number of lines in report
            
        Returns:
            Formatted profiling report
        """
        if not self._profiling_enabled or not self._profiler:
            self.warning("No active profiling session")
            return ""
        
        self._profiler.disable()
        self._profiling_enabled = False
        
        # Capture stats
        stream = io.StringIO()
        stats = pstats.Stats(self._profiler, stream=stream)
        stats.sort_stats(sort_by)
        stats.print_stats(lines)
        
        report = stream.getvalue()
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        profile_file = self._log_dir / f"profile_{timestamp}.prof"
        self._profiler.dump_stats(profile_file)
        
        self.info(f"Performance profiling STOPPED - Report saved to {profile_file}")
        
        # Reset profiler
        self._profiler = None
        
        return report
    
    def is_profiling(self) -> bool:
        """Check if profiling is active."""
        return self._profiling_enabled
    
    def get_log_files(self) -> Dict[str, Path]:
        """
        Get paths to all log files.
        
        Returns:
            Dictionary with log file paths
        """
        return {
            'main_log': self._log_dir / "infoflowlab.log",
            'error_log': self._log_dir / "errors.log",
        }
    
    def get_recent_logs(self, lines: int = 100) -> str:
        """
        Get recent log entries.
        
        Args:
            lines: Number of lines to retrieve
            
        Returns:
            Recent log entries as string
        """
        log_file = self._log_dir / "infoflowlab.log"
        if not log_file.exists():
            return "No log file found"
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return ''.join(all_lines[-lines:])
        except Exception as e:
            return f"Error reading log file: {e}"
    
    def clear_logs(self):
        """Clear all log files."""
        try:
            for log_file in self._log_dir.glob("*.log"):
                log_file.unlink()
            for profile_file in self._log_dir.glob("*.prof"):
                profile_file.unlink()
            self.info("Log files cleared")
        except Exception as e:
            self.error(f"Failed to clear logs: {e}")


# Global instance
log_manager = LogManager()


def get_logger(name: str = "InfoFlowLab") -> logging.Logger:
    """
    Convenience function to get logger.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return log_manager.get_logger(name)


def log_execution_time(func):
    """
    Decorator to log function execution time.
    
    Usage:
        @log_execution_time
        def my_function():
            ...
    """
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger()
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.debug(f"{func.__name__} executed in {elapsed:.4f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"{func.__name__} failed after {elapsed:.4f}s: {e}")
            raise
    
    return wrapper


class PerformanceMonitor:
    """
    Simple performance monitoring for critical operations.
    
    Usage:
        monitor = PerformanceMonitor()
        with monitor.measure("operation_name"):
            # Your code here
            pass
        print(monitor.get_stats())
    """
    
    def __init__(self):
        self._measurements: Dict[str, list] = {}
        self._current_operation: Optional[str] = None
        self._start_time: Optional[float] = None
    
    def measure(self, operation_name: str):
        """
        Context manager for measuring operation time.
        
        Args:
            operation_name: Name of the operation being measured
        """
        return self._MeasurementContext(self, operation_name)
    
    def _start(self, operation_name: str):
        """Start measuring an operation."""
        self._current_operation = operation_name
        self._start_time = time.time()
    
    def _stop(self):
        """Stop measuring and record the result."""
        if self._current_operation and self._start_time:
            elapsed = time.time() - self._start_time
            if self._current_operation not in self._measurements:
                self._measurements[self._current_operation] = []
            self._measurements[self._current_operation].append(elapsed)
            
            logger = get_logger()
            logger.debug(f"PERF: {self._current_operation} took {elapsed:.4f}s")
            
            self._current_operation = None
            self._start_time = None
    
    def get_stats(self) -> Dict[str, Dict[str, float]]:
        """
        Get performance statistics.
        
        Returns:
            Dictionary with stats for each operation
        """
        stats = {}
        for op_name, times in self._measurements.items():
            if times:
                stats[op_name] = {
                    'count': len(times),
                    'total': sum(times),
                    'average': sum(times) / len(times),
                    'min': min(times),
                    'max': max(times)
                }
        return stats
    
    def reset(self):
        """Reset all measurements."""
        self._measurements.clear()
    
    class _MeasurementContext:
        """Context manager for performance measurement."""
        
        def __init__(self, monitor: 'PerformanceMonitor', operation_name: str):
            self.monitor = monitor
            self.operation_name = operation_name
        
        def __enter__(self):
            self.monitor._start(self.operation_name)
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.monitor._stop()
            return False


# Global performance monitor instance
perf_monitor = PerformanceMonitor()