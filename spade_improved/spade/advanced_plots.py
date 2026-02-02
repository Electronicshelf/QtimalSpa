"""
Advanced visualization utilities for SPADE analysis.
"""

from __future__ import annotations

import os
from typing import Iterable, Dict, Optional, Tuple, List

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize, ListedColormap


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _as_numpy(values) -> np.ndarray:
    return np.asarray(values)


def _image_shape(image: np.ndarray) -> Tuple[int, int]:
    if image.ndim == 2:
        return int(image.shape[0]), int(image.shape[1])
    return int(image.shape[0]), int(image.shape[1])


def _normalize_image(image: np.ndarray) -> np.ndarray:
    arr = np.asarray(image)
    if np.issubdtype(arr.dtype, np.integer):
        scale = float(np.iinfo(arr.dtype).max)
        arr = arr.astype(np.float32) / max(scale, 1.0)
    else:
        arr = arr.astype(np.float32)
        if np.nanmax(arr) > 1.5:
            arr = arr / 255.0
    return np.clip(arr, 0.0, 1.0)


def _srgb_to_linear(rgb: np.ndarray) -> np.ndarray:
    rgb = np.asarray(rgb, dtype=np.float32)
    return np.where(
        rgb <= 0.04045,
        rgb / 12.92,
        ((rgb + 0.055) / 1.055) ** 2.4
    )


def _compute_luma(rgb: np.ndarray, linearize: bool = True) -> np.ndarray:
    rgb = _normalize_image(rgb)
    if rgb.ndim == 2:
        return rgb
    if linearize:
        rgb = _srgb_to_linear(rgb)
    return (0.2126 * rgb[..., 0] +
            0.7152 * rgb[..., 1] +
            0.0722 * rgb[..., 2])


def _robust_minmax(x: np.ndarray, lower_pct: float = 1.0, upper_pct: float = 99.0) -> Tuple[float, float]:
    arr = np.asarray(x, dtype=np.float32)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return 0.0, 1.0
    vmin = float(np.percentile(arr, lower_pct))
    vmax = float(np.percentile(arr, upper_pct))
    if not np.isfinite(vmin) or not np.isfinite(vmax) or vmax <= vmin:
        vmin = float(np.min(arr))
        vmax = float(np.max(arr) + 1e-6)
    return vmin, vmax


def _infer_stride(coords: np.ndarray) -> int:
    coords = np.asarray(coords)
    if coords.size == 0:
        return 1
    strides: List[float] = []
    for axis in (0, 1):
        vals = np.unique(coords[:, axis])
        if len(vals) > 1:
            diffs = np.diff(np.sort(vals))
            diffs = diffs[diffs > 0]
            if diffs.size:
                strides.append(float(np.median(diffs)))
    if not strides:
        return 1
    return max(1, int(round(min(strides))))


def _coords_to_centers(coords: np.ndarray, patch_size: Optional[int]) -> Tuple[np.ndarray, np.ndarray]:
    coords = np.asarray(coords, dtype=np.float32)
    if patch_size is None:
        return coords[:, 0], coords[:, 1]
    offset = float(patch_size) / 2.0
    return coords[:, 0] + offset, coords[:, 1] + offset


