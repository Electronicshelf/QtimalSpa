"""
Image I/O and preprocessing utilities.
"""
import os
import numpy as np
from PIL import Image
from typing import Tuple, Optional, Union
import warnings


def load_image(path: str, target_dtype: str = "float32") -> np.ndarray:
    """
    Load image from file and convert to numpy array.
    
    Args:
        path: Path to image file
        target_dtype: Target dtype ("float32", "uint8", "uint16")
    
    Returns:
        image: (H, W, C) numpy array
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Image not found: {path}")
    
    img = Image.open(path)
    
    # Convert to RGB if needed
    if img.mode != "RGB":
        img = img.convert("RGB")
    
    # Convert to numpy
    arr = np.array(img)
    
    # Convert dtype
    if target_dtype == "float32":
        if arr.dtype == np.uint8:
            arr = arr.astype(np.float32) / 255.0
        elif arr.dtype == np.uint16:
            arr = arr.astype(np.float32) / 65535.0
        else:
            arr = arr.astype(np.float32)
    elif target_dtype == "uint8":
        if arr.dtype == np.float32:
            arr = (arr * 255).clip(0, 255).astype(np.uint8)
        elif arr.dtype == np.uint16:
            arr = (arr / 256).astype(np.uint8)
    elif target_dtype == "uint16":
        if arr.dtype == np.float32:
            arr = (arr * 65535).clip(0, 65535).astype(np.uint16)
        elif arr.dtype == np.uint8:
            arr = (arr * 257).astype(np.uint16)
    
    return arr


def save_image(arr: np.ndarray, path: str, quality: int = 95):
    """
    Save numpy array as image.
    
    Args:
        arr: (H, W, C) or (H, W) numpy array
        path: Output path
        quality: JPEG quality (1-100)
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    
    # Convert to uint8
    if arr.dtype == np.float32 or arr.dtype == np.float64:
        arr = (arr * 255).clip(0, 255).astype(np.uint8)
    elif arr.dtype == np.uint16:
        arr = (arr / 256).astype(np.uint8)
    
    # Handle grayscale
    if arr.ndim == 2:
        img = Image.fromarray(arr, mode="L")
    else:
        img = Image.fromarray(arr, mode="RGB")
    
    # Save with appropriate settings
    if path.lower().endswith(('.jpg', '.jpeg')):
        img.save(path, quality=quality, optimize=True)
    elif path.lower().endswith('.png'):
        img.save(path, compress_level=6, optimize=True)
    else:
        img.save(path)


def validate_image_pair(ref: np.ndarray, cap: np.ndarray, 
                       strict: bool = False) -> Tuple[bool, str]:
    """
    Validate that reference and capture images are compatible.
    
    Args:
        ref: Reference image array
        cap: Capture image array
        strict: If True, require exact shape match
    
    Returns:
        (is_valid, message)
    """
    # Check shapes
    if ref.shape != cap.shape:
        if strict:
            return False, f"Shape mismatch: ref {ref.shape} vs cap {cap.shape}"
        elif ref.shape[:2] != cap.shape[:2]:
            return False, f"Spatial dimension mismatch: ref {ref.shape[:2]} vs cap {cap.shape[:2]}"
        else:
            warnings.warn(f"Channel mismatch: ref {ref.shape[2]} vs cap {cap.shape[2]}, will crop")
    
    # Check dtype
    if ref.dtype != cap.dtype:
        warnings.warn(f"Dtype mismatch: ref {ref.dtype} vs cap {cap.dtype}, may cause precision issues")
    
    # Check value range
    if ref.dtype == np.float32:
        if ref.min() < 0 or ref.max() > 1:
            warnings.warn(f"Reference values outside [0, 1]: [{ref.min():.3f}, {ref.max():.3f}]")
        if cap.min() < 0 or cap.max() > 1:
            warnings.warn(f"Capture values outside [0, 1]: [{cap.min():.3f}, {cap.max():.3f}]")
    
    return True, "Valid"


