"""
Core SPADE components.
"""

from .base import (
    MetricPlugin,
    PanelPlugin,
    VisualizationPlugin,
    PatchExtractor,
    PluginRegistry,
    get_registry,
    register_metric,
    register_panel,
    register_visualization,
)

from .metrics import (
    L2Metric,
    L1Metric,
    SSIMMetric,
    PSNRMetric,
    PerceptualMetric,
    AdaptiveMetric,
    WeightedMetric,
    create_metric,
    compute_multi_metric,
)

from .patches import (
    EdgeAnchoredExtractor,
    UniformGridExtractor,
    build_patch_grid,
    normalize_patches,
    compute_patch_statistics,
    PatchCache,
)

__all__ = [
    # Base classes
    "MetricPlugin",
    "PanelPlugin",
    "VisualizationPlugin",
    "PatchExtractor",
    "PluginRegistry",
    "get_registry",
    "register_metric",
    "register_panel",
    "register_visualization",
    
    # Metrics
    "L2Metric",
    "L1Metric",
    "SSIMMetric",
    "PSNRMetric",
    "PerceptualMetric",
    "AdaptiveMetric",
    "WeightedMetric",
    "create_metric",
    "compute_multi_metric",
    
    # Patches
    "EdgeAnchoredExtractor",
    "UniformGridExtractor",
    "build_patch_grid",
    "normalize_patches",
    "compute_patch_statistics",
    "PatchCache",
]
