"""
Pluggable perceptual metrics.
"""
import numpy as np
from typing import Optional
from .base import MetricPlugin


class L2Metric(MetricPlugin):
    """Euclidean (L2) distance metric."""
    
    def __init__(self, config: Optional[dict] = None):
        super().__init__("l2", config)
    
    def compute(self, ref_patches: np.ndarray, cap_patches: np.ndarray) -> np.ndarray:
        """Compute L2 distance."""
        diff = ref_patches - cap_patches
        return np.sqrt(np.mean(diff ** 2, axis=(1, 2, 3)))


class L1Metric(MetricPlugin):
    """Manhattan (L1) distance metric."""
    
    def __init__(self, config: Optional[dict] = None):
        super().__init__("l1", config)
    
    def compute(self, ref_patches: np.ndarray, cap_patches: np.ndarray) -> np.ndarray:
        """Compute L1 distance."""
        diff = np.abs(ref_patches - cap_patches)
        return np.mean(diff, axis=(1, 2, 3))


class SSIMMetric(MetricPlugin):
    """Structural Similarity Index (SSIM) metric."""
    
    def __init__(self, config: Optional[dict] = None):
        super().__init__("ssim", config)
        self.k1 = self.config.get("k1", 0.01)
        self.k2 = self.config.get("k2", 0.03)
        self.L = self.config.get("L", 1.0)  # Dynamic range
        
        self.c1 = (self.k1 * self.L) ** 2
        self.c2 = (self.k2 * self.L) ** 2
    
    def compute(self, ref_patches: np.ndarray, cap_patches: np.ndarray) -> np.ndarray:
        """
        Compute 1 - SSIM (lower SSIM = higher distance).
        Returns values in [0, 2] where 0 = perfect match.
        """
        # Compute means
        mu1 = ref_patches.mean(axis=(1, 2, 3), keepdims=True)
        mu2 = cap_patches.mean(axis=(1, 2, 3), keepdims=True)
        
        # Compute variances and covariance
        mu1_sq = mu1 ** 2
        mu2_sq = mu2 ** 2
        mu1_mu2 = mu1 * mu2
        
        sigma1_sq = np.mean((ref_patches - mu1) ** 2, axis=(1, 2, 3), keepdims=True)
        sigma2_sq = np.mean((cap_patches - mu2) ** 2, axis=(1, 2, 3), keepdims=True)
        sigma12 = np.mean((ref_patches - mu1) * (cap_patches - mu2), axis=(1, 2, 3), keepdims=True)
        
        # SSIM formula
        numerator = (2 * mu1_mu2 + self.c1) * (2 * sigma12 + self.c2)
        denominator = (mu1_sq + mu2_sq + self.c1) * (sigma1_sq + sigma2_sq + self.c2)
        ssim = numerator / (denominator + 1e-12)
        
        # Convert to distance (1 - SSIM)
        return (1.0 - ssim.squeeze()).astype(np.float32)


class PSNRMetric(MetricPlugin):
    """Peak Signal-to-Noise Ratio metric."""
    
    def __init__(self, config: Optional[dict] = None):
        super().__init__("psnr", config)
        self.max_val = self.config.get("max_val", 1.0)
    
    def compute(self, ref_patches: np.ndarray, cap_patches: np.ndarray) -> np.ndarray:
        """
        Compute -PSNR (higher PSNR = lower distance).
        Returns negative PSNR so higher values indicate worse quality.
        """
        mse = np.mean((ref_patches - cap_patches) ** 2, axis=(1, 2, 3))
        psnr = 10 * np.log10(self.max_val ** 2 / (mse + 1e-12))
        return -psnr  # Negate so higher = worse


