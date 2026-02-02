"""
Configuration management for SPADE analysis.
"""
import json
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List
import numpy as np


@dataclass
class PatchConfig:
    """Configuration for patch extraction."""
    patch_size: int = 64
    stride: int = 64
    edge_band: int = 64
    extractor_type: str = "edge_anchored"  # or "uniform"


@dataclass
class MetricConfig:
    """Configuration for metric computation."""
    metric_name: str = "l2"
    metric_params: Dict[str, Any] = field(default_factory=dict)
    use_multi_metric: bool = False
    multi_metrics: List[str] = field(default_factory=lambda: ["l2", "perceptual"])
    multi_weights: List[float] = field(default_factory=lambda: [0.6, 0.4])


@dataclass
class PanelConfig:
    """Configuration for panel color space."""
    panel_name: Optional[str] = "OLED_DEFAULT"
    panel_json_path: str = "panel_matrices.json"
    custom_matrix: Optional[List[List[float]]] = None


@dataclass
class VisualizationConfig:
    """Configuration for visualization outputs."""
    generate_heatmaps: bool = True
    generate_luma_maps: bool = True
    generate_log_radiance: bool = True
    generate_contours: bool = True
    heatmap_style: str = "all"  # "all", "bad_only", "edge_only"
    heatmap_alpha: float = 0.4
    luma_output_encoding: str = "srgb"  # "srgb" or "linear"
    contour_levels: int = 12


@dataclass
class AnalysisConfig:
    """Configuration for defect analysis."""
    score_mode: str = "all"  # "all", "edge", "interior"
    score_topk: int = 30
    topn_patches: int = 20
    bad_mode: str = "percentile"  # "percentile" or "absolute"
    bad_percentile: float = 95.0
    bad_absolute: float = 0.05
    min_cluster: int = 4
    thresholds: Dict[str, float] = field(default_factory=lambda: {"good": 0.01, "warning": 0.05})


@dataclass
class PerformanceConfig:
    """Configuration for performance optimization."""
    device: str = "cpu"  # "cpu" or "cuda"
    batch_size: int = 512
    use_cache: bool = True
    cache_size_mb: float = 500
    n_workers: int = 1
    use_parallel: bool = False


