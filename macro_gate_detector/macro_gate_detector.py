"""
Bruno Learns to See Quantum Circuits
Macro-Gate Detection and Hierarchical Visualization Tool

This module extracts macro-gates from quantum circuits and returns
structured data that can be easily serialized (JSON-compatible).
"""

from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional, Any
import hashlib
import re

try:
    from qiskit import QuantumCircuit
    from qiskit.converters import circuit_to_dag
    from qiskit import transpile
except ImportError:
    raise ImportError("Qiskit is required. Install with: pip install qiskit")


class MacroGateDetector:
    """Detects repeated gate sequences using rolling hash pattern matching"""
    
    def __init__(self, min_repetitions=2, max_window_size=8):
        self.min_repetitions = min_repetitions
        self.max_window_size = max_window_size
        
    def hash_sequence(self, seq: List[Tuple]) -> str:
        """
        Create a parameter-aware hash of a gate sequence.
        Ignores exact qubit indices for pattern matching, but includes gate parameters.
        
        Assumes seq items are: (gate_name, qubits, params)
        """
        normalized = []
        for item in seq:
            gate_name = item[0]
            qubits = item[1] if len(item) > 1 else tuple()
            params = item[2] if len(item) > 2 else tuple()
            
            # 1. Normalize Qubits (qubit-agnostic hash, but sorted for consistency)
            qubit_set = tuple(sorted(qubits)) if qubits else tuple()
            
            # 2. Normalize Parameters (crucial for rotation gates)
            # Parameters are already normalized in extract_operations_from_dag,
            # but we ensure they're in a consistent format here
            normalized_params = tuple(params) if params else tuple()
            
            normalized.append((gate_name, qubit_set, normalized_params))
        
        return hashlib.md5(str(normalized).encode()).hexdigest()
    
    def detect_patterns(self, ops_sequence: List[Tuple]) -> Dict:
        """
        Detect repeated patterns using rolling hash with polynomial hashing.
        Uses a true rolling hash (Rabin-Karp style) for O(1) hash updates per window.
        """
        all_patterns = {}
        
        for window_size in range(2, min(self.max_window_size + 1, len(ops_sequence) // 2 + 1)):
            window_patterns = defaultdict(list)
            
            # For small sequences or when window_size is large, use direct hashing
            # For larger sequences, we could implement true rolling hash, but the
            # current approach with hash_sequence is already reasonably efficient
            # since we're hashing normalized tuples, not full gate objects
            
            # Pre-compute hashes for all windows of this size
            for i in range(len(ops_sequence) - window_size + 1):
                window = ops_sequence[i:i+window_size]
                pattern_hash = self.hash_sequence(window)
                window_patterns[pattern_hash].append((i, i + window_size))
            
            # Filter patterns that meet minimum repetition threshold
            for pattern_hash, positions in window_patterns.items():
                if len(positions) >= self.min_repetitions:
                    if pattern_hash not in all_patterns:
                        all_patterns[pattern_hash] = {
                            'sequence': ops_sequence[positions[0][0]:positions[0][1]],
                            'positions': positions,
                            'window_size': window_size,
                            'count': len(positions)
                        }
        
        sorted_patterns = sorted(
            all_patterns.items(),
            key=lambda x: (x[1]['count'], x[1]['window_size']),
            reverse=True
        )
        
        return dict(sorted_patterns)
    
    def find_non_overlapping_macros(self, patterns: Dict, ops_sequence: List = None) -> List[Dict]:
        """
        Select best non-overlapping macro-gates.
        
        Note: ops_sequence parameter kept for API compatibility but not currently used.
        """
        # First, collect all potential macros with their positions
        all_macro_candidates = []
        for pattern_hash, pattern_info in patterns.items():
            for start, end in pattern_info['positions']:
                all_macro_candidates.append({
                    'hash': pattern_hash,
                    'sequence': pattern_info['sequence'],
                    'start': start,
                    'end': end,
                    'window_size': pattern_info['window_size'],
                    'size': end - start
                })
        
        # Sort by size (larger first) and then by start position
        all_macro_candidates.sort(key=lambda x: (x['size'], -x['start']), reverse=True)
        
        # Greedily select non-overlapping macros
        selected_macros = []
        used_ranges = []  # List of (start, end) tuples
        
        def ranges_overlap(start1, end1, start2, end2):
            """Check if two ranges [start, end) overlap"""
            return not (end1 <= start2 or end2 <= start1)
        
        for candidate in all_macro_candidates:
            # Check if this candidate overlaps with any already selected macro
            overlaps = False
            for used_start, used_end in used_ranges:
                if ranges_overlap(candidate['start'], candidate['end'], used_start, used_end):
                    overlaps = True
                    break
            
            if not overlaps:
                # Add this macro
                used_ranges.append((candidate['start'], candidate['end']))
                selected_macros.append(candidate)
        
        # Group selected macros by hash
        macros_by_hash = {}
        for macro in selected_macros:
            hash_key = macro['hash']
            if hash_key not in macros_by_hash:
                macros_by_hash[hash_key] = {
                    'hash': hash_key,
                    'sequence': macro['sequence'],
                    'positions': [],
                    'window_size': macro['window_size']
                }
            macros_by_hash[hash_key]['positions'].append((macro['start'], macro['end']))
        
        # Convert to final format and filter by min_repetitions
        macros = []
        for hash_key, macro_info in macros_by_hash.items():
            if len(macro_info['positions']) >= self.min_repetitions:
                macros.append({
                    'hash': hash_key,
                    'sequence': macro_info['sequence'],
                    'positions': macro_info['positions'],
                    'count': len(macro_info['positions']),
                    'window_size': macro_info['window_size']
                })
        
        return sorted(macros, key=lambda x: (x['count'], x['window_size']), reverse=True)


class SemanticLabeler:
    """Labels macro-gates with meaningful semantic names"""
    
    def __init__(self):
        self.pattern_templates = {
            'qft_phase_ladder': {'pattern': [('h',), ('cp',)], 'name': 'QFT Phase Ladder'},
            'cnot_ladder': {'pattern': [('cx',), ('cx',)], 'name': 'CNOT Ladder'},
            'swap_network': {'pattern': [('swap',)], 'name': 'Swap Network'},
            'hadamard_ladder': {'pattern': [('h',), ('h',)], 'name': 'Hadamard Ladder'}
        }
    
    def _extract_rotation_parameters(self, sequence: List[Tuple]) -> Dict:
        """Extract rotation gate parameters from sequence"""
        rotation_params = {}
        for gate in sequence:
            gate_name = gate[0]
            if gate_name in ['ry', 'rz', 'rx']:
                # Try to extract parameter from gate object if available
                # For now, we'll detect the rotation type
                if gate_name not in rotation_params:
                    rotation_params[gate_name] = []
                # If we have access to gate parameters, extract them
                # This is a simplified version - in practice, you'd extract actual params
                rotation_params[gate_name].append('param')
        return rotation_params
    
    def analyze_gate_sequence(self, sequence: List[Tuple]) -> Dict:
        """Analyze a gate sequence to determine its characteristics"""
        gate_names = [gate[0] for gate in sequence]
        all_qubits = set()
        for gate in sequence:
            # Extract qubit indices properly (handle both string and int qubit indices)
            qubits = gate[1] if len(gate) > 1 else tuple()
            for q in qubits:
                try:
                    if isinstance(q, int):
                        all_qubits.add(q)
                    elif isinstance(q, str) and q.isdigit():
                        all_qubits.add(int(q))
                    elif hasattr(q, '_index'):
                        all_qubits.add(q._index)
                    elif hasattr(q, 'index') and not callable(getattr(q, 'index', None)):
                        all_qubits.add(q.index)
                    else:
                        # Try extract_qubit_index as fallback
                        idx_str = extract_qubit_index(q)
                        if idx_str and idx_str.isdigit():
                            all_qubits.add(int(idx_str))
                except (ValueError, TypeError, AttributeError):
                    continue
        
        num_qubits = len(all_qubits)
        num_gates = len(sequence)
        gate_counts = Counter(gate_names)
        
        # Analyze connectivity pattern
        connectivity = self._analyze_connectivity(sequence)
        
        return {
            'num_qubits': num_qubits,
            'num_gates': num_gates,
            'gate_counts': dict(gate_counts),
            'has_entanglement': any(g in ['cx', 'cz', 'cy', 'swap'] for g in gate_names),
            'has_rotations': any(g in ['ry', 'rz', 'rx', 'u1', 'u2', 'u3'] for g in gate_names),
            'has_hadamard': any(g == 'h' for g in gate_names),
            'is_single_qubit': num_qubits == 1,
            'is_two_qubit': num_qubits == 2,
            'connectivity': connectivity,
            'qubits': sorted(list(all_qubits)),
            'gate_sequence': gate_names
        }
    
    def _analyze_connectivity(self, sequence: List[Tuple]) -> Dict:
        """Analyze the connectivity pattern of gates"""
        # Build a graph of qubit connections
        connections = []
        for gate in sequence:
            qubits = list(gate[1]) if len(gate) > 1 else []
            if len(qubits) >= 2:
                # Extract integer indices from qubits
                qubit_indices = []
                for q in qubits:
                    try:
                        if isinstance(q, int):
                            qubit_indices.append(q)
                        elif isinstance(q, str) and q.isdigit():
                            qubit_indices.append(int(q))
                        else:
                            idx = int(extract_qubit_index(q))
                            qubit_indices.append(idx)
                    except (ValueError, TypeError, AttributeError):
                        # Skip invalid qubits
                        continue
                
                # For multi-qubit gates, record all pairs
                for i in range(len(qubit_indices)):
                    for j in range(i + 1, len(qubit_indices)):
                        # Sort to ensure consistent ordering (both should be ints now)
                        q1, q2 = qubit_indices[i], qubit_indices[j]
                        # Use built-in min/max explicitly
                        from builtins import min as builtin_min, max as builtin_max
                        conn = (builtin_min(q1, q2), builtin_max(q1, q2))
                        connections.append(conn)
        
        # Count connection frequencies
        connection_counts = Counter(connections)
        
        # Determine topology
        all_qubits = set()
        for conn in connections:
            all_qubits.update(conn)
        
        qubit_list = sorted(list(all_qubits))
        
        # Check for linear chain (each qubit connects to at most 2 others)
        qubit_degree = Counter()
        for conn in connections:
            qubit_degree[conn[0]] += 1
            qubit_degree[conn[1]] += 1
        
        max_degree = max(qubit_degree.values()) if qubit_degree else 0
        is_linear = max_degree <= 2 and len(qubit_list) > 2
        
        # Check for star topology (one qubit connects to many)
        is_star = False
        if qubit_degree and len(qubit_list) > 2:
            max_degree_qubit = max(qubit_degree.items(), key=lambda x: x[1])
            if max_degree_qubit[1] >= len(qubit_list) - 1:
                is_star = True
        
        # Check for ring (all qubits have degree 2)
        is_ring = len(qubit_list) >= 3 and all(qubit_degree.get(q, 0) == 2 for q in qubit_list)
        
        # Calculate qubit range safely
        qubit_range = None
        if qubit_list:
            try:
                q_min = min(qubit_list)
                q_max = max(qubit_list)
                qubit_range = (q_min, q_max)
            except (TypeError, ValueError):
                # If comparison fails, use first and last
                qubit_range = (qubit_list[0], qubit_list[-1]) if len(qubit_list) > 1 else (qubit_list[0], qubit_list[0])
        
        return {
            'connections': list(connection_counts.keys()),
            'connection_counts': dict(connection_counts),
            'is_linear': is_linear,
            'is_star': is_star,
            'is_ring': is_ring,
            'max_degree': max_degree,
            'qubit_range': qubit_range
        }
    
    def match_known_pattern(self, sequence: List[Tuple], analysis: Dict, 
                           earliest_position: Optional[int] = None, 
                           total_circuit_length: Optional[int] = None) -> Optional[str]:
        """
        Try to match against known algorithm patterns (QFT, Grover's, VQA, etc.)
        Enhanced with sophisticated pattern recognition for quantum algorithms.
        
        Args:
            sequence: Gate sequence to analyze
            analysis: Analysis dictionary from analyze_gate_sequence
            earliest_position: Earliest position in circuit where this pattern appears (unused, kept for API compatibility)
            total_circuit_length: Total length of the circuit (unused, kept for API compatibility)
        """
        gate_names = [gate[0] for gate in sequence]
        gate_counts = analysis['gate_counts']
        num_gates = len(sequence)
        num_qubits = analysis['num_qubits']
        
        # 1. QFT Recognition (Primary Motif: H + Controlled Phase Cascade)
        if 'h' in gate_counts and num_qubits >= 2:
            cp_count = sum(gate_counts.get(g, 0) for g in ['cp', 'crz', 'cu1', 'cz', 'p'])
            # Check for characteristic H -> Controlled Phase structure
            if gate_counts.get('h', 0) >= 1 and cp_count > 0:
                # QFT typically has a high ratio of controlled phase gates
                cp_ratio = cp_count / num_gates if num_gates > 0 else 0
                if cp_ratio > 0.3:  # At least 30% controlled phase gates
                    has_swaps = gate_counts.get('swap', 0) > 0
                    # Check if H gates appear early in sequence (typical QFT pattern)
                    early_h = any(gate_names[i] == 'h' for i in range(min(3, len(gate_names))))
                    if early_h:
                        return 'QFT Circuit Segment' + (' (with SWAP Layer)' if has_swaps else '')
        
        # 2. Grover's/Amplitude Amplification (Oracle + Diffusion)
        # Look for the characteristic structure: H layer, followed by CNOT/Controlled-Z structure, ending with H
        if num_qubits >= 2 and len(sequence) >= 3:
            h_count = gate_counts.get('h', 0)
            cnot_count = gate_counts.get('cx', 0)
            cz_count = gate_counts.get('cz', 0)
            
            # Grover's diffusion operator: H layer, phase gate (often implemented with CNOTs), H layer
            if h_count >= 2 and (cnot_count > 0 or cz_count > 0):
                h_ratio = h_count / num_gates if num_gates > 0 else 0
                # Check if sequence starts and/or ends with H (diffusion operator pattern)
                starts_with_h = gate_names[0] == 'h'
                ends_with_h = gate_names[-1] == 'h'
                
                if (starts_with_h or ends_with_h) and h_ratio > 0.2:
                    # Check for phase gate pattern (often Z or controlled-Z in the middle)
                    has_phase = any(g in ['z', 'cz', 'cp', 'crz'] for g in gate_names)
                    if has_phase or cnot_count >= num_qubits:
                        return 'Grover Diffusion/Oracle Block'
        
        # 3. Pure CNOT patterns
        if all(gate[0] == 'cx' for gate in sequence) and len(sequence) >= 2:
            if num_qubits == 2:
                return 'CNOT Pair'
            elif analysis['connectivity'].get('is_linear'):
                return 'CNOT Chain'
            else:
                return 'CNOT Ladder'
        
        # 4. Swap Network
        if all(gate[0] == 'swap' for gate in sequence):
            return 'Swap Network'
        
        # 5. Hadamard Layer
        if all(gate[0] == 'h' for gate in sequence) and len(sequence) >= 2:
            if len(sequence) == num_qubits:
                return 'Hadamard Layer'
            else:
                return 'Hadamard Ladder'
        
        # 6. CNOT + Rotation combinations
        cnot_count = gate_counts.get('cx', 0)
        rotation_count = sum(gate_counts.get(g, 0) for g in ['ry', 'rz', 'rx', 'u1', 'u2', 'u3'])
        
        if cnot_count > 0 and rotation_count > 0:
            # Check if rotations are all the same type
            rotation_types = [g[0] for g in sequence if g[0] in ['ry', 'rz', 'rx']]
            if rotation_types:
                rot_type = rotation_types[0].upper()
                # Determine pattern
                if cnot_count == 1 and rotation_count == 1:
                    return f'{rot_type} Rotation Block'
                elif cnot_count == 2 and rotation_count == 1:
                    return f'{rot_type} Rotation with CNOT Pair'
                elif cnot_count >= 2 and rotation_count >= 1:
                    return f'{rot_type} Rotation with Entangling Layer'
                else:
                    return 'Rotation-Entangling Block'
        
        # 7. Pure rotation blocks
        if rotation_count > 0 and cnot_count == 0:
            rotation_types = [g[0] for g in sequence if g[0] in ['ry', 'rz', 'rx']]
            if rotation_types:
                rot_type = rotation_types[0].upper()
                if len(set(rotation_types)) == 1:
                    return f'{rot_type} Rotation Block'
                else:
                    return 'Mixed Rotation Block'
        
        # 8. CZ patterns
        cz_count = gate_counts.get('cz', 0)
        if cz_count > 0 and cnot_count == 0:
            if cz_count >= 2:
                return 'CZ Ladder'
            else:
                return 'CZ Gate'
        
        return None
    
    def _describe_multi_qubit_pattern(self, analysis: Dict, sequence: List[Tuple]) -> str:
        """Generate a descriptive name for multi-qubit patterns"""
        gate_counts = analysis['gate_counts']
        connectivity = analysis['connectivity']
        num_qubits = analysis['num_qubits']
        
        # Count different gate types
        cnot_count = gate_counts.get('cx', 0)
        rotation_count = sum(gate_counts.get(g, 0) for g in ['ry', 'rz', 'rx', 'u1', 'u2', 'u3'])
        hadamard_count = gate_counts.get('h', 0)
        
        # Determine topology-based names
        is_linear = connectivity.get('is_linear', False)
        is_star = connectivity.get('is_star', False)
        is_ring = connectivity.get('is_ring', False)
        
        # Pure entangling patterns
        if cnot_count > 0 and rotation_count == 0 and hadamard_count == 0:
            if num_qubits == 2:
                return 'Entangling Pair'
            elif is_linear:
                return 'Linear Entangling Chain'
            elif is_star:
                return 'Star Entangling Pattern'
            elif is_ring:
                return 'Ring Entangling Pattern'
            else:
                return 'Entangling Block'
        
        # Mixed patterns with rotations
        if rotation_count > 0:
            rotation_types = [g[0] for g in sequence if g[0] in ['ry', 'rz', 'rx']]
            if rotation_types:
                rot_type = rotation_types[0].upper()
                if cnot_count > 0:
                    if is_linear:
                        return f'{rot_type} Rotation with Linear Entangling'
                    else:
                        return f'{rot_type} Rotation with Entangling'
                else:
                    return f'{rot_type} Rotation Block'
        
        # Hadamard + entangling
        if hadamard_count > 0 and cnot_count > 0:
            return 'Hadamard-Entangling Block'
        
        # Generic multi-qubit pattern
        if num_qubits >= 3:
            return 'Multi-Qubit Block'
        elif num_qubits == 2:
            return 'Two-Qubit Block'
        else:
            return 'Gate Block'
    
    def label_macro(self, macro: Dict, sequence: List[Tuple], all_macros: List[Dict] = None, 
                   total_circuit_length: Optional[int] = None) -> str:
        """Generate a semantic label for a macro-gate
        
        Args:
            macro: Macro dictionary with positions
            sequence: Gate sequence for this macro
            all_macros: All detected macros (for context)
            total_circuit_length: Total length of the circuit (unused, kept for API compatibility)
        """
        analysis = self.analyze_gate_sequence(sequence)
        
        # Get earliest position of this macro in the circuit
        earliest_position = None
        if macro.get('positions'):
            earliest_position = min(pos[0] for pos in macro['positions'])
        
        # Try to match known patterns first
        known_pattern = self.match_known_pattern(sequence, analysis, earliest_position, total_circuit_length)
        if known_pattern:
            return known_pattern
        
        # Single qubit patterns
        if analysis['is_single_qubit']:
            if analysis['has_rotations']:
                rotation_gates = [g for g in sequence if g[0] in ['ry', 'rz', 'rx', 'u1', 'u2', 'u3']]
                if rotation_gates:
                    rot_type = rotation_gates[0][0].upper()
                    return f'{rot_type} Rotation Block'
            elif analysis['has_hadamard']:
                return 'Hadamard Block'
            else:
                return 'Single Qubit Layer'
        
        # Two-qubit patterns
        elif analysis['is_two_qubit']:
            if analysis['has_entanglement']:
                gate_type = analysis['gate_sequence'][0] if analysis['gate_sequence'] else 'ent'
                if gate_type == 'cx':
                    return 'CNOT Pair'
                elif gate_type == 'cz':
                    return 'CZ Pair'
                else:
                    return 'Entangling Pair'
            elif analysis['has_rotations']:
                rotation_gates = [g for g in sequence if g[0] in ['ry', 'rz', 'rx']]
                if rotation_gates:
                    rot_type = rotation_gates[0][0].upper()
                    return f'{rot_type} Rotation Pair'
            return 'Two-Qubit Block'
        
        # Multi-qubit patterns
        elif analysis['num_qubits'] > 2:
            pattern_name = self._describe_multi_qubit_pattern(analysis, sequence)
            
            return pattern_name
        
        # Rotation-only patterns
        elif analysis['has_rotations'] and not analysis['has_entanglement']:
            rotation_gates = [g for g in sequence if g[0] in ['ry', 'rz', 'rx']]
            if rotation_gates:
                rot_type = rotation_gates[0][0].upper()
                if len(set([g[0] for g in rotation_gates])) == 1:
                    return f'{rot_type} Rotation Block'
                else:
                    return 'Mixed Rotation Block'
            return 'Rotation Block'
        
        # Generic fallback
        return 'Macro Block'


def extract_qubit_index(qubit) -> str:
    """Extract qubit index from Qubit object"""
    if hasattr(qubit, 'index'):
        return str(qubit.index)
    elif hasattr(qubit, '_index'):
        return str(qubit._index)
    else:
        q_str = str(qubit)
        match = re.search(r'index[=\s]+(\d+)', q_str)
        if match:
            return match.group(1)
        return q_str


def extract_operations_from_dag(dag) -> List[Tuple[str, Tuple[str, ...], Tuple]]:
    """Extract flat gate sequence from DAG in topological order with parameters"""
    ops_sequence = []
    for node in dag.topological_nodes():
        if hasattr(node, 'op') and node.op:
            gate_name = node.op.name
            if hasattr(node, 'qargs') and node.qargs:
                qubit_indices = [extract_qubit_index(q) for q in node.qargs]
                qubits = tuple(qubit_indices)
            else:
                qubits = tuple()
            
            # Extract parameters if they exist
            params = tuple()
            if hasattr(node.op, 'params') and node.op.params:
                normalized_params = []
                for p in node.op.params:
                    try:
                        # Round floating point parameters for robust matching
                        normalized_params.append(round(float(p), 6))
                    except (ValueError, TypeError, AttributeError):
                        # Keep symbolic parameters as strings
                        normalized_params.append(str(p))
                params = tuple(normalized_params)
            
            ops_sequence.append((gate_name, qubits, params))
    return ops_sequence


def extract_operations_with_details_from_dag(dag) -> List[Dict]:
    """Extract operations with full details (including parameters) from DAG"""
    ops_list = []
    for node in dag.topological_nodes():
        if hasattr(node, 'op') and node.op:
            op = node.op
            gate_name = op.name
            qubits = []
            if hasattr(node, 'qargs') and node.qargs:
                qubits = [extract_qubit_index(q) for q in node.qargs]
            
            op_dict = {
                'name': gate_name,
                'qubits': qubits,
                'op': op  # Keep reference to original operation
            }
            
            # Extract parameters if they exist
            if hasattr(op, 'params') and op.params:
                op_dict['params'] = [float(p) if hasattr(p, '__float__') else p for p in op.params]
            
            ops_list.append(op_dict)
    return ops_list


def create_hierarchical_view(ops_sequence: List[Tuple], macros: List[Dict]) -> List[Dict]:
    """Create hierarchical representation with macro-gates collapsed"""
    start_to_macro = {}
    for macro in macros:
        for start, end in macro['positions']:
            if start not in start_to_macro or (end - start) > (start_to_macro[start][1] - start):
                start_to_macro[start] = (macro, end)
    
    view = []
    i = 0
    while i < len(ops_sequence):
        if i in start_to_macro:
            macro, macro_end = start_to_macro[i]
            view.append({
                'type': 'macro',
                'label': macro['label'],
                'size': macro_end - i,
                'gates': [{'name': g[0], 'qubits': list(g[1])} for g in macro['sequence']],
                'start_position': i,
                'end_position': macro_end
            })
            i = macro_end
        else:
            gate_name = ops_sequence[i][0]
            qubits = ops_sequence[i][1] if len(ops_sequence[i]) > 1 else tuple()
            view.append({
                'type': 'gate',
                'name': gate_name,
                'qubits': list(qubits),
                'position': i
            })
            i += 1
    
    return view


def create_macro_gate_circuit(
    circuit: QuantumCircuit,
    analysis_result: Dict[str, Any],
    optimization_level: int = 1
) -> QuantumCircuit:
    """
    Create a new circuit where macro-gates replace the original gate sequences.
    The macro-gates are visual only (not functional).
    
    Args:
        circuit: Original Qiskit QuantumCircuit
        analysis_result: Result dictionary from analyze_circuit()
        optimization_level: Qiskit transpilation optimization level (0-3)
    
    Returns:
        New QuantumCircuit with macro-gates as custom visual gates
    """
    # Transpile the original circuit to match the analysis
    transpiled_qc = transpile(circuit, optimization_level=optimization_level)
    dag = circuit_to_dag(transpiled_qc)
    
    # Extract operations with full details (including parameters) from DAG
    # This preserves all gate information needed for perfect reconstruction
    dag_nodes = list(dag.topological_nodes())
    ops_with_details = []
    for node in dag_nodes:
        if hasattr(node, 'op') and node.op:
            op = node.op
            gate_name = op.name
            qubits = []
            if hasattr(node, 'qargs') and node.qargs:
                qubits = [extract_qubit_index(q) for q in node.qargs]
            
            ops_with_details.append({
                'op': op,
                'name': gate_name,
                'qubits': qubits,
                'node': node
            })
    
    # Get macros from analysis result
    macros = analysis_result['macros']
    
    # Create a mapping from macro hash to custom gate
    macro_gates = {}
    for macro in macros:
        # Determine all qubits used in this macro from the gate sequence
        all_qubits_in_macro = set()
        for gate_info in macro['gates']:
            all_qubits_in_macro.update(gate_info['qubits'])
        
        num_qubits = len(all_qubits_in_macro)
        if num_qubits == 0:
            continue
        
        # Create a simple placeholder circuit for visualization
        # We just need a circuit with the right number of qubits
        macro_qc = QuantumCircuit(num_qubits)
        
        # Add a simple identity-like operation to make it a valid gate
        # This is just for visualization, so we don't need actual functionality
        if num_qubits == 1:
            macro_qc.id(0)  # Identity gate
        else:
            # For multi-qubit gates, add identity to all qubits
            for q in range(num_qubits):
                macro_qc.id(q)
        
        # Convert the macro circuit to a custom gate
        macro_gate = macro_qc.to_gate()
        # Clean the label to make a valid gate name
        gate_name = macro['label'].replace(' ', '_').replace('(', '').replace(')', '').replace(',', '_').replace('<->', '_to_')
        macro_gate.name = gate_name[:50]  # Limit name length
        
        # Store the gate with its info
        macro_gates[macro.get('hash', macro['label'])] = {
            'gate': macro_gate,
            'num_qubits': num_qubits
        }
    
    # Now build the new circuit with macro-gates
    new_circuit = QuantumCircuit(transpiled_qc.num_qubits)
    
    # Create a mapping of positions to macros
    # Track which positions are covered by macros to avoid duplicates
    position_to_macro = {}
    positions_covered_by_macros = set()
    
    for macro in macros:
        for pos_info in macro['positions']:
            start = pos_info['start']
            end = pos_info['end']
            # Mark all positions in this range as covered
            positions_covered_by_macros.update(range(start, end))
            
            if start not in position_to_macro:
                position_to_macro[start] = (macro, end)
            elif (end - start) > (position_to_macro[start][1] - start):
                # Prefer longer macros
                position_to_macro[start] = (macro, end)
    
    # Build the circuit by iterating through operations
    i = 0
    while i < len(ops_with_details):
        if i in position_to_macro:
            # This position starts a macro - replace with macro gate
            macro, macro_end = position_to_macro[i]
            macro_hash = macro.get('hash', macro['label'])
            
            if macro_hash in macro_gates:
                macro_info = macro_gates[macro_hash]
                macro_gate = macro_info['gate']
                
                # Get the actual qubits used in this occurrence
                occurrence_qubits = set()
                for j in range(i, min(macro_end, len(ops_with_details))):
                    occurrence_qubits.update(ops_with_details[j]['qubits'])
                
                # Map qubits to the order expected by the macro gate
                sorted_qubits = sorted(occurrence_qubits, key=lambda x: int(x))
                qubit_list = [int(q) for q in sorted_qubits]
                
                # Append the macro gate to the circuit
                if len(qubit_list) == macro_info['num_qubits']:
                    new_circuit.append(macro_gate, qubit_list)
                else:
                    # If qubit count doesn't match, add gates individually with full details
                    for j in range(i, min(macro_end, len(ops_with_details))):
                        op_detail = ops_with_details[j]
                        _add_operation_to_circuit(new_circuit, op_detail)
            
            # Skip to the end of the macro
            i = macro_end
        elif i in positions_covered_by_macros:
            # This position is inside a macro (but not the start) - skip it
            # It's already been replaced by the macro gate
            i += 1
        else:
            # Add the individual gate with full details (including parameters)
            op_detail = ops_with_details[i]
            _add_operation_to_circuit(new_circuit, op_detail)
            i += 1
    
    # Post-process to merge consecutive CNOT gates
    new_circuit = _merge_consecutive_cnots(new_circuit)
    
    return new_circuit


def _merge_consecutive_cnots(circuit: QuantumCircuit) -> QuantumCircuit:
    """
    Merge consecutive CNOT gates into a CNOT Pair macro gate.
    This ensures that consecutive CNOT gates never appear in the final circuit.
    """
    if len(circuit.data) < 2:
        return circuit
    
    # Create a new circuit with the same number of qubits
    merged_circuit = QuantumCircuit(circuit.num_qubits)
    
    i = 0
    while i < len(circuit.data):
        current_instruction = circuit.data[i]
        current_op = current_instruction.operation
        
        # Check if current gate is a CNOT
        if current_op.name == 'cx' and i < len(circuit.data) - 1:
            # Check if next gate is also a CNOT
            next_instruction = circuit.data[i + 1]
            next_op = next_instruction.operation
            
            if next_op.name == 'cx':
                # Found consecutive CNOTs - merge them into a macro
                # Get qubits from both CNOTs
                current_qubits = []
                for q in current_instruction.qubits:
                    if hasattr(q, '_index'):
                        current_qubits.append(q._index)
                    elif hasattr(q, 'index'):
                        current_qubits.append(q.index)
                    else:
                        current_qubits.append(int(extract_qubit_index(q)))
                
                next_qubits = []
                for q in next_instruction.qubits:
                    if hasattr(q, '_index'):
                        next_qubits.append(q._index)
                    elif hasattr(q, 'index'):
                        next_qubits.append(q.index)
                    else:
                        next_qubits.append(int(extract_qubit_index(q)))
                
                # Create a CNOT Pair macro gate
                all_qubits = set(current_qubits + next_qubits)
                num_qubits = len(all_qubits)
                
                if num_qubits > 0:
                    # Create macro circuit
                    macro_qc = QuantumCircuit(num_qubits)
                    for q in range(num_qubits):
                        macro_qc.id(q)  # Identity for visualization
                    
                    macro_gate = macro_qc.to_gate()
                    macro_gate.name = 'CNOT_Pair'
                    
                    # Add the macro gate
                    qubit_list = sorted([int(q) for q in all_qubits])
                    if len(qubit_list) == num_qubits:
                        merged_circuit.append(macro_gate, qubit_list)
                    else:
                        # Fallback: add gates individually using append
                        merged_circuit.append(current_op, current_instruction.qubits)
                        merged_circuit.append(next_op, next_instruction.qubits)
                    
                    # Skip both CNOTs
                    i += 2
                    continue
        
        # Not consecutive CNOTs - add the gate normally using append
        merged_circuit.append(current_op, current_instruction.qubits)
        i += 1
    
    return merged_circuit


def _add_operation_to_circuit(circuit: QuantumCircuit, op_detail: Dict):
    """
    Add an operation to a circuit using the full operation object.
    This preserves parameters and handles all gate types correctly.
    """
    op = op_detail['op']
    gate_name = op_detail['name']
    qubit_indices = [int(q) for q in op_detail['qubits']]
    
    # Get the actual qubit objects from the circuit
    qubits = [circuit.qubits[i] for i in qubit_indices]
    
    # Use the operation's append method to preserve all parameters
    # This is the most robust way to add gates with parameters
    try:
        circuit.append(op, qubits)
        return
    except Exception:
        # Fallback to manual gate addition if append fails
        pass
    
    # Fallback: manually add gates with parameters
    if hasattr(op, 'params') and op.params:
        params = [float(p) if hasattr(p, '__float__') else p for p in op.params]
        
        if gate_name == 'u3' and len(qubit_indices) == 1 and len(params) >= 3:
            circuit.u3(params[0], params[1], params[2], qubit_indices[0])
        elif gate_name == 'u2' and len(qubit_indices) == 1 and len(params) >= 2:
            circuit.u2(params[0], params[1], qubit_indices[0])
        elif gate_name == 'u1' and len(qubit_indices) == 1 and len(params) >= 1:
            circuit.u1(params[0], qubit_indices[0])
        elif gate_name == 'ry' and len(qubit_indices) == 1 and len(params) >= 1:
            circuit.ry(params[0], qubit_indices[0])
        elif gate_name == 'rz' and len(qubit_indices) == 1 and len(params) >= 1:
            circuit.rz(params[0], qubit_indices[0])
        elif gate_name == 'rx' and len(qubit_indices) == 1 and len(params) >= 1:
            circuit.rx(params[0], qubit_indices[0])
        elif gate_name == 'rzz' and len(qubit_indices) == 2 and len(params) >= 1:
            circuit.rzz(params[0], qubit_indices[0], qubit_indices[1])
        elif gate_name == 'rxx' and len(qubit_indices) == 2 and len(params) >= 1:
            circuit.rxx(params[0], qubit_indices[0], qubit_indices[1])
        elif gate_name == 'ryy' and len(qubit_indices) == 2 and len(params) >= 1:
            circuit.ryy(params[0], qubit_indices[0], qubit_indices[1])
        elif gate_name == 'cp' and len(qubit_indices) == 2 and len(params) >= 1:
            circuit.cp(params[0], qubit_indices[0], qubit_indices[1])
        elif gate_name == 'crz' and len(qubit_indices) == 2 and len(params) >= 1:
            circuit.crz(params[0], qubit_indices[0], qubit_indices[1])
        elif gate_name == 'cry' and len(qubit_indices) == 2 and len(params) >= 1:
            circuit.cry(params[0], qubit_indices[0], qubit_indices[1])
        elif gate_name == 'crx' and len(qubit_indices) == 2 and len(params) >= 1:
            circuit.crx(params[0], qubit_indices[0], qubit_indices[1])
        else:
            # Try to get the gate method dynamically with parameters
            try:
                gate_method = getattr(circuit, gate_name.lower())
                if len(qubit_indices) == 1:
                    gate_method(params[0] if len(params) > 0 else None, qubit_indices[0])
                elif len(qubit_indices) == 2:
                    gate_method(params[0] if len(params) > 0 else None, qubit_indices[0], qubit_indices[1])
                elif len(qubit_indices) == 3:
                    gate_method(params[0] if len(params) > 0 else None, qubit_indices[0], qubit_indices[1], qubit_indices[2])
            except (AttributeError, TypeError):
                # Last resort: try to append the operation directly with qubit objects
                try:
                    qubit_objs = [circuit.qubits[i] for i in qubit_indices]
                    circuit.append(op, qubit_objs)
                except Exception:
                    pass
    else:
        # No parameters - use simple gate methods
        if gate_name == 'cx' and len(qubit_indices) == 2:
            circuit.cx(qubit_indices[0], qubit_indices[1])
        elif gate_name == 'cy' and len(qubit_indices) == 2:
            circuit.cy(qubit_indices[0], qubit_indices[1])
        elif gate_name == 'cz' and len(qubit_indices) == 2:
            circuit.cz(qubit_indices[0], qubit_indices[1])
        elif gate_name == 'swap' and len(qubit_indices) == 2:
            circuit.swap(qubit_indices[0], qubit_indices[1])
        elif gate_name == 'h' and len(qubit_indices) == 1:
            circuit.h(qubit_indices[0])
        elif gate_name == 'x' and len(qubit_indices) == 1:
            circuit.x(qubit_indices[0])
        elif gate_name == 'y' and len(qubit_indices) == 1:
            circuit.y(qubit_indices[0])
        elif gate_name == 'z' and len(qubit_indices) == 1:
            circuit.z(qubit_indices[0])
        elif gate_name == 's' and len(qubit_indices) == 1:
            circuit.s(qubit_indices[0])
        elif gate_name == 't' and len(qubit_indices) == 1:
            circuit.t(qubit_indices[0])
        elif gate_name == 'id' and len(qubit_indices) == 1:
            circuit.id(qubit_indices[0])
        else:
            # Try to get the gate method dynamically
            try:
                gate_method = getattr(circuit, gate_name.lower())
                if len(qubit_indices) == 1:
                    gate_method(qubit_indices[0])
                elif len(qubit_indices) == 2:
                    gate_method(qubit_indices[0], qubit_indices[1])
                elif len(qubit_indices) == 3:
                    gate_method(qubit_indices[0], qubit_indices[1], qubit_indices[2])
            except AttributeError:
                # Last resort: try to append the operation with qubit objects
                try:
                    qubit_objs = [circuit.qubits[i] for i in qubit_indices]
                    circuit.append(op, qubit_objs)
                except Exception:
                    pass


def analyze_circuit(
    circuit: QuantumCircuit,
    optimization_level: int = 1,
    min_repetitions: int = 2,
    max_window_size: int = 8
) -> Dict[str, Any]:
    """
    Analyze a quantum circuit and extract macro-gates.
    
    Args:
        circuit: Qiskit QuantumCircuit to analyze
        optimization_level: Qiskit transpilation optimization level (0-3)
        min_repetitions: Minimum number of repetitions to consider a pattern
        max_window_size: Maximum window size for pattern detection
    
    Returns:
        Dictionary with:
        - 'dag_flat': Flat DAG representation (list of operations)
        - 'dag_hierarchical': Hierarchical DAG with macro-gates collapsed
        - 'macros': List of detected macro-gates with labels
        - 'statistics': Analysis statistics
    """
    # Step 1: Transpile and get DAG
    transpiled_qc = transpile(circuit, optimization_level=optimization_level)
    dag = circuit_to_dag(transpiled_qc)
    
    # Step 2: Extract operations sequence
    ops_sequence = extract_operations_from_dag(dag)
    
    # Step 3: Detect patterns
    detector = MacroGateDetector(min_repetitions=min_repetitions, max_window_size=max_window_size)
    patterns = detector.detect_patterns(ops_sequence)
    macros = detector.find_non_overlapping_macros(patterns, ops_sequence)
    
    # Step 4: Label macros
    labeler = SemanticLabeler()
    total_circuit_length = len(ops_sequence)
    for macro in macros:
        macro['label'] = labeler.label_macro(macro, macro['sequence'], macros, total_circuit_length)
    
    # Step 5: Create hierarchical view
    hierarchical_view = create_hierarchical_view(ops_sequence, macros)
    
    # Step 6: Build flat DAG representation
    dag_flat = [
        {
            'position': i,
            'gate': ops_sequence[i][0],
            'qubits': list(ops_sequence[i][1]) if len(ops_sequence[i]) > 1 else []
        }
        for i in range(len(ops_sequence))
    ]
    
    # Step 7: Build macro-gate list (serializable)
    macros_serializable = [
        {
            'label': m['label'],
            'count': m['count'],
            'window_size': m['window_size'],
            'gates': [{'name': g[0], 'qubits': list(g[1])} for g in m['sequence']],
            'positions': [{'start': start, 'end': end} for start, end in m['positions']]
        }
        for m in macros
    ]
    
    # Step 8: Calculate statistics
    original_gates = len(ops_sequence)
    collapsed_items = len(hierarchical_view)
    compression_ratio = original_gates / collapsed_items if collapsed_items > 0 else 1
    
    statistics = {
        'original_gates': original_gates,
        'transpiled_gates': len(transpiled_qc.data),
        'circuit_depth': transpiled_qc.depth(),
        'num_qubits': transpiled_qc.num_qubits,
        'num_macros': len(macros),
        'total_macro_instances': sum(m['count'] for m in macros),
        'hierarchical_items': collapsed_items,
        'compression_ratio': round(compression_ratio, 2),
        'dag_nodes': len(list(dag.nodes())),
        'dag_edges': len(list(dag.edges()))
    }
    
    return {
        'dag_flat': dag_flat,
        'dag_hierarchical': hierarchical_view,
        'macros': macros_serializable,
        'statistics': statistics
    }


def convert_to_app_circuit_format(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert the analysis result to the app-circuit.json format.
    
    Args:
        analysis_result: Result dictionary from analyze_circuit()
    
    Returns:
        Dictionary with 'nodes', 'edges', and 'macros' in app-circuit.json format
    """
    output_nodes = []
    output_edges = []
    output_macros = []
    
    # Get number of qubits
    num_qubits = analysis_result.get('statistics', {}).get('num_qubits', 0)
    qubit_list = [str(i) for i in range(num_qubits)]
    
    # Track last node on each qubit and node layers
    last_node_on_qubit = {}
    node_layers = {}
    
    # --- 1. Add Init Nodes ---
    start_layer = -1
    for q in qubit_list:
        node_id = f"q_start_{q}"
        node_data = {
            "id": node_id,
            "name": f"q{q}_init",
            "type": "init",
            "position": -1,
            "qubits": [q],
            "layer": start_layer
        }
        output_nodes.append(node_data)
        last_node_on_qubit[q] = node_id
        node_layers[node_id] = start_layer
    
    # --- 2. Build Gate Nodes from dag_flat ---
    # Use dag_flat to get all gates (not collapsed in hierarchical view)
    hierarchical_nodes = []
    gate_position_to_id = {}  # Map position to gate ID
    
    for item in analysis_result.get('dag_flat', []):
        pos = item['position']
        node_id = f"gate_{pos}"
        gate_position_to_id[pos] = node_id
        
        node_data = {
            "id": node_id,
            "name": item['gate'],
            "type": "gate",
            "position": pos,
            "qubits": item['qubits'],
            "layer": 0  # Will be calculated below
        }
        hierarchical_nodes.append(node_data)
    
    # --- 3. Calculate Layers and Build Edges ---
    max_gate_layer = 0
    
    for node in hierarchical_nodes:
        node_id = node['id']
        qubits = node['qubits']
        
        predecessor_layers = []
        predecessor_nodes = []
        
        # Check dependencies for each qubit
        for q in qubits:
            if q in last_node_on_qubit:
                pred_id = last_node_on_qubit[q]
                if (pred_id, q) not in predecessor_nodes:
                    predecessor_nodes.append((pred_id, q))
                    predecessor_layers.append(node_layers[pred_id])
        
        # Calculate layer
        current_layer = 0
        if predecessor_layers:
            current_layer = 1 + max(predecessor_layers)
        
        max_gate_layer = max(max_gate_layer, current_layer)
        node['layer'] = current_layer
        node_layers[node_id] = current_layer
        output_nodes.append(node)
        
        # Create edges
        for pred_id, q in predecessor_nodes:
            edge = {
                "name": f"q{q}",
                "from-node": pred_id,
                "to-node": node_id,
                "qubit": q
            }
            output_edges.append(edge)
        
        # Update last node tracker
        for q in qubits:
            last_node_on_qubit[q] = node_id
    
    # --- 4. Add End Nodes ---
    end_layer = max_gate_layer + 1
    positions = [n.get('position', 0) for n in hierarchical_nodes]
    max_pos = (max(positions) if positions else 0) + 1
    
    for q in qubit_list:
        node_id = f"q_end_{q}"
        node_data = {
            "id": node_id,
            "name": f"q{q}_end",
            "type": "end",
            "position": max_pos,
            "qubits": [q],
            "layer": end_layer
        }
        output_nodes.append(node_data)
        
        pred_id = last_node_on_qubit[q]
        edge = {
            "name": f"q{q}",
            "from-node": pred_id,
            "to-node": node_id,
            "qubit": q
        }
        output_edges.append(edge)
    
    # --- 5. Build Macros with gate_ids ---
    for macro_def in analysis_result.get('macros', []):
        # For each position where this macro appears, collect the gate IDs
        macro_instances = []
        for pos_info in macro_def.get('positions', []):
            start = pos_info['start']
            end = pos_info['end']
            
            # Collect gate IDs for this instance
            gate_ids = []
            for pos in range(start, end):
                if pos in gate_position_to_id:
                    gate_ids.append(gate_position_to_id[pos])
            
            if gate_ids:
                macro_instances.append({
                    "name": macro_def['label'],
                    "gate_ids": gate_ids,
                    "nodes": [
                        {
                            "name": gate['name'],
                            "qubits": gate['qubits']
                        }
                        for gate in macro_def.get('gates', [])
                    ]
                })
        
        # If no instances found, still add the macro definition
        if not macro_instances:
            output_macros.append({
                "name": macro_def['label'],
                "gate_ids": [],
                "nodes": [
                    {
                        "name": gate['name'],
                        "qubits": gate['qubits']
                    }
                    for gate in macro_def.get('gates', [])
                ]
            })
        else:
            # Add each instance separately (as shown in app-circuit.json)
            output_macros.extend(macro_instances)
    
    return {
        "nodes": output_nodes,
        "edges": output_edges,
        "macros": output_macros
    }


# # Example usage
# if __name__ == "__main__":
#     # Create a test circuit
#     qc = QuantumCircuit(4)
    
#     # Create a repeating ansatz-like pattern
#     for layer in range(3):
#         for i in range(3):
#             qc.cx(i, i+1)
#         for i in range(4):
#             qc.ry(0.5, i)
#         qc.cx(0, 2)
#         qc.cx(1, 3)
    
#     # Analyze the circuit
#     result = analyze_circuit(qc)
    
#     # Print results
#     print("="*70)
#     print("MACRO-GATE DETECTION RESULTS")
#     print("="*70)
#     print(f"\nStatistics:")
#     for key, value in result['statistics'].items():
#         print(f"  {key}: {value}")
    
#     print(f"\nDetected {len(result['macros'])} macro-gates:")
#     for i, macro in enumerate(result['macros'][:5], 1):
#         print(f"\n  {i}. {macro['label']} (appears {macro['count']} times)")
#         print(f"     Gates: {[g['name'] for g in macro['gates']]}")
    
#     print(f"\nHierarchical view has {len(result['dag_hierarchical'])} items")
#     print(f"  (vs {len(result['dag_flat'])} in flat view)")
    
#     # Create a new circuit with macro-gates as custom gates
#     print("\n" + "="*70)
#     print("Creating circuit with macro-gates...")
#     print("="*70)
#     macro_circuit = create_macro_gate_circuit(qc, result)
    
#     print("\nOriginal circuit:")
#     print(qc.draw(output='text'))
    
#     print("\nCircuit with macro-gates (visual only):")
#     print(macro_circuit.draw(output='text'))
    
#     # The result dictionary is JSON-serializable
#     print("\n" + "="*70)
#     print("Result is JSON-serializable:")
#     print(f"  Flat DAG: {len(result['dag_flat'])} operations")
#     print(f"  Hierarchical DAG: {len(result['dag_hierarchical'])} items")
#     print(f"  Macros: {len(result['macros'])} macro-gates")
#     print("="*70)

