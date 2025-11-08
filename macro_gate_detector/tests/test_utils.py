"""
Shared test utilities for macro gate detector tests
"""

import json
import os
import sys
from typing import List, Dict, Tuple, Optional

# Set up Graphviz path - must be set before any qiskit imports
def setup_graphviz():
    """Configure Graphviz path"""
    graphviz_path = r"C:\Program Files\Graphviz\bin\dot.exe"
    if os.path.exists(graphviz_path):
        os.environ["GRAPHVIZ_DOT"] = graphviz_path
        return graphviz_path
    
    # Try alternative common locations
    alt_paths = [
        r"C:\Program Files (x86)\Graphviz\bin\dot.exe",
        r"C:\Graphviz\bin\dot.exe",
    ]
    for alt_path in alt_paths:
        if os.path.exists(alt_path):
            os.environ["GRAPHVIZ_DOT"] = alt_path
            return alt_path
    
    return None

# Setup Graphviz early
graphviz_path = setup_graphviz()

# Add project root to path to import macro_gate_detector
script_dir = os.path.dirname(os.path.abspath(__file__))
# script_dir is macro_gate_detector/tests, so go up two levels to get project root
project_root = os.path.dirname(os.path.dirname(script_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from macro_gate_detector import analyze_circuit, create_macro_gate_circuit
from qiskit import QuantumCircuit
from qiskit.converters import circuit_to_dag
from qiskit.visualization import dag_drawer


class TestResults:
    """Container for test results"""
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
    
    def add_pass(self, test_name: str, message: str = ""):
        self.passed.append((test_name, message))
        print(f"[PASS] {test_name}" + (f" - {message}" if message else ""))
    
    def add_fail(self, test_name: str, message: str):
        self.failed.append((test_name, message))
        print(f"[FAIL] {test_name} - {message}")
    
    def add_warning(self, test_name: str, message: str):
        self.warnings.append((test_name, message))
        print(f"[WARN] {test_name} - {message}")
    
    def summary(self):
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"Passed: {len(self.passed)}")
        print(f"Failed: {len(self.failed)}")
        print(f"Warnings: {len(self.warnings)}")
        
        if self.failed:
            print("\nFailed Tests:")
            for test_name, message in self.failed:
                print(f"  - {test_name}: {message}")
        
        if self.warnings:
            print("\nWarnings:")
            for test_name, message in self.warnings:
                print(f"  - {test_name}: {message}")
        
        return len(self.failed) == 0


def load_circuit_from_qasm(filepath: str) -> QuantumCircuit:
    """Load a circuit from a QASM file (supports both OpenQASM 2.0 and 3.0)"""
    with open(filepath, 'r', encoding='utf-8') as f:
        qasm_str = f.read()
    
    # Check if it's OpenQASM 3.0
    if qasm_str.strip().startswith('OPENQASM 3'):
        try:
            from qiskit import qasm3
            return qasm3.loads(qasm_str)
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Could not load OpenQASM 3.0 file. Error: {str(e)}. "
                           f"Make sure qiskit>=2.2.3 is installed with OpenQASM 3.0 support.")
    else:
        # OpenQASM 2.0
        return QuantumCircuit.from_qasm_str(qasm_str)


def extract_gate_sequence(circuit: QuantumCircuit) -> List[Tuple[str, Tuple[int, ...]]]:
    """Extract gate sequence from circuit"""
    dag = circuit_to_dag(circuit)
    sequence = []
    for node in dag.topological_nodes():
        if hasattr(node, 'op') and node.op:
            gate_name = node.op.name
            qubits = tuple(sorted([q._index for q in node.qargs if hasattr(q, '_index')]))
            sequence.append((gate_name, qubits))
    return sequence


def check_consecutive_gates(circuit: QuantumCircuit, gate_type: str = 'cx') -> List[Tuple[int, int]]:
    """Check for consecutive gates of the same type"""
    consecutive = []
    for i in range(len(circuit.data) - 1):
        gate1 = circuit.data[i]
        gate2 = circuit.data[i + 1]
        if gate1.operation.name == gate_type and gate2.operation.name == gate_type:
            consecutive.append((i, i+1))
    return consecutive


