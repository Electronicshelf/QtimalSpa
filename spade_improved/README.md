# SPADE 2.0 - Spatial Analysis for Display Evaluation

A **modular, plug-and-play** framework for OLED display quality validation with patch-based perceptual analysis.

## ✨ Key Features

- **🔌 Plug-and-Play Architecture**: Easy-to-extend plugin system for metrics, panels, and visualizations
- **⚡ High Performance**: Vectorized operations, batch processing, and intelligent caching
- **🎨 Flexible Configuration**: Hierarchical config system with presets
- **📊 Rich Visualizations**: Heatmaps, luma maps, log radiance, contour plots
- **🎯 Multiple Metrics**: L1, L2, SSIM, PSNR, perceptual, adaptive, and custom
- **🖥️ Panel Support**: Plug-and-play panel color spaces (sRGB, P3, custom)
- **💾 Smart Caching**: Memory-efficient caching for large datasets
- **📈 Comprehensive Analysis**: Statistics, clustering, threshold analysis

## 🚀 Quick Start

### Basic Usage

```python
from spade import quick_analysis

# Run with default settings
results = quick_analysis(
    ref_path="ref.png",
    cap_path="cap.png",
    output_dir="output"
)

# Run with quality preset
results = quick_analysis(
    ref_path="ref.png",
    cap_path="cap.png",
    output_dir="output",
    preset="quality"  # or "fast", "default"
)
```

### Using Configuration

```python
from spade import SPADEConfig, run_analysis

# Create custom configuration
config = SPADEConfig()
config.patch.patch_size = 64
config.patch.stride = 32
config.metric.metric_name = "perceptual"
config.panel.panel_name = "P3A"

# Run analysis
results = run_analysis("ref.png", "cap.png", "output", config)
```

### Advanced Usage with Analyzer Class

```python
from spade import SPADEAnalyzer, SPADEConfig

# Create analyzer
config = SPADEConfig()
analyzer = SPADEAnalyzer(config)

# Run multiple analyses
for ref, cap in image_pairs:
    results = analyzer.analyze(ref, cap, f"output_{i}")
```

### Advanced Plots

SPADE includes advanced plot utilities in `spade.advanced_plots`.
To generate these plots you must enable patch data output.

```python
from spade import quick_analysis
from spade.advanced_plots import generate_all_plots
from utils.image_utils import load_image

results = quick_analysis(
    ref_path="ref.png",
    cap_path="cap.png",
    output_dir="output",
    return_patch_data=True
)

ref_img = load_image("ref.png")
cap_img = load_image("cap.png")
plot_paths = generate_all_plots(results, ref_img, cap_img, "output/advanced_plots")
```

See `ADVANCED_VISUALIZATION_GUIDE.md` and `examples/advanced_plots_examples.py`.

## 📋 Configuration

### Hierarchical Configuration

```python
from spade import SPADEConfig

config = SPADEConfig()

# Patch extraction
config.patch.patch_size = 64
config.patch.stride = 64
config.patch.edge_band = 64
config.patch.extractor_type = "edge_anchored"  # or "uniform"

# Metrics
config.metric.metric_name = "l2"  # l2, l1, ssim, psnr, perceptual, adaptive
config.metric.use_multi_metric = False
config.metric.multi_metrics = ["l2", "perceptual"]
config.metric.multi_weights = [0.6, 0.4]

# Panel color space
config.panel.panel_name = "OLED_DEFAULT"  # or "P3A", "SRGB", custom
config.panel.panel_json_path = "panel_matrices.json"

# Visualization
config.visualization.generate_heatmaps = True
config.visualization.generate_luma_maps = True
config.visualization.generate_log_radiance = True
config.visualization.generate_contours = True
config.visualization.heatmap_alpha = 0.4
config.visualization.luma_output_encoding = "srgb"  # or "linear"

# Analysis
config.analysis.score_mode = "all"  # all, edge, interior
config.analysis.score_topk = 30
config.analysis.bad_percentile = 95.0
config.analysis.thresholds = {"good": 0.01, "warning": 0.05}
config.analysis.return_patch_data = False  # enable for advanced plots

# Performance
config.performance.device = "cpu"  # or "cuda"
config.performance.batch_size = 512
config.performance.use_cache = True
config.performance.cache_size_mb = 500
```

### Save/Load Configuration

```python
# Save
config.save("my_config.json")

# Load
config = SPADEConfig.load("my_config.json")
```

### Configuration Presets

```python
from spade import load_preset

# Available presets
config_default = load_preset("default")   # Balanced
config_fast = load_preset("fast")         # Speed-optimized
config_quality = load_preset("quality")   # Quality-optimized
```

## 🔌 Plugin System

### Custom Metric Plugin

```python
from spade import MetricPlugin, register_metric
import numpy as np

class MyMetric(MetricPlugin):
    def __init__(self, config=None):
        super().__init__("my_metric", config)
    
    def compute(self, ref_patches, cap_patches):
        # Your metric logic here
        diff = np.abs(ref_patches - cap_patches)
        return np.mean(diff, axis=(1, 2, 3))

# Register globally
register_metric(MyMetric())

# Use in config
config = SPADEConfig()
config.metric.metric_name = "my_metric"
```

### Custom Panel Plugin

