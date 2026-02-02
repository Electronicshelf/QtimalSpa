# 🎯 SPADE in PyCharm - Fixed & Ready!

## ✅ What's Fixed

1. **Proper import paths** - All examples work in PyCharm
2. **setup.py** - Install with `pip install -e .`
3. **requirements.txt** - Easy dependency installation
4. **Test scripts** - Verify installation works
5. **Clear documentation** - Step-by-step PyCharm guide

## 🚀 3-Step Quick Start

```
┌─────────────────────────────────────────┐
│ Step 1: Extract                         │
├─────────────────────────────────────────┤
│                                         │
│  tar -xzf spade_v2_pycharm_ready.tar.gz│
│  cd spade_improved                      │
│                                         │
│  Open folder in PyCharm                 │
│                                         │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Step 2: Install (in PyCharm Terminal)  │
├─────────────────────────────────────────┤
│                                         │
│  pip install numpy pillow matplotlib    │
│  pip install -e .                       │
│                                         │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Step 3: Test                            │
├─────────────────────────────────────────┤
│                                         │
│  python simple_test.py                  │
│                                         │
│  Should see:                            │
│  ✓✓✓ SUCCESS! SPADE IS WORKING! ✓✓✓   │
│                                         │
└─────────────────────────────────────────┘
```

## 📁 New Files Added

```
spade_improved/
├── GET_STARTED.md            ← Start here! (Quick guide)
├── PYCHARM_SETUP.md          ← Detailed PyCharm guide
├── setup.py                  ← Install script
├── requirements.txt          ← Dependencies
├── simple_test.py            ← Ultra-simple test
└── test_installation.py      ← Full test suite
```

## 🎯 Test Scripts

### 1. Simple Test (Run This First!)
```bash
python simple_test.py
```
- No images needed
- Tests basic functionality
- Takes 2 seconds

### 2. Full Test
```bash
python test_installation.py
```
- Tests all components
- Checks dependencies
- Verifies everything works

## 📝 Usage in PyCharm

### Create New File: my_analysis.py

```python
from spade import quick_analysis, generate_report

# Analyze
results = quick_analysis("ref.png", "cap.png", "output")

# Generate HTML report
report = generate_report("output")

print(f"Mean distance: {results['mean_distance']:.6f}")
print(f"Report: {report}")
```

### Run It
- Right-click in editor
- Click "Run 'my_analysis'"

## 🔧 If Still Having Issues

### Quick Fix 1: Install Dependencies
```bash
pip install numpy pillow matplotlib
```

### Quick Fix 2: Install SPADE
```bash
pip install -e .
```

### Quick Fix 3: Check Installation
```bash
python test_installation.py
```

### Quick Fix 4: Mark as Sources Root
In PyCharm:
- Right-click `spade_improved` folder
- Mark Directory as → Sources Root

## 📚 Documentation Order

1. **GET_STARTED.md** ← Start here (1 page)
2. **PYCHARM_SETUP.md** ← If issues (detailed)
3. **QUICKSTART.md** ← Usage guide (5 min)
4. **README.md** ← Full reference

## ✨ What Works Now

✅ Import from anywhere:
```python
from spade import quick_analysis
```

✅ Run examples directly:
```bash
python examples/basic_examples.py
```

✅ Use in your scripts:
```python
from spade import SPADEConfig, run_analysis
```

✅ Generate reports:
```python
from spade import generate_report
```

## 🎉 Ready to Use!

1. Extract archive
2. `pip install -e .`
3. `python simple_test.py`
4. Start analyzing!

## 💡 Pro Tips

**Tip 1:** Always run `simple_test.py` first to verify setup

**Tip 2:** If imports fail, check:
```bash
python -c "import spade; print(spade.__file__)"
```

**Tip 3:** Examples now work from anywhere (fixed imports!)

**Tip 4:** Use PyCharm terminal for all commands

**Tip 5:** Install as package (`pip install -e .`) is cleanest

## 🆘 Common Errors & Fixes

### Error: "No module named 'spade'"
**Fix:** `pip install -e .`

### Error: "No module named 'numpy'"
**Fix:** `pip install numpy pillow matplotlib`

### Error: "cannot import name 'generate_report'"
**Fix:** `pip install -e . --force-reinstall`

### Error: Examples don't work
**Fix:** They're already fixed! Just run them:
```bash
python examples/basic_examples.py
```

## ✅ Success Indicators

When setup is correct, you'll see:

```bash
$ python simple_test.py
==========================================================
Testing SPADE Installation
==========================================================

1. Testing imports...
   ✓ Imports working!

2. Creating configuration...
   ✓ Config created! Patch size: 64

3. Testing metric...
   ✓ Metric works! Computed 5 distances
   Mean distance: 0.234567

4. Testing panel...
   ✓ Panel works! Created SRGB panel

==========================================================
✓✓✓ SUCCESS! SPADE IS WORKING! ✓✓✓
==========================================================
```

## 🎊 You're All Set!

The package is now **PyCharm-ready** with:
- ✓ Proper installation support
- ✓ Fixed imports in all examples  
- ✓ Test scripts
- ✓ Clear documentation
- ✓ Quick start guide

**Just extract, install, test, and start analyzing!** 🚀