def create_reduced_circuit(circuit: QuantumCircuit, max_qubits: int = 50) -> QuantumCircuit:
    """
    Create a reduced circuit with only the first max_qubits qubits.
    For circuits over max_qubits, only show the first max_qubits in visualizations.
    """
    if circuit.num_qubits <= max_qubits:
        return circuit
    
    # Create a new circuit with only the first max_qubits qubits
    reduced = QuantumCircuit(max_qubits)
    
    # Copy gates that involve at least one qubit in the first max_qubits
    gate_count = 0
    max_gates_to_keep = 2000  # Limit total gates to keep visualization manageable
    
    for instruction in circuit.data:
        if gate_count >= max_gates_to_keep:
            break
            
        qubits = []
        for q in instruction.qubits:
            if hasattr(q, '_index'):
                qubits.append(q._index)
            elif hasattr(q, 'index'):
                qubits.append(q.index)
        
        # Include gates that involve at least one qubit in our range
        # For gates that span beyond, map the out-of-range qubits to the last qubit in range
        if qubits and any(q < max_qubits for q in qubits):
            try:
                # Map qubits: keep in-range qubits, map out-of-range to max_qubits-1
                mapped_qubits = []
                for q in qubits:
                    if q < max_qubits:
                        mapped_qubits.append(q)
                    else:
                        # Map out-of-range qubits to the last qubit in range
                        mapped_qubits.append(max_qubits - 1)
                
                # Remove duplicates while preserving order
                seen = set()
                unique_mapped = []
                for q in mapped_qubits:
                    if q not in seen:
                        seen.add(q)
                        unique_mapped.append(q)
                
                if len(unique_mapped) == len(qubits):  # Same number of qubits
                    reduced_qubits = [reduced.qubits[q] for q in unique_mapped]
                    reduced.append(instruction.operation, reduced_qubits)
                    gate_count += 1
            except Exception:
                # Skip if we can't append
                pass
    
    return reduced


