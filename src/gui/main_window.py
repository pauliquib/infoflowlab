"""
MainWindow - hlavní okno aplikace s toolbar, sidebar, canvas, inspector,
konzolí a timeline.
"""

import sys
import json
from typing import Optional, Dict
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QToolBar, QPushButton, QLabel, QSplitter, QFrame,
    QDialog, QTextEdit, QVBoxLayout as QVBox, QSlider,
    QSpinBox, QFileDialog, QMessageBox, QStatusBar,
    QPlainTextEdit, QLineEdit, QMenuBar, QMenu, QToolButton
)
from PySide6.QtCore import Qt, QTimer, QSize, QUrl
from PySide6.QtGui import QFont, QDesktopServices, QKeySequence, QAction

from src.gui.canvas import Canvas
from src.gui.sidebar import Sidebar
from src.gui.inspector import Inspector
from src.core.graph import Graph
from src.core.engine import SimulationEngine
from src.nodes.registry import build_node_factory
from src.utils.logger import log_manager, get_logger


class ConsoleWidget(QPlainTextEdit):
    """Application console with colored output using HTML."""
    
    MAX_LINES = 1000
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumBlockCount(self.MAX_LINES)
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #cccccc;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                border: 1px solid #333;
            }
        """)
    
    def log(self, category: str, message: str):
        """Add a log message with category-based coloring using HTML."""
        color_map = {
            "info": "#81C784",
            "warning": "#FFD600",
            "error": "#FF1744",
            "packet": "#81C784",
            "debug": "#AAAAAA",
        }
        color = color_map.get(category, "#CCCCCC")
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        html = f'<span style="color: #666;">[{timestamp}]</span> '
        html += f'<span style="color: {color};">{message}</span>'
        self.appendHtml(html)


class MainWindow(QMainWindow):
    """Hlavní okno aplikace InfoFlowLab v1.0."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("InfoFlowLab v1.0 - Simulátor komprese a komunikace")
        self.setGeometry(50, 50, 1600, 950)
        
        # Core
        self.graph = Graph()
        self.engine = SimulationEngine(self.graph)
        self.logger = get_logger("MainWindow")
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ===== MENU + TOOLBAR + STATUS =====
        self._init_actions()
        self._create_menu_bar()
        self._create_toolbar()
        
        # ===== SPLITTER =====
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Sidebar (left)
        self.sidebar = Sidebar()
        splitter.addWidget(self.sidebar)
        
        # Center canvas
        self.canvas = Canvas(self.graph, self.engine)
        splitter.addWidget(self.canvas)
        
        # Inspector (right)
        self.inspector = Inspector()
        splitter.addWidget(self.inspector)
        
        # Set splitter proportions
        # Sidebar now uses min_width=250 / max_width=500 for fluid resizing
        splitter.setSizes([250, 800, 300])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(2, 1)
        
        # ===== BOTTOM: Console + Speed Control =====
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(4, 2, 4, 2)
        bottom_layout.setSpacing(2)
        
        # Speed control row
        speed_row = QWidget()
        speed_layout = QHBoxLayout(speed_row)
        speed_layout.setContentsMargins(4, 0, 4, 0)
        
        speed_layout.addWidget(QLabel("Rychlost:"))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 50)  # 0.1x - 5.0x
        self.speed_slider.setValue(10)  # 1.0x default
        self.speed_slider.valueChanged.connect(self._on_speed_changed)
        speed_layout.addWidget(self.speed_slider)
        
        self.lbl_speed = QLabel("1.0x")
        self.lbl_speed.setFixedWidth(50)
        speed_layout.addWidget(self.lbl_speed)
        
        speed_layout.addSpacing(20)
        
        speed_layout.addWidget(QLabel("Tick (ms):"))
        self.tick_spin = QSpinBox()
        self.tick_spin.setRange(10, 1000)
        self.tick_spin.setValue(100)
        self.tick_spin.setSingleStep(10)
        self.tick_spin.valueChanged.connect(self.engine.set_tick_interval)
        self.tick_spin.setStyleSheet("background: #3d3d3d; color: white; border: 1px solid #555;")
        speed_layout.addWidget(self.tick_spin)
        
        speed_layout.addStretch()
        speed_layout.addWidget(QLabel("Přichytávání:"))
        self.btn_snap = QPushButton("Zapnuto")
        self.btn_snap.setCheckable(True)
        self.btn_snap.setChecked(True)
        self.btn_snap.clicked.connect(self._toggle_snap)
        self.btn_snap.setStyleSheet("""
            QPushButton {
                background: #2d2d30; color: #d4d4d4;
                border: 1px solid #3c3c3c; padding: 2px 10px;
                border-radius: 3px;
            }
            QPushButton:checked { background: #094771; border-color: #0e639c; }
        """)
        speed_layout.addWidget(self.btn_snap)
        
        bottom_layout.addWidget(speed_row)
        
        # Console
        self.console = ConsoleWidget()
        self.console.setMaximumHeight(120)
        bottom_layout.addWidget(self.console)
        
        # Add bottom to main layout
        main_layout.addWidget(bottom_widget)
        
        # ===== SIGNALS =====
        self._connect_signals()

        # Status bar (after widgets exist)
        self._create_status_bar()
        
        # ===== CONSOLE LOG TIMER =====
        self._console_timer = QTimer(self)
        self._console_timer.timeout.connect(self._flush_console)
        self._console_buffer: list = []
        
        # Initial log
        self.logger.info("MainWindow initialized")
        self.console.log("info", "InfoFlowLab v1.0 initialized")
        self.console.log("info", "Ready for simulation. Drag nodes from the sidebar.")
        self.logger.info("GUI components created")
    
    def _make_action(self, text: str, handler, shortcut=None, tooltip: str = "",
                     primary: bool = False, checkable: bool = False) -> QAction:
        """Create a consistently styled QAction."""
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(shortcut)
        if tooltip:
            action.setToolTip(tooltip)
            action.setStatusTip(tooltip)
        action.triggered.connect(handler)
        action.setCheckable(checkable)
        if primary:
            action.setProperty("primary", True)
        return action

    def _create_menu_bar(self):
        """Hlavní menu — méně časté akce mimo toolbar."""
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        # Soubor
        menu_file = menubar.addMenu("Soubor")
        menu_file.addAction(self.action_save)
        menu_file.addAction(self.action_load)
        menu_file.addSeparator()
        menu_file.addAction(self.action_export)

        # Úpravy
        menu_edit = menubar.addMenu("Úpravy")
        menu_edit.addAction(self.action_undo)
        menu_edit.addAction(self.action_redo)

        # Simulace
        menu_sim = menubar.addMenu("Simulace")
        menu_sim.addAction(self.action_play)
        menu_sim.addAction(self.action_pause)
        menu_sim.addAction(self.action_step)
        menu_sim.addAction(self.action_stop)
        menu_sim.addSeparator()
        menu_sim.addAction(self.action_reset)
        menu_sim.addAction(self.action_inject)

        # Zobrazení
        menu_view = menubar.addMenu("Zobrazení")
        menu_view.addAction(self.action_zoom_fit)
        menu_view.addAction(self.action_snap)

        # Nástroje (pro pokročilé)
        menu_tools = menubar.addMenu("Nástroje")
        menu_tools.addAction(self.action_profile_start)
        menu_tools.addAction(self.action_profile_stop)

        # Nápověda
        menu_help = menubar.addMenu("Nápověda")
        menu_help.addAction(self.action_help)

    def _create_toolbar(self):
        """Kompaktní toolbar — jen nejdůležitější ovládání simulace."""
        toolbar = QToolBar("Hlavní")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setIconSize(QSize(18, 18))
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)

        # Simulace — hlavní workflow pro nové uživatele
        for action in (
            self.action_play, self.action_pause,
            self.action_step, self.action_stop,
        ):
            btn = toolbar.addAction(action)
            if action is self.action_play:
                widget = toolbar.widgetForAction(action)
                if widget:
                    widget.setObjectName("toolbarPrimary")

        toolbar.addSeparator()

        toolbar.addAction(self.action_reset)
        toolbar.addSeparator()
        toolbar.addAction(self.action_undo)
        toolbar.addAction(self.action_redo)
        toolbar.addSeparator()
        toolbar.addAction(self.action_save)
        toolbar.addAction(self.action_load)
        toolbar.addSeparator()
        toolbar.addAction(self.action_help)

        # Zachovat kompatibilitu s existujícím kódem / testy
        self.btn_play = toolbar.widgetForAction(self.action_play)
        self.btn_pause = toolbar.widgetForAction(self.action_pause)
        self.btn_step = toolbar.widgetForAction(self.action_step)
        self.btn_stop = toolbar.widgetForAction(self.action_stop)
        self.btn_reset = toolbar.widgetForAction(self.action_reset)
        self.btn_save = toolbar.widgetForAction(self.action_save)
        self.btn_load = toolbar.widgetForAction(self.action_load)
        self.btn_help = toolbar.widgetForAction(self.action_help)
        self.btn_zoom_fit = None
        self.btn_export = None
        self.btn_inject = None
        self.btn_profile_start = None
        self.btn_profile_stop = None

    def _init_actions(self):
        """Vytvoří všechny akce aplikace."""
        self.action_play = self._make_action(
            "Spustit", self._on_play, QKeySequence("F5"),
            "Spustí simulaci v reálném čase", primary=True
        )
        self.action_pause = self._make_action(
            "Pozastavit", self._on_pause, QKeySequence("F6"),
            "Pozastaví běžící simulaci"
        )
        self.action_step = self._make_action(
            "Krok", self._on_step, QKeySequence("F7"),
            "Provede jeden krok simulace (vhodné pro výuku)"
        )
        self.action_stop = self._make_action(
            "Zastavit", self._on_stop, QKeySequence("F8"),
            "Zastaví simulaci a vyčistí pakety"
        )
        self.action_reset = self._make_action(
            "Reset", self._on_reset,
            tooltip="Smaže celý scénář a začne znovu"
        )
        self.action_inject = self._make_action(
            "Vložit paket", self._on_inject,
            tooltip="Vloží testovací paket do prvního zdroje"
        )
        self.action_save = self._make_action(
            "Uložit", self._on_save, QKeySequence.Save,
            "Uloží scénář do JSON souboru"
        )
        self.action_load = self._make_action(
            "Načíst", self._on_load, QKeySequence.Open,
            "Načte scénář ze souboru"
        )
        self.action_export = self._make_action(
            "Exportovat obrázek", self._on_export,
            tooltip="Uloží canvas jako PNG obrázek"
        )
        self.action_zoom_fit = self._make_action(
            "Přizpůsobit zobrazení", self._on_zoom_fit,
            tooltip="Zobrazí celý scénář na plátně"
        )
        self.action_help = self._make_action(
            "Nápověda", self._on_help, QKeySequence.HelpContents,
            "Otevře průvodce a dokumentaci"
        )

        self.action_undo = QAction("Zpět", self)
        self.action_undo.setShortcut(QKeySequence.Undo)
        self.action_undo.setToolTip("Vrátí poslední úpravu (Ctrl+Z)")
        self.action_undo.setEnabled(False)

        self.action_redo = QAction("Vpřed", self)
        self.action_redo.setShortcut(QKeySequence.Redo)
        self.action_redo.setToolTip("Zopakuje vrácenou úpravu (Ctrl+Y)")
        self.action_redo.setEnabled(False)

        self.action_snap = self._make_action(
            "Přichytávání k mřížce", self._toggle_snap_action,
            tooltip="Zapne/vypne přichytávání uzlů k mřížce",
            checkable=True
        )
        self.action_snap.setChecked(True)

        self.action_profile_start = self._make_action(
            "Spustit profilování", self._on_start_profiling,
            tooltip="Měří výkon aplikace (pro vývojáře)"
        )
        self.action_profile_stop = self._make_action(
            "Zastavit profilování", self._on_stop_profiling,
            tooltip="Ukončí měření výkonu"
        )
        self.action_profile_stop.setEnabled(False)

    def _create_status_bar(self):
        """Stavový řádek — místo přeplněného toolbaru."""
        status = QStatusBar(self)
        status.setSizeGripEnabled(False)
        self.setStatusBar(status)

        self.lbl_status = QLabel("Připraveno")
        self.lbl_status.setObjectName("statusLabel")
        status.addWidget(self.lbl_status)

        status.addPermanentWidget(QLabel("  "))
        self.lbl_tick = QLabel("Krok: 0")
        self.lbl_tick.setObjectName("tickLabel")
        status.addPermanentWidget(self.lbl_tick)

    def _toggle_snap_action(self, checked: bool):
        """Toggle snap from menu action."""
        self.canvas.set_snap_to_grid(checked)
        if hasattr(self, "btn_snap"):
            self.btn_snap.setChecked(checked)
            self.btn_snap.setText("Zapnuto" if checked else "Vypnuto")

    def _set_simulation_status(self, text: str, color: str = "#9cdcfe"):
        """Update status bar label."""
        self.lbl_status.setText(text)
        self.lbl_status.setStyleSheet(f"color: {color}; padding: 0 4px;")
    
    def _connect_signals(self):
        """Connect all signals."""
        # Engine signals
        self.engine.simulation_started.connect(
            lambda: self._set_simulation_status("Simulace běží", "#4ec9b0")
        )
        self.engine.simulation_stopped.connect(
            lambda: self._set_simulation_status("Zastaveno", "#cccccc")
        )
        self.engine.simulation_paused.connect(
            lambda: self._set_simulation_status("Pozastaveno", "#dcdcaa")
        )
        self.engine.tick_processed.connect(self._on_tick)
        self.engine.log_message.connect(self._queue_log)
        self.engine.error_occurred.connect(self._queue_log)
        
        # Canvas selection
        self.canvas.node_selected.connect(self.inspector.set_node)
        self.canvas.undo_state_changed.connect(self._on_undo_state_changed)
        self.action_undo.triggered.connect(self.canvas.undo)
        self.action_redo.triggered.connect(self.canvas.redo)
        
        # Sidebar drag
        self.sidebar.node_requested.connect(self.canvas.add_node_at)
        
        # Inspector param changes
        self.inspector.param_changed.connect(self._on_param_changed)
    
    def _on_undo_state_changed(self, can_undo: bool, can_redo: bool):
        """Update undo/redo action states."""
        self.action_undo.setEnabled(can_undo)
        self.action_redo.setEnabled(can_redo)
        if can_undo:
            self.action_undo.setToolTip(
                f"Vrátí: {self.canvas.undo_stack.undo_text()} (Ctrl+Z)"
            )
        else:
            self.action_undo.setToolTip("Vrátí poslední úpravu (Ctrl+Z)")
        if can_redo:
            self.action_redo.setToolTip(
                f"Zopakuje: {self.canvas.undo_stack.redo_text()} (Ctrl+Y)"
            )
        else:
            self.action_redo.setToolTip("Zopakuje vrácenou úpravu (Ctrl+Y)")

    def _on_play(self):
        self.logger.info("Play button clicked")
        self.engine.start()
        self.canvas.start_animation()
        self.console.log("info", "Simulation started (Real-time mode)")
    
    def _on_pause(self):
        self.logger.info("Pause button clicked")
        self.engine.pause()
        self.canvas.stop_animation()
        self.console.log("info", "Simulation paused")
    
    def _on_step(self):
        self.logger.debug(f"Step button clicked (tick {self.engine.current_tick})")
        self.engine.step()
        self.canvas.update()
        self.console.log("debug", f"Step executed (tick {self.engine.current_tick})")
    
    def _on_stop(self):
        self.logger.info("Stop button clicked")
        self.engine.stop()
        self.canvas.stop_animation()
        self.canvas.clear_packets()
        self.lbl_tick.setText("Krok: 0")
        self.console.log("info", "Simulation stopped")
    
    def _on_reset(self):
        self.logger.info("Reset button clicked")
        self.engine.reset()
        self.graph.clear()
        self.canvas.clear_scene()
        self.inspector.set_node(None)
        self._set_simulation_status("Připraveno", "#9cdcfe")
        self.lbl_tick.setText("Krok: 0")
        self.console.log("info", "Simulation reset - all nodes cleared")
    
    def _on_inject(self):
        """Inject a test packet into the first source node."""
        self.logger.debug("Inject button clicked")
        sources = self.graph.get_sources()
        if sources:
            from src.core.packet import DataPacket
            import uuid
            pkt = DataPacket(
                id=f"pkt_{uuid.uuid4().hex[:6]}",
                payload=b"Hello World!",
                source_format="text"
            )
            self.engine.inject_packet(sources[0].node_id, pkt)
            self.console.log("packet", f"Injected packet {pkt.id} into {sources[0].name}")
            self.logger.info(f"Injected packet {pkt.id} into {sources[0].name}")
        else:
            self.console.log("warning", "No source node found to inject packet")
            self.logger.warning("Inject failed: no source node found")
    
    def _on_help(self):
        """Show help dialog."""
        dialog = HelpDialog(self)
        dialog.exec()

    def _on_help_connections(self):
        """Open connection help documentation in web browser."""
        import os
        help_path = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "NAPOVEDA_PROPOJENI.html")
        help_path = os.path.abspath(help_path)
        if os.path.exists(help_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(help_path))
            self.console.log("info", f"Opened help: {help_path}")
        else:
            self.console.log("error", f"Help file not found: {help_path}")
    
    def _on_help_catalog(self):
        """Open element catalog documentation in web browser."""
        import os
        help_path = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "KATALOG_PRVKU.html")
        help_path = os.path.abspath(help_path)
        if os.path.exists(help_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(help_path))
            self.console.log("info", f"Opened catalog: {help_path}")
        else:
            self.console.log("error", f"Catalog file not found: {help_path}")
    
    def _on_zoom_fit(self):
        """Zoom to fit all nodes in viewport."""
        self.logger.debug("Zoom to fit button clicked")
        self.canvas.zoom_to_fit()
        self.console.log("info", "Zoomed to fit all nodes")
    
    def _on_export(self):
        """Export canvas to image file."""
        self.logger.info("Export button clicked")
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportovat jako obrázek", "canvas.png",
            "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg);;All Files (*)"
        )
        if file_path:
            success = self.canvas.export_to_image(file_path)
            if success:
                self.console.log("info", f"Canvas exported to {file_path}")
                self.logger.info(f"Canvas exported to {file_path}")
            else:
                self.console.log("error", f"Failed to export canvas to {file_path}")
                self.logger.error(f"Failed to export canvas to {file_path}")
    
    def _on_save(self):
        """Save current graph to JSON file."""
        self.logger.info("Save button clicked")
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Uložit scénář", "scenario.json", "JSON Files (*.json)"
        )
        if file_path:
            try:
                data = self.graph.to_dict()
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                self.console.log("info", f"Scenario saved to {file_path}")
                self.logger.info(f"Scenario saved to {file_path}")
            except Exception as e:
                self.console.log("error", f"Failed to save: {e}")
                self.logger.error(f"Failed to save scenario: {e}", exc_info=True)
    
    def _on_load(self):
        """Load graph from JSON file."""
        self.logger.info("Load button clicked")
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Načíst scénář", "", "JSON Files (*.json)"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                self.canvas.undo_stack.recording = False
                self.canvas.clear_scene()

                node_factory = build_node_factory()
                self.graph.from_dict(data, node_factory)

                for node in self.graph.nodes.values():
                    from src.gui.node_item import NodeItem
                    node_item = NodeItem(node)
                    node_item.setPos(node.position[0], node.position[1])
                    self.canvas.scene.addItem(node_item)
                    self.canvas._node_items[node.node_id] = node_item
                    self.engine.register_node(node)

                self.canvas._redraw_connections()
                self.canvas.undo_stack.recording = True
                self.canvas.undo_stack.clear()

                self.console.log("info", f"Scenario loaded from {file_path}")
                self.logger.info(f"Scenario loaded from {file_path}")
            except Exception as e:
                self.console.log("error", f"Failed to load: {e}")
                self.logger.error(f"Failed to load scenario: {e}", exc_info=True)
    
    def _on_speed_changed(self, value: int):
        """Handle speed slider change."""
        speed = value / 10.0
        self.engine.set_speed(speed)
        self.lbl_speed.setText(f"{speed:.1f}x")
    
    def _toggle_snap(self, checked: bool):
        """Toggle snap-to-grid from bottom panel."""
        self.canvas.set_snap_to_grid(checked)
        self.btn_snap.setText("Zapnuto" if checked else "Vypnuto")
        self.action_snap.setChecked(checked)
    
    def _on_tick(self, tick_num: int):
        """Handle simulation tick."""
        self.lbl_tick.setText(f"Krok: {tick_num}")
        
        # Update inspector stats every 10 ticks
        if tick_num % 10 == 0:
            self.inspector.update_stats()
        
        # Flush console buffer
        self._flush_console()
    
    def _on_param_changed(self, node_id: str, key: str, value):
        """Handle parameter change from inspector."""
        self.console.log("debug", f"Param {key}={value} set on node {node_id[:8]}")
        self.logger.debug(f"Parameter changed: {key}={value} on node {node_id[:8]}")
    
    def _on_start_profiling(self):
        """Start performance profiling."""
        self.logger.info("Starting performance profiling")
        log_manager.start_profiling()
        self.action_profile_start.setEnabled(False)
        self.action_profile_stop.setEnabled(True)
        self.console.log("info", "Performance profiling STARTED")
    
    def _on_stop_profiling(self):
        """Stop performance profiling and show report."""
        self.logger.info("Stopping performance profiling")
        report = log_manager.stop_profiling()
        self.action_profile_start.setEnabled(True)
        self.action_profile_stop.setEnabled(False)
        self.console.log("info", "Performance profiling STOPPED")
        
        if report:
            # Show profiling report in a dialog
            self._show_profiling_report(report)
    
    def _queue_log(self, category: str, message: str):
        """Queue a log message for batch display."""
        self._console_buffer.append((category, message))
        if len(self._console_buffer) >= 5:
            self._flush_console()
    
    def _flush_console(self):
        """Flush queued log messages."""
        for category, message in self._console_buffer:
            self.console.log(category, message)
        self._console_buffer.clear()
    
    def _show_profiling_report(self, report: str):
        """Show profiling report in a dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Profiling Report")
        dialog.setGeometry(100, 100, 900, 600)
        
        layout = QVBox(self)
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                padding: 10px;
            }
        """)
        text_edit.setText(report)
        layout.addWidget(text_edit)
        
        btn_close = QPushButton("Close")
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #1177bb; }
        """)
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)
        
        dialog.exec()


class HelpDialog(QDialog):
    """Dialog s nápovědou."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("InfoFlowLab v1.0 - Nápověda")
        self.setGeometry(200, 200, 800, 600)
        
        layout = QVBoxLayout(self)
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
                padding: 10px;
            }
        """)
        
        help_text = """
