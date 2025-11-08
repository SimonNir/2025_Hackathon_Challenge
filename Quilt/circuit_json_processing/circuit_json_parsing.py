import json

def parse_circuit_dag(input_data):
    """
    Parses a quantum circuit's hierarchical DAG into a graph structure
    with nodes, edges, and macro definitions, calculating the
    dependency layer for each node.
    
    This version adds conceptual 'init' nodes at layer -1
    and 'end' nodes at layer (max_layer + 1).

    Macros are ignored as graph nodes/edges; they only appear in the
    output 'macros' section with their name and constituent nodes.
    """
    
    # These will be the components of our final JSON
    output_nodes = []
    output_edges = []
    output_macros = []
    
    # Helper dicts to build the graph
    last_node_on_qubit = {}  # Tracks the most recent node ID on each qubit line
    node_layers = {}         # Stores the calculated layer for each node ID
    
    # --- 0. Add "Init" Nodes (NEW) ---
    # Create start nodes for each qubit at layer -1
    
    # Get the number of qubits from statistics
    num_qubits = input_data.get("statistics", {}).get("num_qubits", 0)
    if num_qubits == 0:
        print("Warning: 'num_qubits' not found in statistics. Graph may be incomplete.")
        # As a fallback, we could try to infer from the gates,
        # but for this problem, we'll rely on the statistics.
    
    qubit_list = [str(i) for i in range(num_qubits)]
    start_layer = -1
    
    for q in qubit_list:
        node_id = f"q_start_{q}"
        node_data = {
            "id": node_id,
            "name": f"q{q}_init",
            "type": "init",
            "position": -1, # Use -1 for position
            "qubits": [q],
            "layer": start_layer
        }
        output_nodes.append(node_data)
        
        # Pre-populate the trackers. This ensures the first
        # *real* gate on this qubit will connect to this 'init' node.
        last_node_on_qubit[q] = node_id
        node_layers[node_id] = start_layer


    # --- 0.5. Build position-to-ID mapping from dag_flat ---
    # This ensures ALL gates have IDs, even those inside macros
    # We need this for gate_ids in macro definitions
    gate_position_to_id = {}
    for item in input_data.get("dag_flat", []):
        pos = item.get("position", item.get("pos", -1))
        if pos >= 0:
            gate_position_to_id[pos] = f"gate_{pos}"
    
    # --- 1. Build Node List ---
    # Iterate through the hierarchical DAG to create our
    # base list of gate nodes. Macros are skipped here and
    # reported only in the 'macros' section below.
    
    hierarchical_nodes = []
    for item in input_data.get("dag_hierarchical", []):
        if item.get("type") == "gate":
            pos = item["position"]
            node_id = f"gate_{pos}"
            qubits = item["qubits"]
            
            node_data = {
                "id": node_id,
                "name": item["name"],
                "type": "gate",
                "position": pos,
                "qubits": qubits
            }
            hierarchical_nodes.append(node_data)
        # Macros are intentionally ignored here.

    # --- 2. Calculate Layers and Build Edges ---
    # Now, iterate through our ordered list of nodes to build
    # dependencies (edges) and calculate layers.
    
    max_gate_layer = 0 # Track the highest layer number
    
    for node in hierarchical_nodes:
        node_id = node["id"]
        qubits = node["qubits"]
        
        predecessor_layers = []
        predecessor_nodes = [] # To build edges
        
        # Check dependencies for each qubit this node touches
        for q in qubits:
            if q in last_node_on_qubit:
                pred_id = last_node_on_qubit[q]
                
                if (pred_id, q) not in predecessor_nodes:
                    predecessor_nodes.append((pred_id, q))
                    # Fetch the layer of the predecessor
                    predecessor_layers.append(node_layers[pred_id])
            else:
                # This should not happen if our 'init' step is correct
                print(f"Warning: Qubit {q} for node {node_id} has no predecessor.")

        # Calculate the layer for the current node
        current_layer = 0
        if predecessor_layers:
            # Layer is 1 + the maximum layer of all its parents
            current_layer = 1 + max(predecessor_layers)
        
        # Track the highest layer number we've seen
        max_gate_layer = max(max_gate_layer, current_layer)
            
        # Add layer data to the node
        node["layer"] = current_layer
        node_layers[node_id] = current_layer
        
        # Add the node to our final output list
        output_nodes.append(node)
        
        # Create edge objects
        for pred_id, q in predecessor_nodes:
            edge = {
                "name": f"q{q}",      
                "from-node": pred_id,
                "to-node": node_id,   
                "qubit": q
            }
            output_edges.append(edge)
            
        # Finally, update the 'last_node' tracker for all qubits
        # this node just operated on.
        for q in qubits:
            last_node_on_qubit[q] = node_id

    # --- 2.5 Add "End" Nodes (NEW) ---
    # Create end nodes for each qubit at (max_layer + 1)
    
    end_layer = max_gate_layer + 1
    # Find the maximum position to place end nodes after
    positions = [n.get('position', 0) for n in hierarchical_nodes]
    max_pos = (max(positions) if positions else 0) + 1
    
    for q in qubit_list:
        node_id = f"q_end_{q}"
        node_data = {
            "id": node_id,
            "name": f"q{q}_end",
            "type": "end", # You can call this 'measure' or 'end'
            "position": max_pos, # Give it a high position number
            "qubits": [q],
            "layer": end_layer
        }
        output_nodes.append(node_data)
        
        # Add the final edge from the last *real* gate to this end node
        pred_id = last_node_on_qubit[q]
        
        edge = {
            "name": f"q{q}",
            "from-node": pred_id,
            "to-node": node_id,
            "qubit": q
        }
        output_edges.append(edge)

    # --- 3. Define Macro Patterns ---
    # Macros are reported only here and are not included as nodes.
    # Each macro instance gets its own entry with gate_ids, matching app-circuit.json format
    
    for macro_def in input_data.get("macros", []):
        # Build the nodes definition (same for all instances)
        constituent_nodes = []
        for gate in macro_def.get("gates", []):
            constituent_nodes.append({
                "name": gate["name"],
                "qubits": gate["qubits"]
            })
        
        # Create a separate macro entry for each position range (instance)
        # This matches the app-circuit.json format where each instance has its own entry
        for pos_info in macro_def.get("positions", []):
            start = pos_info.get("start", pos_info.get("start_position", 0))
            end = pos_info.get("end", pos_info.get("end_position", start + 1))
            
            # Collect gate_ids for this instance
            gate_ids = []
            for pos in range(start, end):
                if pos in gate_position_to_id:
                    gate_ids.append(gate_position_to_id[pos])
            
            # Add macro instance with gate_ids
            output_macros.append({
                "name": macro_def["label"],
                "gate_ids": gate_ids,
                "nodes": constituent_nodes
            })

    # --- 4. Assemble Final JSON ---
    final_output = {
        "nodes": output_nodes,
        "edges": output_edges,
        "macros": output_macros
    }
    
    return final_output


