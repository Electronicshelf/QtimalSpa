"""
Utility modules for SPADE.
"""

from .image_utils import (
    load_image,
    save_image,
    validate_image_pair,
    preprocess_image_pair,
    compute_image_histogram,
    compute_image_stats,
    crop_to_multiple,
    resize_image,
    apply_gamma,
    normalize_image,
)

from .performance import (
    Timer,
    timeit,
    BatchProcessor,
    ParallelProcessor,
    MemoryEfficientCache,
    vectorized_operation,
    ProgressTracker,
    optimize_numpy_ops,
    estimate_memory_usage,
)

__all__ = [
    # Image utilities
    "load_image",
    "save_image",
    "validate_image_pair",
    "preprocess_image_pair",
    "compute_image_histogram",
    "compute_image_stats",
    "crop_to_multiple",
    "resize_image",
    "apply_gamma",
    "normalize_image",
    
    # Performance utilities
    "Timer",
    "timeit",
    "BatchProcessor",
    "ParallelProcessor",
    "MemoryEfficientCache",
    "vectorized_operation",
    "ProgressTracker",
    "optimize_numpy_ops",
    "estimate_memory_usage",
]
