#!/usr/bin/env python3
"""
OLED Display Quality Validator (Simple + ML-pluggable)

WHAT YOU GET:
  - patch_data.csv                  : per-patch scores (x0,y0,score,is_edge,region tags)
  - region_report.csv               : global/edge/center/corners stats (mean, std, median, P95, GM)
  - histogram_with_stats.png        : histogram + stats box (mean/std/median/P95/%bad)
  - heatmap_pixelated_scores.png    : grid heatmap + numeric patch scores (per cell)
  - heatmap_hybrid_scores.png       : smooth heatmap + grid + numeric patch scores
  - luma_ref.png / luma_cap.png     : linear luma (Rec.709) grayscale images
  - log_radiance_ref.png            : log10(luma) map for reference
  - log_radiance_cap.png            : log10(luma) map for capture
  - contour_map_scores.png          : contour lines over patch-score field
  - (optional) cluster_report.csv   : defect clusters based on bad patch threshold

NOTES:
  - Images MUST be aligned and same resolution.
  - Score is "distance": higher = worse (you can flip if your ML is similarity).

HOW TO USE YOUR CUSTOM ML METRIC:
  - Replace `ml_metric_distance()` with your model call.
  - It must accept (B,C,P,P) ref and cap tensors and return (B,) distances.
"""

import os
import csv
import argparse
import numpy as np
import torch
import matplotlib.pyplot as plt
import matplotlib.patheffects as patheffects
from PIL import Image
from matplotlib.patches import Rectangle


# =============================================================================
# Utilities
# =============================================================================

def load_image_rgb(path, device):
    arr = np.array(Image.open(path).convert("RGB"), dtype=np.float32) / 255.0
    t = torch.from_numpy(arr).permute(2, 0, 1).to(device)  # (C,H,W)
    return t


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def anchored_starts(L, P, S):
    if L <= P:
        return [0]
    starts = list(range(0, L - P + 1, S))
    last = L - P
    if starts[-1] != last:
        starts.append(last)
    return starts


def _figure_for_image(w, h, dpi=150):
    w = max(1, int(w))
    h = max(1, int(h))
    return plt.subplots(figsize=(w / dpi, h / dpi), dpi=dpi)


def _imshow_with_extent(ax, image, w, h, **kwargs):
    return ax.imshow(image, origin="upper", extent=(0, w, h, 0), **kwargs)


def _robust_minmax(x, lower_pct=1.0, upper_pct=99.0):
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


def _clip_edge_band(edge_band, H, W):
    return int(np.clip(int(edge_band), 0, min(int(H), int(W))))


def _center_region_rect(edge_band, H, W):
    edge_band = _clip_edge_band(edge_band, H, W)
    if edge_band <= 0:
        return None
    width = int(W - 2 * edge_band)
    height = int(H - 2 * edge_band)
    if width <= 0 or height <= 0:
        return None
    return int(edge_band), int(edge_band), width, height


def _sparse_grid_indices(coords_np, step=2):
    coords_np = np.asarray(coords_np)
    if coords_np.size == 0:
        return np.array([], dtype=int)
    ys_sorted = np.sort(np.unique(coords_np[:, 0]))
    xs_sorted = np.sort(np.unique(coords_np[:, 1]))
    y_to_i = {int(y): i for i, y in enumerate(ys_sorted)}
    x_to_j = {int(x): j for i, x in enumerate(xs_sorted)}
    idx = [
        k for k, (y0, x0) in enumerate(coords_np)
        if (y_to_i[int(y0)] % step == 0 and x_to_j[int(x0)] % step == 0)
    ]
    return np.asarray(idx, dtype=int)


def _accumulate_patch_scores(coords_np, distances, H, W, P):
    heat_sum = np.zeros((H, W), dtype=np.float32)
    heat_count = np.zeros((H, W), dtype=np.float32)
    for (y0, x0), d in zip(coords_np, distances):
        y0 = int(y0)
        x0 = int(x0)
        y1 = min(y0 + P, H)
        x1 = min(x0 + P, W)
        heat_sum[y0:y1, x0:x1] += d
        heat_count[y0:y1, x0:x1] += 1.0
    heat = np.zeros_like(heat_sum)
    mask = heat_count > 0
    heat[mask] = heat_sum[mask] / heat_count[mask]
    return heat, mask


# =============================================================================
# Patch Extraction (Edge-Anchored)
# =============================================================================

