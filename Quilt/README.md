# Quilt 🐻💻

**Quantum circuit macro-gate detection and hierarchical visualization tool**

Bruno's professional quantum circuit analysis toolkit for detecting repeated gate patterns (macro-gates) and creating hierarchical circuit representations.

## 🚀 Quick Start

### Prerequisites

- **Python ≥ 3.12** (required by Professor CNOTworthy!)
- **uv** package manager ([install uv](https://github.com/astral-sh/uv))

### Installation

1. **Install uv** (if not already installed):
   ```bash
   # On macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # On Windows (PowerShell)
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **Clone and setup the repository**:
   ```bash
   git clone <repository-url>
   cd Quilt
   uv sync
   ```

3. **Activate the environment**:
   ```bash
   # On macOS/Linux
   source .venv/bin/activate
   
   # On Windows
   .venv\Scripts\activate
   ```

### Verify Installation

```bash
python -c "import qiskit; print(f'Qiskit version: {qiskit.__version__}')"
# Should show Qiskit >= 2.2.3
```

## 📦 Project Structure

```
Quilt/
├── macro_gate_detector/      # Main package
│   ├── __init__.py
│   ├── macro_gate_detector.py  # Core module
│   ├── big_circuit/          # Large test circuits
│   │   └── 3.qasm
│   └── MACRO_GATE_DETECTOR_README.md
├── examples/                  # Example scripts
│   ├── example_usage.py
│   └── circuit_3.py
├── tests/                     # Test suite
│   └── test_3_qasm.py
├── output/                    # Generated files (images, JSON)
├── pyproject.toml            # Project configuration (uv)
├── uv.lock                   # Locked dependencies
└── README.md                 # This file
```

## 💡 Usage

### Basic Example

```python
from macro_gate_detector import analyze_circuit, create_macro_gate_circuit
from qiskit import QuantumCircuit

# Create your circuit
qc = QuantumCircuit(4)
for layer in range(3):
    for i in range(3):
        qc.cx(i, i+1)
    for i in range(4):
        qc.ry(0.5, i)

# Analyze it
result = analyze_circuit(qc)

# Create macro-compiled circuit
macro_circuit = create_macro_gate_circuit(qc, result)

# Save results
import json
with open('output/analysis.json', 'w') as f:
    json.dump(result, f, indent=2)
```

### Run Examples

```bash
# Basic example
uv run python examples/example_usage.py

# Circuit 3 example
uv run python examples/circuit_3.py

# Comprehensive test on large circuit
cd macro_gate_detector/big_circuit
uv run python -m macro_gate_detector.tests.test_3_qasm
```

## 📊 Output Structure

The `analyze_circuit()` function returns a JSON-serializable dictionary:

```python
{
    "dag_flat": [...],           # Flat DAG (all operations)
    "dag_hierarchical": [...],  # Hierarchical DAG (with macro-gates)
    "macros": [...],             # Detected macro-gates
    "statistics": {...}          # Analysis statistics
}
```

### Converting to App Circuit Format

You can convert the analysis result to the `app-circuit.json` format for use in the React visualization app:

```python
from macro_gate_detector import analyze_circuit, convert_to_app_circuit_format

result = analyze_circuit(qc)
app_circuit = convert_to_app_circuit_format(result)

# Save as circuit_graph.json - THIS FILE GOES INTO THE REACT APP
import json
with open('circuit_graph.json', 'w') as f:
    json.dump(app_circuit, f, indent=2)
```

The `circuit_graph.json` file (in `app-circuit.json` format) includes:
- `nodes`: All circuit nodes (init, gates, end) with layers
- `edges`: Dependencies between nodes
- `macros`: Macro definitions with `gate_ids` referencing specific gate nodes

**React Visualization Workflow:**
1. Analyze your circuit and generate `circuit_graph.json`
2. **Upload `circuit_graph.json` to the React visualization app** (`my-react-app/`)
3. The app will render the circuit with macro-gates highlighted

**Important:** The `circuit_graph.json` file is the output that goes into the React app. This is the file you upload/use in the React visualization.

See [macro_gate_detector/MACRO_GATE_DETECTOR_README.md](macro_gate_detector/MACRO_GATE_DETECTOR_README.md) for detailed documentation.

## 🧪 Testing

### Quick Start
```bash
# Check your environment setup
python setup_env.py

# Run all tests
uv run pytest macro_gate_detector/tests/

# Run specific test
uv run python -m macro_gate_detector.tests.test_small    # Quick basic tests
uv run python -m macro_gate_detector.tests.test_1_qasm    # Test 1.qasm circuit
uv run python -m macro_gate_detector.tests.test_3_qasm    # Test 3.qasm circuit
```

### Test Structure
- **`test_small.py`** - Basic functionality tests (fast, no output files)
- **`test_1_qasm.py`** - Comprehensive test for 1.qasm (output in `macro_gate_detector/tests/output_test_1/`)
- **`test_3_qasm.py`** - Comprehensive test for 3.qasm (output in `macro_gate_detector/tests/output_test_3/`)

### Test Output
Each large circuit test generates:
- `original.pdf` - Original circuit visualization
- `macro.pdf` - Macro circuit visualization
- `original_dag.png` - Original circuit DAG
- `macro_dag.png` - Macro circuit DAG
- `analysis_result.json` - Raw analysis output (full analysis result from `analyze_circuit()`)
- **`circuit_graph.json`** - **THIS FILE GOES INTO THE REACT APP** - Processed circuit graph in `app-circuit.json` format

**Note:** For circuits with >50 qubits, only the first 50 qubits are shown in visualizations.

**Using the JSON Output:**
- **`circuit_graph.json`** is the file you upload to the React visualization app (`my-react-app/`)
- This file contains the circuit graph in the exact format expected by the React app
- Upload `circuit_graph.json` to visualize the circuit with macro-gates highlighted

### More Information
- **Quick Start**: See `QUICK_START.md`
- **Detailed Setup**: See `SETUP.md`
- **Test Details**: See `tests/RUN_TESTS.md`

## 🔧 Development

### Adding Dependencies

```bash
# Add a new dependency
uv add package-name

# Add a dev dependency
uv add --dev package-name

# Update all dependencies
uv sync
```

### Code Quality

```bash
# Format code
uv run black macro_gate_detector/ tests/ examples/

# Lint code
uv run ruff check macro_gate_detector/ tests/ examples/
```

## 📋 Requirements

- **Python**: ≥ 3.12
- **Qiskit**: ≥ 2.2.3
- **Dependencies**: See `pyproject.toml`

All dependencies are managed through `uv` and locked in `uv.lock` for reproducibility.

## 🎯 Features

- ✅ Detects repeated gate patterns (macro-gates)
- ✅ Semantic labeling (e.g., "AnsatzLayer A", "CNOT Ladder")
- ✅ Creates hierarchical circuit representations
- ✅ Generates macro-compiled circuits
- ✅ JSON-serializable output (raw analysis + app-circuit.json format)
- ✅ Works with large circuits (tested on 156-qubit circuits)
- ✅ No consecutive CNOT gates in macro circuits
- ✅ Fully reproducible with uv
- ✅ Generates visualization-ready JSON files for React frontend integration
- ✅ Direct integration with React visualization app

## 📝 License

MIT License

## 🙏 Acknowledgments

Thanks to Professor CNOTworthy for insisting on proper package management and reproducibility! 🕰️

---

**Made with ❤️ by Bruno the Quantum Bear**

