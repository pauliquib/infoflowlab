"""
Inspector - dynamic PropertyGrid generated from node.get_param_schema().
Sections: Basic info, Parameters (editable), Statistics (read-only),
History (last 10 packets), Theory (read-only).
"""

from typing import Dict, Any, Optional, List
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QLineEdit, QSpinBox,
    QDoubleSpinBox, QFormLayout, QGroupBox, QTextEdit,
    QScrollArea, QWidget, QCheckBox, QComboBox, QSlider,
    QHBoxLayout, QPushButton, QTabWidget, QSizePolicy, QGraphicsView, QGraphicsScene
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QPixmap, QPainter

from src.core.node_base import NodeBase, ParamType, NodeStatus


class PropertyWidget(QWidget):
    """Base class for property editor widgets."""
    value_changed = Signal(str, object)  # key, value
    
    def __init__(self, key: str, schema: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.key = key
        self.schema = schema


class IntPropertyWidget(PropertyWidget):
    """Integer property editor with spinbox and slider."""
    
    def __init__(self, key: str, schema: Dict[str, Any], parent=None):
        super().__init__(key, schema, parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.spin = QSpinBox()
        self.spin.setRange(schema.get("min", 0), schema.get("max", 999999))
        self.spin.setValue(schema.get("default", 0))
        self.spin.setSingleStep(schema.get("step", 1))
        self.spin.valueChanged.connect(lambda v: self.value_changed.emit(self.key, v))
        
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(schema.get("min", 0), schema.get("max", 999999))
        self.slider.setValue(schema.get("default", 0))
        self.slider.valueChanged.connect(self.spin.setValue)
        self.spin.valueChanged.connect(self.slider.setValue)
        
        layout.addWidget(self.spin)
        layout.addWidget(self.slider)
        
        self.setStyleSheet("""
            QSpinBox { background: #3d3d3d; color: white; border: 1px solid #555; padding: 2px; }
            QSlider::groove:horizontal { background: #555; height: 4px; }
            QSlider::handle:horizontal { background: #888888; width: 12px; margin: -4px 0; border-radius: 6px; }
        """)


class FloatPropertyWidget(PropertyWidget):
    """Float property editor."""
    
    def __init__(self, key: str, schema: Dict[str, Any], parent=None):
        super().__init__(key, schema, parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.spin = QDoubleSpinBox()
        self.spin.setRange(schema.get("min", 0.0), schema.get("max", 999999.0))
        self.spin.setValue(schema.get("default", 0.0))
        self.spin.setSingleStep(schema.get("step", 0.1))
        self.spin.setDecimals(2)
        self.spin.valueChanged.connect(lambda v: self.value_changed.emit(self.key, v))
        
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 1000)
        self.slider.setValue(int(schema.get("default", 0.0) * 100))
        self.slider.valueChanged.connect(
            lambda v: self.spin.setValue(v / 100.0)
        )
        self.spin.valueChanged.connect(
            lambda v: self.slider.setValue(int(v * 100))
        )
        
        layout.addWidget(self.spin)
        layout.addWidget(self.slider)
        
        self.setStyleSheet("""
            QDoubleSpinBox { background: #3d3d3d; color: white; border: 1px solid #555; padding: 2px; }
            QSlider::groove:horizontal { background: #555; height: 4px; }
            QSlider::handle:horizontal { background: #888888; width: 12px; margin: -4px 0; border-radius: 6px; }
        """)


class StringPropertyWidget(PropertyWidget):
    """String property editor."""
    
    def __init__(self, key: str, schema: Dict[str, Any], parent=None):
        super().__init__(key, schema, parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.edit = QLineEdit(str(schema.get("default", "")))
        self.edit.textChanged.connect(lambda t: self.value_changed.emit(self.key, t))
        self.edit.setStyleSheet("background: #3d3d3d; color: white; border: 1px solid #555; padding: 2px;")
        
        layout.addWidget(self.edit)


class ChoicePropertyWidget(PropertyWidget):
    """Choice (combo box) property editor."""
    
    def __init__(self, key: str, schema: Dict[str, Any], parent=None):
        super().__init__(key, schema, parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.combo = QComboBox()
        choices = schema.get("choices", [])
        self.combo.addItems([str(c) for c in choices])
        default = str(schema.get("default", ""))
        if default in [str(c) for c in choices]:
            self.combo.setCurrentText(default)
        self.combo.currentTextChanged.connect(lambda t: self.value_changed.emit(self.key, t))
        self.combo.setStyleSheet("""
            QComboBox { background: #3d3d3d; color: white; border: 1px solid #555; padding: 2px; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background: #3d3d3d; color: white; selection-background-color: #094771; }
        """)
        
        layout.addWidget(self.combo)


class BoolPropertyWidget(PropertyWidget):
    """Boolean property editor with toggle style."""
    
    def __init__(self, key: str, schema: Dict[str, Any], parent=None):
        super().__init__(key, schema, parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.check = QCheckBox(schema.get("label", key))
        self.check.setChecked(bool(schema.get("default", False)))
        self.check.toggled.connect(lambda v: self.value_changed.emit(self.key, v))
        self.check.setStyleSheet("""
            QCheckBox { color: #cccccc; }
            QCheckBox::indicator { width: 16px; height: 16px; }
            QCheckBox::indicator:checked { background-color: #4CAF50; border-radius: 3px; }
            QCheckBox::indicator:unchecked { background-color: #555; border-radius: 3px; }
        """)
        
        layout.addWidget(self.check)


class TextPropertyWidget(PropertyWidget):
    """Multi-line text property editor."""
    
    def __init__(self, key: str, schema: Dict[str, Any], parent=None):
        super().__init__(key, schema, parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.edit = QTextEdit()
        self.edit.setPlainText(str(schema.get("default", "")))
        self.edit.setMaximumHeight(100)
        self.edit.textChanged.connect(
            lambda: self.value_changed.emit(self.key, self.edit.toPlainText())
        )
        self.edit.setStyleSheet("background: #3d3d3d; color: white; border: 1px solid #555;")
        
        layout.addWidget(self.edit)


class FilePropertyWidget(PropertyWidget):
    """File path property editor with browse button."""
    
    def __init__(self, key: str, schema: Dict[str, Any], parent=None):
        super().__init__(key, schema, parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.edit = QLineEdit(str(schema.get("default", "")))
        self.edit.textChanged.connect(lambda t: self.value_changed.emit(self.key, t))
        self.edit.setStyleSheet("background: #3d3d3d; color: white; border: 1px solid #555; padding: 2px;")
        
        browse_btn = QPushButton("...")
        browse_btn.setMaximumWidth(30)
        browse_btn.clicked.connect(self._browse_file)
        browse_btn.setStyleSheet("""
            QPushButton { background: #4CAF50; color: white; border: none; padding: 2px; }
            QPushButton:hover { background: #45a049; }
        """)
        
        layout.addWidget(self.edit)
        layout.addWidget(browse_btn)
    
    def _browse_file(self):
        """Open file dialog to select file."""
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "",
            "All Files (*.*)"
        )
        if file_path:
            self.edit.setText(file_path)
            self.value_changed.emit(self.key, file_path)


class Inspector(QFrame):
    """
    Dynamic PropertyGrid inspector.
    Generates UI from node.get_param_schema().
    """
    
    param_changed = Signal(str, str, object)  # node_id, key, value
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel)
        self.setMinimumWidth(200)
        self.setMaximumWidth(600)
        self.current_node: Optional[NodeBase] = None
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # Title
        self.lbl_title = QLabel("Inspector")
        self.lbl_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #CCCCCC; padding: 4px;")
        layout.addWidget(self.lbl_title)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(8)
        scroll.setWidget(self.scroll_content)
        layout.addWidget(scroll)
        
        # Styling
        self.setStyleSheet("""
            QFrame { background-color: #252526; color: white; }
            QLabel { color: #cccccc; }
            QGroupBox { 
                color: #CCCCCC; 
                border: 1px solid #555; 
                margin-top: 8px; 
                padding-top: 12px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QTextEdit { background: #3d3d3d; color: white; border: 1px solid #555; }
        """)
    
    def set_node(self, node: Optional[NodeBase]):
        """Set the node to inspect. None clears the inspector."""
        self.current_node = node
        self._rebuild()
    
    def _rebuild(self):
        """Rebuild the entire inspector UI."""
        # Clear existing widgets
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if self.current_node is None:
            self.lbl_title.setText("Inspector")
            empty = QLabel("No node selected\n\nSelect a node on the canvas\nto inspect its properties.")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet("color: #666; padding: 20px;")
            self.scroll_layout.addWidget(empty)
            self.scroll_layout.addStretch()
            return
        
        node = self.current_node
        self.lbl_title.setText(f"{node.name}")
        
        # ===== SECTION 1: Basic Info =====
        info_group = QGroupBox("Basic Info")
        info_layout = QFormLayout(info_group)
        info_layout.setSpacing(4)
        
        info_layout.addRow("ID:", QLabel(f"<span style='color:#888;'>{node.node_id[:12]}...</span>"))
        info_layout.addRow("Type:", QLabel(f"<span style='color:#CCCCCC;'>{node.node_type}</span>"))
        info_layout.addRow("Category:", QLabel(f"<span style='color:#81C784;'>{node.category}</span>"))
        status_text = node.status.value if hasattr(node.status, 'value') else str(node.status)
        info_layout.addRow("Status:", QLabel(f"<span style='color:#FFD600;'>{status_text}</span>"))
        info_layout.addRow("Position:", QLabel(f"({node.position[0]:.0f}, {node.position[1]:.0f})"))
        
        self.scroll_layout.addWidget(info_group)
        
        # ===== SECTION 2: Parameters (from schema) =====
        schema = node.get_param_schema()
        if schema:
            params_group = QGroupBox("Parameters")
            params_layout = QFormLayout(params_group)
            params_layout.setSpacing(4)
            params_layout.setLabelAlignment(Qt.AlignRight)
            
            for key, param_schema in schema.items():
                ptype = param_schema.get("type", ParamType.STR)
                label = param_schema.get("label", key)
                description = param_schema.get("description", "")
                unit = param_schema.get("unit", "")
                
                # Get current value from node
                current_value = node.params.get(key, param_schema.get("default"))
                
                # Create appropriate widget
                widget = self._create_widget(key, param_schema, current_value)
                if widget:
                    label_text = f"{label}{' [' + unit + ']' if unit else ''}:"
                    params_layout.addRow(label_text, widget)
                    
                    # Add description as tooltip
                    if description:
                        widget.setToolTip(description)
                        label_widget = params_layout.labelForField(widget)
                        if label_widget:
                            label_widget.setToolTip(description)
            
            self.scroll_layout.addWidget(params_group)
        
        # ===== SECTION 3: Statistics =====
        stats_group = QGroupBox("Statistics")
        stats_layout = QFormLayout(stats_group)
        stats_layout.setSpacing(4)
        
        stats_layout.addRow("Packets processed:", QLabel(str(node.packets_processed)))
        stats_layout.addRow("Packets dropped:", QLabel(str(node.packets_dropped)))
        stats_layout.addRow("Avg latency:", QLabel(f"{node.average_latency_ms:.2f} ms"))
        stats_layout.addRow("Buffer size:", QLabel(f"{len(node.buffer)}/{node.buffer_maxsize}"))
        
        # Node-specific metrics
        if hasattr(node, 'last_entropy'):
            stats_layout.addRow("Entropy:", QLabel(f"{node.last_entropy:.3f} bit/sym"))
        if hasattr(node, 'last_eff'):
            stats_layout.addRow("Efficiency:", QLabel(f"{node.last_eff:.1f}%"))
        if hasattr(node, 'last_text'):
            stats_layout.addRow("Output:", QLabel(f"<span style='color:#81C784;'>{node.last_text[:50]}</span>"))
        if hasattr(node, 'last_metrics'):
            for k, v in node.last_metrics.items():
                stats_layout.addRow(f"{k}:", QLabel(str(v)[:80]))
        if hasattr(node, 'frequencies'):
            stats_layout.addRow("Unique symbols:", QLabel(str(len(node.frequencies))))
        
        # Image preview for ImageOutputNode
        if hasattr(node, 'last_image_bytes') and node.last_image_bytes:
            self._add_image_preview(node)
        
        self.scroll_layout.addWidget(stats_group)
        
        # ===== SECTION 4: History =====
        history_group = QGroupBox("History (last 10)")
        history_layout = QVBoxLayout(history_group)
        
        history_text = QTextEdit()
        history_text.setReadOnly(True)
        history_text.setMaximumHeight(120)
        history_text.setStyleSheet("background: #1e1e1e; color: #aaa; font-size: 10px;")
        
        if node.buffer:
            lines = []
            for pkt in list(node.buffer)[-10:]:
                for step in pkt.history[-3:]:  # Last 3 steps per packet
                    lines.append(f"[{step.node_name}] {step.operation}: {step.input_size}→{step.output_size}")
            history_text.setPlainText("\n".join(lines) if lines else "No history")
        else:
            history_text.setPlainText("No data")
        
        history_layout.addWidget(history_text)
        self.scroll_layout.addWidget(history_group)
        
        # ===== SECTION 5: Theory =====
        theory_group = QGroupBox("Theory")
        theory_layout = QVBoxLayout(theory_group)
        
        theory_text = QTextEdit()
        theory_text.setReadOnly(True)
        theory_text.setMaximumHeight(100)
        theory_text.setStyleSheet("background: #1e1e1e; color: #888; font-size: 10px;")
        theory_text.setPlainText(self._get_theory_text(node))
        theory_layout.addWidget(theory_text)
        
        self.scroll_layout.addWidget(theory_group)
        
        self.scroll_layout.addStretch()
    
    def _create_widget(self, key: str, schema: Dict[str, Any], 
                       current_value: Any) -> Optional[PropertyWidget]:
        """Create the appropriate property widget based on schema type."""
        ptype = schema.get("type", ParamType.STR)
        
        # Update default to current value
        schema = dict(schema)
        if current_value is not None:
            schema["default"] = current_value
        
        widget = None
        if ptype == ParamType.INT:
            widget = IntPropertyWidget(key, schema)
        elif ptype == ParamType.FLOAT:
            widget = FloatPropertyWidget(key, schema)
        elif ptype == ParamType.STR:
            widget = StringPropertyWidget(key, schema)
        elif ptype == ParamType.CHOICE:
            widget = ChoicePropertyWidget(key, schema)
        elif ptype == ParamType.BOOL:
            widget = BoolPropertyWidget(key, schema)
        elif ptype == ParamType.TEXT:
            widget = TextPropertyWidget(key, schema)
        elif ptype == ParamType.RANGE:
            widget = FloatPropertyWidget(key, schema)
        elif ptype == ParamType.FILE:
            widget = FilePropertyWidget(key, schema)
        
        if widget:
            widget.value_changed.connect(self._on_param_changed)
        
        return widget
    
    def _on_param_changed(self, key: str, value):
        """Handle parameter change from widget."""
        if self.current_node:
            self.current_node.set_param(key, value)
            self.param_changed.emit(self.current_node.node_id, key, value)
    
    def _get_theory_text(self, node: NodeBase) -> str:
        """Get theory/help text for a node type."""
        theory_map = {
            "source": "Data source node. Generates or provides input data for the simulation pipeline.",
            "encoder": "Encodes data from one format to another. Common encodings: Base64, UTF-8, Morse, Huffman.",
            "decoder": "Reverses encoding. Must match the corresponding encoder's format.",
            "compressor": "Compresses data using algorithms like RLE, LZ77, LZW, or Huffman.",
            "channel": "Simulates a communication channel with configurable noise, latency, and bandwidth.",
            "ecc": "Error Correction Code. Adds redundancy to detect and correct transmission errors.",
            "checksums": "Validates data integrity using checksum algorithms (EAN, ISBN, Luhn, etc.).",
            "analyzer": "Analyzes data properties: entropy, frequency distribution, compression ratio.",
            "sink": "Output node. Displays or stores the final processed data.",
            "signal": "Signal processing: sampling, quantization, FFT, modulation/demodulation.",
        }
        return theory_map.get(node.category, "No theory available for this node type.")
    
    def _add_image_preview(self, node: NodeBase):
        """Add image preview widget for image nodes."""
        preview_group = QGroupBox("Image Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        # Create label for image
        preview_label = QLabel()
        preview_label.setAlignment(Qt.AlignCenter)
        preview_label.setMinimumHeight(150)
        preview_label.setStyleSheet("""
            QLabel {
                background: #1e1e1e;
                border: 1px solid #555;
                border-radius: 4px;
            }
        """)
        
        try:
            from PIL import Image
            import io
            
            # Load image from bytes
            img = Image.open(io.BytesIO(node.last_image_bytes))
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Calculate scaled size (max 250px width/height)
            max_size = 250
            w, h = img.size
            scale = min(max_size / w, max_size / h, 1.0)
            new_size = (int(w * scale), int(h * scale))
            
            # Resize for preview
            img_preview = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Convert to QPixmap
            buffer = io.BytesIO()
            img_preview.save(buffer, format='PNG')
            pixmap = QPixmap()
            pixmap.loadFromData(buffer.getvalue())
            
            # Set pixmap to label
            preview_label.setPixmap(pixmap)
            preview_label.setToolTip(f"Original size: {w}x{h}\nScaled: {new_size[0]}x{new_size[1]}")
            
        except Exception as e:
            preview_label.setText(f"Error loading preview:\n{str(e)}")
            preview_label.setStyleSheet("""
                QLabel {
                    background: #1e1e1e;
                    border: 1px solid #F44336;
                    border-radius: 4px;
                    color: #F44336;
                    padding: 10px;
                }
            """)
        
        preview_layout.addWidget(preview_label)
        self.scroll_layout.addWidget(preview_group)
    
    def update_stats(self):
        """Refresh statistics display (called on simulation tick)."""
        if self.current_node:
            self._rebuild()