def extract_patches_edge_anchored(img, patch_size, stride):
    """
    img: (C,H,W)
    returns:
      patches: (N,C,P,P)
      coords:  (N,2) [y0,x0] top-left in pixels
    """
    C, H, W = img.shape
    P, S = patch_size, stride
    device = img.device

    if H < P or W < P:
        raise ValueError(
            f"patch_size {P} exceeds image size ({H}x{W}); "
            "reduce --patch or resize inputs."
        )

    # Regular grid using Unfold
    unfold = torch.nn.Unfold(kernel_size=P, stride=S)
    reg = unfold(img.unsqueeze(0))                 # (1, C*P*P, N)
    reg = reg.transpose(1, 2).reshape(-1, C, P, P)

    ys = torch.arange(0, max(H - P + 1, 1), S, device=device)
    xs = torch.arange(0, max(W - P + 1, 1), S, device=device)
    yy, xx = torch.meshgrid(ys, xs, indexing="ij")
    coords = torch.stack([yy.flatten(), xx.flatten()], dim=1)

    extras, ecoords = [], []

    add_bottom = (H - P) % S != 0
    add_right = (W - P) % S != 0

    # Bottom edge anchoring
    if add_bottom:
        y = H - P
        for x in anchored_starts(W, P, S):
            extras.append(img[:, y:y+P, x:x+P])
            ecoords.append((y, x))

    # Right edge anchoring
    if add_right:
        x = W - P
        for y in anchored_starts(H, P, S):
            if add_bottom and y == H - P:
                continue  # avoid duplicate bottom-right patch
            extras.append(img[:, y:y+P, x:x+P])
            ecoords.append((y, x))

    if extras:
        extras = torch.stack(extras, dim=0)
        ecoords = torch.tensor(ecoords, device=device)
        reg = torch.cat([reg, extras], dim=0)
        coords = torch.cat([coords, ecoords], dim=0)

    return reg, coords


# =============================================================================
# Scoring: Default distance + ML plug-in hook
# =============================================================================

@torch.no_grad()
def default_distance_metric(ref_patches, cap_patches):
    """
    Fast, decent baseline distance:
      - per-patch normalization
      - pixel MSE + gradient MSE
    returns: (B,) distance (higher = worse)
    """
    eps = 1e-6

    def norm(x):
        mu = x.mean((2, 3), keepdim=True)
        sd = x.std((2, 3), keepdim=True).clamp_min(eps)
        return (x - mu) / sd

    r = norm(ref_patches)
    c = norm(cap_patches)

    gx_r = r[:, :, :, 1:] - r[:, :, :, :-1]
    gy_r = r[:, :, 1:, :] - r[:, :, :-1, :]
    gx_c = c[:, :, :, 1:] - c[:, :, :, :-1]
    gy_c = c[:, :, 1:, :] - c[:, :, :-1, :]

    pixel = (r - c).pow(2).mean((1, 2, 3))
    gradx = (gx_r - gx_c).pow(2).mean((1, 2, 3))
    grady = (gy_r - gy_c).pow(2).mean((1, 2, 3))

    return pixel + 0.5 * gradx + 0.5 * grady


@torch.no_grad()
def ml_metric_distance(ref_patches, cap_patches):
    """
    <<< YOUR CUSTOM ML METRIC HOOK >>>

    Replace the body of this function to call YOUR model.

    Requirements:
      - Input tensors: ref_patches, cap_patches shape (B,C,P,P) in [0,1]
      - Output: 1D tensor/array shape (B,) = distance (higher = worse)

    Examples:
      - If your model outputs similarity (higher = better), convert:
          distance = 1 - similarity
      - If your model outputs per-patch logits, map to distance via softplus, etc.

    For now we fallback to default metric so the script runs.
    """
    # TODO: replace with your ML model inference
    return default_distance_metric(ref_patches, cap_patches)


def compute_distances_batched(ref_patches, cap_patches, batch_size, use_ml=True):
    """
    returns numpy float32 distances (N,)
    """
    scorer = ml_metric_distance if use_ml else default_distance_metric
    ds = []
    for i in range(0, len(ref_patches), batch_size):
        r = ref_patches[i:i+batch_size]
        c = cap_patches[i:i+batch_size]
        d = scorer(r, c).detach().cpu()
        ds.append(d)
    return torch.cat(ds, dim=0).numpy().astype(np.float32)


# =============================================================================
# Regions + stats
# =============================================================================

def define_regions(coords_np, H, W, patch_size, edge_band):
    edge_band = _clip_edge_band(edge_band, H, W)
    y0 = coords_np[:, 0]
    x0 = coords_np[:, 1]
    y1 = y0 + patch_size
    x1 = x0 + patch_size

    # Mark as edge if any part of the patch overlaps the edge band.
    left = x0 < edge_band
    right = x1 > (W - edge_band)
    top = y0 < edge_band
    bottom = y1 > (H - edge_band)

    return {
        "global": np.ones_like(left, dtype=bool),
        "edge": left | right | top | bottom,
        "center": ~(left | right | top | bottom),
        "left": left, "right": right, "top": top, "bottom": bottom,
        "corner_TL": top & left,
        "corner_TR": top & right,
        "corner_BL": bottom & left,
        "corner_BR": bottom & right,
    }


def geom_mean(x):
    x = np.asarray(x, dtype=np.float64)
    return float(np.exp(np.mean(np.log(np.maximum(x, 0.0) + 1e-6))))


def compute_region_stats(distances, masks):
    rows = []
    for name, m in masks.items():
        if m.sum() == 0:
            continue
        v = distances[m]
        rows.append({
            "region": name,
            "count": int(m.sum()),
            "mean": float(np.mean(v)),
            "std": float(np.std(v)),
            "median": float(np.median(v)),
            "P95": float(np.percentile(v, 95)),
            "GM": geom_mean(v),
        })
    return rows