def save_circuit_images(
    original_circuit: QuantumCircuit,
    macro_circuit: QuantumCircuit,
    output_dir: str,
    results: TestResults,
    max_qubits: int = 50
):
    """
    Save DAG visualizations and circuit PDFs.
    For circuits over max_qubits, only show the first max_qubits.
    """
    print("\n" + "="*70)
    print("SAVING CIRCUIT VISUALIZATIONS")
    print("="*70)
    
    # Reduce circuits to first max_qubits for visualization if needed
    if original_circuit.num_qubits > max_qubits:
        print(f"Note: Circuit has {original_circuit.num_qubits} qubits, visualizing first {max_qubits} only")
        original_reduced = create_reduced_circuit(original_circuit, max_qubits)
        macro_reduced = create_reduced_circuit(macro_circuit, max_qubits)
        print(f"  Reduced original: {len(original_reduced.data)} gates (from {len(original_circuit.data)})")
        print(f"  Reduced macro: {len(macro_reduced.data)} gates (from {len(macro_circuit.data)})")
    else:
        original_reduced = original_circuit
        macro_reduced = macro_circuit
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Always save circuit PDFs (even if DAG fails)
    print("\nSaving circuit PDFs...")
    try:
        import matplotlib.pyplot as plt
        
        # Save original circuit PDF
        original_pdf = os.path.join(output_dir, 'original.pdf')
        try:
            print(f"  Generating original circuit PDF...")
            style = {
                'backgroundcolor': '#FFFFFF',
                'fold': 100,
                'cregbundle': True,
            }
            fig = original_reduced.draw(
                output='mpl', 
                style=style, 
                fold=-1 if len(original_reduced.data) < 200 else 100
            )
            fig.savefig(original_pdf, format='pdf', bbox_inches='tight', dpi=150)
            plt.close(fig)
            results.add_pass(
                "Save original PDF", 
                f"Saved to {original_pdf} ({len(original_reduced.data)} gates, {original_reduced.num_qubits} qubits)"
            )
            print(f"  Original circuit PDF saved to: {original_pdf}")
        except Exception as e:
            results.add_warning("Save original PDF", f"Error: {str(e)}")
            print(f"  Warning: Could not save original PDF: {str(e)}")
        
        # Save macro circuit PDF
        macro_pdf = os.path.join(output_dir, 'macro.pdf')
        try:
            print(f"  Generating macro circuit PDF...")
            style = {
                'backgroundcolor': '#FFFFFF',
                'fold': 100,
                'cregbundle': True,
            }
            fig = macro_reduced.draw(
                output='mpl', 
                style=style, 
                fold=-1 if len(macro_reduced.data) < 200 else 100
            )
            fig.savefig(macro_pdf, format='pdf', bbox_inches='tight', dpi=150)
            plt.close(fig)
            results.add_pass(
                "Save macro PDF", 
                f"Saved to {macro_pdf} ({len(macro_reduced.data)} gates, {macro_reduced.num_qubits} qubits)"
            )
            print(f"  Macro circuit PDF saved to: {macro_pdf}")
        except Exception as e:
            results.add_warning("Save macro PDF", f"Error: {str(e)}")
            print(f"  Warning: Could not save macro PDF: {str(e)}")
            
    except ImportError:
        results.add_warning("Save circuit PDFs", "matplotlib not available. Install with: pip install matplotlib")
        print("  Warning: matplotlib not available. Circuit PDFs will not be saved.")
    except Exception as e:
        results.add_warning("Save circuit PDFs", f"Error: {str(e)}")
        print(f"  Error saving circuit PDFs: {str(e)}")
    
    # Try to save DAGs (optional, may fail)
    print("\nSaving circuit DAGs...")
    
    # Verify Graphviz is available
    graphviz_dot = os.environ.get('GRAPHVIZ_DOT', '')
    if not graphviz_dot or not os.path.exists(graphviz_dot):
        results.add_warning("Save circuit DAGs", "Graphviz not found. Install Graphviz from https://graphviz.org/download/")
        print("  Warning: Graphviz not found. DAG visualizations will be skipped.")
        return
    
    # Test if Graphviz can actually be executed
    try:
        import subprocess
        result = subprocess.run(
            [graphviz_dot, '-V'],
            capture_output=True,
            timeout=5,
            text=True
        )
        if result.returncode != 0:
            raise Exception("Graphviz dot.exe returned non-zero exit code")
        print(f"  Using Graphviz at: {graphviz_dot}")
    except Exception as e:
        results.add_warning("Save circuit DAGs", f"Graphviz found but cannot be executed: {str(e)}")
        print(f"  Warning: Graphviz at {graphviz_dot} cannot be executed: {str(e)}")
        return
    
    # Try to import pydot
    try:
        import pydot
        # Test if pydot can create graphs
        test_graph = pydot.Dot()
        test_graph.set_graph_defaults()
        print(f"  pydot is available and can create graphs")
    except ImportError:
        print(f"  Warning: pydot not found. Install with: uv add pydot")
        results.add_warning("Save circuit DAGs", "pydot package not installed. Install with: uv add pydot")
        return
    except Exception as e:
        print(f"  pydot is available but may have issues: {str(e)}")
    
    try:
        # Configure PATH and environment for Graphviz/pydot
        graphviz_bin_dir = os.path.dirname(graphviz_dot)
        current_path = os.environ.get('PATH', '')
        if graphviz_bin_dir not in current_path:
            os.environ['PATH'] = graphviz_bin_dir + os.pathsep + current_path
        os.environ["GRAPHVIZ_DOT"] = graphviz_dot
        
        # Save original DAG
        original_dag_file = os.path.join(output_dir, 'original_dag.png')
        try:
            print(f"Generating original circuit DAG...")
            dag_original = circuit_to_dag(original_reduced)
            dag_drawer(dag_original, scale=1.5, filename=original_dag_file)
            results.add_pass("Save original DAG", f"Saved to {original_dag_file}")
            print(f"  Original DAG saved to: {original_dag_file}")
        except Exception as e:
            error_msg = str(e)
            results.add_warning("Save original DAG", f"Error: {error_msg}")
            print(f"  Warning: Could not save original DAG: {error_msg}")
            try:
                print(f"  Trying fallback method...")
                dag_drawer(dag_original, filename=original_dag_file)
                results.add_pass("Save original DAG (fallback)", f"Saved to {original_dag_file}")
            except Exception as e2:
                print(f"  Fallback also failed: {str(e2)}")
        
        # Save macro DAG
        macro_dag_file = os.path.join(output_dir, 'macro_dag.png')
        try:
            print(f"Generating macro circuit DAG...")
            dag_macro = circuit_to_dag(macro_reduced)
            dag_drawer(dag_macro, scale=1.5, filename=macro_dag_file)
            results.add_pass("Save macro DAG", f"Saved to {macro_dag_file}")
            print(f"  Macro DAG saved to: {macro_dag_file}")
        except Exception as e:
            error_msg = str(e)
            results.add_warning("Save macro DAG", f"Error: {error_msg}")
            print(f"  Warning: Could not save macro DAG: {error_msg}")
            try:
                print(f"  Trying fallback method...")
                dag_drawer(dag_macro, filename=macro_dag_file)
                results.add_pass("Save macro DAG (fallback)", f"Saved to {macro_dag_file}")
            except Exception as e2:
                print(f"  Fallback also failed: {str(e2)}")
            
    except Exception as e:
        results.add_warning("Save circuit DAGs", f"Error: {str(e)}")
        print(f"  Error saving DAGs: {str(e)}")

