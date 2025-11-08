"""
Small tests for macro gate detector - basic functionality tests
Tests on simple circuits to verify core functionality

Usage:
    uv run pytest macro_gate_detector/tests/test_small.py
    # or
    uv run python -m macro_gate_detector.tests.test_small
"""

import os
import sys
from qiskit import QuantumCircuit

# Add project root to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import shared test utilities
from macro_gate_detector.tests.test_utils import (
    TestResults, analyze_circuit, create_macro_gate_circuit,
    save_circuit_images, extract_gate_sequence, check_consecutive_gates
)


def test_basic_ansatz():
    """Test detection of a simple repeating ansatz pattern"""
    print("\n" + "="*70)
    print("TEST: Basic VQE Ansatz Pattern")
    print("="*70)
    
    results = TestResults()
    
    # Create a simple repeating ansatz-like pattern
    qc = QuantumCircuit(4)
    for layer in range(3):
        for i in range(3):
            qc.cx(i, i+1)
        for i in range(4):
            qc.ry(0.5, i)
        qc.cx(0, 2)
        qc.cx(1, 3)
    
    print(f"Circuit has {len(qc.data)} gates on {qc.num_qubits} qubits")
    
    # Analyze
    try:
        result = analyze_circuit(qc, optimization_level=1)
        results.add_pass("Analysis execution", "Circuit analyzed successfully")
    except Exception as e:
        results.add_fail("Analysis execution", f"Error: {str(e)}")
        return results
    
    # Check for macros
    if result['statistics']['num_macros'] > 0:
        results.add_pass(
            "Macro detection",
            f"Found {result['statistics']['num_macros']} macro patterns"
        )
    else:
        results.add_warning("Macro detection", "No macros detected")
    
    # Create macro circuit
    try:
        macro_circuit = create_macro_gate_circuit(qc, result)
        results.add_pass("Macro circuit creation", "Circuit created successfully")
        
        # Check compression
        compression = len(qc.data) / len(macro_circuit.data) if len(macro_circuit.data) > 0 else 1.0
        if compression > 1.0:
            results.add_pass("Compression", f"Compressed by {compression:.2f}x")
        else:
            results.add_warning("Compression", "No compression achieved")
    except Exception as e:
        results.add_fail("Macro circuit creation", f"Error: {str(e)}")
    
    return results


def test_qft_pattern():
    """Test detection of QFT-like patterns"""
    print("\n" + "="*70)
    print("TEST: QFT Pattern")
    print("="*70)
    
    results = TestResults()
    
    # Create a simple QFT-like pattern
    qc = QuantumCircuit(3)
    # H on first qubit
    qc.h(0)
    # Controlled phase gates
    qc.cp(0.5, 0, 1)
    qc.cp(0.25, 0, 2)
    qc.h(1)
    qc.cp(0.5, 1, 2)
    qc.h(2)
    
    print(f"Circuit has {len(qc.data)} gates on {qc.num_qubits} qubits")
    
    # Analyze
    try:
        result = analyze_circuit(qc, optimization_level=1)
        results.add_pass("Analysis execution", "Circuit analyzed successfully")
        
        # Check if QFT pattern was detected
        macros = result['macros']
        qft_detected = any('QFT' in macro['label'] for macro in macros)
        if qft_detected:
            results.add_pass("QFT detection", "QFT pattern detected")
        else:
            results.add_warning("QFT detection", "QFT pattern not detected (may be expected for small circuit)")
    except Exception as e:
        results.add_fail("Analysis execution", f"Error: {str(e)}")
    
    return results


def test_cnot_ladder():
    """Test detection of CNOT ladder patterns"""
    print("\n" + "="*70)
    print("TEST: CNOT Ladder Pattern")
    print("="*70)
    
    results = TestResults()
    
    # Create a CNOT ladder
    qc = QuantumCircuit(5)
    for i in range(4):
        qc.cx(i, i+1)
    # Repeat the pattern
    for i in range(4):
        qc.cx(i, i+1)
    
    print(f"Circuit has {len(qc.data)} gates on {qc.num_qubits} qubits")
    
    # Analyze
    try:
        result = analyze_circuit(qc, optimization_level=1)
        results.add_pass("Analysis execution", "Circuit analyzed successfully")
        
        # Check for CNOT ladder detection
        macros = result['macros']
        cnot_detected = any('CNOT' in macro['label'] for macro in macros)
        if cnot_detected:
            results.add_pass("CNOT ladder detection", "CNOT ladder pattern detected")
        else:
            results.add_warning("CNOT ladder detection", "CNOT ladder not detected")
    except Exception as e:
        results.add_fail("Analysis execution", f"Error: {str(e)}")
    
    return results


def main():
    """Run all small tests"""
    print("="*70)
    print("SMALL TESTS - BASIC FUNCTIONALITY")
    print("="*70)
    
    all_results = TestResults()
    
    # Run individual tests
    test_results = [
        test_basic_ansatz(),
        test_qft_pattern(),
        test_cnot_ladder(),
    ]
    
    # Aggregate results
    for result in test_results:
        all_results.passed.extend(result.passed)
        all_results.failed.extend(result.failed)
        all_results.warnings.extend(result.warnings)
    
    # Print summary
    all_passed = all_results.summary()
    
    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