# =============================================================================
# Bad patch marking + simple clustering on patch grid
# =============================================================================

def mark_bad(distances, mode="percentile", bad_percentile=95.0, bad_absolute=0.05):
    if mode == "percentile":
        thr = float(np.percentile(distances, bad_percentile))
        bad = distances >= thr
        return bad, thr
    else:
        thr = float(bad_absolute)
        bad = distances >= thr
        return bad, thr


def build_patch_grid(coords_np, H, W, P, S):
    """
    Convert patches to a logical grid index for clustering.
    We quantize by stride (S), but because we have anchored edges,
    we map each patch to its nearest (y_idx,x_idx) grid location.
    """
    ys = np.unique(coords_np[:, 0])
    xs = np.unique(coords_np[:, 1])
    ys_sorted = np.sort(ys)
    xs_sorted = np.sort(xs)

    y_to_i = {int(y): i for i, y in enumerate(ys_sorted)}
    x_to_j = {int(x): j for j, x in enumerate(xs_sorted)}

    grid = -np.ones((len(ys_sorted), len(xs_sorted)), dtype=np.int32)
    for k, (y0, x0) in enumerate(coords_np):
        grid[y_to_i[int(y0)], x_to_j[int(x0)]] = k

    return grid, ys_sorted, xs_sorted


def cluster_bad_patches(coords_np, distances, bad_mask, H, W, P, S, min_cluster=4):
    """
    Cluster adjacency in the patch grid (4-connected).
    Returns list of clusters with stats.
    """
    grid, ys_sorted, xs_sorted = build_patch_grid(coords_np, H, W, P, S)
    hG, wG = grid.shape

    bad_grid = np.zeros((hG, wG), dtype=bool)
    for i in range(hG):
        for j in range(wG):
            k = grid[i, j]
            if k >= 0 and bad_mask[k]:
                bad_grid[i, j] = True

    visited = np.zeros_like(bad_grid, dtype=bool)
    clusters = []

    def neighbors(i, j):
        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ni, nj = i + di, j + dj
            if 0 <= ni < hG and 0 <= nj < wG:
                yield ni, nj

    for i in range(hG):
        for j in range(wG):
            if not bad_grid[i, j] or visited[i, j]:
                continue
            # BFS
            q = [(i, j)]
            visited[i, j] = True
            members = []

            while q:
                ci, cj = q.pop()
                k = grid[ci, cj]
                if k >= 0:
                    members.append(k)
                for ni, nj in neighbors(ci, cj):
                    if bad_grid[ni, nj] and not visited[ni, nj]:
                        visited[ni, nj] = True
                        q.append((ni, nj))

            if len(members) < min_cluster:
                continue

            mem = np.array(members, dtype=int)
            ys = coords_np[mem, 0]
            xs = coords_np[mem, 1]
            vals = distances[mem]

            clusters.append({
                "cluster_size_patches": int(len(mem)),
                "mean_score": float(np.mean(vals)),
                "max_score": float(np.max(vals)),
                "centroid_y": float(np.mean(ys + P / 2.0)),
                "centroid_x": float(np.mean(xs + P / 2.0)),
                "bbox_y0": int(np.min(ys)),
                "bbox_x0": int(np.min(xs)),
                "bbox_y1": int(np.max(ys) + P),
                "bbox_x1": int(np.max(xs) + P),
            })

    return clusters


# =============================================================================
# Visualization helpers (legible per-patch text)
# =============================================================================

def annotate_patch_scores(ax, coords_np, distances, patch_size,
                          mode="all", topk=30, edge_mask=None,
                          text_frac=0.35, min_px=12, max_px=72,
                          box_alpha=0.85):
    """
    DPI-aware text that scales with patch size so it is readable in big cells.
    """
    coords_np = np.asarray(coords_np)
    distances = np.asarray(distances)

    if mode == "all":
        idx = np.arange(len(distances))
    elif mode == "all_sparse":
        idx = _sparse_grid_indices(coords_np, step=2)
        if idx.size == 0:
            return
    elif mode == "topk":
        idx = np.argsort(distances)[-topk:]
    elif mode == "edge_topk":
        if edge_mask is None:
            raise ValueError("edge_mask required for edge_topk")
        edge_idx = np.where(edge_mask)[0]
        if edge_idx.size == 0:
            return
        order = edge_idx[np.argsort(distances[edge_idx])]
        idx = order[-min(topk, order.size):]
    else:
        raise ValueError("score_mode must be all/all_sparse/topk/edge_topk")

    dpi = float(ax.figure.dpi) if ax.figure is not None else 150.0
    if ax.figure is not None:
        fig = ax.figure
        fig_w, fig_h = fig.get_size_inches()
        ax_pos = ax.get_position()
        ax_w_px = fig_w * dpi * ax_pos.width
        ax_h_px = fig_h * dpi * ax_pos.height
        data_w = float(np.max(coords_np[:, 1]) + patch_size)
        data_h = float(np.max(coords_np[:, 0]) + patch_size)
        px_per_data_x = ax_w_px / max(data_w, 1.0)
        px_per_data_y = ax_h_px / max(data_h, 1.0)
        patch_px = patch_size * min(px_per_data_x, px_per_data_y)
        desired_px = int(round(patch_px * text_frac))
    else:
        desired_px = int(round(patch_size * text_frac))
    desired_px = int(np.clip(desired_px, min_px, max_px))
    if mode in ("all", "all_sparse") and len(idx) > 600:
        desired_px = max(min_px, int(desired_px * 0.9))
    font_pt = max(6.0, desired_px * 72.0 / dpi)
    stroke = max(1.2, font_pt / 6.0)
    effects = [patheffects.withStroke(linewidth=stroke, foreground="black")]

    for i in idx:
        y0, x0 = coords_np[i]
        cx = x0 + patch_size / 2.0
        cy = y0 + patch_size / 2.0
        ax.text(
            cx, cy, f"{distances[i]:.4f}",
            ha="center", va="center",
            fontsize=font_pt, weight="bold",
            color="white",
            bbox=dict(
                boxstyle="round,pad=0.25",
                facecolor="black", alpha=box_alpha,
                edgecolor="white", linewidth=0.6
            ),
            path_effects=effects
        )


