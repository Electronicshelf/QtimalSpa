# SPADE 2.0 Architecture Documentation

## 📁 Project Structure

```
spade_improved/
├── README.md                          # Main documentation
├── setup.py                           # Installation script (to be added)
├── requirements.txt                   # Dependencies (to be added)
│
├── spade/                            # Main package
│   ├── __init__.py                   # Clean API exports
│   ├── config.py                     # Configuration management
│   ├── framework.py                  # Main orchestration
│   │
│   ├── core/                         # Core components
│   │   ├── __init__.py
│   │   ├── base.py                   # Base plugin classes
│   │   ├── metrics.py                # Metric implementations
│   │   └── patches.py                # Patch extraction
│   │
│   └── plugins/                      # Plugin system
│       ├── __init__.py
│       ├── panels/                   # Panel plugins
│       │   └── __init__.py          # Panel implementations
│       ├── metrics/                  # Custom metric plugins
│       │   └── __init__.py
│       └── visualizations/           # Visualization plugins
│           └── __init__.py
│
├── utils/                            # Utility modules
│   ├── __init__.py
│   ├── image_utils.py               # Image I/O and preprocessing
│   └── performance.py               # Performance optimization
│
└── examples/                         # Example scripts
    ├── basic_examples.py            # Basic usage examples
    ├── advanced_examples.py         # Advanced/plugin examples
    ├── default_config.json          # Example configuration
    └── panel_matrices.json          # Panel definitions (to be copied)
```

## 🏗️ Architecture Overview

### Design Principles

1. **Modularity**: Each component has a single responsibility
2. **Extensibility**: Plugin system for easy customization
3. **Performance**: Vectorization, caching, batch processing
4. **Usability**: Clean API, sensible defaults, presets
5. **Maintainability**: Type hints, documentation, tests

### Core Components

#### 1. Configuration System (`config.py`)

**Purpose**: Hierarchical configuration with validation

**Key Classes**:
- `SPADEConfig`: Master configuration
- `PatchConfig`: Patch extraction settings
- `MetricConfig`: Metric computation settings
- `PanelConfig`: Color space settings
- `VisualizationConfig`: Output settings
- `AnalysisConfig`: Analysis parameters
- `PerformanceConfig`: Performance tuning

**Features**:
- Nested dataclass structure
- JSON serialization
- Validation with error messages
- Preset configurations
- Legacy config support

#### 2. Plugin System (`core/base.py`)

**Purpose**: Extensible architecture for custom components

**Base Classes**:
- `MetricPlugin`: Perceptual metrics
- `PanelPlugin`: Color space transforms
- `VisualizationPlugin`: Output generation
- `PatchExtractor`: Patch extraction strategies

**Features**:
- Abstract base classes with clear interfaces
- Global registry for plugin discovery
- Simple registration API
- Runtime plugin creation

#### 3. Framework (`framework.py`)

**Purpose**: Main orchestration and workflow

**Key Classes**:
- `SPADEAnalyzer`: Main analysis class

**Features**:
- End-to-end workflow management
- Component initialization
- Memory estimation
- Progress tracking
- Result aggregation

#### 4. Metrics (`core/metrics.py`)

**Purpose**: Perceptual distance metrics

**Implementations**:
- L1/L2: Simple distance metrics
- SSIM: Structural similarity
- PSNR: Signal-to-noise ratio
- Perceptual: Luma/chroma weighted
- Adaptive: Content-aware
- Weighted: Multi-metric combination

**Features**:
- Vectorized operations
- Batch processing support
- Configurable parameters
- Easy to extend

#### 5. Patches (`core/patches.py`)

**Purpose**: Efficient patch extraction and management

**Classes**:
- `EdgeAnchoredExtractor`: Production extractor
- `UniformGridExtractor`: Simple grid
- `PatchCache`: Memory-efficient caching

**Features**:
- Vectorized extraction
- Multiple strategies
- Grid building for visualization
- Statistics computation

#### 6. Panels (`plugins/panels/`)

**Purpose**: Color space transformations

**Implementations**:
- `SRGBPanel`: Standard RGB
- `P3APanel`: Display P3
- `CustomPanel`: User-defined
- JSON-based panels

**Features**:
- 3x3 matrix transforms
- Gamma correction
- Easy to extend
- Registry system

#### 7. Image Utilities (`utils/image_utils.py`)

**Purpose**: Image I/O and preprocessing

**Functions**:
- `load_image()`: Multi-format loading
- `save_image()`: Optimized saving
- `preprocess_image_pair()`: Validation & prep
- `compute_image_stats()`: Analysis
- Image transforms (resize, crop, gamma)

**Features**:
- Automatic dtype conversion
- Validation checks
- PIL integration
- Memory-efficient

#### 8. Performance (`utils/performance.py`)

**Purpose**: Performance optimization

**Tools**:
- `Timer`: Profiling context manager
- `BatchProcessor`: Memory-efficient batching
- `MemoryEfficientCache`: LRU caching
- `ProgressTracker`: Progress indication
- `estimate_memory_usage()`: Planning

**Features**:
- Parallel processing support
- Numpy optimization
- Memory management
- Profiling decorators

## 🔄 Data Flow

