# PyCharm Setup Guide - SPADE 2.0

## 🔧 Quick Fix for PyCharm Issues

### Method 1: Install as Package (EASIEST - Recommended)

1. **Extract the archive**
   ```bash
   tar -xzf spade_v2_with_reports.tar.gz
   cd spade_improved
   ```

2. **Open in PyCharm**
   - File → Open → Select `spade_improved` folder
   - Click "OK"

3. **Install dependencies**
   
   Open PyCharm Terminal (Alt+F12 or View → Tool Windows → Terminal):
   ```bash
   pip install numpy pillow matplotlib
   ```

4. **Install SPADE in development mode**
   
   In the same terminal:
   ```bash
   pip install -e .
   ```
   
   This installs SPADE so you can import it from anywhere.

5. **Test it works**
   
   Run the test script:
   ```bash
   python test_installation.py
   ```
   
   You should see:
   ```
   ✓✓✓ ALL TESTS PASSED ✓✓✓
   SPADE is ready to use!
   ```

6. **Start using SPADE**
   
   Create a new Python file anywhere in the project:
   ```python
   from spade import quick_analysis, generate_report
   print("SPADE loaded successfully!")
   ```

---

## Method 2: If `pip install -e .` Doesn't Work

### Option A: Set Python Path in PyCharm

1. **Open PyCharm Settings**
   - File → Settings (Windows/Linux)
   - PyCharm → Preferences (Mac)

2. **Add Content Root**
   - Project → Project Structure
   - Click on `spade_improved` folder
   - Click "Add Content Root"
   - Select the `spade_improved` folder
   - Click "OK"

3. **Mark directories**
   - In Project view, right-click `spade_improved` folder
   - Mark Directory as → Sources Root
   
4. **Test imports**
   ```python
   from spade import quick_analysis
   print("Works!")
   ```

### Option B: Manual PYTHONPATH

1. **Edit Run Configuration**
   - Run → Edit Configurations
   - Click "+" → Python
   - Set Script path to your script
   - In "Environment variables", add:
     ```
     PYTHONPATH=/path/to/spade_improved
     ```

2. **Or add at top of your script**
   ```python
   import sys
   import os
   
   # Add SPADE to path
   spade_dir = os.path.abspath(os.path.dirname(__file__))
   if spade_dir not in sys.path:
       sys.path.insert(0, spade_dir)
   
   # Now import works
   from spade import quick_analysis
   ```

---

## Common Issues & Solutions

### Issue 1: "No module named 'spade'"

**Solution A:** Install as package
```bash
cd spade_improved
pip install -e .
```

**Solution B:** Add to sys.path
```python
import sys
sys.path.insert(0, '/full/path/to/spade_improved')
from spade import quick_analysis
```

**Solution C:** Mark as Sources Root
- Right-click `spade_improved` folder in PyCharm
- Mark Directory as → Sources Root

---

### Issue 2: "No module named 'utils'"

This happens when trying to import from examples.

**Solution:** Use absolute imports
```python
# Instead of:
from utils import load_image  # ✗ Wrong

# Do this:
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import load_image  # ✓ Correct
```

**Or install the package:**
```bash
pip install -e .
```

---

### Issue 3: "ImportError: cannot import name 'generate_report'"

**Solution:** Make sure you have the latest version and installed it:
```bash
cd spade_improved
pip install -e . --force-reinstall
```

---

### Issue 4: PyCharm can't find dependencies (numpy, PIL, matplotlib)

**Solution:** Install in PyCharm's Python interpreter

**Method 1 - Terminal:**
```bash
pip install numpy pillow matplotlib
```

**Method 2 - PyCharm UI:**
- File → Settings → Project → Python Interpreter
- Click "+"
- Search for: numpy, pillow, matplotlib
- Click "Install Package"

---

## Running Examples

### From PyCharm

1. **Open an example file**
   - `examples/basic_examples.py`

2. **Right-click in the editor**
   - Run 'basic_examples'

3. **Or use terminal**
   ```bash
   cd examples
   python basic_examples.py
   ```

### If examples don't work

Add this to the top of the example file:
```python
import sys
from pathlib import Path
# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

---

## Testing Your Setup

### Quick Test

Create `test_spade.py` anywhere in the project:

```python
"""Quick test to verify SPADE works."""