def save_heatmap_pixelated(cap_np, coords_np, distances, H, W, P, edge_band, out_path,
                           alpha=0.5, score_mode="all", score_topk=30, edge_mask=None):
    heat, mask = _accumulate_patch_scores(coords_np, distances, H, W, P)
    vmin, vmax = _robust_minmax(distances, 5.0, 95.0)
    denom = max(vmax - vmin, 1e-6)
    hm = np.clip((heat - vmin) / denom, 0, 1)
    alpha_map = np.where(mask, alpha, 0.0).astype(np.float32)

    fig, ax = _figure_for_image(W, H, dpi=150)
    _imshow_with_extent(ax, cap_np, W, H)
    _imshow_with_extent(ax, hm, W, H, cmap="inferno", alpha=alpha_map, interpolation="nearest")

    # Patch borders (light)
    for (y0, x0) in coords_np:
        y0, x0 = int(y0), int(x0)
        ax.add_patch(Rectangle((x0, y0), P, P, linewidth=0.5, edgecolor="white",
                               facecolor="none", alpha=0.25))

    # Center ROI box
    center_rect = _center_region_rect(edge_band, H, W)
    if center_rect is not None:
        x0, y0, width, height = center_rect
        ax.add_patch(Rectangle((x0, y0), width, height,
                               linewidth=2.0, edgecolor="cyan",
                               facecolor="none", linestyle="--"))

    annotate_patch_scores(ax, coords_np, distances, P,
                          mode=score_mode, topk=score_topk, edge_mask=edge_mask)

    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    ax.axis("off")
    ax.set_title("Pixelated Heatmap + Patch Scores (higher=worse)", fontsize=12, weight="bold")
    fig.tight_layout(pad=0.2)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def save_heatmap_hybrid(cap_np, coords_np, distances, H, W, P, edge_band, out_path,
                        alpha=0.45, score_mode="all", score_topk=30, edge_mask=None):
    # Smooth splat (simple gaussian-ish kernel)
    heat = np.zeros((H, W), np.float32)
    wgt = np.zeros((H, W), np.float32)

    yy, xx = np.mgrid[0:P, 0:P]
    cy = cx = (P - 1) / 2.0
    sigma = max(P * 0.45, 1.0)
    kern = np.exp(-((yy - cy) ** 2 + (xx - cx) ** 2) / (2 * sigma * sigma)).astype(np.float32)
    kern /= kern.max()

    for (y0, x0), d in zip(coords_np, distances):
        y0, x0 = int(y0), int(x0)
        heat[y0:y0+P, x0:x0+P] += d * kern
        wgt[y0:y0+P, x0:x0+P] += kern

    mask = wgt > 1e-6
    heat = np.divide(heat, wgt, out=np.zeros_like(heat), where=mask)

    vmin, vmax = _robust_minmax(distances, 5.0, 95.0)
    denom = max(vmax - vmin, 1e-6)
    hm = np.clip((heat - vmin) / denom, 0, 1)
    alpha_map = np.where(mask, alpha, 0.0).astype(np.float32)

    fig, ax = _figure_for_image(W, H, dpi=150)
    _imshow_with_extent(ax, cap_np, W, H)
    _imshow_with_extent(ax, hm, W, H, cmap="inferno", alpha=alpha_map, interpolation="bilinear")

    # Light grid (every other row/col to reduce clutter)
    sparse_idx = _sparse_grid_indices(coords_np, step=2)
    if sparse_idx.size:
        for (y0, x0) in coords_np[sparse_idx]:
            y0, x0 = int(y0), int(x0)
            ax.add_patch(Rectangle((x0, y0), P, P, linewidth=0.3, edgecolor="white",
                                   facecolor="none", alpha=0.18))

    center_rect = _center_region_rect(edge_band, H, W)
    if center_rect is not None:
        x0, y0, width, height = center_rect
        ax.add_patch(Rectangle((x0, y0), width, height,
                               linewidth=2.0, edgecolor="cyan",
                               facecolor="none", linestyle="--"))

    annotate_patch_scores(ax, coords_np, distances, P,
                          mode=score_mode, topk=score_topk, edge_mask=edge_mask)

    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    ax.axis("off")
    ax.set_title("Hybrid Heatmap (smooth+grid) + Patch Scores", fontsize=12, weight="bold")
    fig.tight_layout(pad=0.2)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