```python
from spade import PanelPlugin, register_panel
import numpy as np

class MyPanel(PanelPlugin):
    def __init__(self):
        matrix = np.array([...])  # 3x3 matrix
        super().__init__("MY_PANEL", matrix=matrix)
    
    def to_linear(self, rgb):
        # Your linearization logic
        return rgb ** 2.2
    
    def from_linear(self, rgb):
        # Your gamma encoding logic
        return rgb ** (1/2.2)

# Register globally
register_panel(MyPanel())

# Use in config
config = SPADEConfig()
config.panel.panel_name = "MY_PANEL"
```

### Add Panel via JSON

```json
{
  "MY_PANEL": {
    "matrix": [
      [1.0, 0.0, 0.0],
      [0.0, 1.0, 0.0],
      [0.0, 0.0, 1.0]
    ],
    "notes": "My custom panel matrix"
  }
}
```

```python
config = SPADEConfig()
config.panel.panel_name = "MY_PANEL"
config.panel.panel_json_path = "my_panels.json"
```

## 📊 Available Metrics

- **L1**: Manhattan distance (fast, simple)
- **L2**: Euclidean distance (balanced)
- **SSIM**: Structural similarity (quality-focused)
- **PSNR**: Peak signal-to-noise ratio
- **Perceptual**: Luminance + chrominance weighted
- **Adaptive**: Content-adaptive weighting
- **Multi-metric**: Weighted combination

## 🎨 Built-in Panels

- **SRGB**: Standard sRGB (identity matrix)
- **P3A**: Display P3 color space
- **OLED_DEFAULT**: Default OLED (same as P3A)
- **Custom**: Add your own via JSON

## 📈 Output Structure

```
output/
├── analysis_summary.json      # Comprehensive statistics
├── heatmap.png               # Visual heatmap overlay
├── luma_ref.png              # Reference luminance map
├── luma_cap.png              # Capture luminance map
├── log_radiance_ref.png      # Log radiance visualization
├── log_radiance_cap.png      # Log radiance visualization
└── contour_map_scores.png    # Contour plot of patch scores
```

### Analysis Summary JSON

```json
{
  "mean_distance": 0.0234,
  "std_distance": 0.0156,
  "min_distance": 0.0001,
  "max_distance": 0.0892,
  "median_distance": 0.0198,
  "num_patches": 4096,
  "metric": "perceptual",
  "panel": "OLED_DEFAULT",
  "worst_patches": {
    "indices": [1234, 5678, ...],
    "coordinates": [[100, 200], [300, 400], ...],
    "distances": [0.0892, 0.0761, ...]
  },
  "good_threshold": {
    "value": 0.01,
    "count": 3072,
    "percentage": 75.0
  },
  "warning_threshold": {
    "value": 0.05,
    "count": 128,
    "percentage": 3.1
  }
}
```

## 🛠️ Advanced Features

### Batch Processing

```python
from spade import SPADEAnalyzer, SPADEConfig

config = SPADEConfig()
analyzer = SPADEAnalyzer(config)

image_pairs = [...]  # List of (ref, cap) paths

for i, (ref, cap) in enumerate(image_pairs):
    results = analyzer.analyze(ref, cap, f"output_{i}")
    print(f"Batch {i}: mean={results['mean_distance']:.4f}")
```

### Memory Estimation

```python
from utils import estimate_memory_usage

mem_est = estimate_memory_usage(
    height=4000,
    width=6000,
    channels=3,
    patch_size=64,
    stride=64
)

print(f"Estimated memory: {mem_est['total_mb']:.1f} MB")
print(f"Recommendation: {mem_est['recommendation']}")
```

### Performance Profiling

```python
from utils import Timer

with Timer("Patch extraction"):
    # Your code here
    pass
```

## 🔧 Migration from SPADE 1.x

```python
# Old way (SPADE 1.x)
from SPADE_5 import validate_oled_display

result = validate_oled_display(ref, cap, output, config_dict)

# New way (SPADE 2.0)
from spade import quick_analysis

results = quick_analysis(ref, cap, output)
```

### Converting Legacy Config

```python
from spade.config import load_legacy_config

# Load old flat config
config = load_legacy_config("old_spade_config.json")

# Use with new framework
from spade import run_analysis
results = run_analysis(ref, cap, output, config)
```

## 📊 HTML Report Generation

Generate professional HTML reports with one line:

```python
from spade import quick_analysis, generate_report

# Run analysis
results = quick_analysis("ref.png", "cap.png", "output")

# Generate beautiful HTML report
report = generate_report("output")
```

**Report includes:**
- 📈 Complete statistics with quality grading (A+ to F)
- 🎨 All visualizations embedded
- 🗺️ Spatial maps and heatmaps
- ⚠️ Top 20 problem areas identified
- 📱 Responsive design (works on mobile)
- 🔗 Self-contained single HTML file

See [REPORT_GENERATOR_GUIDE.md](REPORT_GENERATOR_GUIDE.md) for details.

## 📦 Installation

```bash
# From source
git clone https://github.com/yourorg/spade
cd spade
pip install -e .

# Dependencies
pip install numpy pillow matplotlib
```

## 🤝 Contributing

### Adding a New Metric

1. Implement `MetricPlugin` base class
2. Register with `register_metric()`
3. Add tests and documentation

### Adding a New Panel

1. Implement `PanelPlugin` base class
2. Register with `register_panel()`
3. Add to panel_matrices.json

## 📄 License

MIT License - see LICENSE file

## 🙏 Acknowledgments

Built for OLED display quality validation and uniformity testing at Apple.