def test_spade():
    try:
        # Test imports
        from spade import SPADEConfig, quick_analysis, generate_report
        print("✓ Imports work")
        
        # Test configuration
        config = SPADEConfig()
        config.patch.patch_size = 64
        print("✓ Configuration works")
        
        # Test metric creation
        from spade import create_metric
        metric = create_metric("l2")
        print("✓ Metrics work")
        
        print("\n✓✓✓ SPADE is working correctly! ✓✓✓")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_spade()
```

Run it:
```bash
python test_spade.py
```

---

## Complete Working Example

Create `my_analysis.py`:

```python
"""
Complete working example for SPADE analysis.
"""
import numpy as np
from spade import SPADEConfig, SPADEAnalyzer

def create_fake_images():
    """Create fake images for testing."""
    # 1000x1000 RGB images
    ref = np.random.rand(1000, 1000, 3).astype(np.float32)
    cap = ref + np.random.randn(1000, 1000, 3).astype(np.float32) * 0.01
    cap = np.clip(cap, 0, 1)
    return ref, cap

def main():
    print("Creating fake images...")
    ref, cap = create_fake_images()
    
    print("Configuring SPADE...")
    config = SPADEConfig()
    config.patch.patch_size = 64
    config.patch.stride = 64
    config.metric.metric_name = "l2"
    
    print("Creating analyzer...")
    analyzer = SPADEAnalyzer(config)
    
    # Note: analyzer.analyze() expects file paths
    # For this demo, we show the configuration works
    print(f"✓ Configuration: {config.metric.metric_name}")
    print(f"✓ Patch size: {config.patch.patch_size}")
    print(f"✓ Analyzer ready!")
    
    print("\nTo run full analysis with real images:")
    print("  from spade import quick_analysis")
    print("  results = quick_analysis('ref.png', 'cap.png', 'output')")

if __name__ == '__main__':
    main()
```

---

## Project Structure for PyCharm

```
your_project/
├── spade_improved/          ← Extract here
│   ├── spade/              ← Core package
│   ├── utils/              ← Utilities
│   ├── examples/           ← Examples
│   ├── setup.py            ← Install script
│   └── requirements.txt    ← Dependencies
│
├── your_scripts/           ← Your code here
│   └── my_analysis.py
│
└── data/                   ← Your images
    ├── ref.png
    └── cap.png
```

---

## Recommended PyCharm Settings

### 1. Enable Auto Import

- Settings → Editor → General → Auto Import
- ✓ Show import popup
- ✓ Add unambiguous imports on the fly

### 2. Set Python Interpreter

- Settings → Project → Python Interpreter
- Make sure correct Python version is selected (3.7+)

### 3. Configure Console

- Settings → Build, Execution, Deployment → Console
- ✓ Use IPython if available (optional)

---

## Still Having Issues?

### Debug Checklist

1. ✓ Python 3.7+ installed?
   ```bash
   python --version
   ```

2. ✓ Dependencies installed?
   ```bash
   pip list | grep -E "numpy|Pillow|matplotlib"
   ```

3. ✓ SPADE installed?
   ```bash
   pip show spade-analysis
   ```
   Or:
   ```bash
   python -c "import spade; print(spade.__file__)"
   ```

4. ✓ Correct working directory?
   ```bash
   pwd  # Should be in spade_improved/
   ```

5. ✓ Run test script?
   ```bash
   python test_installation.py
   ```

### Get Help

If still stuck, check:
1. Run `test_installation.py` and share the output
2. Check PyCharm's Python interpreter (Settings → Project → Python Interpreter)
3. Try in a fresh terminal outside PyCharm:
   ```bash
   cd spade_improved
   python -c "from spade import quick_analysis; print('OK')"
   ```

---

## Quick Reference

### Install Command
```bash
cd spade_improved
pip install -e .
```

### Test Command
```bash
python test_installation.py
```

### Basic Usage
```python
from spade import quick_analysis, generate_report

results = quick_analysis("ref.png", "cap.png", "output")
report = generate_report("output")
```

### With Configuration
```python
from spade import SPADEConfig, run_analysis

config = SPADEConfig()
config.metric.metric_name = "perceptual"

results = run_analysis("ref.png", "cap.png", "output", config)
```

---

## Success!

Once `test_installation.py` shows all tests passing, you're ready to use SPADE!

Next steps:
1. Check `examples/basic_examples.py`
2. Read `QUICKSTART.md`
3. Try with your own images

Happy analyzing! 🚀
