# Python Environment Setup

## Quick Setup (Recommended)

### Option 1: Using pip (Simplest)

```bash
cd scans
pip install -r requirements.txt
```

That's it! Now you can run the backtester.

---

## Detailed Setup Steps

### 1. Check Python Version

```bash
python --version
```

**Required:** Python 3.7 or higher (you have Python 3.14)

### 2. Install Dependencies

```bash
cd C:\Users\angu2\OneDrive\Documents\scans
pip install -r requirements.txt
```

**What gets installed:**
- `pandas` - Data analysis (your screening results)
- `numpy` - Mathematical operations
- `yfinance` - Historical stock data
- `python-dateutil` - Date handling

### 3. Verify Installation

```bash
python -c "import pandas, numpy, yfinance; print('All packages installed successfully!')"
```

**Expected output:**
```
All packages installed successfully!
```

---

## Test Your Setup

### Test 1: Position Calculator

```bash
cd scans
python test_position_calculator.py
```

**Expected:** NVDA position sizing for 3 scenarios

### Test 2: Historical Screener

```bash
cd backtesting/utils
python historical_screener.py
```

**Expected:** Quarterly screening results for 2023

### Test 3: Full Backtest

```bash
cd scans/backtesting
python run_backtest.py --system 2
```

**Expected:** Full backtest of System 2 (Turtle) from 2020-2024

---

## Troubleshooting

### Issue: "pip is not recognized"

**Solution:** Use full Python path
```bash
python -m pip install -r requirements.txt
```

### Issue: "Permission denied"

**Solution:** Install for user only
```bash
pip install --user -r requirements.txt
```

### Issue: "Could not find a version that satisfies..."

**Solution:** Upgrade pip first
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Issue: Import errors when running

**Check packages are installed:**
```bash
pip list | findstr pandas
pip list | findstr numpy
pip list | findstr yfinance
```

**Reinstall if missing:**
```bash
pip install pandas numpy yfinance --upgrade
```

---

## Virtual Environment (Optional - Recommended for Isolation)

If you want to keep this project's dependencies separate:

### Create Virtual Environment

```bash
cd C:\Users\angu2\OneDrive\Documents\scans
python -m venv venv
```

### Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**You'll see:** `(venv)` at the start of your command prompt

### Install Dependencies in Virtual Environment

```bash
pip install -r requirements.txt
```

### Deactivate When Done

```bash
deactivate
```

---

## Quick Start After Setup

Once installed, you can run:

```bash
# Position sizing calculator
python position_calculator.py

# Batch position calculator
python batch_position_calculator.py

# Test position calculator
python test_position_calculator.py

# Backtest System 2 (Turtle)
cd backtesting
python run_backtest.py --system 2

# Backtest all systems
python run_backtest.py --all
```

---

## Package Versions

The system is tested with:
- Python 3.10+ (you have 3.14 ✅)
- pandas 2.0+
- numpy 1.24+
- yfinance 0.2.28+

Your system should work perfectly with Python 3.14.

---

## Already Have These Packages?

Check what you have installed:

```bash
pip list
```

If you already have pandas, numpy, and yfinance, you're ready to go! Just run:

```bash
cd scans/backtesting
python run_backtest.py --system 2
```

---

## Next Steps After Setup

1. ✅ Install dependencies
2. ✅ Test with `test_position_calculator.py`
3. ✅ Run small backtest: `python run_backtest.py --system 2`
4. ✅ Analyze results in `backtesting/results/`
5. ✅ Run all systems: `python run_backtest.py --all`
6. ✅ Choose best system
7. ✅ Paper trade

---

**Total Install Time:** ~30 seconds

Let me know if you hit any issues!
