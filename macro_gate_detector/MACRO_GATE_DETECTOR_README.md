# Macro-Gate Detector

A Python module that analyzes quantum circuits, builds DAGs, and extracts macro-gates (repeated patterns) into easily transferable data structures.

## Quick Start

```python
from macro_gate_detector import analyze_circuit
from qiskit import QuantumCircuit

# Create your circuit
qc = QuantumCircuit(4)
# ... add gates ...

# Analyze it
result = analyze_circuit(qc)

# Result contains:
# - result['dag_flat']: Flat DAG (all operations)
# - result['dag_hierarchical']: Hierarchical DAG (with macro-gates)
# - result['macros']: List of detected macro-gates
# - result['statistics']: Analysis statistics
```

## Output Data Structure

The `analyze_circuit()` function returns a dictionary with the following structure:

### 1. `dag_flat` - Flat DAG Representation
List of all operations in topological order:
```json
[
  {
    "position": 0,
    "gate": "cx",
    "qubits": ["0", "1"]
  },
  {
    "position": 1,
    "gate": "ry",
    "qubits": ["0"]
  },
  ...
]
```

### 2. `dag_hierarchical` - Hierarchical DAG with Macro-Gates
List where macro-gates are collapsed into single items:
```json
[
  {
    "type": "macro",
    "label": "AnsatzLayer A",
    "size": 8,
    "gates": [{"name": "cx", "qubits": ["0", "1"]}, ...],
    "start_position": 0,
    "end_position": 8
  },
  {
    "type": "gate",
    "name": "cx",
    "qubits": ["1", "3"],
    "position": 8
  },
  ...
]
```

### 3. `macros` - Detected Macro-Gates
List of all detected macro-gates with their properties:
```json
[
  {
    "label": "AnsatzLayer A",
    "count": 3,
    "window_size": 8,
    "gates": [{"name": "cx", "qubits": ["0", "1"]}, ...],
    "positions": [
      {"start": 0, "end": 8},
      {"start": 9, "end": 17},
      {"start": 18, "end": 26}
    ]
  },
  ...
]
```

### 4. `statistics` - Analysis Statistics
```json
{
  "original_gates": 27,
  "transpiled_gates": 27,
  "circuit_depth": 15,
  "num_qubits": 4,
  "num_macros": 2,
  "total_macro_instances": 6,
  "hierarchical_items": 6,
  "compression_ratio": 4.5,
  "dag_nodes": 35,
  "dag_edges": 46
}
```

## Saving to JSON

The entire result is JSON-serializable:

```python
import json

result = analyze_circuit(qc)

with open('circuit_analysis.json', 'w') as f:
    json.dump(result, f, indent=2)
```

## Parameters

```python
analyze_circuit(
    circuit: QuantumCircuit,
    optimization_level: int = 1,      # Qiskit transpilation level (0-3)
    min_repetitions: int = 2,          # Min repetitions to detect pattern
    max_window_size: int = 8           # Max pattern window size
)
```

## Example

See `example_usage.py` for a complete example.

## Features

- ✅ Builds DAG from Qiskit circuit
- ✅ Detects repeated gate patterns (macro-gates)
- ✅ Semantic labeling (e.g., "AnsatzLayer A", "CNOT Ladder")
- ✅ Returns both flat and hierarchical representations
- ✅ JSON-serializable output
- ✅ Easy to transfer/share between systems

