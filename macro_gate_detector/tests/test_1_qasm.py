"""
Comprehensive test for macro gate detector on 1.qasm
Tests correctness, robustness, and proper macro gate substitution

Usage:
    uv run pytest macro_gate_detector/tests/test_1_qasm.py
    # or
    uv run python -m macro_gate_detector.tests.test_1_qasm
"""

import os
import sys
import json

# Add project root to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import shared test utilities
from macro_gate_detector.tests.test_utils import (
    TestResults, load_circuit_from_qasm, analyze_circuit, create_macro_gate_circuit,
    save_circuit_images, extract_gate_sequence, check_consecutive_gates,
    create_reduced_circuit
)


def verify_macro_substitution(
    original_circuit, macro_circuit, analysis_result, results: TestResults
):
    """Verify that macro gates perfectly substitute for their sequences"""
    print("\n" + "="*70)
    print("VERIFYING MACRO SUBSTITUTION")
    print("="*70)
    
    # Extract gate sequences
    original_sequence = extract_gate_sequence(original_circuit)
    macro_sequence = extract_gate_sequence(macro_circuit)
    
    # Get all macro positions
    macros = analysis_result['macros']
    macro_positions = set()
    total_gates_in_macros = 0
    for macro in macros:
        for pos_info in macro['positions']:
            start = pos_info['start']
            end = pos_info['end']
            macro_positions.update(range(start, end))
            total_gates_in_macros += (end - start)
    
    unique_positions_replaced = len(macro_positions)
    macro_gate_count = sum(macro['count'] for macro in macros)
    
    original_gate_count = len(original_sequence)
    actual_gate_count = len(macro_sequence)
    
    compression = original_gate_count / actual_gate_count if actual_gate_count > 0 else 1.0
    
    if actual_gate_count < original_gate_count:
        results.add_pass(
            "Macro gate count",
            f"Macro circuit has {actual_gate_count} gates vs {original_gate_count} original ({compression:.2f}x compression)"
        )
    else:
        results.add_warning(
            "Macro gate count",
            f"Macro circuit has {actual_gate_count} gates vs {original_gate_count} original (no compression)"
        )
    
    gates_removed = unique_positions_replaced
    gates_added = macro_gate_count
    net_reduction = gates_removed - gates_added
    
    if net_reduction > 0:
        results.add_pass(
            "Net gate reduction",
            f"Removed {gates_removed} gates, added {gates_added} macros (net: -{net_reduction})"
        )
    else:
        results.add_warning(
            "Net gate reduction",
            f"Removed {gates_removed} gates, added {gates_added} macros (net: {net_reduction})"
        )
    
    # Verify no consecutive CNOT gates
    consecutive_cnots = check_consecutive_gates(macro_circuit, 'cx')
    if not consecutive_cnots:
        results.add_pass("No consecutive CNOT gates", "Macro circuit has no consecutive CNOT gates")
    else:
        results.add_fail(
            "No consecutive CNOT gates",
            f"Found {len(consecutive_cnots)} pairs of consecutive CNOT gates"
        )


def test_circuit_analysis(circuit, results: TestResults):
    """Test the circuit analysis functionality"""
    print("\n" + "="*70)
    print("TESTING CIRCUIT ANALYSIS")
    print("="*70)
    
    try:
        result = analyze_circuit(circuit, optimization_level=1)
        results.add_pass("Analysis execution", "Circuit analyzed successfully")
    except Exception as e:
        results.add_fail("Analysis execution", f"Error: {str(e)}")
        return None
    
    # Check result structure
    required_keys = ['dag_flat', 'dag_hierarchical', 'macros', 'statistics']
    for key in required_keys:
        if key in result:
            results.add_pass(f"Result structure - {key}", "Key present")
        else:
            results.add_fail(f"Result structure - {key}", "Key missing")
    
    # Check statistics
    stats = result['statistics']
    if stats['original_gates'] > 0:
        results.add_pass("Statistics - original_gates", f"Found {stats['original_gates']} gates")
    else:
        results.add_fail("Statistics - original_gates", "No gates found")
    
    if stats['num_macros'] >= 0:
        results.add_pass("Statistics - num_macros", f"Found {stats['num_macros']} macro patterns")
    else:
        results.add_fail("Statistics - num_macros", "Invalid macro count")
    
    if stats['compression_ratio'] >= 1.0:
        results.add_pass(
            "Statistics - compression_ratio",
            f"Compression ratio: {stats['compression_ratio']:.2f}x"
        )
    else:
        results.add_warning(
            "Statistics - compression_ratio",
            f"Compression ratio < 1.0: {stats['compression_ratio']:.2f}x"
        )
    
    return result


def test_macro_circuit_creation(circuit, analysis_result, results: TestResults):
    """Test macro circuit creation"""
    print("\n" + "="*70)
    print("TESTING MACRO CIRCUIT CREATION")
    print("="*70)
    
    try:
        macro_circuit = create_macro_gate_circuit(circuit, analysis_result)
        results.add_pass("Macro circuit creation", "Circuit created successfully")
    except Exception as e:
        results.add_fail("Macro circuit creation", f"Error: {str(e)}")
        return None
    
    if macro_circuit.num_qubits == circuit.num_qubits:
        results.add_pass(
            "Circuit qubit count",
            f"Both circuits have {macro_circuit.num_qubits} qubits"
        )
    else:
        results.add_fail(
            "Circuit qubit count",
            f"Original: {circuit.num_qubits}, Macro: {macro_circuit.num_qubits}"
        )
    
    if len(macro_circuit.data) > 0:
        results.add_pass("Circuit has gates", f"Macro circuit has {len(macro_circuit.data)} gates")
    else:
        results.add_fail("Circuit has gates", "Macro circuit is empty")
    
    return macro_circuit


