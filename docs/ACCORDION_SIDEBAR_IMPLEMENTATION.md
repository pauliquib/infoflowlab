# Accordion Sidebar Implementation

## Overview

The left sidebar has been redesigned from a static, long list into a modern, collapsible accordion system with educational categories. This transformation makes InfoFlowLab more approachable for first-semester students learning Information Theory.

## Key Features Implemented

### 1. Educational Taxonomy & Naming

The categories have been reorganized into a logical learning progression that follows the data flow through a communication system:

| # | Category | Subtitle (Czech) | Color |
|---|----------|------------------|-------|
| 1 | **Zdroje (Sources)** | Kde data vznikají (Text, Generátory, Zvuk) | 🟢 #4CAF50 |
| 2 | **Zpracování a Komprese (Source Coding)** | Zmenšení objemu a formátování (Huffman, RLE, Base64) | 🔵 #2196F3 |
| 3 | **Zabezpečení proti chybám (Channel Coding)** | Přidání redundance a detekce chyb (Hamming, CRC, Parita) | 🟠 #FF9800 |
| 4 | **Přenosové Kanály (Environment)** | Kudy data tečou a kde vzniká šum (BSK, AWGN) | 🟣 #9C27B0 |
| 5 | **Dekódování na příjmu (Receivers)** | Oprava chyb a obnova původních dat | 🔵 #00BCD4 |
| 6 | **Kontrolní kódy (Checksums)** | Ověření integrity dat (EAN, ISBN, Luhn) | 🟢 #8BC34A |
| 7 | **Měření a Výstupy (Analytics)** | Výpočet entropie, latence a zobrazení výsledků | 🔴 #FF5722 |

### 2. Accordion UI Component

**Features:**
- **Smooth Animations**: 150ms expand/collapse animations using `QPropertyAnimation`
- **Visual Feedback**: Hover effects on category headers
- **Color-Coded**: Each category has a distinct color for quick identification
- **Subtitles**: Educational descriptions help beginners understand the purpose
- **Wider Sidebar**: Increased from 240px to 280px to accommodate subtitles

**Implementation Details:**
```python
class CategoryPanel(QFrame):
    """Collapsible category panel with node buttons and educational subtitles."""
    
    def toggle_collapse(self, force_state: bool = None):
        """Toggle collapse with smooth animation."""
        if self._collapsed:
            self._animate_collapse()
        else:
            self._animate_expand()
    
    def _animate_collapse(self):
        """Animate collapsing the panel."""
        self._animation = QPropertyAnimation(self.content_container, b"maximumHeight")
        self._animation.setDuration(150)
        self._animation.setStartValue(start_height)
        self._animation.setEndValue(0)
        self._animation.setEasingCurve(QEasingCurve.InOutQuad)
        self._animation.start()
```

### 3. Smart Search Integration

The search functionality has been enhanced with intelligent auto-expand behavior:

**Behavior:**
- When user types "Hamming", the system:
  1. Filters all categories for matching items
  2. Auto-expands the "Zabezpečení proti chybám" category
  3. Auto-collapses other categories (if `auto_close_others=True`)
  4. Shows only matching items
- When search is cleared, all categories return to their default state

**Implementation:**
```python
def _filter_categories(self, text: str):
    """Smart filter with auto-expand for matching categories."""
    if not text:
        # Clear search - restore all panels
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
```

### 4. Data Structure

The new dictionary-based structure provides flexibility and clarity:

```python
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
            # ... more items
        ]
    },
    # ... more categories
]
```

**Benefits:**
- Easy to add/remove/reorder categories
- Each category is self-contained
- Supports future extensions (tooltips, icons, metadata)
- Clear separation of concerns

## Usage

### Basic Usage

```python
from gui.sidebar import Sidebar

# Create sidebar with auto-close behavior
sidebar = Sidebar(auto_close_others=True)

# Or allow multiple categories open simultaneously
sidebar = Sidebar(auto_close_others=False)
```

### Programmatic Control

```python
# Expand all categories
sidebar.expand_all()

# Collapse all categories
sidebar.collapse_all()

# Access specific panel
panel = sidebar._panels[2]  # Channel coding panel
panel.toggle_collapse(False)  # Expand it
```

### Search Filtering

The search is automatically connected to the `QLineEdit` widget:

```python
# This happens automatically via signal connection
sidebar.search_box.textChanged.connect(sidebar._filter_categories)

# Or manually trigger search
sidebar._filter_categories("Hamming")
```

## Testing

A comprehensive test suite is provided in `test_sidebar_accordion.py`:

```bash
python test_sidebar_accordion.py
```

**Test Coverage:**
- ✓ Category structure validation
- ✓ Panel initialization and state management
- ✓ Expand/collapse functionality
- ✓ Search filtering with auto-expand
- ✓ Helper methods (expand_all, collapse_all)

## Migration from Old System

### What Changed

**Before:**
```python
CATEGORIES = [
    ("📝 Zdroje", "sources", [
        ("Text", "Text source - enter text in inspector"),
        # ...
    ]),
    # ... more tuples
]
```

**After:**
```python
CATEGORIES = [
    {
        "id": "sources",
        "name": "1. Zdroje (Sources)",
        "subtitle": "Kde data vznikají (Text, Generátory, Zvuk)",
        "icon": "📝",
        "color": "#4CAF50",
        "items": [
            ("Text", "Text source - enter text in inspector"),
            # ...
        ]
    },
    # ... more dictionaries
]
```

### Backward Compatibility

The `CategoryPanel` constructor now accepts additional parameters but maintains backward compatibility:

```python
# Old way (still works)
panel = CategoryPanel("Category Name", ["Item1", "Item2"])

# New way (with all features)
panel = CategoryPanel(
    category_name="Category Name",
    subtitle="Educational description",
    items=["Item1", "Item2"],
    icon="📝",
    color="#4CAF50",
    auto_close_others=True
)
```

## Performance Considerations

- **Animation Duration**: 150ms provides smooth visual feedback without feeling sluggish
- **Height Calculation**: Uses `sizeHint()` for accurate content height
- **Search Performance**: O(n*m) where n=categories, m=items per category (efficient for <1000 items)
- **Memory**: Minimal overhead - animations are lightweight `QPropertyAnimation` objects

## Future Enhancements

Potential improvements for future iterations:

1. **Chevron Icons**: Add rotating arrow indicators (▲/▼) to show expand state
2. **Favorites System**: Star/highlight frequently used nodes at the top
3. **Category Reordering**: Drag-and-drop to reorder categories
4. **Tooltips**: Rich tooltips with educational content on hover
5. **Keyboard Navigation**: Arrow keys to navigate categories
6. **Remember State**: Save collapsed/expanded state between sessions
7. **Category Badges**: Show item count badges on category headers

## Files Modified

- `src/gui/sidebar.py` - Complete rewrite with accordion functionality
- `test_sidebar_accordion.py` - Comprehensive test suite (new)
- `docs/ACCORDION_SIDEBAR_IMPLEMENTATION.md` - This documentation (new)

## Conclusion

The accordion sidebar successfully transforms InfoFlowLab from a technical tool into an educational platform. The logical categorization, descriptive subtitles, and smooth interactions make it accessible for beginners while maintaining the power and flexibility needed by advanced users.

**Test Results:** ✅ ALL TESTS PASSED