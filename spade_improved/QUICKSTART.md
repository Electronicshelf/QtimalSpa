# SPADE 2.0 Quick Start Guide

## 🎯 5-Minute Quick Start

### Installation

```bash
cd spade_improved
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Your First Analysis

```python
from spade import quick_analysis

results = quick_analysis(
    ref_path="reference.png",
    cap_path="capture.png", 
    output_dir="output"
)

print(f"Mean distance: {results['mean_distance']:.4f}")
print(f"Max distance: {results['max_distance']:.4f}")
```

That's it! Check the `output/` directory for:
- `analysis_summary.json` - Complete statistics
- `heatmap.png` - Visual analysis
- Other visualizations

## 📊 Common Use Cases

### 1. Quick Quality Check

```python
from spade import quick_analysis

# Fast analysis for quick testing
results = quick_analysis(ref, cap, output, preset="fast")

if results['mean_distance'] < 0.01:
    print("✓ Display quality: Excellent")
elif results['mean_distance'] < 0.05:
    print("⚠ Display quality: Acceptable")
else:
    print("✗ Display quality: Issues detected")
```

### 2. Production Validation

```python
from spade import SPADEConfig, run_analysis

config = SPADEConfig()
config.patch.stride = 32              # Fine-grained
config.metric.metric_name = "perceptual"
config.panel.panel_name = "P3A"

results = run_analysis(ref, cap, output, config)

# Check against thresholds
good_pct = results['good_threshold']['percentage']
if good_pct > 95:
    print("✓ PASS: 95%+ patches within tolerance")
```

### 3. Batch Processing

```python
from spade import SPADEAnalyzer, SPADEConfig

config = SPADEConfig()
analyzer = SPADEAnalyzer(config)

test_cases = [
    ("ref1.png", "cap1.png", "output1"),
    ("ref2.png", "cap2.png", "output2"),
    # ... more test cases
]

for ref, cap, output in test_cases:
    results = analyzer.analyze(ref, cap, output)
    print(f"{output}: {results['mean_distance']:.4f}")
```

### 4. Custom Analysis

```python
from spade import SPADEConfig, run_analysis

config = SPADEConfig()

# Customize everything
config.patch.patch_size = 64
config.patch.stride = 64
config.metric.metric_name = "perceptual"
config.panel.panel_name = "OLED_DEFAULT"
config.visualization.heatmap_alpha = 0.5
config.analysis.bad_percentile = 98.0
config.performance.batch_size = 1024

results = run_analysis(ref, cap, output, config)
```

## 🔧 Configuration Presets

```python
from spade import load_preset

# Three built-in presets
default = load_preset("default")   # Balanced
fast = load_preset("fast")         # Speed > quality
quality = load_preset("quality")   # Quality > speed
```

### Preset Comparison

| Setting | Default | Fast | Quality |
|---------|---------|------|---------|
| Stride | 64 | 128 | 32 |
| Metric | L2 | L1 | Multi (L2+SSIM+Perceptual) |
| Batch Size | 512 | 1024 | 256 |
| Log Radiance | ✓ | ✗ | ✓ |
| Contours | ✓ | ✗ | ✓ |

## 📝 Configuration Files

### Save Your Config

```python
from spade import SPADEConfig

config = SPADEConfig()
# ... customize ...
config.save("my_analysis.json")
```

### Load Config

```python
from spade import SPADEConfig, run_analysis

