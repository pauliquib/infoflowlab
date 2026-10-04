"""
logger_config.py - Non-blocking background logging system for InfoFlowLab.

Provides:
- Centralized logging configuration importable across all modules
- Non-blocking logging via QueueHandler + QueueListener (no 60 FPS stutter)
- Exact format: [TIMESTAMP] [LEVEL] [COMPONENT] - Message
- Easy toggling between DEBUG (verbose) and WARNING (production) modes
"""

import logging
import logging.handlers
import queue
import sys
import atexit
from typing import Optional


# =============================================================================
# Custom Formatter
# =============================================================================

class ConsoleFormatter(logging.Formatter):
    """
    Custom formatter producing the exact required output format:
        [14:02:33.105] [INFO] [UI] Selection box created
    """

    def format(self, record: logging.LogRecord) -> str:
        timestamp = self.formatTime(record, datefmt="%H:%M:%S")
        # Add milliseconds manually
        msec = f"{int(record.msecs):03d}"
        component = record.name
        level = record.levelname
        msg = record.getMessage()
        return f"[{timestamp}.{msec}] [{level}] [{component}] - {msg}"


class FileFormatter(logging.Formatter):
    """Detailed formatter for file logging with full context."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = self.formatTime(record, datefmt="%Y-%m-%d %H:%M:%S")
        msec = f"{int(record.msecs):03d}"
        component = record.name
        level = record.levelname
        msg = record.getMessage()
        location = f"{record.pathname}:{record.lineno}"
        return f"[{timestamp}.{msec}] [{level}] [{component}] ({location}) - {msg}"


# =============================================================================
# Logger Configuration Manager
# =============================================================================

class LoggerConfig:
    """
    Centralized, non-blocking logger configuration.

    Uses QueueHandler + QueueListener to ensure logging calls never block
    the calling thread (critical for 60 FPS simulation performance).

    Usage:
        from src.utils.logger_config import logger_config

        # Get a logger for any module
        logger = logger_config.get_logger("UI")
        logger.info("Selection box created")

        # Toggle verbosity
        logger_config.set_verbose(True)   # Includes DEBUG messages
        logger_config.set_verbose(False)  # WARNING and above only
    """

    def __init__(self):
        self._initialized = False
        self._log_queue: Optional[queue.SimpleQueue] = None
        self._queue_handler: Optional[logging.handlers.QueueHandler] = None
        self._queue_listener: Optional[logging.handlers.QueueListener] = None
        self._root_logger: Optional[logging.Logger] = None
        self._verbose = True  # Default: show DEBUG

    def setup(self, log_file_path: str = "logs/infoflowlab.log",
              level: int = logging.DEBUG) -> None:
        """
        Initialize the non-blocking logging system.
        Safe to call multiple times — only configures once.

        Args:
            log_file_path: Path to the rotating log file
            level: Base logging level (typically DEBUG, filtering done per-handler)
        """
        if self._initialized:
            return
        self._initialized = True

        # --- Root logger ---
        self._root_logger = logging.getLogger("InfoFlowLab")
        self._root_logger.setLevel(level)
        self._root_logger.handlers.clear()
        self._root_logger.propagate = False

        # --- Queue for non-blocking logging ---
        self._log_queue = queue.SimpleQueue()

        # --- QueueHandler (producer side — lightning fast, never blocks) ---
        self._queue_handler = logging.handlers.QueueHandler(self._log_queue)
        self._queue_handler.setLevel(level)
        self._root_logger.addHandler(self._queue_handler)

        # --- Console handler (consumer side — runs in listener thread) ---
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG if self._verbose else logging.WARNING)
        console_handler.setFormatter(ConsoleFormatter())

        # --- File handler with rotation (consumer side) ---
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # Always capture everything to file
        file_handler.setFormatter(FileFormatter())

        # --- Error-only file handler (consumer side) ---
        err_handler = logging.handlers.RotatingFileHandler(
            "logs/errors.log",
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=3,
            encoding='utf-8'
        )
        err_handler.setLevel(logging.ERROR)
        err_handler.setFormatter(FileFormatter())

        # --- QueueListener (consumer — runs in its own thread) ---
        self._queue_listener = logging.handlers.QueueListener(
            self._log_queue,
            console_handler,
            file_handler,
            err_handler,
            respect_handler_level=True
        )
        self._queue_listener.start()

        # Register cleanup on interpreter exit
        atexit.register(self.shutdown)

        # Log startup banner
        self._root_logger.info("=" * 60)
        self._root_logger.info("Non-blocking logging system initialized")
        self._root_logger.info(f"Log file: {log_file_path}")
        self._root_logger.info("=" * 60)

    def get_logger(self, name: str) -> logging.Logger:
        """
        Get or create a logger with the given component name.

        Args:
            name: Component name (e.g. "UI", "Engine", "Canvas")

        Returns:
            Logger instance that uses the non-blocking queue
        """
        if not self._initialized:
            self.setup()
        return logging.getLogger(f"InfoFlowLab.{name}")

    def set_verbose(self, enabled: bool) -> None:
        """
        Toggle verbose (DEBUG) logging.

        Args:
            enabled: True to show DEBUG/INFO/WARNING/ERROR,
                     False to show only WARNING and above
        """
        self._verbose = enabled
        if self._queue_listener and self._queue_listener.handlers:
            for handler in self._queue_listener.handlers:
                if isinstance(handler, logging.StreamHandler):
                    handler.setLevel(
                        logging.DEBUG if enabled else logging.WARNING
                    )
        level_name = "DEBUG" if enabled else "WARNING"
        self._root_logger.info(f"Console log level set to {level_name}")

    def is_verbose(self) -> bool:
        """Check if verbose (DEBUG) logging is enabled."""
        return self._verbose

    def shutdown(self) -> None:
        """Gracefully shut down the logging system."""
        if self._queue_listener:
            self._queue_listener.stop()
        if self._root_logger:
            for handler in self._root_logger.handlers[:]:
                handler.close()
                self._root_logger.removeHandler(handler)


# =============================================================================
# Global singleton instance
# =============================================================================

logger_config = LoggerConfig()


def get_logger(name: str = "App") -> logging.Logger:
    """
    Convenience function to quickly obtain a configured logger.

    Args:
        name: Component name (e.g. "UI", "Engine", "Canvas", "Sidebar")

    Returns:
        Logger instance backed by the non-blocking queue
    """
    return logger_config.get_logger(name)