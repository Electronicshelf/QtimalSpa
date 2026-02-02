"""
Main SPADE analysis framework orchestration.
"""
import os
import json
import numpy as np
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

from .config import SPADEConfig
from .core.base import PatchExtractor
from .core.patches import EdgeAnchoredExtractor, UniformGridExtractor, PatchCache
from .core.metrics import create_metric, compute_multi_metric
from .plugins.panels import create_panel

from utils.image_utils import (
    load_image, 
    validate_image_pair, 
    preprocess_image_pair,
    compute_image_stats
)
from utils.performance import (
    Timer, 
    BatchProcessor, 
    MemoryEfficientCache,
    ProgressTracker,
    estimate_memory_usage
)


class SPADEAnalyzer:
    """Main SPADE analyzer class."""
    
    def __init__(self, config: Optional[SPADEConfig] = None):
        """
        Initialize analyzer.
        
        Args:
            config: SPADEConfig instance (uses default if None)
        """
        self.config = config or SPADEConfig()
        self._validate_config()
        
        # Initialize components
        self.extractor = self._create_extractor()
        self.metric = self._create_metric()
        self.panel = self._create_panel()
        
        # Caches
        self.patch_cache = PatchCache(max_size_mb=self.config.performance.cache_size_mb) if self.config.performance.use_cache else None
        self.result_cache = MemoryEfficientCache(max_size_mb=100)
        
        # Stats
        self.stats = {}
    
    def _validate_config(self):
        """Validate configuration."""
        errors = self.config.validate()
        if errors:
            raise ValueError(f"Invalid configuration:\n" + "\n".join(errors))
    
    def _create_extractor(self) -> PatchExtractor:
        """Create patch extractor."""
        if self.config.patch.extractor_type == "edge_anchored":
            return EdgeAnchoredExtractor(
                patch_size=self.config.patch.patch_size,
                stride=self.config.patch.stride,
                edge_band=self.config.patch.edge_band
            )
        elif self.config.patch.extractor_type == "uniform":
            return UniformGridExtractor(
                patch_size=self.config.patch.patch_size,
                stride=self.config.patch.stride,
                edge_band=0
            )
        else:
            raise ValueError(f"Unknown extractor type: {self.config.patch.extractor_type}")
    
    def _create_metric(self):
        """Create metric(s)."""
        if self.config.metric.use_multi_metric:
            # Create multiple metrics
            metrics = []
            for name in self.config.metric.multi_metrics:
                metric = create_metric(name, self.config.metric.metric_params)
                metrics.append(metric)
            return metrics
        else:
            return create_metric(self.config.metric.metric_name, self.config.metric.metric_params)
    
    def _create_panel(self):
        """Create panel plugin."""
        if self.config.panel.panel_name is None:
            return None
        
        return create_panel(
            self.config.panel.panel_name,
            json_path=self.config.panel.panel_json_path
        )
    
    def analyze(self, ref_path: str, cap_path: str, output_dir: str) -> Dict[str, Any]:
        """
        Run complete SPADE analysis.
        
        Args:
            ref_path: Path to reference image
            cap_path: Path to capture image
            output_dir: Output directory for results
        
        Returns:
            Dictionary containing analysis results
        """
        print(f"\n{'='*60}")
        print(f"SPADE Analysis")
        print(f"{'='*60}")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Load images
        with Timer("Loading images"):
            ref = load_image(ref_path, target_dtype="float32")
            cap = load_image(cap_path, target_dtype="float32")
        
        # Validate
        valid, msg = validate_image_pair(ref, cap)
        if not valid:
            raise ValueError(f"Image validation failed: {msg}")
        
        # Preprocess
        ref, cap = preprocess_image_pair(ref, cap)
        H, W = ref.shape[:2]
        
        print(f"Image size: {H}x{W}")
        
        # Memory estimation
        mem_est = estimate_memory_usage(
            H, W, ref.shape[2],
            self.config.patch.patch_size,
            self.config.patch.stride
        )
        print(f"Estimated memory: {mem_est['total_mb']:.1f} MB ({mem_est['recommendation']})")
        
        # Extract patches
        with Timer("Extracting patches"):
            coords = self.extractor.extract_coordinates(H, W)
            
            # Use vectorized extraction
            if hasattr(self.extractor, 'extract_patches_vectorized'):
                ref_patches = self.extractor.extract_patches_vectorized(ref, coords)
                cap_patches = self.extractor.extract_patches_vectorized(cap, coords)
            else:
                ref_patches = self.extractor.extract_patches(ref, coords)
                cap_patches = self.extractor.extract_patches(cap, coords)
        
        print(f"Extracted {len(coords)} patches ({self.config.patch.patch_size}x{self.config.patch.patch_size})")
        
        # Apply panel color transform if needed
        if self.panel is not None:
            with Timer("Applying panel color transform"):
                ref_linear = self.panel.to_linear(ref)
                ref_linear = self.panel.apply_transform(ref_linear)
                ref_patches = self.panel.to_linear(ref_patches)
                ref_patches = self.panel.apply_transform(ref_patches)
                
                cap_linear = self.panel.to_linear(cap)
                cap_linear = self.panel.apply_transform(cap_linear)
                cap_patches = self.panel.to_linear(cap_patches)
                cap_patches = self.panel.apply_transform(cap_patches)
        
        # Compute metrics
        with Timer("Computing metrics"):
            if self.config.metric.use_multi_metric:
                # Multi-metric
                distances_dict = compute_multi_metric(ref_patches, cap_patches, self.metric)
                
                # Combine with weights
                weights = np.array(self.config.metric.multi_weights, dtype=np.float32)
                weights /= weights.sum()
                
                distances = sum(
                    distances_dict[m.name] * w 
                    for m, w in zip(self.metric, weights)
                )
            else:
                # Single metric
                batch_processor = BatchProcessor(self.config.performance.batch_size)
                
                def compute_batch(batch_idx):
                    start = batch_idx * self.config.performance.batch_size
                    end = min(start + self.config.performance.batch_size, len(ref_patches))
                    return self.metric.compute(ref_patches[start:end], cap_patches[start:end])
                
                n_batches = (len(ref_patches) + self.config.performance.batch_size - 1) // self.config.performance.batch_size
                distances = []
                
                with ProgressTracker(n_batches, "Computing distances") as pbar:
                    for i in range(n_batches):
                        dist = compute_batch(i)
                        distances.append(dist)
                        pbar.update(1)
                
                distances = np.concatenate(distances)
        
        # Analyze results
        results = self._analyze_distances(distances, coords, H, W)
        results["num_patches"] = len(coords)
        results["metric"] = self.config.metric.metric_name
        results["panel"] = self.config.panel.panel_name
        
        # Generate visualizations
        if any([
            self.config.visualization.generate_heatmaps,
            self.config.visualization.generate_luma_maps,
            self.config.visualization.generate_log_radiance,
            self.config.visualization.generate_contours
        ]):
            with Timer("Generating visualizations"):
                viz_results = self._generate_visualizations(
                    ref, cap, coords, distances, output_dir
                )
                results.update(viz_results)
        
        # Save summary
        summary_path = os.path.join(output_dir, "analysis_summary.json")
        with open(summary_path, "w") as f:
            # Convert numpy types to Python types for JSON
            json_results = {}
            for k, v in results.items():
                if isinstance(v, np.ndarray):
                    json_results[k] = v.tolist()
                elif isinstance(v, (np.integer, np.floating)):
                    json_results[k] = v.item()
                else:
                    json_results[k] = v
            
            json.dump(json_results, f, indent=2)
        
        print(f"\n{'='*60}")
        print(f"Analysis complete!")
        print(f"Results saved to: {output_dir}")
        print(f"{'='*60}\n")
        
        return results
    
    def _analyze_distances(self, distances: np.ndarray, 
                          coords: np.ndarray, 
                          height: int, width: int) -> Dict[str, Any]:
        """Analyze distance statistics."""
        results = {
            "mean_distance": float(distances.mean()),
            "std_distance": float(distances.std()),
            "min_distance": float(distances.min()),
            "max_distance": float(distances.max()),
            "median_distance": float(np.median(distances)),
        }
        
        # Find worst patches
        topk = min(self.config.analysis.score_topk, len(distances))
        worst_indices = np.argsort(distances)[-topk:][::-1]
        
        results["worst_patches"] = {
            "indices": worst_indices.tolist(),
            "coordinates": coords[worst_indices].tolist(),
            "distances": distances[worst_indices].tolist(),
        }
        
        # Threshold analysis
        for name, threshold in self.config.analysis.thresholds.items():
            count = int(np.sum(distances > threshold))
            pct = (count / len(distances)) * 100
            results[f"{name}_threshold"] = {
                "value": threshold,
                "count": count,
                "percentage": pct
            }
        
        return results
    
    def _generate_visualizations(self, ref: np.ndarray, cap: np.ndarray,
                                coords: np.ndarray, distances: np.ndarray,
                                output_dir: str) -> Dict[str, str]:
        """Generate visualization outputs."""
        viz_paths = {}
        
        # Import visualization modules lazily
        from utils.image_utils import save_image
        
        # Generate heatmap (simplified version)
        if self.config.visualization.generate_heatmaps:
            import matplotlib.pyplot as plt
            from matplotlib.patches import Rectangle
            
            H, W = cap.shape[:2]
            P = self.config.patch.patch_size
            
            fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=150)
            ax.imshow(cap)
            
            # Draw patches colored by distance
            vmax = np.percentile(distances, 95)
            cmap = plt.cm.get_cmap('hot')
            
            for (y, x), dist in zip(coords, distances):
                color = cmap(min(dist / vmax, 1.0))
                rect = Rectangle((x, y), P, P, linewidth=0, 
                               facecolor=color, 
                               alpha=self.config.visualization.heatmap_alpha)
                ax.add_patch(rect)
            
            ax.axis('off')
            ax.set_title('SPADE Analysis Heatmap', fontsize=12, weight='bold')
            
            heatmap_path = os.path.join(output_dir, 'heatmap.png')
            plt.tight_layout()
            plt.savefig(heatmap_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            viz_paths['heatmap'] = heatmap_path
        
        return viz_paths


def run_analysis(ref_path: str, cap_path: str, output_dir: str, 
                config: Optional[SPADEConfig] = None) -> Dict[str, Any]:
    """
    Convenient function to run analysis with default or provided config.
    
    Args:
        ref_path: Path to reference image
        cap_path: Path to capture image
        output_dir: Output directory
        config: Optional configuration
    
    Returns:
        Analysis results dictionary
    """
    analyzer = SPADEAnalyzer(config)
    return analyzer.analyze(ref_path, cap_path, output_dir)


def quick_analysis(ref_path: str, cap_path: str, output_dir: str, 
                  preset: str = "default") -> Dict[str, Any]:
    """
    Run quick analysis with preset configuration.
    
    Args:
        ref_path: Path to reference image
        cap_path: Path to capture image
        output_dir: Output directory
        preset: Preset name ("default", "fast", "quality")
    
    Returns:
        Analysis results dictionary
    """
    from .config import load_preset
    config = load_preset(preset)
    return run_analysis(ref_path, cap_path, output_dir, config)