# --- Main execution ---
if __name__ == "__main__":
    
    # Your provided JSON data
    input_data = {
      "dag_flat": [
        {"position": 0, "gate": "h", "qubits": ["2"]},
        {"position": 1, "gate": "cx", "qubits": ["1", "2"]},
        {"position": 2, "gate": "u3", "qubits": ["2"]},
        {"position": 3, "gate": "cx", "qubits": ["1", "2"]},
        {"position": 4, "gate": "h", "qubits": ["1"]},
        {"position": 5, "gate": "u3", "qubits": ["2"]},
        {"position": 6, "gate": "cx", "qubits": ["0", "2"]},
        {"position": 7, "gate": "u3", "qubits": ["2"]},
        {"position": 8, "gate": "cx", "qubits": ["0", "2"]},
        {"position": 9, "gate": "cx", "qubits": ["0", "1"]},
        {"position": 10, "gate": "u3", "qubits": ["1"]},
        {"position": 11, "gate": "cx", "qubits": ["0", "1"]},
        {"position": 12, "gate": "h", "qubits": ["0"]},
        {"position": 13, "gate": "u3", "qubits": ["1"]},
        {"position": 14, "gate": "u3", "qubits": ["2"]}
      ],
      "dag_hierarchical": [
        {"type": "gate", "name": "h", "qubits": ["2"], "position": 0},
        {"type": "gate", "name": "cx", "qubits": ["1", "2"], "position": 1},
        {"type": "gate", "name": "u3", "qubits": ["2"], "position": 2},
        {"type": "gate", "name": "cx", "qubits": ["1", "2"], "position": 3},
        {"type": "gate", "name": "h", "qubits": ["1"], "position": 4},
        {"type": "macro", "label": "EntanglingLayer(2<->0)", "size": 2, "gates": [{"name": "u3", "qubits": ["2"]}, {"name": "cx", "qubits": ["0", "2"]}], "start_position": 5, "end_position": 7},
        {"type": "macro", "label": "EntanglingLayer(2<->0)", "size": 2, "gates": [{"name": "u3", "qubits": ["2"]}, {"name": "cx", "qubits": ["0", "2"]}], "start_position": 7, "end_position": 9},
        {"type": "gate", "name": "cx", "qubits": ["0", "1"], "position": 9},
        {"type": "gate", "name": "u3", "qubits": ["1"], "position": 10},
        {"type": "gate", "name": "cx", "qubits": ["0", "1"], "position": 11},
        {"type": "gate", "name": "h", "qubits": ["0"], "position": 12},
        {"type": "gate", "name": "u3", "qubits": ["1"], "position": 13},
        {"type": "gate", "name": "u3", "qubits": ["2"], "position": 14}
      ],
      "macros": [
        {"label": "EntanglingLayer(2<->0)", "count": 2, "window_size": 2, "gates": [{"name": "u3", "qubits": ["2"]}, {"name": "cx", "qubits": ["0", "2"]}], "positions": [{"start": 5, "end": 7}, {"start": 7, "end": 9}]}
      ],
      "statistics": {"original_gates": 15, "transpiled_gates": 15, "circuit_depth": 12, "num_qubits": 3, "num_macros": 1, "total_macro_instances": 2, "hierarchical_items": 13, "compression_ratio": 1.15, "dag_nodes": 21, "dag_edges": 24}
    }
    
    # Process the data
    graph_data = parse_circuit_dag(input_data)
    
    # Save the output to a file
    output_filename = "circuit_graph.json" # New filename
    with open(output_filename, 'w') as f:
        json.dump(graph_data, f, indent=2)

    print(f"Successfully processed circuit and saved to {output_filename}")
    
    # Print a preview
    print("\n--- Output JSON Preview (showing new nodes) ---")
    
    # Create a small preview showing just the new nodes and edges
    preview = {
        "nodes": [n for n in graph_data["nodes"] if n["type"] in ("init", "end")],
        "edges": [e for e in graph_data["edges"] if "start" in e["from-node"] or "end" in e["to-node"]]
    }
    print(json.dumps(preview, indent=2))