<h1 style="color: #4ec9b0;">InfoFlowLab v1.0 - Nápověda</h1>

<h2 style="color: #569cd6;">O aplikaci</h2>
<p>InfoFlowLab je interaktivní simulátor komprese a komunikace pro studenty informačních systémů a teorie přenosu informací.</p>

<h2 style="color: #569cd6;">Ovládání</h2>
<ul>
<li><strong>▶ Play</strong> - Spustí simulaci v reálném čase</li>
<li><strong>⏸ Pause</strong> - Pozastaví simulaci</li>
<li><strong>⏭ Step</strong> - Jeden krok simulace</li>
<li><strong>⏹ Stop</strong> - Zastaví simulaci</li>
<li><strong>↺ Reset</strong> - Smaže všechny prvky</li>
<li><strong>💉 Inject</strong> - Vloží testovací packet do zdroje</li>
</ul>

<h2 style="color: #569cd6;">Práce s canvasem</h2>
<ul>
<li><strong>Drag & Drop</strong> - Přetáhněte prvek ze sidebaru na canvas</li>
<li><strong>Ctrl+Scroll</strong> - Zoom</li>
<li><strong>Middle mouse drag</strong> - Posun plátna</li>
<li><strong>Delete</strong> - Smazání vybraného prvku</li>
<li><strong>Propojování</strong> - Klikněte na port a táhněte k jinému portu</li>
</ul>