class WeightedMetric(MetricPlugin):
    """Combine multiple metrics with weights."""
    
    def __init__(self, metrics: list, weights: list, config: Optional[dict] = None):
        super().__init__("weighted", config)
        if len(metrics) != len(weights):
            raise ValueError("Number of metrics must match number of weights")
        self.metrics = metrics
        self.weights = np.array(weights, dtype=np.float32)
        self.weights /= self.weights.sum()  # Normalize
    
    @property
    def requires_gpu(self) -> bool:
        return any(m.requires_gpu for m in self.metrics)
    
    def compute(self, ref_patches: np.ndarray, cap_patches: np.ndarray) -> np.ndarray:
        """Compute weighted combination of metrics."""
        distances = []
        for metric in self.metrics:
            dist = metric.compute(ref_patches, cap_patches)
            distances.append(dist)
        
        # Stack and weight
        distances = np.stack(distances, axis=1)  # (N, M)
        weighted = distances @ self.weights  # (N,)
        
        return weighted


class PerceptualMetric(MetricPlugin):
    """
    Perceptual metric using luminance + chrominance weighting.
    Mimics human visual sensitivity.
    """
    
    def __init__(self, config: Optional[dict] = None):
        super().__init__("perceptual", config)
        # ITU-R BT.709 luma weights
        self.luma_weights = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
        # Weight luma errors more than chroma
        self.luma_factor = self.config.get("luma_factor", 2.0)
    
    def compute(self, ref_patches: np.ndarray, cap_patches: np.ndarray) -> np.ndarray:
        """
        Compute perceptually-weighted distance.
        """
        # Compute per-channel differences
        diff = np.abs(ref_patches - cap_patches)  # (N, H, W, C)
        
        # Compute luma and chroma errors separately
        luma_diff = diff @ self.luma_weights  # (N, H, W)
        chroma_diff = diff - luma_diff[..., None]  # (N, H, W, C)
        
        # Weight and combine
        luma_error = np.mean(luma_diff ** 2, axis=(1, 2)) * self.luma_factor
        chroma_error = np.mean(chroma_diff ** 2, axis=(1, 2, 3))
        
        return np.sqrt(luma_error + chroma_error)


class AdaptiveMetric(MetricPlugin):
    """
    Adaptive metric that adjusts based on local content.
    More sensitive in flat regions, less in textured areas.
    """
    
    def __init__(self, config: Optional[dict] = None):
        super().__init__("adaptive", config)
        self.texture_threshold = self.config.get("texture_threshold", 0.1)
    
    def compute(self, ref_patches: np.ndarray, cap_patches: np.ndarray) -> np.ndarray:
        """Compute content-adaptive distance."""
        # Compute base L2 distance
        diff = ref_patches - cap_patches
        base_dist = np.sqrt(np.mean(diff ** 2, axis=(1, 2, 3)))
        
        # Compute local texture measure (std dev)
        texture = ref_patches.std(axis=(1, 2, 3))
        
        # Adaptive weighting: higher weight in flat regions
        weight = 1.0 / (1.0 + texture / self.texture_threshold)
        
        return base_dist * weight


def create_metric(name: str, config: Optional[dict] = None) -> MetricPlugin:
    """
    Factory function to create metrics by name.
    
    Args:
        name: Metric name ("l2", "l1", "ssim", "psnr", "perceptual", "adaptive")
        config: Optional configuration dict
    
    Returns:
        MetricPlugin instance
    """
    name = name.lower()
    
    if name == "l2":
        return L2Metric(config)
    elif name == "l1":
        return L1Metric(config)
    elif name == "ssim":
        return SSIMMetric(config)
    elif name == "psnr":
        return PSNRMetric(config)
    elif name == "perceptual":
        return PerceptualMetric(config)
    elif name == "adaptive":
        return AdaptiveMetric(config)
    else:
        raise ValueError(f"Unknown metric: {name}. Available: l2, l1, ssim, psnr, perceptual, adaptive")


def compute_multi_metric(ref_patches: np.ndarray, 
                        cap_patches: np.ndarray,
                        metrics: list) -> dict:
    """
    Compute multiple metrics efficiently.
    
    Args:
        ref_patches: (N, H, W, C) reference patches
        cap_patches: (N, H, W, C) capture patches
        metrics: List of MetricPlugin instances
    
    Returns:
        Dictionary mapping metric name to distances array
    """
    results = {}
    
    for metric in metrics:
        distances = metric.compute(ref_patches, cap_patches)
        results[metric.name] = distances
    
    return results
