# Getting Started with SPADE in PyCharm

## 🚀 3-Step Setup

### Step 1: Extract and Open
```bash
tar -xzf spade_v2_with_reports.tar.gz
```
Open the `spade_improved` folder in PyCharm

### Step 2: Install
Open PyCharm Terminal and run:
```bash
pip install numpy pillow matplotlib
pip install -e .
```

### Step 3: Test
Run the test script:
```bash
python simple_test.py
```

You should see:
```
✓✓✓ SUCCESS! SPADE IS WORKING! ✓✓✓
```

## ✅ That's It!

Now you can use SPADE:

```python
from spade import quick_analysis, generate_report

# Run analysis
results = quick_analysis("ref.png", "cap.png", "output")

# Generate HTML report
report = generate_report("output")
```

## 🔧 If It Doesn't Work

### Problem: "No module named 'spade'"

**Solution 1** (Easiest):
```bash
pip install -e .
```

**Solution 2** (If that doesn't work):
Add to top of your script:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
```

**Solution 3** (In PyCharm):
- Right-click `spade_improved` folder
- Mark Directory as → Sources Root

### Problem: "No module named 'numpy'" (or pillow, matplotlib)

**Solution**:
```bash
pip install numpy pillow matplotlib
```

## 📚 Examples

All examples are fixed to work in PyCharm!

- `simple_test.py` - Ultra-simple test (no images needed)
- `test_installation.py` - Full installation test
- `examples/basic_examples.py` - 8 basic examples
- `examples/advanced_examples.py` - 7 advanced examples
- `examples/report_generation_examples.py` - Report examples

## 📖 Documentation

- **PYCHARM_SETUP.md** - Detailed PyCharm guide
- **QUICKSTART.md** - 5-minute guide
- **README.md** - Full documentation

## 💡 Quick Tips

1. **Always install first**: `pip install -e .`
2. **Test before coding**: `python simple_test.py`
3. **Start simple**: Try `simple_test.py` first
4. **Use examples**: Copy from examples directory

## 🆘 Still Stuck?

Run this and share the output:
```bash
python test_installation.py
```

This will tell you exactly what's wrong!

## ✨ Success Checklist

- ✓ Extracted archive
- ✓ Opened in PyCharm
- ✓ Ran `pip install -e .`
- ✓ Ran `python simple_test.py`
- ✓ Saw "SUCCESS!" message

You're ready to go! 🎉
