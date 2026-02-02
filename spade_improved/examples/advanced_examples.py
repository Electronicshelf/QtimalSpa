"""
Advanced SPADE usage: Custom plugins and extensions.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path (for running from examples/ directory)
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

import numpy as np
from spade import (
    MetricPlugin, 
    PanelPlugin, 
    register_metric, 
    register_panel,
    SPADEConfig,
    run_analysis
)


# ============================================================================
# CUSTOM METRIC PLUGIN
# ============================================================================

class HuberMetric(MetricPlugin):
    """
    Huber loss metric - robust to outliers.
    Less sensitive than L2, more than L1.
    """
    
    def __init__(self, config=None):
        super().__init__("huber", config)
        self.delta = self.config.get("delta", 0.1)
    
    def compute(self, ref_patches, cap_patches):
        """Compute Huber loss."""
        diff = np.abs(ref_patches - cap_patches)
        
        # Huber loss: quadratic for small errors, linear for large
        huber = np.where(
            diff <= self.delta,
            0.5 * diff ** 2,
            self.delta * (diff - 0.5 * self.delta)
        )
        
        return np.mean(huber, axis=(1, 2, 3))


class LocalContrastMetric(MetricPlugin):
    """
    Local contrast sensitivity metric.
    Focuses on spatial frequency content.
    """
    
    def __init__(self, config=None):
        super().__init__("local_contrast", config)
    
    def compute(self, ref_patches, cap_patches):
        """Compute local contrast differences."""
        def compute_contrast(patches):
            # Simple local contrast: std dev within each patch
            return patches.std(axis=(1, 2, 3))
        
        ref_contrast = compute_contrast(ref_patches)
        cap_contrast = compute_contrast(cap_patches)
        
        # Return contrast difference
        return np.abs(ref_contrast - cap_contrast)


class GradientMagnitudeMetric(MetricPlugin):
    """
    Gradient magnitude metric for edge preservation.
    """
    
    def __init__(self, config=None):
        super().__init__("gradient", config)
    
    def compute(self, ref_patches, cap_patches):
        """Compute gradient magnitude differences."""
        def gradient_magnitude(patches):
            # Compute gradients along spatial dimensions
            grad_y = np.diff(patches, axis=1)
            grad_x = np.diff(patches, axis=2)
            
            # Pad to maintain shape
            grad_y = np.pad(grad_y, ((0,0), (0,1), (0,0), (0,0)), mode='edge')
            grad_x = np.pad(grad_x, ((0,0), (0,0), (0,1), (0,0)), mode='edge')
            
            # Magnitude
            mag = np.sqrt(grad_y**2 + grad_x**2)
            return np.mean(mag, axis=(1, 2, 3))
        
        ref_grad = gradient_magnitude(ref_patches)
        cap_grad = gradient_magnitude(cap_patches)
        
        return np.abs(ref_grad - cap_grad)


# ============================================================================
# CUSTOM PANEL PLUGIN
# ============================================================================

class DCI_P3_Panel(PanelPlugin):
    """
    DCI-P3 cinema color space panel.
    Similar to Display P3 but with different white point.
    """
    
    def __init__(self):
        # DCI-P3 to XYZ matrix (simplified)
        matrix = np.array([
            [1.22, -0.22, 0.0],
            [-0.04, 1.04, 0.0],
            [0.0, -0.08, 1.08]
        ], dtype=np.float32)
        
        super().__init__("DCI_P3", matrix=matrix)
    
    def to_linear(self, rgb):
        """DCI-P3 uses gamma 2.6."""
        return np.power(np.clip(rgb, 0, 1), 2.6)
    
    def from_linear(self, rgb):
        """Inverse gamma 2.6."""
        return np.power(np.clip(rgb, 0, 1), 1/2.6)


class Rec2020Panel(PanelPlugin):
    """
    Rec. 2020 wide color gamut panel.
    Used for HDR content.
    """
    
    def __init__(self):
        # Rec. 2020 to sRGB matrix (simplified approximation)
        matrix = np.array([
            [1.66, -0.59, -0.07],
            [-0.12, 1.02, 0.10],
            [-0.02, -0.14, 1.16]
        ], dtype=np.float32)
        
        super().__init__("REC2020", matrix=matrix)
    
    def to_linear(self, rgb):
        """Rec. 2020 uses same transfer as Rec. 709 (sRGB-like)."""
        v = np.asarray(rgb, dtype=np.float32)
        beta = 0.018053968510807
        return np.where(
            v < beta * 4.5,
            v / 4.5,
            np.power((v + 0.09929682680944) / 1.09929682680944, 1/0.45)
        )
    
    def from_linear(self, rgb):
        """Inverse transfer function."""
        v = np.asarray(rgb, dtype=np.float32)
        beta = 0.018053968510807
        return np.where(
            v < beta,
            v * 4.5,
            1.09929682680944 * np.power(v, 0.45) - 0.09929682680944
        )


# ============================================================================
# EXAMPLES
# ============================================================================

def example_1_custom_metric():
    """Example: Register and use custom metric."""
    print("\n" + "="*60)
    print("Example 1: Custom Metric (Huber Loss)")
    print("="*60)
    
    # Register custom metric
    register_metric(HuberMetric(config={"delta": 0.1}))
    
    # Use in config
    config = SPADEConfig()
    config.metric.metric_name = "huber"
    
    print("Registered Huber metric with delta=0.1")
    print("Usage: config.metric.metric_name = 'huber'")


def example_2_multi_custom_metrics():
    """Example: Use multiple custom metrics."""
    print("\n" + "="*60)
    print("Example 2: Multiple Custom Metrics")
    print("="*60)
    
    # Register all custom metrics
    register_metric(HuberMetric(config={"delta": 0.1}))
    register_metric(LocalContrastMetric())
    register_metric(GradientMagnitudeMetric())
    
    # Use multi-metric with custom metrics
    config = SPADEConfig()
    config.metric.use_multi_metric = True
    config.metric.multi_metrics = ["huber", "local_contrast", "gradient"]
    config.metric.multi_weights = [0.4, 0.3, 0.3]
    
    print("Registered 3 custom metrics:")
    print("  - Huber (weight=0.4)")
    print("  - Local Contrast (weight=0.3)")
    print("  - Gradient Magnitude (weight=0.3)")


def example_3_custom_panel():
    """Example: Register and use custom panel."""
    print("\n" + "="*60)
    print("Example 3: Custom Panel (DCI-P3)")
    print("="*60)
    
    # Register custom panel
    register_panel(DCI_P3_Panel())
    
    # Use in config
    config = SPADEConfig()
    config.panel.panel_name = "DCI_P3"
    
    print("Registered DCI-P3 panel")
    print("Matrix shape: 3x3")
    print("Gamma: 2.6")


def example_4_rec2020_panel():
    """Example: Rec. 2020 wide gamut panel."""
    print("\n" + "="*60)
    print("Example 4: Rec. 2020 Wide Gamut Panel")
    print("="*60)
    
    # Register Rec. 2020
    register_panel(Rec2020Panel())
    
    # Use in config
    config = SPADEConfig()
    config.panel.panel_name = "REC2020"
    
    print("Registered Rec. 2020 panel")
    print("Color gamut: Wide (for HDR)")


def example_5_complete_custom_workflow():
    """Example: Complete workflow with custom components."""
    print("\n" + "="*60)
    print("Example 5: Complete Custom Workflow")
    print("="*60)
    
    # Register custom components
    register_metric(HuberMetric(config={"delta": 0.05}))
    register_panel(DCI_P3_Panel())
    
    # Create config using custom components
    config = SPADEConfig()
    
    # Custom patch settings
    config.patch.patch_size = 64
    config.patch.stride = 32
    config.patch.edge_band = 96
    
    # Custom metric
    config.metric.metric_name = "huber"
    
    # Custom panel
    config.panel.panel_name = "DCI_P3"
    
    # Performance tuning
    config.performance.batch_size = 256
    config.performance.use_cache = True
    
    print("Created custom configuration:")
    print(f"  Metric: {config.metric.metric_name}")
    print(f"  Panel: {config.panel.panel_name}")
    print(f"  Patch size: {config.patch.patch_size}")
    print(f"  Stride: {config.patch.stride}")
    
    # Save for reuse
    config.save("custom_workflow.json")
    print("\nSaved to custom_workflow.json")


def example_6_adaptive_workflow():
    """Example: Adaptive workflow based on image characteristics."""
    print("\n" + "="*60)
    print("Example 6: Adaptive Workflow")
    print("="*60)
    
    from utils import compute_image_stats, load_image
    
    def create_adaptive_config(image_path):
        """Create config adapted to image characteristics."""
        # Load and analyze image
        img = load_image(image_path)
        stats = compute_image_stats(img)
        
        config = SPADEConfig()
        
        # Adapt based on image variance
        if stats['std'] < 0.1:
            # Low contrast image - use sensitive metric
            config.metric.metric_name = "adaptive"
            config.patch.stride = 32  # Fine-grained
            print("  Detected: Low contrast image")
            print("  Using: Adaptive metric, fine stride")
        else:
            # High contrast - use robust metric
            register_metric(HuberMetric(config={"delta": 0.1}))
            config.metric.metric_name = "huber"
            config.patch.stride = 64  # Coarser
            print("  Detected: High contrast image")
            print("  Using: Huber metric, coarse stride")
        
        return config
    
    # Example usage (would need actual image)
    print("\nAdaptive workflow based on image statistics")
    print("  - Low contrast → Adaptive metric + fine stride")
    print("  - High contrast → Huber metric + coarse stride")


def example_7_plugin_listing():
    """Example: List available plugins."""
    print("\n" + "="*60)
    print("Example 7: List Available Plugins")
    print("="*60)
    
    from spade import get_registry, get_panel_registry
    
    # Register our custom plugins first
    register_metric(HuberMetric())
    register_metric(LocalContrastMetric())
    register_metric(GradientMagnitudeMetric())
    register_panel(DCI_P3_Panel())
    register_panel(Rec2020Panel())
    
    # Get registries
    metric_registry = get_registry()
    panel_registry = get_panel_registry()
    
    print("\nAvailable Metrics:")
    for metric_name in metric_registry.list_metrics():
        print(f"  - {metric_name}")
    
    print("\nAvailable Panels:")
    for panel_name in panel_registry.list_panels():
        print(f"  - {panel_name}")


if __name__ == "__main__":
    print("\nSPADE 2.0 Advanced Examples")
    print("===========================")
    print("\nThese examples show how to create and use custom plugins.")
    
    # Run all examples
    # example_1_custom_metric()
    # example_2_multi_custom_metrics()
    # example_3_custom_panel()
    # example_4_rec2020_panel()
    example_5_complete_custom_workflow()
    # example_6_adaptive_workflow()
    # example_7_plugin_listing()
    
    print("\n" + "="*60)
    print("Advanced examples complete!")
    print("="*60)
    print("\nNext steps:")
    print("  1. Create your own metric by extending MetricPlugin")
    print("  2. Create your own panel by extending PanelPlugin")
    print("  3. Register with register_metric() / register_panel()")
    print("  4. Use in your workflow!")