# =============================================================================
# Histogram + stats on same plot
# =============================================================================

def plot_histogram_with_stats(scores, out_path, title="Patch Score Histogram", threshold=None, bins=60):
    scores = np.asarray(scores, dtype=np.float32)

    mean = float(np.mean(scores))
    median = float(np.median(scores))
    std = float(np.std(scores))
    p95 = float(np.percentile(scores, 95))

    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    ax.hist(scores, bins=bins, alpha=0.85, edgecolor="black")

    ax.axvline(mean, linestyle="--", linewidth=2, label=f"Mean {mean:.4f}")
    ax.axvline(median, linestyle="-.", linewidth=2, label=f"Median {median:.4f}")
    ax.axvline(p95, linestyle=":", linewidth=2, label=f"P95 {p95:.4f}")

    pct_bad = None
    if threshold is not None:
        ax.axvline(float(threshold), linestyle="-", linewidth=2, label=f"BadThr {float(threshold):.4f}")
        pct_bad = 100.0 * float(np.mean(scores >= float(threshold)))

    ax.set_xlabel("Patch distance score (higher = worse)")
    ax.set_ylabel("Count of patches")
    ax.set_title(title, fontsize=13, weight="bold")
    ax.legend(fontsize=9)

    stats = (
        f"Mean   : {mean:.4f}\n"
        f"Median : {median:.4f}\n"
        f"Std    : {std:.4f}\n"
        f"P95    : {p95:.4f}"
    )
    if pct_bad is not None:
        stats += f"\n>=BadThr: {pct_bad:.2f}%"

    ax.text(
        0.98, 0.95, stats,
        transform=ax.transAxes,
        ha="right", va="top",
        fontsize=10,
        bbox=dict(boxstyle="round,pad=0.5", facecolor="white", alpha=0.90)
    )

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


# =============================================================================
# Luma + log-radiance + contour maps
# =============================================================================

def srgb_to_linear(rgb):
    """
    Approximate sRGB -> linear light conversion (piecewise).
    Input/Output range: [0, 1].
    """
    rgb = np.asarray(rgb, dtype=np.float32)
    return np.where(
        rgb <= 0.04045,
        rgb / 12.92,
        ((rgb + 0.055) / 1.055) ** 2.4
    )


def compute_luma(rgb_np, linearize=True):
    """
    Compute linear luma (Rec.709). Assumes rgb in [0,1].
    If linearize=True, converts from sRGB to linear first.
    """
    rgb = np.clip(rgb_np, 0.0, 1.0).astype(np.float32, copy=False)
    if linearize:
        rgb = srgb_to_linear(rgb)
    return (0.2126 * rgb[..., 0] +
            0.7152 * rgb[..., 1] +
            0.0722 * rgb[..., 2])


