#!/usr/bin/env python3
"""
InfoFlowLab v1.0 - Production Ready
Interaktivní Simulátor Komprese a Komunikace

Professional academic tool for information theory, data compression,
and communication channel simulation. Features:
- 50+ simulation nodes with drag-and-drop canvas
- Real-time and step-by-step simulation modes
- Bézier packet animations with type-specific visuals
- Dynamic property inspector with schema-driven UI
- JSON scenario import/export
- Professional dark theme with category color coding
- Comprehensive logging and profiling system
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QStyleFactory
from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtGui import QIcon


def main():
    """Main entry point - launches InfoFlowLab v1.0."""
    try:
        # Initialize logging system FIRST
        from src.utils.logger import log_manager
        log_manager.info("=" * 60)
        log_manager.info("InfoFlowLab Application Starting")
        log_manager.info("=" * 60)
        
        # Enable High DPI support
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        
        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("InfoFlowLab")
        app.setOrganizationName("InfoFlowLab")
        app.setApplicationVersion("1.0.0")
        
        # Set application icon
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        app.setWindowIcon(QIcon(icon_path))
        
        # Force Fusion style for consistent look across platforms
        app.setStyle(QStyleFactory.create("Fusion"))
        
        # Global dark theme stylesheet
        app.setStyleSheet("""
            /* Global */
            QMainWindow, QWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
            }
            
            QMainWindow {
                background-color: #252526;
            }
            
            /* Menu */
            QMenuBar {
                background-color: #2d2d30;
                color: #d4d4d4;
                border-bottom: 1px solid #3c3c3c;
                padding: 2px;
            }
            QMenuBar::item:selected {
                background-color: #094771;
            }
            QMenu {
                background-color: #2d2d30;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
            }
            QMenu::item:selected {
                background-color: #094771;
            }
            QMenu::separator {
                height: 1px;
                background: #3c3c3c;
                margin: 4px 8px;
            }
            
            /* Toolbar */
            QToolBar {
                background-color: #252526;
                border-bottom: 1px solid #3c3c3c;
                spacing: 6px;
                padding: 4px 8px;
            }
            QToolBar::separator {
                width: 1px;
                background: #3c3c3c;
                margin: 4px 8px;
            }
            QToolButton {
                background: transparent;
                color: #d4d4d4;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QToolButton:hover {
                background: #2a2d2e;
                border-color: #3c3c3c;
            }
            QToolButton:pressed {
                background: #094771;
            }
            QToolButton:disabled {
                color: #5a5a5a;
            }
            QToolButton#toolbarPrimary {
                background: #0e639c;
                border-color: #1177bb;
                font-weight: 600;
            }
            QToolButton#toolbarPrimary:hover {
                background: #1177bb;
            }
            
            /* Status Bar */
            QStatusBar {
                background-color: #1e1e1e;
                color: #cccccc;
                border-top: 1px solid #3c3c3c;
                font-size: 12px;
                padding: 2px 8px;
            }
            QLabel#statusLabel {
                color: #9cdcfe;
                padding: 0 6px;
            }
            QLabel#tickLabel {
                color: #858585;
                padding: 0 6px;
            }
            
            /* Splitter */
            QSplitter::handle {
                background-color: #3c3c3c;
                width: 1px;
            }
            
            /* Scroll Bars */
            QScrollBar:vertical {
                width: 10px;
                background: #1e1e1e;
            }
            QScrollBar::handle:vertical {
                background: #424242;
                min-height: 30px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #555;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar:horizontal {
                height: 10px;
                background: #1e1e1e;
            }
            QScrollBar::handle:horizontal {
                background: #424242;
                min-width: 30px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #555;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            
            /* Tool Tips */
            QToolTip {
                background-color: #2d2d30;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                padding: 4px;
                font-size: 12px;
            }
            
            /* Dialogs */
            QDialog {
                background-color: #1e1e1e;
            }
            
            /* File Dialog */
            QFileDialog {
                background-color: #1e1e1e;
            }
            QFileDialog QListView, QFileDialog QTreeView {
                background-color: #2d2d30;
                color: #d4d4d4;
            }
        """)
        
        # Create and show main window
        from src.gui.main_window import MainWindow
        
        window = MainWindow()
        window.setWindowIcon(QIcon(icon_path))
        window.show()
        
        log_manager.info("Main window displayed, entering event loop")
        
        # Run application
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"Error: Missing required module - {e}")
        print("Please install dependencies: pip install -r docs/requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Log application shutdown
        try:
            from src.utils.logger import log_manager
            log_manager.info("InfoFlowLab Application Shutting Down")
            log_manager.info("=" * 60)
        except:
            pass


if __name__ == "__main__":
    main()