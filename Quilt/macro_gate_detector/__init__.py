"""
Quilt - Quantum circuit macro-gate detection and hierarchical visualization

A Python module that analyzes quantum circuits, builds DAGs, and extracts 
macro-gates (repeated patterns) into easily transferable data structures.
"""

from .macro_gate_detector import (
    analyze_circuit,
    create_macro_gate_circuit,
    convert_to_app_circuit_format,
    MacroGateDetector,
    SemanticLabeler,
)

__version__ = "0.1.0"
__all__ = [
    "analyze_circuit",
    "create_macro_gate_circuit",
    "convert_to_app_circuit_format",
    "MacroGateDetector",
    "SemanticLabeler",
]

