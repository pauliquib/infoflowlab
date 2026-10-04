"""
Pytest configuration and shared fixtures.
"""

import os
import pytest
from PySide6.QtWidgets import QApplication

# Headless Qt for CI and local test runs without display
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def qapp():
    """Provide QApplication instance for Qt-based tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
