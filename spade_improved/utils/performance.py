"""
Performance optimization utilities.
"""
import time
import numpy as np
from functools import wraps
from typing import Callable, Any, Optional
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp


class Timer:
    """Context manager for timing code blocks."""
    
    def __init__(self, name: str = "Operation", verbose: bool = True):
        self.name = name
        self.verbose = verbose
        self.elapsed = 0
    
    def __enter__(self):
        self.start = time.time()
        return self
    
    def __exit__(self, *args):
        self.end = time.time()
        self.elapsed = self.end - self.start
        if self.verbose:
            print(f"{self.name}: {self.elapsed:.3f}s")


def timeit(func: Callable) -> Callable:
    """Decorator to time function execution."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"{func.__name__}: {elapsed:.3f}s")
        return result
    return wrapper


class BatchProcessor:
    """Process data in batches for memory efficiency."""
    
    def __init__(self, batch_size: int = 512):
        self.batch_size = batch_size
    
    def process(self, data: np.ndarray, func: Callable) -> np.ndarray:
        """
        Process data in batches.
        
        Args:
            data: (N, ...) input data
            func: Function to apply to each batch
        
        Returns:
            Processed results
        """
        N = len(data)
        results = []
        
        for i in range(0, N, self.batch_size):
            batch = data[i:i + self.batch_size]
            result = func(batch)
            results.append(result)
        
        return np.concatenate(results, axis=0) if results else np.array([])


class ParallelProcessor:
    """Parallel processing using threads or processes."""
    
    def __init__(self, n_workers: Optional[int] = None, use_processes: bool = False):
        self.n_workers = n_workers or mp.cpu_count()
        self.use_processes = use_processes
    
    def map(self, func: Callable, data: list) -> list:
        """
        Apply function to data in parallel.
        
        Args:
            func: Function to apply
            data: List of inputs
        
        Returns:
            List of outputs
        """
        executor_cls = ProcessPoolExecutor if self.use_processes else ThreadPoolExecutor
        
        with executor_cls(max_workers=self.n_workers) as executor:
            results = list(executor.map(func, data))
        
        return results


class MemoryEfficientCache:
    """
    LRU cache with memory limit.
    Evicts least recently used items when memory limit is reached.
    """
    
    def __init__(self, max_size_mb: float = 500):
        self.max_size_mb = max_size_mb
        self._cache = {}
        self._access_times = {}
        self._sizes_mb = {}
        self._current_size_mb = 0
        self._access_counter = 0
    
    def _compute_size_mb(self, obj: Any) -> float:
        """Estimate object size in MB."""
        if isinstance(obj, np.ndarray):
            return obj.nbytes / (1024 * 1024)
        else:
            # Rough estimate for other objects
            return 0.001
    
    def _evict_lru(self):
        """Evict least recently used item."""
        if not self._access_times:
            return
        
        lru_key = min(self._access_times, key=self._access_times.get)
        size = self._sizes_mb[lru_key]
        
        del self._cache[lru_key]
        del self._access_times[lru_key]
        del self._sizes_mb[lru_key]
        
        self._current_size_mb -= size
    
    def put(self, key: str, value: Any):
        """Add item to cache."""
        size_mb = self._compute_size_mb(value)
        
        # Evict if necessary
        while self._current_size_mb + size_mb > self.max_size_mb and self._cache:
            self._evict_lru()
        
        # Add to cache
        self._cache[key] = value
        self._sizes_mb[key] = size_mb
        self._access_times[key] = self._access_counter
        self._access_counter += 1
        self._current_size_mb += size_mb
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache."""
        if key in self._cache:
            self._access_times[key] = self._access_counter
            self._access_counter += 1
            return self._cache[key]
        return None
    
    def clear(self):
        """Clear cache."""
        self._cache.clear()
        self._access_times.clear()
        self._sizes_mb.clear()
        self._current_size_mb = 0
    
    def __contains__(self, key: str) -> bool:
        return key in self._cache
    
    def __len__(self) -> int:
        return len(self._cache)
    
    @property
    def size_mb(self) -> float:
        """Current cache size in MB."""
        return self._current_size_mb


def vectorized_operation(func: Callable) -> Callable:
    """
    Decorator to ensure function operates on vectorized input.
    Automatically batches input if too large.
    """
    @wraps(func)
    def wrapper(data: np.ndarray, *args, max_batch: int = 1000, **kwargs):
        if len(data) <= max_batch:
            return func(data, *args, **kwargs)
        
        # Process in batches
        results = []
        for i in range(0, len(data), max_batch):
            batch = data[i:i + max_batch]
            result = func(batch, *args, **kwargs)
            results.append(result)
        
        return np.concatenate(results, axis=0)
    
    return wrapper


class ProgressTracker:
    """Simple progress tracker for long-running operations."""
    
    def __init__(self, total: int, desc: str = "Processing", verbose: bool = True):
        self.total = total
        self.desc = desc
        self.verbose = verbose
        self.current = 0
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, *args):
        if self.verbose:
            elapsed = time.time() - self.start_time
            print(f"\n{self.desc} completed: {self.total} items in {elapsed:.2f}s")
    
    def update(self, n: int = 1):
        """Update progress by n items."""
        self.current += n
        if self.verbose and self.current % max(1, self.total // 20) == 0:
            pct = (self.current / self.total) * 100
            elapsed = time.time() - self.start_time
            rate = self.current / elapsed if elapsed > 0 else 0
            print(f"\r{self.desc}: {pct:.1f}% ({self.current}/{self.total}) [{rate:.1f} items/s]", 
                  end="", flush=True)


def optimize_numpy_ops():
    """Configure numpy for optimal performance."""
    # Enable multi-threading in numpy operations
    try:
        import os
        # Set number of threads for various libraries
        os.environ['OMP_NUM_THREADS'] = str(mp.cpu_count())
        os.environ['MKL_NUM_THREADS'] = str(mp.cpu_count())
        os.environ['OPENBLAS_NUM_THREADS'] = str(mp.cpu_count())
    except:
        pass


def estimate_memory_usage(height: int, width: int, channels: int, 
                         patch_size: int, stride: int) -> dict:
    """
    Estimate memory usage for patch-based analysis.
    
    Args:
        height: Image height
        width: Image width
        channels: Number of channels
        patch_size: Patch size
        stride: Stride between patches
    
    Returns:
        Dictionary with memory estimates
    """
    # Estimate number of patches
    n_patches_y = max(1, (height - patch_size) // stride + 1)
    n_patches_x = max(1, (width - patch_size) // stride + 1)
    n_patches = n_patches_y * n_patches_x
    
    # Memory per image (float32)
    image_mb = (height * width * channels * 4) / (1024 * 1024)
    
    # Memory for all patches
    patches_mb = (n_patches * patch_size * patch_size * channels * 4) / (1024 * 1024)
    
    # Memory for distances
    distances_mb = (n_patches * 4) / (1024 * 1024)
    
    return {
        "num_patches": n_patches,
        "image_mb": image_mb,
        "patches_mb": patches_mb,
        "distances_mb": distances_mb,
        "total_mb": image_mb * 2 + patches_mb * 2 + distances_mb,
        "recommendation": "OK" if patches_mb < 1000 else "Consider larger stride or smaller patches"
    }


# Initialize numpy optimizations on module import
optimize_numpy_ops()
