"""
Base classes for SPADE plugin system.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
import numpy as np


class MetricPlugin(ABC):
    """Base class for perceptual metrics."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
    
    @abstractmethod
    def compute(self, ref_patches: np.ndarray, cap_patches: np.ndarray) -> np.ndarray:
        """
        Compute metric between reference and capture patches.
        
        Args:
            ref_patches: (N, C, H, W) reference patches
            cap_patches: (N, C, H, W) capture patches
        
        Returns:
            distances: (N,) array of distances/scores
        """
        pass
    
    @property
    def requires_gpu(self) -> bool:
        """Whether this metric benefits from GPU acceleration."""
        return False
    
    def preprocess(self, patches: np.ndarray) -> np.ndarray:
        """Optional preprocessing step."""
        return patches
    
    def postprocess(self, distances: np.ndarray) -> np.ndarray:
        """Optional postprocessing step."""
        return distances


class PanelPlugin(ABC):
    """Base class for display panel color spaces."""
    
    def __init__(self, name: str, matrix: Optional[np.ndarray] = None):
        self.name = name
        self._matrix = self._validate_matrix(matrix) if matrix is not None else None
    
    @staticmethod
    def _validate_matrix(matrix: np.ndarray) -> np.ndarray:
        """Validate and normalize matrix to 3x3."""
        arr = np.asarray(matrix, dtype=np.float32)
        if arr.shape == (3, 3):
            return arr
        if arr.size == 9:
            return arr.reshape(3, 3)
        raise ValueError(f"Panel matrix must be 3x3, got shape {arr.shape}")
    
    @property
    def matrix(self) -> Optional[np.ndarray]:
        """Get the color transformation matrix (linear domain)."""
        return self._matrix
    
    @abstractmethod
    def to_linear(self, rgb: np.ndarray) -> np.ndarray:
        """Convert non-linear RGB to linear."""
        pass
    
    @abstractmethod
    def from_linear(self, rgb: np.ndarray) -> np.ndarray:
        """Convert linear RGB to non-linear."""
        pass
    
    def apply_transform(self, rgb_linear: np.ndarray) -> np.ndarray:
        """Apply panel matrix in linear domain."""
        if self._matrix is None:
            return rgb_linear
        flat = rgb_linear.reshape(-1, 3)
        out = flat @ self._matrix.T
        return out.reshape(rgb_linear.shape)


class VisualizationPlugin(ABC):
    """Base class for visualization outputs."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
    
    @abstractmethod
    def generate(self, data: Dict[str, Any], output_path: str) -> str:
        """
        Generate visualization and save to file.
        
        Args:
            data: Dictionary containing visualization data
            output_path: Path to save output
        
        Returns:
            Path to saved file
        """
        pass
    
    @property
    def supported_formats(self) -> Tuple[str, ...]:
        """Supported output formats."""
        return ("png",)


class PatchExtractor(ABC):
    """Base class for patch extraction strategies."""
    
    def __init__(self, patch_size: int, stride: int, edge_band: int = 0):
        self.patch_size = patch_size
        self.stride = stride
        self.edge_band = edge_band
    
    @abstractmethod
    def extract_coordinates(self, height: int, width: int) -> np.ndarray:
        """
        Generate patch coordinates.
        
        Args:
            height: Image height
            width: Image width
        
        Returns:
            coords: (N, 2) array of (y, x) coordinates
        """
        pass
    
    def extract_patches(self, image: np.ndarray, coords: np.ndarray) -> np.ndarray:
        """
        Extract patches from image at given coordinates.
        
        Args:
            image: (H, W, C) image array
            coords: (N, 2) coordinate array
        
        Returns:
            patches: (N, P, P, C) patch array
        """
        H, W = image.shape[:2]
        P = self.patch_size
        patches = []
        
        for y0, x0 in coords:
            y1, x1 = y0 + P, x0 + P
            if y1 <= H and x1 <= W:
                patch = image[y0:y1, x0:x1]
                patches.append(patch)
        
        return np.array(patches)


class PluginRegistry:
    """Registry for managing plugins."""
    
    def __init__(self):
        self._metrics: Dict[str, MetricPlugin] = {}
        self._panels: Dict[str, PanelPlugin] = {}
        self._visualizations: Dict[str, VisualizationPlugin] = {}
    
    def register_metric(self, plugin: MetricPlugin):
        """Register a metric plugin."""
        self._metrics[plugin.name.lower()] = plugin
    
    def register_panel(self, plugin: PanelPlugin):
        """Register a panel plugin."""
        self._panels[plugin.name.upper()] = plugin
    
    def register_visualization(self, plugin: VisualizationPlugin):
        """Register a visualization plugin."""
        self._visualizations[plugin.name.lower()] = plugin
    
    def get_metric(self, name: str) -> MetricPlugin:
        """Get metric plugin by name."""
        key = name.lower()
        if key not in self._metrics:
            raise ValueError(f"Metric '{name}' not found. Available: {list(self._metrics.keys())}")
        return self._metrics[key]
    
    def get_panel(self, name: str) -> PanelPlugin:
        """Get panel plugin by name."""
        key = name.upper()
        if key not in self._panels:
            raise ValueError(f"Panel '{name}' not found. Available: {list(self._panels.keys())}")
        return self._panels[key]
    
    def get_visualization(self, name: str) -> VisualizationPlugin:
        """Get visualization plugin by name."""
        key = name.lower()
        if key not in self._visualizations:
            raise ValueError(f"Visualization '{name}' not found. Available: {list(self._visualizations.keys())}")
        return self._visualizations[key]
    
    def list_metrics(self) -> list:
        """List available metrics."""
        return list(self._metrics.keys())
    
    def list_panels(self) -> list:
        """List available panels."""
        return list(self._panels.keys())
    
    def list_visualizations(self) -> list:
        """List available visualizations."""
        return list(self._visualizations.keys())


# Global registry instance
_registry = PluginRegistry()


def register_metric(plugin: MetricPlugin):
    """Register a metric plugin globally."""
    _registry.register_metric(plugin)


def register_panel(plugin: PanelPlugin):
    """Register a panel plugin globally."""
    _registry.register_panel(plugin)


def register_visualization(plugin: VisualizationPlugin):
    """Register a visualization plugin globally."""
    _registry.register_visualization(plugin)


def get_registry() -> PluginRegistry:
    """Get the global plugin registry."""
    return _registry