<h2 style="color: #569cd6;">Kategorie prvků</h2>
<p>Každá kategorie má vlastní barevné schéma pro snadnou identifikaci:</p>
<ul>
<li style="color: #4CAF50;">📝 Zdroje - Zelená</li>
<li style="color: #2196F3;">🔀 Kódovače - Modrá</li>
<li style="color: #03A9F4;">🔁 Dekódovače - Světle modrá</li>
<li style="color: #FFC107;">🗜️ Komprese - Žlutá</li>
<li style="color: #FF5722;">📡 Kanály - Červeno-oranžová</li>
<li style="color: #F44336;">🔴 ECC - Červená</li>
<li style="color: #9C27B0;">✅ Kontrolní číslice - Fialová</li>
<li style="color: #00BCD4;">📊 Analyzátory - Cyan</li>
<li style="color: #607D8B;">💾 Výstupy - Šedá</li>
</ul>

<h2 style="color: #569cd6;">Klávesové zkratky</h2>
<ul>
<li><strong>Delete/Backspace</strong> - Smazat vybraný prvek</li>
<li><strong>Escape</strong> - Zrušit propojování</li>
<li><strong>Ctrl+Scroll</strong> - Zoom</li>
<li><strong>Middle mouse</strong> - Posun plátna</li>
</ul>

<hr style="border-color: #4ec9b0;">
<p style="color: #888;">InfoFlowLab v1.0 - Production Ready</p>
"""
        
        text_edit.setHtml(help_text)
        layout.addWidget(text_edit)
        
        # Button to open detailed connection help
        btn_connections_help = QPushButton("📖 Nápověda k propojování prvků")
        btn_connections_help.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #1177bb; }
        """)
        btn_connections_help.clicked.connect(self.parent()._on_help_connections)
        layout.addWidget(btn_connections_help)
        
        # Button to open element catalog
        btn_catalog_help = QPushButton("📚 Katalog všech prvků")
        btn_catalog_help.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        btn_catalog_help.clicked.connect(self.parent()._on_help_catalog)
        layout.addWidget(btn_catalog_help)

        btn_close = QPushButton("Zavřít")
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)