def save_luma_image(luma, out_path, title="Luma (Y, linear)"):
    h, w = luma.shape[:2]
    fig, ax = _figure_for_image(w, h, dpi=150)
    _imshow_with_extent(ax, luma, w, h, cmap="gray", vmin=0.0, vmax=1.0)
    ax.set_title(title, fontsize=12, weight="bold")
    ax.axis("off")
    fig.tight_layout(pad=0.2)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def save_log_radiance_map(luma, out_path, title="Log Radiance (log10 Y)"):
    log_rad = np.log10(np.maximum(luma, 0.0) + 1e-6)
    vmin, vmax = _robust_minmax(log_rad, 1.0, 99.0)

    h, w = luma.shape[:2]
    fig, ax = _figure_for_image(w, h, dpi=150)
    im = _imshow_with_extent(ax, log_rad, w, h, cmap="magma", vmin=vmin, vmax=vmax)
    ax.set_title(title, fontsize=12, weight="bold")
    ax.axis("off")
    cbar = fig.colorbar(im, ax=ax, fraction=0.045, pad=0.02)
    cbar.set_label("log10(luma)")
    fig.tight_layout(pad=0.2)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def save_contour_map(cap_np, coords_np, distances, H, W, P, S, edge_band, out_path,
                     levels=12, overlay_alpha=0.45, cmap="inferno"):
    grid, ys_sorted, xs_sorted = build_patch_grid(coords_np, H, W, P, S)
    score_grid = np.full(grid.shape, np.nan, dtype=np.float32)
    valid = grid >= 0
    if not np.any(valid):
        return
    score_grid[valid] = distances[grid[valid]]
    score_grid = np.ma.masked_invalid(score_grid)

    if score_grid.shape[0] < 2 or score_grid.shape[1] < 2:
        # Fallback: show the single-cell map without contours
        fig, ax = _figure_for_image(W, H, dpi=150)
        _imshow_with_extent(ax, cap_np, W, H)
        _imshow_with_extent(ax, score_grid, W, H, cmap=cmap, alpha=overlay_alpha,
                            interpolation="nearest")
        ax.axis("off")
        ax.set_title("Contour Map (insufficient grid size)", fontsize=12, weight="bold")
        fig.tight_layout(pad=0.2)
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        return

    x_centers = xs_sorted + P / 2.0
    y_centers = ys_sorted + P / 2.0
    xx, yy = np.meshgrid(x_centers, y_centers)

    vmin, vmax = _robust_minmax(distances, 5.0, 95.0)
    if isinstance(levels, int):
        levels = np.linspace(vmin, vmax, max(2, levels))

    fig, ax = _figure_for_image(W, H, dpi=150)
    _imshow_with_extent(ax, cap_np, W, H)
    cf = ax.contourf(xx, yy, score_grid, levels=levels, cmap=cmap, alpha=overlay_alpha)
    cl = ax.contour(xx, yy, score_grid, levels=levels, colors="white", linewidths=0.6, alpha=0.75)
    ax.clabel(cl, inline=True, fontsize=7, fmt="%.3f")

    center_rect = _center_region_rect(edge_band, H, W)
    if center_rect is not None:
        x0, y0, width, height = center_rect
        ax.add_patch(Rectangle((x0, y0), width, height,
                               linewidth=2.0, edgecolor="cyan",
                               facecolor="none", linestyle="--"))
    ax.set_title("Contour Map of Patch Scores (higher=worse)", fontsize=12, weight="bold")
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    ax.axis("off")
    cbar = fig.colorbar(cf, ax=ax, fraction=0.03, pad=0.01)
    cbar.set_label("Patch distance")
    fig.tight_layout(pad=0.2)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def generate_analysis_maps(ref_np, cap_np, coords_np, distances, H, W, P, S, edge_band, output_dir):
    luma_ref = compute_luma(ref_np, linearize=True)
    luma_cap = compute_luma(cap_np, linearize=True)

    luma_ref_path = os.path.join(output_dir, "luma_ref.png")
    luma_cap_path = os.path.join(output_dir, "luma_cap.png")
    save_luma_image(luma_ref, luma_ref_path, title="Reference Luma (Y, linear)")
    save_luma_image(luma_cap, luma_cap_path, title="Capture Luma (Y, linear)")

    log_ref_path = os.path.join(output_dir, "log_radiance_ref.png")
    log_cap_path = os.path.join(output_dir, "log_radiance_cap.png")
    save_log_radiance_map(luma_ref, log_ref_path, title="Reference Log Radiance (log10 Y)")
    save_log_radiance_map(luma_cap, log_cap_path, title="Capture Log Radiance (log10 Y)")

    contour_path = os.path.join(output_dir, "contour_map_scores.png")
    save_contour_map(cap_np, coords_np, distances, H, W, P, S, edge_band, contour_path)

    return {
        "luma_ref": luma_ref_path,
        "luma_cap": luma_cap_path,
        "log_radiance_ref": log_ref_path,
        "log_radiance_cap": log_cap_path,
        "contour_map_scores": contour_path,
    }


# =============================================================================
# Main pipeline
# =============================================================================