@dataclass
class SPADEConfig:
    """Master configuration for SPADE analysis."""
    patch: PatchConfig = field(default_factory=PatchConfig)
    metric: MetricConfig = field(default_factory=MetricConfig)
    panel: PanelConfig = field(default_factory=PanelConfig)
    visualization: VisualizationConfig = field(default_factory=VisualizationConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "patch": asdict(self.patch),
            "metric": asdict(self.metric),
            "panel": asdict(self.panel),
            "visualization": asdict(self.visualization),
            "analysis": asdict(self.analysis),
            "performance": asdict(self.performance),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SPADEConfig":
        """Create from dictionary."""
        config = cls()
        
        if "patch" in data:
            config.patch = PatchConfig(**data["patch"])
        if "metric" in data:
            config.metric = MetricConfig(**data["metric"])
        if "panel" in data:
            config.panel = PanelConfig(**data["panel"])
        if "visualization" in data:
            config.visualization = VisualizationConfig(**data["visualization"])
        if "analysis" in data:
            config.analysis = AnalysisConfig(**data["analysis"])
        if "performance" in data:
            config.performance = PerformanceConfig(**data["performance"])
        
        return config
    
    def save(self, path: str):
        """Save configuration to JSON file."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, path: str) -> "SPADEConfig":
        """Load configuration from JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    def validate(self) -> List[str]:
        """
        Validate configuration parameters.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Patch validation
        if self.patch.patch_size < 1:
            errors.append("patch_size must be >= 1")
        if self.patch.stride < 1:
            errors.append("stride must be >= 1")
        if self.patch.edge_band < 0:
            errors.append("edge_band must be >= 0")
        
        # Metric validation
        valid_metrics = ["l2", "l1", "ssim", "psnr", "perceptual", "adaptive"]
        if self.metric.metric_name not in valid_metrics:
            errors.append(f"metric_name must be one of {valid_metrics}")
        
        if self.metric.use_multi_metric:
            if len(self.metric.multi_metrics) != len(self.metric.multi_weights):
                errors.append("multi_metrics and multi_weights must have same length")
        
        # Analysis validation
        if self.analysis.score_topk < 1:
            errors.append("score_topk must be >= 1")
        if self.analysis.topn_patches < 1:
            errors.append("topn_patches must be >= 1")
        if self.analysis.bad_percentile < 0 or self.analysis.bad_percentile > 100:
            errors.append("bad_percentile must be in [0, 100]")
        
        # Visualization validation
        if self.visualization.heatmap_alpha < 0 or self.visualization.heatmap_alpha > 1:
            errors.append("heatmap_alpha must be in [0, 1]")
        
        # Performance validation
        if self.performance.batch_size < 1:
            errors.append("batch_size must be >= 1")
        if self.performance.n_workers < 1:
            errors.append("n_workers must be >= 1")
        
        return errors


def load_legacy_config(path: str) -> SPADEConfig:
    """
    Load configuration from legacy format.
    Converts old flat config to new hierarchical format.
    """
    with open(path, "r", encoding="utf-8") as f:
        legacy = json.load(f)
    
    config = SPADEConfig()
    
    # Map legacy keys to new structure
    patch_keys = ["patch_size", "stride", "edge_band"]
    metric_keys = ["use_ml"]
    panel_keys = ["analysis_panel", "analysis_panel_file", "analysis_color_matrix", "analysis_color_space"]
    viz_keys = ["heatmap_style", "alpha", "luma_output_encoding"]
    analysis_keys = ["score_mode", "score_topk", "topn_patches", "bad_mode", 
                    "bad_percentile", "bad_absolute", "min_cluster", "thresholds"]
    perf_keys = ["device", "batch"]
    
    for key, value in legacy.items():
        if key in patch_keys:
            setattr(config.patch, key, value)
        elif key in metric_keys:
            if key == "use_ml":
                config.metric.metric_name = "perceptual" if value else "l2"
        elif key in panel_keys:
            if key == "analysis_panel":
                config.panel.panel_name = value
            elif key == "analysis_panel_file":
                config.panel.panel_json_path = value
        elif key in viz_keys:
            if key == "alpha":
                config.visualization.heatmap_alpha = value
            else:
                setattr(config.visualization, key, value)
        elif key in analysis_keys:
            setattr(config.analysis, key, value)
        elif key in perf_keys:
            if key == "batch":
                config.performance.batch_size = value
            else:
                setattr(config.performance, key, value)
    
    return config


def create_default_config() -> SPADEConfig:
    """Create default configuration."""
    return SPADEConfig()


def create_fast_config() -> SPADEConfig:
    """Create configuration optimized for speed."""
    config = SPADEConfig()
    config.patch.patch_size = 64
    config.patch.stride = 128  # Larger stride for speed
    config.metric.metric_name = "l1"  # Fast metric
    config.visualization.generate_log_radiance = False
    config.visualization.generate_contours = False
    config.performance.batch_size = 1024
    return config


def create_quality_config() -> SPADEConfig:
    """Create configuration optimized for quality."""
    config = SPADEConfig()
    config.patch.patch_size = 64
    config.patch.stride = 32  # Smaller stride for better coverage
    config.metric.use_multi_metric = True
    config.metric.multi_metrics = ["l2", "ssim", "perceptual"]
    config.metric.multi_weights = [0.3, 0.3, 0.4]
    config.analysis.topn_patches = 50
    config.performance.batch_size = 256  # Smaller for memory
    return config


# Preset configurations
PRESETS = {
    "default": create_default_config,
    "fast": create_fast_config,
    "quality": create_quality_config,
}


def load_preset(name: str) -> SPADEConfig:
    """Load a preset configuration by name."""
    if name not in PRESETS:
        raise ValueError(f"Unknown preset: {name}. Available: {list(PRESETS.keys())}")
    return PRESETS[name]()
