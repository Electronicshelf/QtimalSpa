# HTML Report Generator - User Guide

## 📊 Overview

The SPADE HTML Report Generator creates professional, self-contained HTML reports from your analysis results. Each report includes:

- **📈 Statistical Analysis** - Mean, median, std dev, min/max
- **🎨 Visualizations** - All generated images embedded
- **⚠️ Problem Areas** - Top worst patches identified
- **✅ Quality Assessment** - A+ to F grading system
- **📱 Responsive Design** - Works on desktop, tablet, mobile
- **🔗 Single File** - All assets embedded (easy to share)

## 🚀 Quick Start

### Basic Usage

```python
from spade import quick_analysis, generate_report

# Run analysis
results = quick_analysis("ref.png", "cap.png", "output")

# Generate report
report_path = generate_report("output")

print(f"Report: {report_path}")
# Opens: output/analysis_report.html
```

### Command Line

```bash
# After running SPADE analysis
python generate_report.py ./output

# Custom filename
python generate_report.py ./output --output my_report.html
```

## 📋 Report Sections

### 1. Header
- **Title**: SPADE Analysis Report
- **Timestamp**: Generation date/time
- **Quality Badge**: A+, A, B, C, or F grade
- **Gradient Design**: Professional purple gradient

### 2. Navigation Menu
Sticky menu with quick links to:
- 📊 Overview
- 📈 Statistics
- 🎨 Visualizations
- 🗺️ Spatial Maps
- ⚠️ Problem Areas
- ℹ️ Metadata

### 3. Overview Section
**Key Metrics Cards:**
- Mean Distance
- Standard Deviation
- Median Distance
- Min Distance (green card)
- Max Distance (red card)
- Total Patches

**Quality Assessment:**
- Letter grade (A+ to F)
- Explanation text

### 4. Statistics Section
**Distribution Analysis Table:**
- All distance metrics explained
- Statistical interpretation

**Threshold Analysis:**
- Progress bars for each threshold
- Percentage of patches exceeding limits
- Color-coded (green/orange/red)

### 5. Visualizations Section
**Spatial Heatmap:**
- Full-size embedded image
- Color-coded patch distances
- Description text

**Contour Map:**
- Full-size embedded image
- Spatial quality distribution
- Contour line labels

### 6. Spatial Maps Section
**Grid of 4 Maps:**
1. Reference Luma Map
2. Capture Luma Map
3. Reference Log Radiance
4. Capture Log Radiance

Each with caption and description.

### 7. Problem Areas Section
**Top 20 Worst Patches Table:**
- Rank
- Patch index
- Coordinates (Y, X)
- Distance value

### 8. Metadata Section
**Configuration Table:**
- Analysis date
- Metric used
- Panel color space
- Total patches
- Output directory
- Framework version

**Links to Raw Data:**
- Reference to analysis_summary.json

### 9. Footer
- SPADE branding
- Generation info
- Copyright notice

## 🎨 Design Features

### Color Scheme
```css
Primary: #667eea → #764ba2 (purple gradient)
Background: #f5f5f5 (light gray)
Text: #333 (dark gray)
Cards: white with subtle shadows
```