def validate_oled_display(ref_path, cap_path, output_dir, cfg):
    ensure_dir(output_dir)

    P = int(cfg["patch_size"])
    S = int(cfg["stride"])
    edge_band = int(cfg["edge_band"])
    device = cfg["device"]
    batch = int(cfg["batch"])
    alpha = float(cfg["alpha"])
    heatmap_style = cfg["heatmap_style"]
    score_mode = cfg["score_mode"]
    score_topk = int(cfg["score_topk"])
    topn_patches = int(cfg["topn_patches"])
    bad_mode = cfg["bad_mode"]
    bad_percentile = float(cfg["bad_percentile"])
    bad_absolute = float(cfg["bad_absolute"])
    min_cluster = int(cfg["min_cluster"])
    thresholds = cfg["thresholds"]
    use_ml = bool(cfg.get("use_ml", True))

    print("\n============================================================")
    print("OLED DISPLAY QUALITY VALIDATOR (Simple + ML-pluggable)")
    print("============================================================")
    print(f"ref: {ref_path}")
    print(f"cap: {cap_path}")
    print(f"out: {output_dir}")
    print(f"P={P} S={S} edge_band={edge_band} device={device} batch={batch} ML={use_ml}")
    print("============================================================\n")

    ref = load_image_rgb(ref_path, device)
    cap = load_image_rgb(cap_path, device)

    if ref.shape != cap.shape:
        raise ValueError(f"Ref/Cap mismatch. ref={tuple(ref.shape)} cap={tuple(cap.shape)}")

    C, H, W = ref.shape
    print(f"Resolution: {H} x {W}")
    edge_band_effective = _clip_edge_band(edge_band, H, W)
    if edge_band_effective != edge_band:
        print(f"Note: edge_band clamped to {edge_band_effective} for {H}x{W} input.")
        edge_band = edge_band_effective

    # Extract patches
    print("Extracting patches (edge-anchored)...")
    ref_patches, coords = extract_patches_edge_anchored(ref, P, S)
    cap_patches, _ = extract_patches_edge_anchored(cap, P, S)
    coords_np = coords.detach().cpu().numpy().astype(np.int32)
    print(f"Total patches: {len(ref_patches)}")

    # Score
    print("Scoring patches (batched)...")
    distances = compute_distances_batched(ref_patches, cap_patches, batch_size=batch, use_ml=use_ml)

    # Regions
    print("Computing region stats...")
    masks = define_regions(coords_np, H, W, P, edge_band)
    region_stats = compute_region_stats(distances, masks)

    # Save region report
    region_path = os.path.join(output_dir, "region_report.csv")
    with open(region_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=region_stats[0].keys())
        w.writeheader()
        w.writerows(region_stats)
    print(f"Saved: {region_path}")

    # Save patch data
    patch_path = os.path.join(output_dir, "patch_data.csv")
    with open(patch_path, "w", newline="") as f:
        cols = ["patch_id", "y0", "x0", "distance", "is_edge"]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for k, (y0, x0) in enumerate(coords_np):
            w.writerow({
                "patch_id": k,
                "y0": int(y0),
                "x0": int(x0),
                "distance": float(distances[k]),
                "is_edge": bool(masks["edge"][k]),
            })
    print(f"Saved: {patch_path}")

    # Bad threshold + histogram
    bad_mask, bad_thr = mark_bad(distances, mode=bad_mode, bad_percentile=bad_percentile, bad_absolute=bad_absolute)
    hist_path = os.path.join(output_dir, "histogram_with_stats.png")
    plot_histogram_with_stats(distances, hist_path, threshold=bad_thr)
    print(f"Saved: {hist_path}")

    # Visuals + analysis maps
    ref_np = ref.detach().cpu().permute(1, 2, 0).numpy()
    cap_np = cap.detach().cpu().permute(1, 2, 0).numpy()

    print("Generating luma/log-radiance/contour maps...")
    analysis_outputs = generate_analysis_maps(ref_np, cap_np, coords_np, distances, H, W, P, S, edge_band, output_dir)
    for path in analysis_outputs.values():
        print(f"Saved: {path}")

    if heatmap_style in ("pixelated", "all"):
        outp = os.path.join(output_dir, "heatmap_pixelated_scores.png")
        save_heatmap_pixelated(cap_np, coords_np, distances, H, W, P, edge_band, outp,
                               alpha=alpha, score_mode=score_mode, score_topk=score_topk, edge_mask=masks["edge"])
        print(f"Saved: {outp}")

    if heatmap_style in ("hybrid", "all"):
        outp = os.path.join(output_dir, "heatmap_hybrid_scores.png")
        save_heatmap_hybrid(cap_np, coords_np, distances, H, W, P, edge_band, outp,
                            alpha=alpha, score_mode=score_mode, score_topk=score_topk, edge_mask=masks["edge"])
        print(f"Saved: {outp}")

    # Worst patch crops (simple + helpful)
    if topn_patches > 0:
        print(f"Saving top-{topn_patches} worst patches...")
        idx = np.argsort(distances)[-topn_patches:][::-1]
        crops_dir = os.path.join(output_dir, "worst_patches")
        ensure_dir(crops_dir)

        for rank, k in enumerate(idx, start=1):
            y0, x0 = coords_np[k]
            r = ref_np[y0:y0+P, x0:x0+P]
            c = cap_np[y0:y0+P, x0:x0+P]

            # side-by-side image
            side = np.concatenate([r, c], axis=1)
            fig, ax = plt.subplots(figsize=(4, 2), dpi=150)
            ax.imshow(side, origin="upper")
            ax.axis("off")
            ax.set_title(f"#{rank} score={distances[k]:.4f}", fontsize=10, weight="bold")
            fig.tight_layout()
            fig.savefig(os.path.join(crops_dir, f"worst_{rank:02d}_score_{distances[k]:.4f}.png"),
                        dpi=150)
            plt.close(fig)
        print(f"Saved: {crops_dir}/ (ref|cap) crops")

    # Optional clustering
    clusters = cluster_bad_patches(coords_np, distances, bad_mask, H, W, P, S, min_cluster=min_cluster)
    if clusters:
        cl_path = os.path.join(output_dir, "cluster_report.csv")
        with open(cl_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(clusters[0].keys()))
            w.writeheader()
            w.writerows(clusters)
        print(f"Saved: {cl_path}  (clusters >= {min_cluster} patches)")
    else:
        print(f"No clusters found (min_cluster={min_cluster}).")

    # Console summary
    print("\n==================== SUMMARY ====================")
    key = {r["region"]: r for r in region_stats}
    for region in ["global", "edge", "center", "corner_TL", "corner_TR", "corner_BL", "corner_BR"]:
        if region in key:
            r = key[region]
            print(f"{region:>10}: mean={r['mean']:.5f} std={r['std']:.5f} P95={r['P95']:.5f} GM={r['GM']:.5f} N={r['count']}")
    print(f"Bad threshold ({bad_mode}): {bad_thr:.5f}   bad%={100*np.mean(bad_mask):.2f}%")
    print("=================================================\n")


# =============================================================================
# CLI
# =============================================================================
# =========================
# FIXED main() for SPADE_5.py
# - Uses your previous default paths (so `python SPADE_5.py` works)
# - Adds --no_defaults to force explicit CLI paths when you want
# - Keeps everything else the same
# =========================