def preprocess_image_pair(ref: np.ndarray, cap: np.ndarray,
                         align_channels: bool = True) -> Tuple[np.ndarray, np.ndarray]:
    """
    Preprocess image pair for analysis.
    
    Args:
        ref: Reference image
        cap: Capture image
        align_channels: If True, align channel counts
    
    Returns:
        (ref_processed, cap_processed)
    """
    ref = np.asarray(ref, dtype=np.float32)
    cap = np.asarray(cap, dtype=np.float32)
    
    # Ensure 3D
    if ref.ndim == 2:
        ref = ref[..., None]
    if cap.ndim == 2:
        cap = cap[..., None]
    
    # Align channels if needed
    if align_channels and ref.shape[2] != cap.shape[2]:
        min_c = min(ref.shape[2], cap.shape[2])
        ref = ref[..., :min_c]
        cap = cap[..., :min_c]
    
    # Ensure float32 in [0, 1]
    ref = np.clip(ref, 0.0, 1.0)
    cap = np.clip(cap, 0.0, 1.0)
    
    return ref, cap


def compute_image_histogram(image: np.ndarray, bins: int = 256) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute normalized histogram of image.
    
    Args:
        image: Input image array
        bins: Number of histogram bins
    
    Returns:
        (hist, bin_edges)
    """
    flat = image.ravel()
    hist, edges = np.histogram(flat, bins=bins, range=(0.0, 1.0), density=True)
    return hist, edges


def compute_image_stats(image: np.ndarray) -> dict:
    """
    Compute comprehensive image statistics.
    
    Args:
        image: (H, W, C) image array
    
    Returns:
        Dictionary of statistics
    """
    return {
        "shape": image.shape,
        "dtype": str(image.dtype),
        "mean": float(image.mean()),
        "std": float(image.std()),
        "min": float(image.min()),
        "max": float(image.max()),
        "median": float(np.median(image)),
        "percentile_1": float(np.percentile(image, 1)),
        "percentile_99": float(np.percentile(image, 99)),
    }


def crop_to_multiple(image: np.ndarray, multiple: int = 64) -> np.ndarray:
    """
    Crop image dimensions to be multiples of a given value.
    Useful for ensuring patch extraction works cleanly.
    
    Args:
        image: Input image
        multiple: Crop to multiples of this value
    
    Returns:
        Cropped image
    """
    H, W = image.shape[:2]
    H_new = (H // multiple) * multiple
    W_new = (W // multiple) * multiple
    
    if H_new != H or W_new != W:
        warnings.warn(f"Cropping image from {H}x{W} to {H_new}x{W_new}")
        return image[:H_new, :W_new]
    
    return image


def resize_image(image: np.ndarray, size: Tuple[int, int], 
                method: str = "lanczos") -> np.ndarray:
    """
    Resize image using PIL.
    
    Args:
        image: Input image
        size: Target (width, height)
        method: Resampling method ("lanczos", "bilinear", "nearest")
    
    Returns:
        Resized image
    """
    # Convert to uint8 for PIL
    if image.dtype == np.float32:
        img_uint8 = (image * 255).clip(0, 255).astype(np.uint8)
    else:
        img_uint8 = image
    
    # Convert to PIL
    if img_uint8.ndim == 2:
        pil_img = Image.fromarray(img_uint8, mode="L")
    else:
        pil_img = Image.fromarray(img_uint8, mode="RGB")
    
    # Resize
    method_map = {
        "lanczos": Image.LANCZOS,
        "bilinear": Image.BILINEAR,
        "nearest": Image.NEAREST,
        "bicubic": Image.BICUBIC,
    }
    resample = method_map.get(method.lower(), Image.LANCZOS)
    pil_img = pil_img.resize(size, resample=resample)
    
    # Convert back
    arr = np.array(pil_img)
    
    # Restore original dtype
    if image.dtype == np.float32:
        arr = arr.astype(np.float32) / 255.0
    
    return arr


def apply_gamma(image: np.ndarray, gamma: float) -> np.ndarray:
    """
    Apply gamma correction.
    
    Args:
        image: Input image (assumed linear if float32)
        gamma: Gamma value (>1 darkens, <1 brightens)
    
    Returns:
        Gamma-corrected image
    """
    return np.power(np.clip(image, 0.0, 1.0), gamma)


def normalize_image(image: np.ndarray, method: str = "minmax") -> np.ndarray:
    """
    Normalize image values.
    
    Args:
        image: Input image
        method: "minmax" or "zscore"
    
    Returns:
        Normalized image
    """
    if method == "minmax":
        vmin = image.min()
        vmax = image.max()
        if vmax > vmin:
            return (image - vmin) / (vmax - vmin)
        else:
            return image - vmin
    
    elif method == "zscore":
        mean = image.mean()
        std = image.std()
        if std > 0:
            return (image - mean) / std
        else:
            return image - mean
    
    else:
        raise ValueError(f"Unknown normalization method: {method}")