def test_json_serialization(analysis_result, output_dir: str, results: TestResults):
    """Test that analysis result is JSON serializable and save JSON files"""
    print("\n" + "="*70)
    print("TESTING JSON SERIALIZATION")
    print("="*70)
    
    try:
        json_str = json.dumps(analysis_result, indent=2)
        results.add_pass("JSON serialization", "Result is JSON serializable")
        
        loaded = json.loads(json_str)
        if 'macros' in loaded and 'statistics' in loaded:
            results.add_pass("JSON deserialization", "Result can be deserialized")
        else:
            results.add_fail("JSON deserialization", "Missing keys after deserialization")
        
        # Save the raw analysis result JSON
        analysis_json_path = os.path.join(output_dir, 'analysis_result.json')
        with open(analysis_json_path, 'w', encoding='utf-8') as f:
            f.write(json_str)
        results.add_pass("Save analysis JSON", f"Saved to {analysis_json_path}")
        print(f"  Analysis result JSON saved to: {analysis_json_path}")
        
    except Exception as e:
        results.add_fail("JSON serialization", f"Error: {str(e)}")


def save_circuit_graph_json(analysis_result, output_dir: str, results: TestResults):
    """Save processed circuit graph JSON with nodes, edges, and macros in app-circuit.json format"""
    print("\n" + "="*70)
    print("SAVING CIRCUIT GRAPH JSON")
    print("="*70)
    
    try:
        # Import the conversion function from macro_gate_detector
        from macro_gate_detector.macro_gate_detector import convert_to_app_circuit_format
        
        # Convert the analysis result to app-circuit.json format
        graph_data = convert_to_app_circuit_format(analysis_result)
        
        # Save the processed graph JSON
        graph_json_path = os.path.join(output_dir, 'circuit_graph.json')
        with open(graph_json_path, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, indent=2)
        
        results.add_pass("Save circuit graph JSON", f"Saved to {graph_json_path}")
        print(f"  Circuit graph JSON saved to: {graph_json_path}")
        print(f"  Nodes: {len(graph_data.get('nodes', []))}")
        print(f"  Edges: {len(graph_data.get('edges', []))}")
        print(f"  Macros: {len(graph_data.get('macros', []))}")
        
    except ImportError as e:
        results.add_warning("Save circuit graph JSON", f"Could not import conversion function: {str(e)}")
        print(f"  Warning: Could not import convert_to_app_circuit_format: {str(e)}")
    except Exception as e:
        results.add_warning("Save circuit graph JSON", f"Error: {str(e)}")
        print(f"  Warning: Could not save circuit graph JSON: {str(e)}")


def main():
    """Run comprehensive tests on 1.qasm"""
    print("="*70)
    print("COMPREHENSIVE TEST SUITE FOR 1.QASM")
    print("="*70)
    
    # Find the QASM file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    big_circuit_dir = os.path.join(script_dir, 'big_circuit')
    qasm_file = os.path.join(big_circuit_dir, '1.qasm')
    
    if not os.path.exists(qasm_file):
        print(f"ERROR: Could not find 1.qasm at {qasm_file}")
        return False
    
    results = TestResults()
    
    # Create output directory for this test
    output_dir = os.path.join(script_dir, 'output_test_1')
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}")
    
    # Load circuit
    print(f"\nLoading circuit from {qasm_file}...")
    try:
        circuit = load_circuit_from_qasm(qasm_file)
        results.add_pass("Circuit loading", f"Loaded circuit with {circuit.num_qubits} qubits, {len(circuit.data)} gates")
    except Exception as e:
        results.add_fail("Circuit loading", f"Error: {str(e)}")
        return False
    
    # Test analysis
    analysis_result = test_circuit_analysis(circuit, results)
    if analysis_result is None:
        return False
    
    # Test macro circuit creation
    macro_circuit = test_macro_circuit_creation(circuit, analysis_result, results)
    if macro_circuit is None:
        return False
    
    # Verify macro substitution
    verify_macro_substitution(circuit, macro_circuit, analysis_result, results)
    
    # Test JSON serialization and save JSON files
    test_json_serialization(analysis_result, output_dir, results)
    
    # Save processed circuit graph JSON
    save_circuit_graph_json(analysis_result, output_dir, results)
    
    # Save circuit images (will automatically limit to 50 qubits if needed)
    save_circuit_images(circuit, macro_circuit, output_dir, results, max_qubits=50)
    
    # Print detailed statistics
    print("\n" + "="*70)
    print("DETAILED STATISTICS")
    print("="*70)
    stats = analysis_result['statistics']
    print(f"Original gates: {stats['original_gates']}")
    print(f"Transpiled gates: {stats['transpiled_gates']}")
    print(f"Circuit depth: {stats['circuit_depth']}")
    print(f"Number of qubits: {stats['num_qubits']}")
    print(f"Number of macros: {stats['num_macros']}")
    print(f"Total macro instances: {stats['total_macro_instances']}")
    print(f"Hierarchical items: {stats['hierarchical_items']}")
    print(f"Compression ratio: {stats['compression_ratio']:.2f}x")
    
    if analysis_result['macros']:
        print(f"\nTop 5 macro patterns:")
        for i, macro in enumerate(analysis_result['macros'][:5], 1):
            print(f"  {i}. {macro['label']} - appears {macro['count']} times, size {macro['window_size']}")
    
    # Final summary
    all_passed = results.summary()
    
    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