def main():
    import argparse
    import os
    import torch

    # ---- PREVIOUS DEFAULTS (your details) ----
    DEFAULT_REF = "/Users/system_box/Documents/Tasks_DPE/Quick/ABG rendering tool samples/ref_ABG/IMG_0057.JPG"
    DEFAULT_CAP = "/Users/system_box/Documents/Tasks_DPE/Quick/ABG rendering tool samples/distort_ABG/IMG_0057.JPG"
    DEFAULT_OUT = "/Users/system_box/Documents/Tasks_DPE"

    parser = argparse.ArgumentParser(
        description="OLED Display Quality Validator (no knob sensitivity)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Paths (now real defaults)
    parser.add_argument("--ref", default=DEFAULT_REF, help="Path to reference image")
    parser.add_argument("--cap", default=DEFAULT_CAP, help="Path to captured/test image (aligned to ref)")
    parser.add_argument("--out", default=DEFAULT_OUT, help="Output directory")

    # Strict mode toggle
    parser.add_argument(
        "--no_defaults",
        action="store_true",
        help="Require --ref/--cap/--out explicitly (ignore built-in defaults)."
    )

    # Patch analysis parameters
    parser.add_argument("--patch", type=int, default=64, help="Patch size (default 64)")
    parser.add_argument("--stride", type=int, default=64, help="Stride (default 64; smaller for denser)")
    parser.add_argument("--edge_band", type=int, default=64, help="Edge band width (pixels)")

    # Processing parameters
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"], help="cpu or cuda")
    parser.add_argument("--batch", type=int, default=512, help="Patch scoring batch size")

    # Heatmaps
    parser.add_argument("--heatmap_style", default="all",
                        choices=["pixelated", "hybrid", "all"],
                        help="Which heatmaps to generate")
    parser.add_argument("--alpha", type=float, default=0.4, help="Overlay alpha (0..1)")

    # Per-patch text rendering
    parser.add_argument("--score_mode", default="all",
                        choices=["all", "all_sparse", "topk", "edge_topk"],
                        help="How to show patch scores on heatmaps (all = every cell)")
    parser.add_argument("--score_topk", type=int, default=30,
                        help="K for topk/edge_topk modes")

    # Metric selection
    parser.add_argument("--use_ml", action="store_true", help="Use your custom ML metric hook")
    parser.add_argument("--use_baseline", action="store_true", help="Force baseline metric (ignore ML)")

    # Clustering thresholds (local)
    parser.add_argument("--bad_mode", default="percentile", choices=["percentile", "absolute"],
                        help="How to mark 'bad' patches for clustering")
    parser.add_argument("--bad_percentile", type=float, default=95.0,
                        help="If bad_mode=percentile: patches >= this percentile are bad")
    parser.add_argument("--bad_absolute", type=float, default=0.05,
                        help="If bad_mode=absolute: patches >= this distance are bad")
    parser.add_argument("--min_cluster", type=int, default=4,
                        help="Minimum connected bad patches to count as a defect cluster")

    # Worst patch crops
    parser.add_argument("--topn_patches", type=int, default=20,
                        help="Save top-N worst patch crops (0 disables)")

    args = parser.parse_args()

    # ---- decide metric mode ----
    # default: baseline unless user explicitly enables ML
    use_ml = False
    if args.use_baseline:
        use_ml = False
    elif args.use_ml:
        use_ml = True

    # ---- strict mode enforcement ----
    if args.no_defaults:
        # If user didn't override defaults, force them to pass explicit paths
        if args.ref == DEFAULT_REF or args.cap == DEFAULT_CAP or args.out == DEFAULT_OUT:
            parser.error("--no_defaults set: please provide --ref, --cap, and --out explicitly.")

    # ---- validate paths ----
    if not os.path.isfile(args.ref):
        parser.error(f"--ref not found: {args.ref}")
    if not os.path.isfile(args.cap):
        parser.error(f"--cap not found: {args.cap}")
    os.makedirs(args.out, exist_ok=True)

    # ---- device availability ----
    if args.device == "cuda" and not torch.cuda.is_available():
        print("WARNING: CUDA requested but not available. Falling back to CPU.")
        args.device = "cpu"

    cfg = {
        "patch_size": args.patch,
        "stride": args.stride,
        "edge_band": args.edge_band,
        "device": args.device,
        "batch": args.batch,
        "alpha": args.alpha,
        "heatmap_style": args.heatmap_style,
        "score_mode": args.score_mode,
        "score_topk": args.score_topk,
        "topn_patches": args.topn_patches,
        "bad_mode": args.bad_mode,
        "bad_percentile": args.bad_percentile,
        "bad_absolute": args.bad_absolute,
        "min_cluster": args.min_cluster,
        "thresholds": {
            "good": 0.01,     # keep your defaults here
            "warning": 0.05,
        },
        "use_ml": use_ml,
    }

    validate_oled_display(args.ref, args.cap, args.out, cfg)
    print("Done.\n")


if __name__ == "__main__":
    main()
