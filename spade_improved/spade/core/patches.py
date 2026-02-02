"""
Efficient patch extraction and processing.
"""
import numpy as np
from typing import Tuple, Optional
from .base import PatchExtractor


class EdgeAnchoredExtractor(PatchExtractor):
    """Extract patches anchored to image edges with interior striding."""
    
    def extract_coordinates(self, height: int, width: int) -> np.ndarray:
        """
        Generate edge-anchored patch coordinates.
        Patches are anchored at edges and stride through interior.
        """
        P, S, E = self.patch_size, self.stride, self.edge_band
        coords = []
        
        # Compute edge anchors
        y_min = max(0, E - P // 2)
        x_min = max(0, E - P // 2)
        y_max = height - P
        x_max = width - P
        
        # Interior grid
        y_interior = np.arange(P, y_max, S)
        x_interior = np.arange(P, x_max, S)
        
        # Filter interior to stay within edge band
        if E > 0:
            y_interior = y_interior[(y_interior >= E) & (y_interior <= y_max - E)]
            x_interior = x_interior[(x_interior >= E) & (x_interior <= x_max - E)]
        
        # Generate full grid
        for y in y_interior:
            for x in x_interior:
                coords.append([y, x])
        
        return np.array(coords, dtype=np.int32)
    
    def extract_patches_vectorized(self, image: np.ndarray, coords: np.ndarray) -> np.ndarray:
        """
        Vectorized patch extraction using advanced indexing.
        Faster than loop-based extraction.
        """
        if len(coords) == 0:
            return np.array([])
        
        H, W, C = image.shape
        P = self.patch_size
        N = len(coords)
        
        # Create index arrays
        y_base = coords[:, 0, None, None]
        x_base = coords[:, 1, None, None]
        y_offset = np.arange(P)[None, :, None]
        x_offset = np.arange(P)[None, None, :]
        
        y_idx = y_base + y_offset
        x_idx = x_base + x_offset
        
        # Extract patches
        patches = image[y_idx, x_idx]  # (N, P, P, C)
        return patches


class UniformGridExtractor(PatchExtractor):
    """Extract patches on a uniform grid."""
    
    def extract_coordinates(self, height: int, width: int) -> np.ndarray:
        """Generate uniform grid coordinates."""
        P, S = self.patch_size, self.stride
        
        y_coords = np.arange(0, height - P + 1, S)
        x_coords = np.arange(0, width - P + 1, S)
        
        yy, xx = np.meshgrid(y_coords, x_coords, indexing='ij')
        coords = np.stack([yy.ravel(), xx.ravel()], axis=1)
        
        return coords.astype(np.int32)


def build_patch_grid(coords: np.ndarray, height: int, width: int, 
                    patch_size: int, stride: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Convert patches to a logical 2D grid for visualization.
    
    Args:
        coords: (N, 2) patch coordinates
        height: Image height
        width: Image width
        patch_size: Patch size
        stride: Stride between patches
    
    Returns:
        grid: (H_grid, W_grid) mapping to patch indices (-1 for empty)
        y_centers: (H_grid,) y-coordinates of grid centers
        x_centers: (W_grid,) x-coordinates of grid centers
    """
    if len(coords) == 0:
        return np.array([[]]), np.array([]), np.array([])
    
    # Get unique coordinates
    ys = np.unique(coords[:, 0])
    xs = np.unique(coords[:, 1])
    
    # Create mapping
    y_to_idx = {int(y): i for i, y in enumerate(ys)}
    x_to_idx = {int(x): i for i, x in enumerate(xs)}
    
    # Build grid
    grid = -np.ones((len(ys), len(xs)), dtype=np.int32)
    
    for patch_idx, (y, x) in enumerate(coords):
        grid_y = y_to_idx[int(y)]
        grid_x = x_to_idx[int(x)]
        grid[grid_y, grid_x] = patch_idx
    
    # Compute centers
    y_centers = ys + patch_size / 2.0
    x_centers = xs + patch_size / 2.0
    
    return grid, y_centers, x_centers


def normalize_patches(patches: np.ndarray, method: str = "instance") -> np.ndarray:
    """
    Normalize patches for metric computation.
    
    Args:
        patches: (N, H, W, C) or (N, C, H, W) patches
        method: "instance", "batch", or "none"
    
    Returns:
        Normalized patches
    """
    if method == "none":
        return patches
    
    if method == "instance":
        # Normalize each patch independently
        mean = patches.mean(axis=(1, 2, 3), keepdims=True)
        std = patches.std(axis=(1, 2, 3), keepdims=True) + 1e-8
        return (patches - mean) / std
    
    elif method == "batch":
        # Normalize across all patches
        mean = patches.mean()
        std = patches.std() + 1e-8
        return (patches - mean) / std
    
    else:
        raise ValueError(f"Unknown normalization method: {method}")


def compute_patch_statistics(patches: np.ndarray, coords: np.ndarray) -> dict:
    """
    Compute useful statistics about patches.
    
    Args:
        patches: (N, H, W, C) patch array
        coords: (N, 2) coordinate array
    
    Returns:
        Dictionary of statistics
    """
    N = len(patches)
    
    stats = {
        "num_patches": N,
        "mean_brightness": float(patches.mean()),
        "std_brightness": float(patches.std()),
        "min_brightness": float(patches.min()),
        "max_brightness": float(patches.max()),
        "spatial_extent": {
            "y_min": int(coords[:, 0].min()),
            "y_max": int(coords[:, 0].max()),
            "x_min": int(coords[:, 1].min()),
            "x_max": int(coords[:, 1].max()),
        }
    }
    
    return stats


class PatchCache:
    """Cache for extracted patches to avoid recomputation."""
    
    def __init__(self, max_size_mb: float = 1000):
        self._cache = {}
        self.max_size_mb = max_size_mb
        self._current_size_mb = 0
    
    def _compute_size_mb(self, patches: np.ndarray) -> float:
        """Compute memory size in MB."""
        return patches.nbytes / (1024 * 1024)
    
    def put(self, key: str, patches: np.ndarray):
        """Add patches to cache."""
        size_mb = self._compute_size_mb(patches)
        
        # Simple eviction: clear all if over limit
        if self._current_size_mb + size_mb > self.max_size_mb:
            self.clear()
        
        self._cache[key] = patches
        self._current_size_mb += size_mb
    
    def get(self, key: str) -> Optional[np.ndarray]:
        """Get patches from cache."""
        return self._cache.get(key)
    
    def clear(self):
        """Clear cache."""
        self._cache.clear()
        self._current_size_mb = 0
    
    def __contains__(self, key: str) -> bool:
        return key in self._cache