```
1. Configuration
   └─> SPADEConfig → validate() → SPADEAnalyzer

2. Image Loading
   └─> load_image() → preprocess_image_pair() → validate_image_pair()

3. Panel Transform
   └─> PanelPlugin.to_linear() → apply_transform()

4. Patch Extraction
   └─> PatchExtractor.extract_coordinates() → extract_patches_vectorized()

5. Metric Computation
   └─> MetricPlugin.compute() → [batch processing] → distances

6. Analysis
   └─> analyze_distances() → statistics + worst patches + thresholds

7. Visualization
   └─> generate_visualizations() → [heatmaps, luma, contours]

8. Output
   └─> save results + visualizations + summary.json
```

## 🔌 Plugin Development Guide

### Creating a Custom Metric

```python
from spade import MetricPlugin, register_metric
import numpy as np

class MyMetric(MetricPlugin):
    def __init__(self, config=None):
        super().__init__("my_metric", config)
        self.param = self.config.get("param", 1.0)
    
    def compute(self, ref_patches, cap_patches):
        # Your implementation
        diff = ref_patches - cap_patches
        # ... compute distance ...
        return distances  # (N,) array
    
    @property
    def requires_gpu(self):
        return False  # or True if GPU-accelerated

# Register
register_metric(MyMetric(config={"param": 2.0}))

# Use
config = SPADEConfig()
config.metric.metric_name = "my_metric"
```

### Creating a Custom Panel

```python
from spade import PanelPlugin, register_panel
import numpy as np

class MyPanel(PanelPlugin):
    def __init__(self):
        matrix = np.array([...])  # 3x3 linear transform
        super().__init__("MY_PANEL", matrix=matrix)
    
    def to_linear(self, rgb):
        # Gamma correction: non-linear → linear
        return rgb ** 2.2
    
    def from_linear(self, rgb):
        # Inverse gamma: linear → non-linear
        return rgb ** (1/2.2)

# Register
register_panel(MyPanel())

# Use
config = SPADEConfig()
config.panel.panel_name = "MY_PANEL"
```

## 🚀 Performance Optimizations

### Implemented Optimizations

1. **Vectorization**
   - Numpy operations on full arrays
   - No Python loops over patches
   - Advanced indexing for extraction

2. **Batch Processing**
   - Configurable batch sizes
   - Memory-aware batching
   - Progress tracking

3. **Caching**
   - LRU cache for patches
   - Memory limits
   - Automatic eviction

4. **Lazy Loading**
   - Components created on demand
   - Visualizations only if requested
   - Panel transforms only if needed

5. **Parallel Processing**
   - Multi-threaded/multi-process support
   - Configurable worker count
   - Batch-level parallelism

### Performance Tips

```python
# For speed
config = load_preset("fast")
config.patch.stride = 128          # Fewer patches
config.metric.metric_name = "l1"   # Fastest metric
config.performance.batch_size = 1024

# For quality
config = load_preset("quality")
config.patch.stride = 32           # More patches
config.metric.use_multi_metric = True
config.metric.multi_metrics = ["l2", "ssim", "perceptual"]

# For large images
config.performance.use_cache = True
config.performance.cache_size_mb = 1000
config.performance.batch_size = 256
```

## 📊 Comparison: Old vs New

### API Simplification

**Old (SPADE 1.x)**:
```python
from SPADE_5 import validate_oled_display

config = {
    "patch_size": 64,
    "stride": 64,
    "edge_band": 64,
    "device": "cpu",
    "batch": 512,
    "alpha": 0.4,
    "heatmap_style": "all",
    # ... 15+ more parameters
}

result = validate_oled_display(ref_path, cap_path, output_dir, config)
```

**New (SPADE 2.0)**:
```python
from spade import quick_analysis

# Quick start
results = quick_analysis(ref_path, cap_path, output_dir)

# With customization
from spade import SPADEConfig, run_analysis

config = SPADEConfig()
config.patch.stride = 32
config.metric.metric_name = "perceptual"

results = run_analysis(ref_path, cap_path, output_dir, config)
```

### Extensibility

**Old**: Requires modifying core files

**New**: Plugin system
```python
# Create plugin
class MyMetric(MetricPlugin):
    def compute(self, ref, cap):
        # Your code
        pass

# Register and use
register_metric(MyMetric())
config.metric.metric_name = "my_metric"
```

### Configuration Management

**Old**: Flat dictionary, no validation

**New**: Hierarchical, validated, serializable
```python
config = SPADEConfig()
config.patch.stride = 32           # Organized
config.save("config.json")         # Serializable
errors = config.validate()         # Validated
```

## 🔧 Migration Guide

See `MIGRATION.md` for detailed migration instructions from SPADE 1.x to 2.0.

## 📝 Next Steps

1. **Add Tests**
   - Unit tests for all components
   - Integration tests
   - Performance benchmarks

2. **Add CLI**
   - Command-line interface
   - Argument parsing
   - Multiple file processing

3. **Enhanced Visualizations**
   - Interactive plots
   - More visualization types
   - Customizable styles

4. **GPU Support**
   - CUDA/PyTorch integration
   - GPU-accelerated metrics
   - Memory management

5. **Documentation**
   - API reference
   - Tutorial notebooks
   - Video guides

## 📄 License

MIT License - see LICENSE file for details
