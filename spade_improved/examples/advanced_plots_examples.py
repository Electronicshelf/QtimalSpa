"""
Advanced plots examples for SPADE analysis.
"""

from pathlib import Path
import sys

# Add parent directory to path (for running from examples/ directory)
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from spade import SPADEConfig, run_analysis
from spade.advanced_plots import generate_all_plots, DisplayVisualizer
from utils.image_utils import load_image


def example_generate_all_plots():
    """Generate all advanced plots in one call."""
    ref_path = "ref.png"
    cap_path = "cap.png"
    output_dir = "output_advanced_plots"

    config = SPADEConfig()
    config.analysis.return_patch_data = True

    results = run_analysis(ref_path, cap_path, output_dir, config)
    ref_img = load_image(ref_path)
    cap_img = load_image(cap_path)

    plot_paths = generate_all_plots(results, ref_img, cap_img, f"{output_dir}/advanced_plots")
    print(f"Generated {len(plot_paths)} plot types:")
    for name, path in plot_paths.items():
        print(f"  {name}: {path}")


def example_individual_plots():
    """Generate selected plots directly."""
    ref_path = "ref.png"
    cap_path = "cap.png"
    output_dir = "output_advanced_plots"

    config = SPADEConfig()
    config.analysis.return_patch_data = True
    results = run_analysis(ref_path, cap_path, output_dir, config)

    coords = results["patch_coords"]
    distances = results["patch_distances"]
    image_shape = results["image_shape"]

    viz = DisplayVisualizer()
    viz.plot_cdf(distances, thresholds=[0.01, 0.05], save_path=f"{output_dir}/cdf.png")
    viz.plot_box_regions(coords, distances, image_shape, grid_size=(3, 3),
                         save_path=f"{output_dir}/box_regions.png",
                         patch_size=results.get("patch_size"))
    viz.plot_scatter_2d(coords, distances, image_shape, save_path=f"{output_dir}/scatter.png",
                        patch_size=results.get("patch_size"))


if __name__ == "__main__":
    print("Advanced Plots Examples")
    print("========================")
    print("Note: update ref.png/cap.png to your images before running.")
    # example_generate_all_plots()
    # example_individual_plots()
