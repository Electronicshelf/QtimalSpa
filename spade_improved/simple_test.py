"""
SIMPLEST POSSIBLE SPADE EXAMPLE
Run this in PyCharm to test your setup!

This example doesn't need any images - it just tests that SPADE works.
"""

print("="*60)
print("Testing SPADE Installation")
print("="*60)

# Step 1: Test imports
print("\n1. Testing imports...")
try:
    from spade import SPADEConfig
    print("   ✓ Imports working!")
except ImportError as e:
    print(f"   ✗ Import error: {e}")
    print("\n   Fix:")
    print("   Option A: Run in terminal: pip install -e .")
    print("   Option B: Add this at top of script:")
    print("       import sys")
    print("       sys.path.insert(0, '/path/to/spade_improved')")
    exit(1)

# Step 2: Create configuration
print("\n2. Creating configuration...")
config = SPADEConfig()
config.patch.patch_size = 64
config.patch.stride = 64
config.metric.metric_name = "l2"
print(f"   ✓ Config created! Patch size: {config.patch.patch_size}")

# Step 3: Test metric
print("\n3. Testing metric...")
try:
    from spade.core.metrics import L2Metric
    import numpy as np
    
    metric = L2Metric()
    
    # Create tiny fake patches
    ref = np.random.rand(5, 32, 32, 3).astype(np.float32)
    cap = np.random.rand(5, 32, 32, 3).astype(np.float32)
    
    distances = metric.compute(ref, cap)
    print(f"   ✓ Metric works! Computed {len(distances)} distances")
    print(f"   Mean distance: {distances.mean():.6f}")
except Exception as e:
    print(f"   ✗ Metric test failed: {e}")
    exit(1)

# Step 4: Test panel
print("\n4. Testing panel...")
try:
    from spade import create_panel
    panel = create_panel("SRGB")
    print(f"   ✓ Panel works! Created {panel.name} panel")
except Exception as e:
    print(f"   ✗ Panel test failed: {e}")
    exit(1)

# Success!
print("\n" + "="*60)
print("✓✓✓ SUCCESS! SPADE IS WORKING! ✓✓✓")
print("="*60)

print("\nNext steps:")
print("  1. Try with real images:")
print("     from spade import quick_analysis")
print("     results = quick_analysis('ref.png', 'cap.png', 'output')")
print("")
print("  2. Check examples/basic_examples.py")
print("")
print("  3. Read QUICKSTART.md for full guide")

print("\n" + "="*60)
