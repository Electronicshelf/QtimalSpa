"""
Display panel color space plugins.
"""
import json
import os
import numpy as np
from typing import Optional, Dict
from spade.core.base import PanelPlugin


def _srgb_to_linear(rgb: np.ndarray) -> np.ndarray:
    """Convert sRGB to linear RGB."""
    v = np.asarray(rgb, dtype=np.float32)
    return np.where(
        v <= 0.04045,
        v / 12.92,
        ((v + 0.055) / 1.055) ** 2.4
    )


def _linear_to_srgb(rgb: np.ndarray) -> np.ndarray:
    """Convert linear RGB to sRGB."""
    v = np.asarray(rgb, dtype=np.float32)
    sign = np.sign(v)
    v_abs = np.abs(v)
    v_out = np.where(
        v_abs <= 0.0031308,
        v_abs * 12.92,
        1.055 * (v_abs ** (1.0 / 2.4)) - 0.055
    )
    return v_out * sign


class SRGBPanel(PanelPlugin):
    """Standard sRGB color space (identity matrix)."""
    
    def __init__(self):
        super().__init__("SRGB", matrix=np.eye(3, dtype=np.float32))
    
    def to_linear(self, rgb: np.ndarray) -> np.ndarray:
        return _srgb_to_linear(rgb)
    
    def from_linear(self, rgb: np.ndarray) -> np.ndarray:
        return _linear_to_srgb(rgb)


class P3APanel(PanelPlugin):
    """Display P3 (P3-A) color space."""
    
    def __init__(self):
        matrix = np.array([
            [1.417667657819538, -0.417667657819538, 0.000000000000000],
            [-0.048674037828808, 1.048674037828808, 0.000000000000000],
            [-0.022727253592021, -0.075539047401077, 1.098266300993098],
        ], dtype=np.float32)
        super().__init__("P3A", matrix=matrix)
    
    def to_linear(self, rgb: np.ndarray) -> np.ndarray:
        return _srgb_to_linear(rgb)
    
    def from_linear(self, rgb: np.ndarray) -> np.ndarray:
        return _linear_to_srgb(rgb)


class CustomPanel(PanelPlugin):
    """Custom panel with user-provided matrix."""
    
    def __init__(self, name: str, matrix: np.ndarray, 
                 gamma_func=None, inv_gamma_func=None):
        super().__init__(name, matrix=matrix)
        self._gamma_func = gamma_func or _srgb_to_linear
        self._inv_gamma_func = inv_gamma_func or _linear_to_srgb
    
    def to_linear(self, rgb: np.ndarray) -> np.ndarray:
        return self._gamma_func(rgb)
    
    def from_linear(self, rgb: np.ndarray) -> np.ndarray:
        return self._inv_gamma_func(rgb)


def load_panel_from_json(panel_name: str, json_path: str) -> PanelPlugin:
    """
    Load a panel from JSON file.
    
    Args:
        panel_name: Name of panel in JSON
        json_path: Path to panel_matrices.json
    
    Returns:
        PanelPlugin instance
    """
    if not os.path.isfile(json_path):
        raise FileNotFoundError(f"Panel JSON not found: {json_path}")
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    key = panel_name.strip().upper()
    if key not in data:
        available = ", ".join(sorted(data.keys()))
        raise ValueError(f"Panel '{panel_name}' not found. Available: {available}")
    
    panel_data = data[key]
    if isinstance(panel_data, dict):
        matrix = panel_data.get("matrix")
        notes = panel_data.get("notes", "")
    else:
        matrix = panel_data
        notes = ""
    
    if matrix is None:
        raise ValueError(f"No matrix found for panel '{panel_name}'")
    
    matrix = np.asarray(matrix, dtype=np.float32).reshape(3, 3)
    
    return CustomPanel(panel_name, matrix)


def create_panel(name: str, json_path: Optional[str] = None) -> PanelPlugin:
    """
    Factory function to create panel by name.
    
    Args:
        name: Panel name ("SRGB", "P3A", or custom name)
        json_path: Optional path to panel_matrices.json for custom panels
    
    Returns:
        PanelPlugin instance
    """
    name_upper = name.strip().upper()
    
    # Built-in panels
    if name_upper in ("SRGB", "IDENTITY", "NONE"):
        return SRGBPanel()
    elif name_upper == "P3A":
        return P3APanel()
    elif name_upper == "OLED_DEFAULT":
        return P3APanel()  # OLED_DEFAULT is P3A
    
    # Custom panel from JSON
    if json_path is None:
        raise ValueError(f"json_path required for custom panel '{name}'")
    
    return load_panel_from_json(name, json_path)


class PanelRegistry:
    """Registry for managing panel plugins."""
    
    def __init__(self, json_path: Optional[str] = None):
        self.json_path = json_path
        self._panels: Dict[str, PanelPlugin] = {}
        
        # Register built-in panels
        self.register(SRGBPanel())
        self.register(P3APanel())
    
    def register(self, panel: PanelPlugin):
        """Register a panel plugin."""
        self._panels[panel.name.upper()] = panel
    
    def get(self, name: str) -> PanelPlugin:
        """Get panel by name."""
        key = name.strip().upper()
        
        # Check if already registered
        if key in self._panels:
            return self._panels[key]
        
        # Try to load from JSON
        if self.json_path and os.path.isfile(self.json_path):
            try:
                panel = load_panel_from_json(name, self.json_path)
                self.register(panel)
                return panel
            except (ValueError, KeyError):
                pass
        
        available = ", ".join(sorted(self._panels.keys()))
        raise ValueError(f"Panel '{name}' not found. Available: {available}")
    
    def list_panels(self) -> list:
        """List available panel names."""
        return sorted(self._panels.keys())
    
    def load_from_json(self, json_path: str):
        """Load all panels from a JSON file."""
        self.json_path = json_path
        
        if not os.path.isfile(json_path):
            return
        
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for panel_name in data.keys():
            try:
                panel = load_panel_from_json(panel_name, json_path)
                self.register(panel)
            except Exception as e:
                print(f"Warning: Failed to load panel '{panel_name}': {e}")


# Global panel registry
_panel_registry = PanelRegistry()


def get_panel_registry() -> PanelRegistry:
    """Get the global panel registry."""
    return _panel_registry


def register_panel(panel: PanelPlugin):
    """Register a panel globally."""
    _panel_registry.register(panel)