### Quality Badge Colors
- **Excellent (A+)**: Green (#48bb78)
- **Very Good (A)**: Teal (#38b2ac)
- **Good (B)**: Teal (#38b2ac)
- **Acceptable (C)**: Orange (#ed8936)
- **Issues (F)**: Red (#f56565)

### Statistical Cards
- **Good metrics**: Green left border
- **Warning metrics**: Orange left border
- **Error metrics**: Red left border
- **Neutral**: Purple left border

### Progress Bars
- **Good (<5%)**: Green gradient
- **Warning (5-20%)**: Orange gradient
- **Error (>20%)**: Red gradient

## 📊 Quality Grading System

Reports automatically assign quality grades based on mean distance:

| Grade | Mean Distance | Description |
|-------|---------------|-------------|
| **A+** | < 0.005 | Excellent quality |
| **A** | 0.005 - 0.01 | Very good quality |
| **B** | 0.01 - 0.02 | Good quality |
| **C** | 0.02 - 0.05 | Acceptable quality |
| **F** | > 0.05 | Issues detected |

## 💻 Advanced Usage

### Custom Filename

```python
from spade.report_generator import generate_report

report_path = generate_report(
    "output",
    output_filename="custom_report.html"
)
```

### Manual Results

```python
from spade.report_generator import generate_report

# Provide results manually (without analysis_summary.json)
custom_results = {
    'mean_distance': 0.0234,
    'std_distance': 0.0156,
    'min_distance': 0.0001,
    'max_distance': 0.0892,
    'median_distance': 0.0198,
    'num_patches': 4096,
    'metric': 'perceptual',
    'panel': 'P3A',
    # ... more fields
}

report_path = generate_report(
    "output",
    results=custom_results
)
```

### Using the Class Directly

```python
from spade.report_generator import SPADEReportGenerator

# Create generator
generator = SPADEReportGenerator("output_dir", results)

# Generate report
report_path = generator.generate("my_report.html")
```

### Batch Report Generation

```python
from spade import quick_analysis
from spade.report_generator import generate_report

test_cases = [
    ("ref1.png", "cap1.png", "output1"),
    ("ref2.png", "cap2.png", "output2"),
    ("ref3.png", "cap3.png", "output3"),
]

for ref, cap, output in test_cases:
    # Run analysis
    results = quick_analysis(ref, cap, output)
    
    # Generate report
    report = generate_report(output)
    
    print(f"Report: {report}")
```

## 📱 Responsive Design

Reports adapt to screen size:

### Desktop (>768px)
- Full navigation menu (horizontal)
- Multi-column stats grid
- Side-by-side image grid
- Large visualizations

### Tablet/Mobile (<768px)
- Collapsible navigation (vertical)
- Single-column stats
- Stacked images
- Touch-friendly buttons

## 🔧 Customization

### Modifying Styles

The report uses embedded CSS. To customize:

```python
from spade.report_generator import SPADEReportGenerator

class CustomReportGenerator(SPADEReportGenerator):
    def _get_css(self):
        # Override CSS
        custom_css = super()._get_css()
        custom_css += """
        <style>
            .header {
                background: linear-gradient(135deg, #your-colors);
            }
        </style>
        """
        return custom_css

# Use custom generator
generator = CustomReportGenerator("output", results)
report = generator.generate()
```

### Adding Sections

```python
class ExtendedReportGenerator(SPADEReportGenerator):
    def _generate_custom_section(self):
        return """
        <section class="section">
            <h2>My Custom Section</h2>
            <p>Custom content here</p>
        </section>
        """
    
    def generate(self, filename="report.html"):
        # Call parent to get base HTML
        html = super().generate(filename)
        # Modify as needed
        return html
```

## 🖼️ Image Embedding

All images are embedded as base64 data URIs:

**Benefits:**
- ✅ Single file (no external dependencies)
- ✅ Easy to email/share
- ✅ Works offline
- ✅ No broken image links

**Limitations:**
- File size increases (~33% for base64)
- Not ideal for huge images (>10MB)

### Manual Image Control

```python
generator = SPADEReportGenerator("output", results)

# Access image encoding
image_b64 = generator._encode_image("path/to/image.png")

# Use in custom HTML
custom_html = f'<img src="{image_b64}" alt="Custom">'
```

## 📄 Report File Structure

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width">
    <title>SPADE Analysis Report</title>
    <style>
        /* Embedded CSS (~300 lines) */
    </style>
</head>
<body>
    <div class="container">
        <!-- Header with gradient -->
        <!-- Navigation menu -->
        <div class="content">
            <!-- All sections -->
        </div>
        <!-- Footer -->
    </div>
    <script>
        /* Smooth scrolling JS */
    </script>
</body>
</html>
```

**Typical File Size:**
- With visualizations: 2-5 MB
- Without images: 50-100 KB

## 🔍 Troubleshooting

### Missing Images

**Problem:** Images don't appear in report
**Solution:** Make sure SPADE analysis generated the visualizations

```python
# Enable all visualizations
config.visualization.generate_heatmaps = True
config.visualization.generate_luma_maps = True
config.visualization.generate_log_radiance = True
config.visualization.generate_contours = True
```

### Missing Statistics

**Problem:** Threshold sections missing
**Solution:** Ensure analysis config includes thresholds

```python
config.analysis.thresholds = {
    "good": 0.01,
    "warning": 0.05,
}
```

### File Not Found

**Problem:** `analysis_summary.json not found`
**Solution:** Run SPADE analysis first or provide results manually

```python
# Option 1: Run analysis
results = quick_analysis(ref, cap, output)
generate_report(output)

# Option 2: Provide results
generate_report(output, results=my_results)
```

## 🎯 Best Practices

### 1. Always Enable Visualizations

```python
config = SPADEConfig()
config.visualization.generate_heatmaps = True
config.visualization.generate_luma_maps = True
config.visualization.generate_log_radiance = True
config.visualization.generate_contours = True

results = run_analysis(ref, cap, output, config)
generate_report(output)
```

### 2. Use Descriptive Output Directories

```python
# Good
output_dir = f"analysis_{device_id}_{timestamp}"

# Better
output_dir = f"panel_{panel_id}_test_{test_id}_{date}"
```

### 3. Archive Reports with Data

```python
import shutil

# After analysis and report generation
shutil.make_archive(f"archive_{timestamp}", 'zip', output_dir)
```

### 4. Automated Reporting Pipeline

```python
def analyze_and_report(ref, cap, output):
    """Complete analysis with automatic reporting."""
    # Configure
    config = SPADEConfig()
    config.metric.metric_name = "perceptual"
    config.visualization.generate_heatmaps = True
    
    # Analyze
    results = run_analysis(ref, cap, output, config)
    
    # Report
    report = generate_report(output)
    
    # Log
    quality = "PASS" if results['mean_distance'] < 0.01 else "FAIL"
    print(f"{quality}: {results['mean_distance']:.6f}")
    print(f"Report: {report}")
    
    return results, report
```

## 📚 Examples

See `examples/report_generation_examples.py` for:
- Basic report generation
- Custom filenames
- Manual results
- Batch processing
- Integrated workflows
- Automation examples

## 🔗 Related Documentation

- [QUICKSTART.md](QUICKSTART.md) - Get started with SPADE
- [README.md](README.md) - Full API reference
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design

## 💡 Tips & Tricks

### Viewing Reports

```bash
# Open in default browser (macOS)
open output/analysis_report.html

# Open in default browser (Linux)
xdg-open output/analysis_report.html

# Open in default browser (Windows)
start output/analysis_report.html
```

### Sharing Reports

```bash
# Email the single HTML file
# - Self-contained, no external files needed
# - Recipient can open directly in browser
# - No installation required
```

### Print to PDF

1. Open report in browser
2. File → Print
3. Select "Save as PDF"
4. Print-friendly styles automatically applied

### Multiple Analyses Comparison

Create a master index.html linking to individual reports:

```html
<!DOCTYPE html>
<html>
<head><title>Test Results Index</title></head>
<body>
    <h1>SPADE Test Results</h1>
    <ul>
        <li><a href="test1/analysis_report.html">Test 1</a></li>
        <li><a href="test2/analysis_report.html">Test 2</a></li>
        <li><a href="test3/analysis_report.html">Test 3</a></li>
    </ul>
</body>
</html>
```

---

**Questions or issues?** Check the examples in `examples/report_generation_examples.py`