config = SPADEConfig.load("my_analysis.json")
results = run_analysis(ref, cap, output, config)
```

### Example Config File

```json
{
  "patch": {
    "patch_size": 64,
    "stride": 64
  },
  "metric": {
    "metric_name": "perceptual"
  },
  "panel": {
    "panel_name": "P3A"
  }
}
```

## 🎨 Available Metrics

Quick reference for metric selection:

| Metric | Speed | Accuracy | Use Case |
|--------|-------|----------|----------|
| **l1** | ⚡⚡⚡ | ⭐⭐ | Quick tests |
| **l2** | ⚡⚡⚡ | ⭐⭐⭐ | General purpose |
| **ssim** | ⚡⚡ | ⭐⭐⭐⭐ | Structural quality |
| **perceptual** | ⚡⚡ | ⭐⭐⭐⭐ | Visual quality |
| **adaptive** | ⚡⚡ | ⭐⭐⭐⭐ | Content-aware |

```python
config.metric.metric_name = "perceptual"  # Recommended
```

## 🖥️ Panel Color Spaces

```python
# Built-in panels
config.panel.panel_name = "SRGB"          # Standard RGB
config.panel.panel_name = "P3A"           # Display P3
config.panel.panel_name = "OLED_DEFAULT"  # Default OLED (P3A)

# Custom panel from JSON
config.panel.panel_name = "MY_PANEL"
config.panel.panel_json_path = "panels.json"
```

## 📊 Understanding Results

### Key Metrics

```python
results = run_analysis(...)

# Overall quality
mean_dist = results['mean_distance']      # Average error
max_dist = results['max_distance']        # Worst error

# Worst patches
worst = results['worst_patches']
coords = worst['coordinates']             # Where problems are
distances = worst['distances']            # How bad

# Threshold analysis
good = results['good_threshold']
print(f"{good['percentage']:.1f}% within tolerance")
```

### Quality Interpretation

```python
mean = results['mean_distance']

if mean < 0.005:
    grade = "A+ (Excellent)"
elif mean < 0.01:
    grade = "A (Very Good)"
elif mean < 0.02:
    grade = "B (Good)"
elif mean < 0.05:
    grade = "C (Acceptable)"
else:
    grade = "F (Issues Detected)"
```

## ⚡ Performance Tips

### For Large Images (>10MP)

```python
config = SPADEConfig()
config.patch.stride = 128               # Fewer patches
config.performance.batch_size = 256     # Smaller batches
config.performance.use_cache = True     # Enable caching
config.performance.cache_size_mb = 1000
config.visualization.generate_contours = False  # Skip slow viz
```

### For Small Images (<2MP)

```python
config = SPADEConfig()
config.patch.stride = 32                # More coverage
config.performance.batch_size = 1024    # Larger batches
```

### Estimate Before Running

```python
from utils import estimate_memory_usage

mem = estimate_memory_usage(
    height=4000, width=6000, channels=3,
    patch_size=64, stride=64
)

print(f"Estimated: {mem['total_mb']:.0f} MB")
print(f"Patches: {mem['num_patches']}")
```

## 🔍 Troubleshooting

### Image Size Mismatch

```python
# Error: "Shape mismatch: ref (4000, 6000, 3) vs cap (4000, 6000, 4)"

# Solution: Images will be cropped to match channels automatically
# Or use:
from utils import preprocess_image_pair
ref, cap = preprocess_image_pair(ref, cap, align_channels=True)
```

### Memory Issues

```python
# Reduce batch size
config.performance.batch_size = 128

# Increase stride (fewer patches)
config.patch.stride = 128

# Disable some visualizations
config.visualization.generate_log_radiance = False
config.visualization.generate_contours = False
```

### Slow Performance

```python
# Use fast preset
config = load_preset("fast")

# Or optimize manually
config.metric.metric_name = "l1"        # Fastest metric
config.patch.stride = 128               # Fewer patches
config.performance.batch_size = 1024    # Larger batches
```

## 📚 Next Steps

- Read [`README.md`](README.md) for full documentation
- See [`examples/basic_examples.py`](examples/basic_examples.py) for more examples
- Check [`ARCHITECTURE.md`](ARCHITECTURE.md) for system design
- Try [`examples/advanced_examples.py`](examples/advanced_examples.py) for custom plugins

## 💬 Getting Help

1. Check error messages carefully
2. Use `config.validate()` to check configuration
3. Enable verbose output: set `verbose=True` in Timer contexts
4. Review examples that match your use case
5. Check the comprehensive README

Happy analyzing! 🚀
