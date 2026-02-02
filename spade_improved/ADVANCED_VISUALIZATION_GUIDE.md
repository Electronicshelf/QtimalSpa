## Advanced Visualization Guide for Display Analysis

### Overview

Beyond histograms, SPADE supports 7 advanced plot types for comprehensive
display quality analysis.

### Quick Reference

| Plot Type | Best For | Key Insight |
|-----------|----------|-------------|
| CDF | Pass/fail criteria | What percent below threshold? |
| Box Regions | Regional comparison | Which area is worst? |
| Luminance Profiles | Gradient detection | Is there brightness falloff? |
| 2D Scatter | Spatial defects | Where are problems located? |
| KDE | Distribution shape | Normal or skewed? |
| Percentile Maps | Outlier detection | Where are worst 5%? |
| Error Dist 2D | Smooth spatial view | Heatmap alternative |

---

## 1. CDF (Cumulative Distribution Function)

### What It Shows
Percentage of the display that falls below each quality level.

### When to Use
- Setting acceptance criteria ("95% must be < 0.01")
- Comparing different displays
- Before/after compensation comparison
- Creating quality specs

### How to Read
- X-axis: quality distance
- Y-axis: cumulative percentage (0-100%)
- Steep curve: uniform quality
- Flat sections: wide quality range

### Example Question
"What percentage of the display has quality distance below 0.01?"

Answer: read Y value at X=0.01.

### Code
```python
from spade.advanced_plots import DisplayVisualizer

viz = DisplayVisualizer()
viz.plot_cdf(
    distances,
    thresholds=[0.01, 0.05, 0.1],  # Your quality gates
    save_path="cdf.png"
)
```

### Pro Tips
- Steeper = more uniform
- Look for inflection points (quality changes)
- Compare multiple CDFs to see improvements
- Use for setting realistic thresholds

---

## 2. Box Plots by Region

### What It Shows
Quality distribution comparison across display regions (e.g., corners, edges, center).

### When to Use
- Finding worst region
- Checking edge effects
- Zone-by-zone quality control
- Identifying systematic issues

### How to Read
- Box: 25th-75th percentile
- Line in box: median
- Whiskers: min/max (excluding outliers)
- Dots: outliers
- Height: quality variation

### Example Question
"Is the top-left corner worse than the center?"

Answer: compare box heights and medians.

### Code
```python
viz.plot_box_regions(
    coords, distances, image_shape,
    grid_size=(3, 3),  # 3x3 grid = 9 regions
    save_path="box_regions.png"
)
```

### Pro Tips
- Try different grid sizes (2x2, 3x3, 4x4)
- Taller boxes = more variation
- Overlapping boxes = similar quality
- Red line shows overall mean for reference

---

## 3. Luminance Profiles

### What It Shows
Average luminance along horizontal and vertical axes.

### When to Use
- Detecting gradients
- Finding edge dimming/brightening
- Checking vignetting
- Verifying uniformity compensation

### How to Read
- Top plot: left-to-right variation
- Bottom plot: top-to-bottom variation
- Flat line: uniform
- Slope: gradient present
- Dips/peaks: local issues

### Example Question
"Is there a brightness falloff toward the edges?"

Answer: look for slopes in profile curves.

### Code
```python
viz.plot_luminance_profiles(
    capture_image,
    coords,
    save_path="profiles.png"
)
```

### Pro Tips
- Perfect uniformity = flat line
- Look for symmetry (or lack of it)
- Compare ref vs cap profiles
- Useful for tuning compensation algorithms

---

## 4. 2D Scatter Plot

### What It Shows
Exact spatial location of each patch, colored by quality.

### When to Use
- Pinpointing defects
- Showing problem locations to team
- Identifying spatial patterns
- Correlating with physical features

### How to Read
- Green dots: good quality
- Yellow/orange: medium quality
- Red dots: poor quality
- Red circles: top 10 worst
- Clustering: systematic issue

### Example Question
"Where exactly are the worst 10 patches?"

Answer: look at red circled dots.

### Code
```python
viz.plot_scatter_2d(
    coords, distances, image_shape,
    save_path="scatter.png"
)
```

### Pro Tips
- Most intuitive visualization
- Great for presentations
- Easy to correlate with physical display
- Complements heatmap view

---

## 5. KDE (Kernel Density Estimation)

### What It Shows
Smooth probability distribution of quality values.

### When to Use
- Understanding distribution shape
- Detecting bimodal distributions (two populations)
- Statistical analysis
- Reporting and documentation

### How to Read
- Peak height: most common values
- Peak location: typical quality
- Width: spread of values
- Multiple peaks: multiple quality populations
- Skew: asymmetric quality

### Example Question
"Is quality normally distributed or skewed?"

