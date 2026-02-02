"""
Test script to verify SPADE installation works correctly.
Run this in PyCharm to test your setup.
"""

def test_imports():
    """Test that all core imports work."""
    print("Testing SPADE imports...")
    
    try:
        # Test main imports
        from spade import quick_analysis, generate_report
        print("✓ Main imports work")
    except ImportError as e:
        print(f"✗ Main imports failed: {e}")
        return False
    
    try:
        # Test configuration
        from spade import SPADEConfig
        config = SPADEConfig()
        print("✓ Configuration works")
    except Exception as e:
        print(f"✗ Configuration failed: {e}")
        return False
    
    try:
        # Test plugins
        from spade import create_metric, create_panel
        metric = create_metric("l2")
        panel = create_panel("SRGB")
        print("✓ Plugin system works")
    except Exception as e:
        print(f"✗ Plugin system failed: {e}")
        return False
    
    try:
        # Test utils
        from utils import load_image, Timer
        print("✓ Utility imports work")
    except Exception as e:
        print(f"✗ Utility imports failed: {e}")
        return False
    
    return True


def test_basic_functionality():
    """Test basic functionality without actual images."""
    print("\nTesting basic functionality...")
    
    try:
        from spade import SPADEConfig
        import numpy as np
        
        # Create config
        config = SPADEConfig()
        config.patch.patch_size = 64
        config.metric.metric_name = "perceptual"
        print("✓ Configuration creation works")
        
        # Test metric
        from spade.core.metrics import L2Metric
        metric = L2Metric()
        
        # Create fake patches
        ref_patches = np.random.rand(10, 64, 64, 3).astype(np.float32)
        cap_patches = np.random.rand(10, 64, 64, 3).astype(np.float32)
        
        # Compute distances
        distances = metric.compute(ref_patches, cap_patches)
        print(f"✓ Metric computation works (computed {len(distances)} distances)")
        
        return True
        
    except Exception as e:
        print(f"✗ Basic functionality failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dependencies():
    """Test that required dependencies are installed."""
    print("\nChecking dependencies...")
    
    deps = {
        'numpy': None,
        'PIL': 'pillow',
        'matplotlib': None
    }
    
    all_ok = True
    for module, package in deps.items():
        try:
            __import__(module)
            print(f"✓ {package or module} installed")
        except ImportError:
            print(f"✗ {package or module} NOT installed - run: pip install {package or module}")
            all_ok = False
    
    return all_ok


if __name__ == '__main__':
    print("="*60)
    print("SPADE 2.0 Installation Test")
    print("="*60)
    
    # Test dependencies first
    deps_ok = test_dependencies()
    
    if not deps_ok:
        print("\n" + "="*60)
        print("Install missing dependencies with:")
        print("  pip install numpy pillow matplotlib")
        print("="*60)
    else:
        # Test imports
        imports_ok = test_imports()
        
        # Test functionality
        if imports_ok:
            func_ok = test_basic_functionality()
            
            if func_ok:
                print("\n" + "="*60)
                print("✓✓✓ ALL TESTS PASSED ✓✓✓")
                print("="*60)
                print("\nSPADE is ready to use!")
                print("\nNext steps:")
                print("  1. Check examples/basic_examples.py")
                print("  2. Try: from spade import quick_analysis")
                print("  3. Read QUICKSTART.md for full guide")
            else:
                print("\n" + "="*60)
                print("✗ Some tests failed")
                print("="*60)
        else:
            print("\n" + "="*60)
            print("✗ Import tests failed")
            print("="*60)
            print("\nMake sure you've installed SPADE:")
            print("  pip install -e .")
            print("\nOr set PYTHONPATH:")
            print("  export PYTHONPATH=/path/to/spade_improved")
