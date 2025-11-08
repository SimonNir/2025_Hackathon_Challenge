# How to Run Tests

## Quick Start

### Using UV (Recommended)

```bash
# Run all tests
uv run pytest macro_gate_detector/tests/

# Run specific test
uv run python -m macro_gate_detector.tests.test_small
uv run python -m macro_gate_detector.tests.test_1_qasm
uv run python -m macro_gate_detector.tests.test_3_qasm
```

### Using Traditional venv

```bash
# Activate venv first
.\venv\Scripts\Activate.ps1  # Windows PowerShell
# or
source venv/bin/activate  # Linux/Mac

# Then run tests
pytest macro_gate_detector/tests/
python -m macro_gate_detector.tests.test_small
```

## Test Files Explained

### 1. `test_small.py` - Basic Functionality Tests
**Purpose:** Quick tests to verify core functionality works
**Duration:** Fast (< 1 minute)
**Output:** Console output only, no files

**Run:**
```bash
uv run python -m macro_gate_detector.tests.test_small
```

**Tests:**
- Basic ansatz pattern detection
- QFT pattern recognition
- CNOT ladder detection

### 2. `test_1_qasm.py` - Comprehensive Test for 1.qasm
**Purpose:** Full test suite for the 1.qasm circuit file
**Duration:** Medium (1-5 minutes depending on circuit size)
**Output:** Saved to `tests/output_test_1/`

**Run:**
```bash
uv run python -m macro_gate_detector.tests.test_1_qasm
```

**What it does:**
- Loads `tests/big_circuit/1.qasm`
- Analyzes circuit for macro patterns
- Creates macro circuit
- Verifies macro substitution
- Tests JSON serialization
- Generates visualizations (PDFs and DAGs)
- Saves all output to `tests/output_test_1/`

### 3. `test_3_qasm.py` - Comprehensive Test for 3.qasm
**Purpose:** Full test suite for the 3.qasm circuit file
**Duration:** Medium (1-5 minutes depending on circuit size)
**Output:** Saved to `tests/output_test_3/`

**Run:**
```bash
uv run python -m macro_gate_detector.tests.test_3_qasm
```

**What it does:**
- Loads `tests/big_circuit/3.qasm`
- Analyzes circuit for macro patterns
- Creates macro circuit
- Tests robustness across optimization levels
- Verifies macro consistency
- Generates visualizations (PDFs and DAGs)
- Saves all output to `tests/output_test_3/`

## Understanding Test Output

### Console Output

Each test prints:
- `[PASS]` - Test passed
- `[FAIL]` - Test failed
- `[WARN]` - Warning (non-critical issue)

At the end, you'll see a summary:
```
TEST SUMMARY
======================================================================
Passed: 15
Failed: 0
Warnings: 2
```

### File Output

For large circuit tests (1.qasm and 3.qasm), files are saved:

**Location:** `tests/output_test_X/` (where X is 1 or 3)

**Files:**
- `original.pdf` - Visual representation of original circuit
- `macro.pdf` - Visual representation with macro gates
- `original_dag.png` - DAG (Directed Acyclic Graph) of original circuit
- `macro_dag.png` - DAG with macro gates collapsed

**Note:** For circuits with >50 qubits, only the first 50 qubits are shown in visualizations.

## Running All Tests

```bash
# Run all tests with pytest
uv run pytest macro_gate_detector/tests/ -v

# Run all tests and show coverage
uv run pytest macro_gate_detector/tests/ --cov=macro_gate_detector --cov-report=html

# Run tests in parallel (faster)
uv run pytest macro_gate_detector/tests/ -n auto
```

## Common Issues

### "Python version not supported"
- Ensure Python 3.12+ is installed
- If using UV: `uv python install 3.12` then `uv sync`
- If using venv: Recreate with Python 3.12+

### "Module not found" errors
- Run `uv sync` (if using UV)
- Or `pip install -e .` (if using venv)

### "Graphviz not found" warnings
- Install Graphviz from https://graphviz.org/download/
- Tests will still run, but DAG visualizations won't be generated

### "File not found" for QASM files
- Ensure `macro_gate_detector/tests/big_circuit/1.qasm` and `macro_gate_detector/tests/big_circuit/3.qasm` exist
- Check you're running from the project root directory

## Test Structure

```
macro_gate_detector/tests/
├── test_utils.py          # Shared utilities
├── test_small.py          # Quick basic tests
├── test_1_qasm.py         # Test for 1.qasm
├── test_3_qasm.py         # Test for 3.qasm
├── big_circuit/           # QASM circuit files
│   ├── 1.qasm
│   └── 3.qasm
├── output_test_1/         # Output from test_1_qasm.py
│   ├── original.pdf
│   ├── macro.pdf
│   ├── original_dag.png
│   └── macro_dag.png
└── output_test_3/         # Output from test_3_qasm.py
    ├── original.pdf
    ├── macro.pdf
    ├── original_dag.png
    └── macro_dag.png
```

