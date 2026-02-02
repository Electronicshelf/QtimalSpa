"""
SPADE - Spatial Analysis for Display Evaluation

A modular, plug-and-play framework for OLED display quality analysis.
"""

__version__ = "2.0.0"

from .config import (
    SPADEConfig,
    PatchConfig,
    MetricConfig,
    PanelConfig,
    VisualizationConfig,
    AnalysisConfig,
    PerformanceConfig,
    load_preset,
    create_default_config,
    create_fast_config,
    create_quality_config,
)

from spade.framework import (
    SPADEAnalyzer,
    run_analysis,
    quick_analysis,
)

from spade.core.base import (
    MetricPlugin,
    PanelPlugin,
    VisualizationPlugin,
    PatchExtractor,
    get_registry,
    register_metric,
    register_panel,
    register_visualization,
)

from .core.metrics import create_metric
from .plugins.panels import create_panel, get_panel_registry
from .report_generator import generate_report, SPADEReportGenerator

__all__ = [
    # Main API
    "run_analysis",
    "quick_analysis",
    "SPADEAnalyzer",
    
    # Configuration
    "SPADEConfig",
    "PatchConfig",
    "MetricConfig",
    "PanelConfig",
    "VisualizationConfig",
    "AnalysisConfig",
    "PerformanceConfig",
    "load_preset",
    "create_default_config",
    "create_fast_config",
    "create_quality_config",
    
    # Plugin System
    "MetricPlugin",
    "PanelPlugin",
    "VisualizationPlugin",
    "PatchExtractor",
    "get_registry",
    "register_metric",
    "register_panel",
    "register_visualization",
    
    # Factories
    "create_metric",
    "create_panel",
    "get_panel_registry",
    
    # Report Generation
    "generate_report",
    "SPADEReportGenerator",
]