def _build_patch_grid(coords: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    coords = np.asarray(coords, dtype=np.int32)
    if coords.size == 0:
        return np.array([[]], dtype=np.int32), np.array([]), np.array([])
    ys = np.unique(coords[:, 0])
    xs = np.unique(coords[:, 1])
    y_to_i = {int(y): i for i, y in enumerate(ys)}
    x_to_j = {int(x): j for j, x in enumerate(xs)}
    grid = -np.ones((len(ys), len(xs)), dtype=np.int32)
    for patch_idx, (y, x) in enumerate(coords):
        grid[y_to_i[int(y)], x_to_j[int(x)]] = patch_idx
    return grid, ys, xs


def _accumulate_patch_scores(coords: np.ndarray,
                             distances: np.ndarray,
                             height: int,
                             width: int,
                             patch_size: int) -> Tuple[np.ndarray, np.ndarray]:
    heat_sum = np.zeros((height, width), dtype=np.float32)
    heat_count = np.zeros((height, width), dtype=np.float32)
    for (y0, x0), d in zip(coords, distances):
        y0 = int(y0)
        x0 = int(x0)
        y1 = min(y0 + patch_size, height)
        x1 = min(x0 + patch_size, width)
        heat_sum[y0:y1, x0:x1] += d
        heat_count[y0:y1, x0:x1] += 1.0
    heat = np.zeros_like(heat_sum)
    mask = heat_count > 0
    heat[mask] = heat_sum[mask] / heat_count[mask]
    return heat, mask


def _gaussian_kernel1d(sigma: float, radius: Optional[int] = None) -> np.ndarray:
    if sigma <= 0:
        return np.array([1.0], dtype=np.float32)
    if radius is None:
        radius = int(max(1, round(3 * sigma)))
    x = np.arange(-radius, radius + 1, dtype=np.float32)
    kernel = np.exp(-0.5 * (x / sigma) ** 2)
    kernel /= np.sum(kernel)
    return kernel.astype(np.float32)


def _gaussian_blur(image: np.ndarray, sigma: float) -> np.ndarray:
    kernel = _gaussian_kernel1d(sigma)
    radius = len(kernel) // 2
    padded = np.pad(image, ((0, 0), (radius, radius)), mode="edge")
    temp = np.apply_along_axis(lambda m: np.convolve(m, kernel, mode="valid"), axis=1, arr=padded)
    padded = np.pad(temp, ((radius, radius), (0, 0)), mode="edge")
    blurred = np.apply_along_axis(lambda m: np.convolve(m, kernel, mode="valid"), axis=0, arr=padded)
    return blurred


def _kde_1d(samples: np.ndarray,
            num_points: int = 200,
            bandwidth: Optional[float] = None,
            max_samples: int = 5000) -> Tuple[np.ndarray, np.ndarray]:
    samples = np.asarray(samples, dtype=np.float32)
    samples = samples[np.isfinite(samples)]
    if samples.size == 0:
        return np.array([0.0, 1.0]), np.array([0.0, 0.0])
    if samples.size > max_samples:
        rng = np.random.default_rng(0)
        samples = rng.choice(samples, size=max_samples, replace=False)
    n = samples.size
    std = float(np.std(samples))
    if bandwidth is None:
        bandwidth = 1.06 * std * (n ** (-1 / 5))
    if not np.isfinite(bandwidth) or bandwidth <= 0:
        bandwidth = max(std, 1e-6)
    x = np.linspace(samples.min(), samples.max(), num_points)
    diffs = (x[:, None] - samples[None, :]) / bandwidth
    density = np.exp(-0.5 * diffs ** 2).mean(axis=1) / (bandwidth * np.sqrt(2 * np.pi))
    return x, density


class DisplayVisualizer:
    """Visualizer for advanced plot types."""

    def __init__(self, dpi: int = 150):
        self.dpi = dpi

    def plot_cdf(self,
                 distances: np.ndarray,
                 thresholds: Optional[Iterable[float]] = None,
                 save_path: Optional[str] = None,
                 ax: Optional[plt.Axes] = None,
                 label: Optional[str] = None) -> Optional[str]:
        distances = np.asarray(distances, dtype=np.float32)
        distances = distances[np.isfinite(distances)]
        if distances.size == 0:
            return None
        sorted_vals = np.sort(distances)
        y = 100.0 * (np.arange(1, len(sorted_vals) + 1) / len(sorted_vals))

        fig = None
        if ax is None:
            fig, ax = plt.subplots(figsize=(6, 4), dpi=self.dpi)
        ax.plot(sorted_vals, y, label=label or "CDF")

        if thresholds:
            for thr in thresholds:
                ax.axvline(float(thr), linestyle="--", linewidth=1.2, color="gray")
                ax.text(float(thr), 3.0, f"{thr:.3g}", rotation=90, va="bottom", fontsize=8)

        ax.set_xlabel("Distance")
        ax.set_ylabel("Cumulative %")
        ax.set_title("CDF of Patch Distances", fontsize=12, weight="bold")
        if label or thresholds:
            ax.legend(fontsize=9)
        ax.grid(alpha=0.25, linestyle="--")

        if save_path:
            fig = fig or ax.figure
            fig.tight_layout()
            fig.savefig(save_path, dpi=self.dpi)
            plt.close(fig)
            return save_path
        return None

    def plot_box_regions(self,
                         coords: np.ndarray,
                         distances: np.ndarray,
                         image_shape: Tuple[int, int],
                         grid_size: Tuple[int, int] = (3, 3),
                         save_path: Optional[str] = None,
                         patch_size: Optional[int] = None) -> Optional[str]:
        coords = np.asarray(coords)
        distances = np.asarray(distances)
        if coords.size == 0 or distances.size == 0:
            return None
        h, w = image_shape
        rows, cols = grid_size
        y_centers, x_centers = _coords_to_centers(coords, patch_size)

        y_edges = np.linspace(0, h, rows + 1)
        x_edges = np.linspace(0, w, cols + 1)

        region_values = []
        labels = []
        for r in range(rows):
            for c in range(cols):
                y0, y1 = y_edges[r], y_edges[r + 1]
                x0, x1 = x_edges[c], x_edges[c + 1]
                mask = (y_centers >= y0) & (y_centers < y1) & (x_centers >= x0) & (x_centers < x1)
                vals = distances[mask]
                region_values.append(vals if vals.size else np.array([np.nan], dtype=np.float32))
                labels.append(f"R{r+1}C{c+1}")

        fig, ax = plt.subplots(figsize=(max(6, cols * 1.6), 4), dpi=self.dpi)
        bplot = ax.boxplot(region_values, labels=labels, patch_artist=True, showfliers=True)
        for patch in bplot["boxes"]:
            patch.set_facecolor("#6fa8dc")
            patch.set_alpha(0.6)
        mean_val = float(np.nanmean(distances))
        ax.axhline(mean_val, color="red", linestyle="--", linewidth=1.2, label=f"Mean {mean_val:.4f}")
        ax.set_xlabel("Region Grid")
        ax.set_ylabel("Distance")
        ax.set_title("Box Plot by Region", fontsize=12, weight="bold")
        ax.legend(fontsize=9)
        ax.grid(axis="y", alpha=0.2)

        if save_path:
            fig.tight_layout()
            fig.savefig(save_path, dpi=self.dpi)
            plt.close(fig)
            return save_path
        return None

    def plot_luminance_profiles(self,
                                image: np.ndarray,
                                coords: Optional[np.ndarray] = None,
                                save_path: Optional[str] = None,
                                ref_image: Optional[np.ndarray] = None) -> Optional[str]:
        luma = _compute_luma(image, linearize=True)
        luma_ref = _compute_luma(ref_image, linearize=True) if ref_image is not None else None

        profile_x = luma.mean(axis=0)
        profile_y = luma.mean(axis=1)
        profile_x_ref = luma_ref.mean(axis=0) if luma_ref is not None else None
        profile_y_ref = luma_ref.mean(axis=1) if luma_ref is not None else None

        fig, axes = plt.subplots(2, 1, figsize=(8, 6), dpi=self.dpi, sharex=False)
        axes[0].plot(profile_x, label="Capture")
        if profile_x_ref is not None:
            axes[0].plot(profile_x_ref, label="Reference")
        axes[0].set_title("Left-to-Right Luminance Profile", fontsize=11, weight="bold")
        axes[0].set_ylabel("Mean Luma")
        axes[0].grid(alpha=0.25)
        axes[0].legend(fontsize=9)

        axes[1].plot(profile_y, label="Capture")
        if profile_y_ref is not None:
            axes[1].plot(profile_y_ref, label="Reference")
        axes[1].set_title("Top-to-Bottom Luminance Profile", fontsize=11, weight="bold")
        axes[1].set_xlabel("Pixel Index")
        axes[1].set_ylabel("Mean Luma")
        axes[1].grid(alpha=0.25)
        axes[1].legend(fontsize=9)

        if save_path:
            fig.tight_layout()
            fig.savefig(save_path, dpi=self.dpi)
            plt.close(fig)
            return save_path
        return None

    def plot_scatter_2d(self,
                        coords: np.ndarray,
                        distances: np.ndarray,
                        image_shape: Tuple[int, int],
                        save_path: Optional[str] = None,
                        patch_size: Optional[int] = None,
                        topk: int = 10) -> Optional[str]:
        coords = np.asarray(coords)
        distances = np.asarray(distances)
        if coords.size == 0 or distances.size == 0:
            return None
        h, w = image_shape
        y_centers, x_centers = _coords_to_centers(coords, patch_size)
        vmin, vmax = _robust_minmax(distances, 5.0, 95.0)
        norm = Normalize(vmin=vmin, vmax=vmax)

        fig, ax = plt.subplots(figsize=(6, 5), dpi=self.dpi)
        sc = ax.scatter(x_centers, y_centers, c=distances, cmap="viridis", norm=norm, s=18)

        if topk > 0:
            top_idx = np.argsort(distances)[-topk:]
            ax.scatter(x_centers[top_idx], y_centers[top_idx],
                       facecolors="none", edgecolors="red", s=80, linewidths=1.5)

        ax.set_xlim(0, w)
        ax.set_ylim(h, 0)
        ax.set_aspect("equal")
        ax.set_title("2D Scatter of Patch Scores", fontsize=12, weight="bold")
        ax.set_xlabel("X (pixels)")
        ax.set_ylabel("Y (pixels)")
        fig.colorbar(sc, ax=ax, fraction=0.046, pad=0.04).set_label("Distance")

        if save_path:
            fig.tight_layout()
            fig.savefig(save_path, dpi=self.dpi)
            plt.close(fig)
            return save_path
        return None

    def plot_kde(self,
                 distances: np.ndarray,
                 save_path: Optional[str] = None,
                 ax: Optional[plt.Axes] = None) -> Optional[str]:
        distances = np.asarray(distances, dtype=np.float32)
        distances = distances[np.isfinite(distances)]
        if distances.size == 0:
            return None
        x, density = _kde_1d(distances)

        fig = None
        if ax is None:
            fig, ax = plt.subplots(figsize=(6, 4), dpi=self.dpi)
        ax.plot(x, density, color="#2c7fb8")
        ax.set_xlabel("Distance")
        ax.set_ylabel("Density")
        ax.set_title("Kernel Density Estimate", fontsize=12, weight="bold")
        ax.grid(alpha=0.25, linestyle="--")

        if save_path:
            fig = fig or ax.figure
            fig.tight_layout()
            fig.savefig(save_path, dpi=self.dpi)
            plt.close(fig)
            return save_path
        return None

    def plot_percentile_map(self,
                            coords: np.ndarray,
                            distances: np.ndarray,
                            image_shape: Tuple[int, int],
                            percentiles: Iterable[float],
                            save_path: Optional[str] = None,
                            patch_size: Optional[int] = None,
                            stride: Optional[int] = None) -> Optional[str]:
        coords = np.asarray(coords)
        distances = np.asarray(distances)
        if coords.size == 0 or distances.size == 0:
            return None
        if stride is None:
            stride = _infer_stride(coords)
        if patch_size is None:
            patch_size = stride

        grid, ys, xs = _build_patch_grid(coords)
        valid = grid >= 0
        score_grid = np.full(grid.shape, np.nan, dtype=np.float32)
        score_grid[valid] = distances[grid[valid]]

        percentiles = list(percentiles)
        if not percentiles:
            return None

        cols = min(3, len(percentiles))
        rows = int(np.ceil(len(percentiles) / cols))
        fig, axes = plt.subplots(rows, cols, figsize=(cols * 4, rows * 3), dpi=self.dpi)
        axes = np.atleast_1d(axes).ravel()

        cmap = ListedColormap(["#2ecc71", "#e74c3c"])
        extent = (float(xs.min()),
                  float(xs.max() + patch_size),
                  float(ys.max() + patch_size),
                  float(ys.min()))

        for ax, pct in zip(axes, percentiles):
            thr = float(np.percentile(distances, pct))
            bad = score_grid >= thr
            bad_pct = 100.0 * float(np.nanmean(bad))
            mask = np.where(bad, 1.0, 0.0)
            ax.imshow(mask, cmap=cmap, origin="upper", extent=extent, interpolation="nearest")
            ax.set_title(f"{pct:.0f}th pct (>= {thr:.4f})\nBad: {bad_pct:.1f}%", fontsize=10)
            ax.set_xlim(0, image_shape[1])
            ax.set_ylim(image_shape[0], 0)
            ax.axis("off")

        for ax in axes[len(percentiles):]:
            ax.axis("off")

        fig.suptitle("Percentile Maps", fontsize=12, weight="bold")
        fig.tight_layout(rect=(0, 0, 1, 0.95))

        if save_path:
            fig.savefig(save_path, dpi=self.dpi)
            plt.close(fig)
            return save_path
        return None

    def plot_error_distribution_2d(self,
                                   coords: np.ndarray,
                                   distances: np.ndarray,
                                   image_shape: Tuple[int, int],
                                   save_path: Optional[str] = None,
                                   patch_size: Optional[int] = None,
                                   blur_sigma: Optional[float] = None) -> Optional[str]:
        coords = np.asarray(coords)
        distances = np.asarray(distances)
        if coords.size == 0 or distances.size == 0:
            return None
        h, w = image_shape
        if patch_size is None:
            patch_size = _infer_stride(coords)
        if blur_sigma is None:
            blur_sigma = max(1.0, patch_size / 3.0)

        heat, mask = _accumulate_patch_scores(coords, distances, h, w, patch_size)
        heat = _gaussian_blur(heat, sigma=blur_sigma)
        heat = np.ma.masked_where(~mask, heat)

        vmin, vmax = _robust_minmax(distances, 5.0, 95.0)
        fig, ax = plt.subplots(figsize=(6, 5), dpi=self.dpi)
        im = ax.imshow(heat, cmap="inferno", vmin=vmin, vmax=vmax, origin="upper")
        ax.set_title("2D Error Distribution", fontsize=12, weight="bold")
        ax.set_xlim(0, w)
        ax.set_ylim(h, 0)
        ax.axis("off")
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04).set_label("Distance")

        if save_path:
            fig.tight_layout()
            fig.savefig(save_path, dpi=self.dpi)
            plt.close(fig)
            return save_path
        return None


