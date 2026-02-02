"""
Basic SPADE usage examples.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path (for running from examples/ directory)
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from spade import quick_analysis, SPADEConfig, run_analysis, SPADEAnalyzer


def example_1_quick_start():
    """Example 1: Quick start with defaults."""
    print("\n" + "="*60)
    print("Example 1: Quick Start")
    print("="*60)
    
    # Run with default settings
    results = quick_analysis(
        ref_path="ref.png",
        cap_path="cap.png",
        output_dir="output_example1"
    )
    
    print(f"Mean distance: {results['mean_distance']:.4f}")
    print(f"Worst patch: {results['max_distance']:.4f}")


def example_2_presets():
    """Example 2: Using presets."""
    print("\n" + "="*60)
    print("Example 2: Using Presets")
    print("="*60)
    
    # Fast preset for quick testing
    results_fast = quick_analysis(
        ref_path="ref.png",
        cap_path="cap.png",
        output_dir="output_fast",
        preset="fast"
    )
    
    # Quality preset for thorough analysis
    results_quality = quick_analysis(
        ref_path="ref.png",
        cap_path="cap.png",
        output_dir="output_quality",
        preset="quality"
    )
    
    print(f"Fast analysis: {results_fast['mean_distance']:.4f}")
    print(f"Quality analysis: {results_quality['mean_distance']:.4f}")


def example_3_custom_config():
    """Example 3: Custom configuration."""
    print("\n" + "="*60)
    print("Example 3: Custom Configuration")
    print("="*60)
    
    # Create custom config
    config = SPADEConfig()
    
    # Customize patches
    config.patch.patch_size = 64
    config.patch.stride = 32  # Smaller stride for better coverage
    
    # Use perceptual metric
    config.metric.metric_name = "perceptual"
    
    # P3A panel
    config.panel.panel_name = "P3A"
    
    # Enable all visualizations
    config.visualization.generate_heatmaps = True
    config.visualization.generate_luma_maps = True
    config.visualization.generate_log_radiance = True
    config.visualization.generate_contours = True
    
    # Run analysis
    results = run_analysis("ref.png", "cap.png", "output_custom", config)
    
    print(f"Results: {results['mean_distance']:.4f}")


def example_4_multi_metric():
    """Example 4: Multi-metric analysis."""
    print("\n" + "="*60)
    print("Example 4: Multi-Metric Analysis")
    print("="*60)
    
    config = SPADEConfig()
    
    # Enable multi-metric
    config.metric.use_multi_metric = True
    config.metric.multi_metrics = ["l2", "ssim", "perceptual"]
    config.metric.multi_weights = [0.3, 0.3, 0.4]
    
    results = run_analysis("ref.png", "cap.png", "output_multimetric", config)
    
    print(f"Combined metric: {results['mean_distance']:.4f}")


def example_5_batch_processing():
    """Example 5: Batch processing multiple images."""
    print("\n" + "="*60)
    print("Example 5: Batch Processing")
    print("="*60)
    
    # Create analyzer once
    config = SPADEConfig()
    analyzer = SPADEAnalyzer(config)
    
    # Process multiple image pairs
    image_pairs = [
        ("ref1.png", "cap1.png"),
        ("ref2.png", "cap2.png"),
        ("ref3.png", "cap3.png"),
    ]
    
    for i, (ref, cap) in enumerate(image_pairs):
        print(f"\nProcessing pair {i+1}...")
        try:
            results = analyzer.analyze(ref, cap, f"output_batch_{i}")
            print(f"  Mean distance: {results['mean_distance']:.4f}")
        except FileNotFoundError:
            print(f"  Skipping (files not found)")


def example_6_save_load_config():
    """Example 6: Save and load configuration."""
    print("\n" + "="*60)
    print("Example 6: Save/Load Configuration")
    print("="*60)
    
    # Create and save config
    config = SPADEConfig()
    config.patch.stride = 32
    config.metric.metric_name = "perceptual"
    config.save("my_config.json")
    print("Config saved to my_config.json")
    
    # Load and use
    loaded_config = SPADEConfig.load("my_config.json")
    print(f"Loaded config with stride={loaded_config.patch.stride}")
    
    # Use it
    # results = run_analysis("ref.png", "cap.png", "output", loaded_config)


def example_7_memory_estimation():
    """Example 7: Memory estimation before running."""
    print("\n" + "="*60)
    print("Example 7: Memory Estimation")
    print("="*60)
    
    from utils import estimate_memory_usage
    
    mem_est = estimate_memory_usage(
        height=4000,
        width=6000,
        channels=3,
        patch_size=64,
        stride=64
    )
    
    print(f"Estimated memory: {mem_est['total_mb']:.1f} MB")
    print(f"Number of patches: {mem_est['num_patches']}")
    print(f"Recommendation: {mem_est['recommendation']}")


def example_8_threshold_analysis():
    """Example 8: Custom threshold analysis."""
    print("\n" + "="*60)
    print("Example 8: Threshold Analysis")
    print("="*60)
    
    config = SPADEConfig()
    
    # Set custom thresholds
    config.analysis.thresholds = {
        "excellent": 0.005,
        "good": 0.01,
        "acceptable": 0.02,
        "warning": 0.05,
        "critical": 0.10
    }
    
    results = run_analysis("ref.png", "cap.png", "output_threshold", config)
    
    # Print threshold results
    for name, data in results.items():
        if name.endswith("_threshold"):
            threshold_name = name.replace("_threshold", "")
            print(f"{threshold_name}: {data['percentage']:.1f}% above {data['value']}")


if __name__ == "__main__":
    print("\nSPADE 2.0 Examples")
    print("==================")
    print("\nNote: These examples assume ref.png and cap.png exist.")
    print("Update paths as needed for your images.")
    
    # Run examples that don't require actual image files
    example_7_memory_estimation()
    
    # Uncomment to run examples requiring images:
    # example_1_quick_start()
    # example_2_presets()
    # example_3_custom_config()
    # example_4_multi_metric()
    # example_5_batch_processing()
    # example_6_save_load_config()
    # example_8_threshold_analysis()
    
    print("\n" + "="*60)
    print("Examples complete!")
    print("="*60)