Answer: look at curve shape.

### Code
```python
viz.plot_kde(
    distances,
    save_path="kde.png"
)
```

### Pro Tips
- Better than histogram for seeing shape
- Bimodal = two different quality zones
- Compare before/after KDEs
- Use with CDF for complete picture

---

## 6. Percentile Maps

### What It Shows
Spatial map of patches exceeding various percentile thresholds.

### When to Use
- Finding outliers
- Checking if outliers cluster
- Setting pass/fail zones
- Quality gate visualization

### How to Read
- Green: below threshold (good)
- Red: above threshold (bad)
- Percentage: how many fail
- Multiple maps: different strictness levels

### Example Question
"Do the worst 5% of patches cluster in one area?"

Answer: look at 95th percentile map.

### Code
```python
viz.plot_percentile_map(
    coords, distances, image_shape,
    percentiles=[50, 75, 90, 95, 99],
    save_path="percentile_maps.png"
)
```

### Pro Tips
- 50th = median split
- 95th = outliers
- 99th = extreme outliers
- Clustering = systematic problem

---

## 7. 2D Error Distribution

### What It Shows
Smooth spatial heatmap of error distribution.

### When to Use
- Alternative to heatmap
- Smooth visualization
- Presentations
- Pattern detection

### How to Read
- Color: average error in region
- Smooth gradients: good
- Sharp transitions: abrupt quality change
- Hot spots: problem areas

### Example Question
"What does the overall spatial quality pattern look like?"

Answer: visual inspection of the color map.

### Code
```python
viz.plot_error_distribution_2d(
    coords, distances, image_shape,
    save_path="error_dist_2d.png"
)
```

### Pro Tips
- Smoother than heatmap
- Good for presentations
- Shows overall patterns
- Complements 2D scatter

---

## Plot Combinations That Work Well

### Combination 1: Statistical Overview
CDF + KDE

### Combination 2: Spatial Analysis
2D Scatter + Percentile Maps

### Combination 3: Regional Analysis
Box Regions + Luminance Profiles

### Combination 4: Complete View
All 7 plots

---

## Quick Start

### Generate All Plots at Once
```python
from spade import quick_analysis
from spade.advanced_plots import generate_all_plots
from utils.image_utils import load_image

# 1. Run analysis (enable patch data for plotting)
results = quick_analysis(
    "ref.png",
    "cap.png",
    "output",
    return_patch_data=True
)

# 2. Load images
ref_img = load_image("ref.png")
cap_img = load_image("cap.png")

# 3. Generate all plots
plot_paths = generate_all_plots(
    results,
    ref_img,
    cap_img,
    "output/advanced_plots"
)

print(f"Generated {len(plot_paths)} plot types.")
```

### Generate Individual Plots
```python
from spade.advanced_plots import DisplayVisualizer

viz = DisplayVisualizer()

# Just CDF
viz.plot_cdf(distances, [0.01, 0.05], "cdf.png")

# Just box plots
viz.plot_box_regions(coords, distances, image_shape, (3, 3), "box.png")

# Just profiles
viz.plot_luminance_profiles(image, coords, "profiles.png")
```

---

## Decision Tree: Which Plot Should I Use?

START: What is your main question?

- "What percent passes threshold?" -> CDF
- "Which region is worst?" -> Box Regions
- "Is there a gradient?" -> Luminance Profiles
- "Where are defects?" -> 2D Scatter
- "Is distribution normal?" -> KDE
- "Where are outliers?" -> Percentile Maps
- "Overall spatial pattern?" -> Error Dist 2D
- "I want everything!" -> generate_all_plots()

---

## Tips for Each Use Case

### Quality Control
- CDF (pass/fail percent)
- Box Regions (regional check)
- 2D Scatter (defect locations)

### Algorithm Development
- Luminance Profiles (before/after)
- KDE (distribution changes)
- Box Regions (regional improvements)

### Manufacturing Feedback
- 2D Scatter (show locations)
- Percentile Maps (how many fail)
- Box Regions (which area needs work)

### Research/Publication
- CDF (quantitative comparison)
- KDE (statistical analysis)
- Box Regions (systematic comparison)

### Executive Summary
- CDF (one number: percent passing)
- 2D Scatter (visual impact)
- Box Regions (regional summary)

---

## Summary

### The 7 Plot Types
1. CDF - cumulative percent (pass/fail)
2. Box Regions - regional comparison
3. Luminance Profiles - gradient detection
4. 2D Scatter - spatial defect map
5. KDE - distribution shape
6. Percentile Maps - outlier locations
7. Error Dist 2D - smooth heatmap

### Key Takeaway
Different plots reveal different insights. Use combinations for comprehensive analysis.
