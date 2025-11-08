# Test Suite for Macro Gate Detector

This directory contains comprehensive tests for the macro gate detector.

## Test Structure

### Test Files

- **`test_small.py`** - Basic functionality tests on simple circuits
  - Tests basic ansatz pattern detection
  - Tests QFT pattern recognition
  - Tests CNOT ladder detection
  
- **`test_1_qasm.py`** - Comprehensive test suite for `1.qasm`
  - Full analysis and macro detection
  - Macro circuit creation and verification
  - JSON serialization tests
  - Output saved to `output_test_1/`
  
- **`test_3_qasm.py`** - Comprehensive test suite for `3.qasm`
  - Full analysis and macro detection
  - Robustness tests across optimization levels
  - Macro consistency checks
  - Output saved to `output_test_3/`

### Shared Utilities

- **`test_utils.py`** - Shared test utilities
  - `TestResults` - Test result tracking
  - `load_circuit_from_qasm()` - QASM file loading
  - `save_circuit_images()` - Visualization saving (automatically limits to 50 qubits for large circuits)
  - `create_reduced_circuit()` - Circuit reduction for visualization
  - Other helper functions

## Output Organization

Each test suite saves its output to a separate folder:

- **`output_test_1/`** - Output from `test_1_qasm.py`
  - `original.pdf` - Original circuit visualization
  - `macro.pdf` - Macro circuit visualization
  - `original_dag.png` - Original circuit DAG
  - `macro_dag.png` - Macro circuit DAG
  - `analysis_result.json` - Raw analysis output (full result from `analyze_circuit()`)
  - `circuit_graph.json` - Processed circuit graph in `app-circuit.json` format

- **`output_test_3/`** - Output from `test_3_qasm.py`
  - Same structure as `output_test_1/`

### JSON Output Files

- **`analysis_result.json`**: Contains the complete analysis result including:
  - `dag_flat`: Flat DAG representation with all operations
  - `dag_hierarchical`: Hierarchical DAG with macro-gates collapsed
  - `macros`: Detected macro-gates with labels, counts, and positions
  - `statistics`: Analysis statistics (gate counts, compression ratio, etc.)

- **`circuit_graph.json`**: **THIS FILE GOES INTO THE REACT APP** - Processed graph in `app-circuit.json` format:
  - `nodes`: All circuit nodes (init nodes, gate nodes, end nodes) with layer information
  - `edges`: Dependencies between nodes showing qubit flow
  - `macros`: Macro definitions with `gate_ids` arrays referencing specific gate nodes
  - **Usage**: Upload `circuit_graph.json` to the React visualization app (`my-react-app/`) to visualize the circuit with macro-gates highlighted
  - **Important**: This is the file that goes into the React app - not `analysis_result.json`

## Running Tests

### Run all tests:
```bash
uv run pytest macro_gate_detector/tests/
```

### Run specific test:
```bash
# Small tests
uv run pytest macro_gate_detector/tests/test_small.py
# or
uv run python -m macro_gate_detector.tests.test_small

# Test 1
uv run pytest macro_gate_detector/tests/test_1_qasm.py
# or
uv run python -m macro_gate_detector.tests.test_1_qasm

# Test 3
uv run pytest macro_gate_detector/tests/test_3_qasm.py
# or
uv run python -m macro_gate_detector.tests.test_3_qasm
```

## Circuit Visualization

For circuits with more than 50 qubits, visualizations automatically show only the first 50 qubits to keep the output manageable. The `create_reduced_circuit()` function handles this reduction.

## Requirements

- Qiskit
- matplotlib (for PDF generation)
- Graphviz (for DAG visualization)
- pydot (for Graphviz integration)

Install with:
```bash
uv add qiskit matplotlib pydot
```

Graphviz must be installed separately from https://graphviz.org/download/