def generate_all_plots(results: Dict[str, object],
                       ref_image: np.ndarray,
                       cap_image: np.ndarray,
                       output_dir: str,
                       grid_size: Tuple[int, int] = (3, 3),
                       percentiles: Optional[Iterable[float]] = None,
                       thresholds: Optional[Iterable[float]] = None) -> Dict[str, str]:
    """
    Generate all seven advanced plot types.
    Requires results to include patch_coords and patch_distances.
    """
    _ensure_dir(output_dir)
    coords = results.get("patch_coords")
    distances = results.get("patch_distances")
    if coords is None or distances is None:
        raise ValueError(
            "results must include patch_coords and patch_distances. "
            "Enable config.analysis.return_patch_data or pass return_patch_data=True."
        )
    coords = np.asarray(coords)
    distances = np.asarray(distances)

    image_shape = _image_shape(cap_image)
    patch_size = results.get("patch_size")
    stride = results.get("stride")
    if patch_size is not None:
        patch_size = int(patch_size)
    if stride is not None:
        stride = int(stride)

    viz = DisplayVisualizer()
    outputs = {}

    outputs["cdf"] = viz.plot_cdf(
        distances,
        thresholds=thresholds or [0.01, 0.05, 0.1],
        save_path=os.path.join(output_dir, "cdf.png")
    )

    outputs["box_regions"] = viz.plot_box_regions(
        coords, distances, image_shape, grid_size=grid_size,
        save_path=os.path.join(output_dir, "box_regions.png"),
        patch_size=patch_size
    )

    outputs["luminance_profiles"] = viz.plot_luminance_profiles(
        cap_image, coords,
        save_path=os.path.join(output_dir, "luminance_profiles.png"),
        ref_image=ref_image
    )

    outputs["scatter_2d"] = viz.plot_scatter_2d(
        coords, distances, image_shape,
        save_path=os.path.join(output_dir, "scatter.png"),
        patch_size=patch_size
    )

    outputs["kde"] = viz.plot_kde(
        distances,
        save_path=os.path.join(output_dir, "kde.png")
    )

    outputs["percentile_maps"] = viz.plot_percentile_map(
        coords, distances, image_shape,
        percentiles=percentiles or [50, 75, 90, 95, 99],
        save_path=os.path.join(output_dir, "percentile_maps.png"),
        patch_size=patch_size,
        stride=stride
    )

    outputs["error_dist_2d"] = viz.plot_error_distribution_2d(
        coords, distances, image_shape,
        save_path=os.path.join(output_dir, "error_dist_2d.png"),
        patch_size=patch_size
    )

    return {k: v for k, v in outputs.items() if v}
