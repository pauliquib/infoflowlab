"""
Sidebar s kategoriemi prvků pro přidání na canvas.
- Collapsible panely s ikonami a tooltipy
- Search box pro filtrování v reálném čase
- Favorites (označené hvězdičkou) nahoře
- Drag & Drop s ghost node pod kurzorem
"""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QPushButton, QLineEdit,
    QScrollArea, QWidget, QGridLayout, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QMimeData, QTimer, QPoint, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QFont, QDrag, QPixmap, QPainter, QColor, QPen, QBrush, QIcon


class CategoryPanel(QFrame):
    """Collapsible category panel with node buttons and educational subtitles."""
    
    def __init__(self, category_name: str, subtitle: str, items: list, 
                 icon: str = "", color: str = "#CCCCCC", parent=None,
                 auto_close_others: bool = True):
        super().__init__(parent)
        self.category_name = category_name
        self.subtitle = subtitle
        self.items = items
        self._collapsed = False
        self.auto_close_others = auto_close_others
        self._animation = None
        
        self.setStyleSheet(f"""
            QFrame {{ background: transparent; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(0)
        
        # Header button (collapsible) with chevron
        header_container = QWidget()
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(4, 6, 4, 4)
        header_layout.setSpacing(2)
        
        # Title row with icon and chevron
        title_row = QWidget()
        title_layout = QVBoxLayout(title_row)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)
        
        self.header = QPushButton(f"{icon} {category_name}")
        self.header.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {color};
                font-weight: bold;
                font-size: 12px;
                text-align: left;
                padding: 4px 0px;
                border: none;
            }}
            QPushButton:hover {{
                color: {color};
                background: #2a2a2a;
                border-radius: 3px;
            }}
        """)
        self.header.clicked.connect(self.toggle_collapse)
        title_layout.addWidget(self.header)
        
        # Subtitle
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet("""
                QLabel {
                    color: #888;
                    font-size: 10px;
                    padding-left: 4px;
                }
            """)
            title_layout.addWidget(subtitle_label)
        
        header_layout.addWidget(title_row)
        layout.addWidget(header_container)
        
        # Content container with animation support
        self.content_container = QWidget()
        self.content_container.setVisible(True)  # Ensure visible on init
        self.content_container.setMaximumHeight(2000)  # Large enough for content
        content_layout = QVBoxLayout(self.content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Content grid
        self.content = QWidget()
        self.grid = QGridLayout(self.content)
        self.grid.setSpacing(3)
        self.grid.setContentsMargins(4, 4, 4, 4)
        
        for i, item_name in enumerate(items):
            btn = NodeButton(item_name)
            self.grid.addWidget(btn, i // 2, i % 2)
        
        content_layout.addWidget(self.content)
        layout.addWidget(self.content_container)
        
        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #333; max-height: 1px;")
        layout.addWidget(separator)
        
        # Style
        self.setStyleSheet("""
            CategoryPanel {
                background: transparent;
                border: none;
            }
        """)
    
    def toggle_collapse(self, force_state: bool = None):
        """Toggle collapse with smooth animation."""
        if force_state is not None:
            self._collapsed = force_state
        else:
            self._collapsed = not self._collapsed
        
        if self._collapsed:
            self._animate_collapse()
        else:
            self._animate_expand()
    
    def _animate_collapse(self):
        """Animate collapsing the panel."""
        if self._animation and self._animation.state() == QPropertyAnimation.Running:
            self._animation.stop()
        
        start_height = self.content_container.sizeHint().height()
        end_height = 0
        
        self._animation = QPropertyAnimation(self.content_container, b"maximumHeight")
        self._animation.setDuration(150)
        self._animation.setStartValue(start_height)
        self._animation.setEndValue(end_height)
        self._animation.setEasingCurve(QEasingCurve.InOutQuad)
        self._animation.finished.connect(lambda: self.content_container.setVisible(False))
        self._animation.start()
    
    def _animate_expand(self):
        """Animate expanding the panel."""
        self.content_container.setVisible(True)
        
        if self._animation and self._animation.state() == QPropertyAnimation.Running:
            self._animation.stop()
        
        # Calculate target height
        self.content_container.setMaximumHeight(2000)
        target_height = self.content_container.sizeHint().height()
        
        self._animation = QPropertyAnimation(self.content_container, b"maximumHeight")
        self._animation.setDuration(150)
        self._animation.setStartValue(0)
        self._animation.setEndValue(target_height)
        self._animation.setEasingCurve(QEasingCurve.InOutQuad)
        self._animation.start()
    
    def filter_items(self, search_text: str, auto_expand: bool = True) -> bool:
        """
        Filter visible items based on search text with smart auto-expand.
        
        Returns:
            bool: True if any items are visible after filtering
        """
        search_lower = search_text.lower()
        visible_count = 0
        
        for i in range(self.grid.count()):
            widget = self.grid.itemAt(i).widget()
            if widget:
                match = search_lower in widget.text().lower()
                widget.setVisible(match)
                if match:
                    visible_count += 1
        
        # Auto-expand if searching and items match
        if search_text and auto_expand and visible_count > 0:
            if self._collapsed:
                self.toggle_collapse(False)
        
        # Show/hide based on search
        has_visible = visible_count > 0
        self.header.setVisible(not search_text or has_visible)
        if not search_text:
            # Restore collapsed state when search is cleared
            pass
        
        return has_visible


class NodeButton(QPushButton):
    """A node button with drag-and-drop support."""
    
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setMinimumHeight(28)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        self.setStyleSheet("""
            QPushButton {
                background-color: #3e3e42;
                color: #d4d4d4;
                border: 1px solid #555;
                padding: 4px 6px;
                font-size: 10px;
                border-radius: 3px;
            }
            QPushButton:checked {
                background-color: #0e639c;
                border-color: #1177bb;
                color: white;
            }
            QPushButton:hover {
                background-color: #4e4e52;
                border-color: #777;
            }
            QPushButton:checked:hover {
                background-color: #1177bb;
            }
        """)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Start drag
            self._start_pos = event.pos()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            if (event.pos() - self._start_pos).manhattanLength() > 10:
                drag = QDrag(self)
                mime_data = QMimeData()
                mime_data.setText(self.text())
                drag.setMimeData(mime_data)
                
                # Create ghost pixmap
                pixmap = QPixmap(180, 32)
                pixmap.fill(Qt.transparent)
                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                rect = pixmap.rect().adjusted(1, 1, -1, -1)
                painter.setBrush(QBrush(QColor("#0e639c")))
                painter.setPen(QPen(QColor("#1177bb"), 1))
                painter.drawRoundedRect(rect, 4, 4)
                painter.setPen(Qt.white)
                font = QFont("Segoe UI", 10, QFont.Bold)
                painter.setFont(font)
                painter.drawText(rect, Qt.AlignCenter, self.text())
                painter.end()
                
                drag.setPixmap(pixmap)
                drag.setHotSpot(QPoint(90, 16))
                drag.exec(Qt.CopyAction)
        super().mouseMoveEvent(event)


class Sidebar(QFrame):
    """Levý panel s kategoriemi, vyhledáváním a drag & drop."""
    
    node_requested = Signal(str, tuple)  # node_type, position
    
    # Educational category definitions with icons, subtitles, and node lists
    CATEGORIES = [
        {
            "id": "sources",
            "name": "1. Zdroje (Sources)",
            "subtitle": "Kde data vznikají (Text, Generátory, Zvuk)",
            "icon": "📝",
            "color": "#4CAF50",
            "items": [
                ("Text", "Text source - enter text in inspector"),
                ("Random", "Random byte generator"),
                ("Číslo", "Numeric input"),
                ("AudioSrc", "Load WAV/MP3 audio"),
                ("ImageSrc", "Load image file"),
            ]
        },
        {
            "id": "source_coding",
            "name": "2. Zpracování a Komprese (Source Coding)",
            "subtitle": "Zmenšení objemu a formátování (Huffman, RLE, Base64)",
            "icon": "🗜️",
            "color": "#2196F3",
            "items": [
                ("Base64", "Base64 encode"),
                ("BaseConv", "Base converter (2-36)"),
                ("UTF-8", "UTF-8 encode"),
                ("Morse", "Morse code encode"),
                ("HuffmanEnc", "Huffman encode"),
                ("Hex", "Hex encode"),
                ("RLE", "Run-Length Encoding"),
                ("Huffman", "Huffman compression"),
                ("LZ77", "LZ77 sliding window"),
                ("LZW", "LZW dictionary"),
            ]
        },
        {
            "id": "channel_coding",
            "name": "3. Zabezpečení proti chybám (Channel Coding)",
            "subtitle": "Přidání redundance a detekce chyb (Hamming, CRC, Parita)",
            "icon": "🛡️",
            "color": "#FF9800",
            "items": [
                ("Hamming74", "Hamming(7,4) encode/decode"),
                ("Hamming1511", "Hamming(15,11)"),
                ("CRC8", "CRC-8 checksum"),
                ("CRC16", "CRC-16 checksum"),
                ("CRC32", "CRC-32 checksum"),
                ("ReedSolomon", "Reed-Solomon encode"),
                ("ReedSolomonDec", "Reed-Solomon decode"),
                ("ParityEnc", "Parity encoder"),
                ("ParityDec", "Parity decoder"),
            ]
        },
        {
            "id": "channels",
            "name": "4. Přenosové Kanály (Environment)",
            "subtitle": "Kudy data tečou a kde vzniká šum (BSK, AWGN)",
            "icon": "📡",
            "color": "#9C27B0",
            "items": [
                ("Ideal", "Ideal channel (latency only)"),
                ("BSK", "Binary Symmetric Channel"),
                ("GilbertElliott", "Burst error channel"),
                ("AWGN", "Additive White Gaussian Noise"),
            ]
        },
        {
            "id": "decoders",
            "name": "5. Dekódování na příjmu (Receivers)",
            "subtitle": "Oprava chyb a obnova původních dat",
            "icon": "🔁",
            "color": "#00BCD4",
            "items": [
                ("Base64Dec", "Base64 decode"),
                ("MorseDec", "Morse code decode"),
                ("UTF-8Dec", "UTF-8 decode"),
                ("HuffmanDec", "Huffman decode"),
            ]
        },
        {
            "id": "checksums",
            "name": "6. Kontrolní kódy (Checksums)",
            "subtitle": "Ověření integrity dat (EAN, ISBN, Luhn)",
            "icon": "✅",
            "color": "#8BC34A",
            "items": [
                ("EAN", "EAN-13/EAN-8 barcode"),
                ("ISBN", "ISBN-10/ISBN-13"),
                ("ISSN", "ISSN validation"),
                ("Luhn", "Luhn algorithm"),
                ("Verhoeff", "Verhoeff algorithm"),
                ("ICO", "IČO validation"),
            ]
        },
        {
            "id": "analytics",
            "name": "7. Měření a Výstupy (Analytics)",
            "subtitle": "Výpočet entropie, latence a zobrazení výsledků",
            "icon": "📊",
            "color": "#FF5722",
            "items": [
                ("Entropie", "Shannon entropy meter"),
                ("Frekvence", "Symbol frequency"),
                ("CompRatio", "Compression ratio"),
                ("BER Meter", "Bit Error Rate"),
                ("LatencyMeter", "Latency measurement"),
                ("TextOut", "Text display output"),
                ("Soubor", "File sink"),
                ("Konzole", "Console output"),
                ("HexDump", "Hex dump output"),
                ("Compare", "A/B comparison"),
            ]
        },
        {
            "id": "image_processing",
            "name": "8. Zpracování obrázků (Image)",
            "subtitle": "Simulace ztrát, transformace a porovnání obrázků",
            "icon": "🖼️",
            "color": "#E91E63",
            "items": [
                ("ImageOut", "Image display output"),
                ("BlockLoss", "Block loss simulation"),
                ("Transform", "Image transform (resize, rotate)"),
                ("ImageCompare", "Image A/B comparison"),
            ]
        },
    ]
    
    def __init__(self, parent=None, auto_close_others: bool = True):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel)
        # Make sidebar resizable via QSplitter: min 250px, max 500px
        self.setMinimumWidth(250)
        self.setMaximumWidth(500)
        self.auto_close_others = auto_close_others
        
        # Use fluid layout that stretches/shrinks with panel width
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Title with educational branding
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(2)
        
        title = QLabel("📦 Prvky")
        title.setStyleSheet("font-weight: bold; font-size: 16px; color: #CCCCCC;")
        title_layout.addWidget(title)
        
        subtitle = QLabel("Informační teorie - Interaktivní simulátor")
        subtitle.setStyleSheet("font-size: 10px; color: #888; font-style: italic;")
        title_layout.addWidget(subtitle)
        
        layout.addWidget(title_container)
        
        # Search box with enhanced styling
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Hledat (např. Hamming, Huffman...)")
        self.search_box.textChanged.connect(self._filter_categories)
        self.search_box.setStyleSheet("""
            QLineEdit {
                background: #3d3d3d;
                color: white;
                border: 1px solid #555;
                padding: 8px 10px;
                border-radius: 4px;
                font-size: 11px;
            }
            QLineEdit:focus {
                border-color: #0078d4;
                background: #3e3e42;
            }
        """)
        layout.addWidget(self.search_box)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { 
                border: none; 
                background: transparent; 
            }
            QScrollBar:vertical { 
                width: 10px; 
                background: #2d2d2d; 
            }
            QScrollBar::handle:vertical { 
                background: #555; 
                border-radius: 5px; 
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #666;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
        """)
        
        container = QWidget()
        self.categories_layout = QVBoxLayout(container)
        self.categories_layout.setSpacing(2)
        self.categories_layout.setContentsMargins(0, 0, 0, 0)
        
        # Build categories from new structure
        self._panels = []
        for cat_data in self.CATEGORIES:
            panel = CategoryPanel(
                category_name=cat_data["name"],
                subtitle=cat_data["subtitle"],
                items=[name for name, _ in cat_data["items"]],
                icon=cat_data["icon"],
                color=cat_data["color"],
                auto_close_others=auto_close_others
            )
            self.categories_layout.addWidget(panel)
            self._panels.append(panel)
        
        self.categories_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        # Info label with educational hint
        info_container = QWidget()
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(4, 4, 4, 4)
        
        info_label = QLabel("💡 Přetáhněte prvek na plátno")
        info_label.setStyleSheet("color: #888; font-size: 10px;")
        info_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(info_label)
        
        hint_label = QLabel("Klikněte na kategorii pro rozbalení")
        hint_label.setStyleSheet("color: #666; font-size: 9px; font-style: italic;")
        hint_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(hint_label)
        
        layout.addWidget(info_container)
        
        # Overall style with modern dark theme
        self.setStyleSheet("""
            Sidebar {
                background-color: #252526;
                border-right: 1px solid #333;
            }
        """)
        
        self._selected_btn = None
        self._last_search_text = ""
    
    def _filter_categories(self, text: str):
        """Smart filter with auto-expand for matching categories."""
        self._last_search_text = text
        
        if not text:
            # Clear search - restore all panels to their default state
            for panel in self._panels:
                panel.filter_items("", auto_expand=False)
            return
        
        # Search mode - filter and auto-expand matching categories
        matching_panels = []
        for panel in self._panels:
            has_match = panel.filter_items(text, auto_expand=True)
            if has_match:
                matching_panels.append(panel)
        
        # Auto-close other panels if enabled
        if self.auto_close_others and matching_panels:
            for panel in self._panels:
                if panel not in matching_panels and not panel._collapsed:
                    panel.toggle_collapse(True)
    
    def _add_selected(self):
        """Add the selected node to the canvas center."""
        if self._selected_btn:
            self.node_requested.emit(self._selected_btn.text(), (400, 300))
    
    def _on_item_selected(self, name: str, btn: QPushButton):
        """Handle item selection."""
        if self._selected_btn and self._selected_btn != btn:
            self._selected_btn.setChecked(False)
        self._selected_btn = btn if btn.isChecked() else None
    
    def expand_all(self):
        """Expand all categories."""
        for panel in self._panels:
            if panel._collapsed:
                panel.toggle_collapse(False)
    
    def collapse_all(self):
        """Collapse all categories."""
        for panel in self._panels:
            if not panel._collapsed:
                panel.toggle_collapse(True)
