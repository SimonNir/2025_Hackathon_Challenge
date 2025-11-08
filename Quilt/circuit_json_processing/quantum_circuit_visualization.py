import json
import networkx as nx
import matplotlib.pyplot as plt

def visualize_circuit_graph(json_filepath):
    """
    Loads the circuit graph JSON and visualizes it using
    networkx and matplotlib, arranging nodes by layer and qubit.
    """
    
    # --- 1. Load Data ---
    try:
        with open(json_filepath, 'r') as f:
            graph_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: The file {json_filepath} was not found.")
        print("Please make sure it's in the same directory as this script.")
        return
    
    nodes = graph_data.get('nodes', [])
    edges = graph_data.get('edges', [])

    if not nodes:
        print("No nodes found in the JSON data.")
        return

    # --- 2. Create NetworkX Graph ---
    G = nx.DiGraph()

    # Add nodes and store their data
    for node in nodes:
        G.add_node(node['id'], **node)

    # Add edges
    for edge in edges:
        G.add_edge(edge['from-node'], edge['to-node'], **edge)

    # --- 3. Prepare for Plotting ---
    
    # Create a layout (position) for each node.
    # x-position = layer
    # y-position = -qubit_id (negative to put qubit 0 at the top)
    pos = {}
    for node_id, data in G.nodes(data=True):
        layer = data.get('layer', 0)
        
        # We'll use the *first* qubit in the list for Y-positioning
        # This keeps multi-qubit gates anchored to a line.
        try:
            # Qubit IDs are strings, convert to int
            y_pos = -int(data['qubits'][0]) 
        except (IndexError, ValueError, TypeError):
            y_pos = 0 # Fallback for any unusual nodes
            
        pos[node_id] = (layer, y_pos)

    # Create color map for nodes
    color_map = []
    for node_id, data in G.nodes(data=True):
        if data.get('type') == 'macro':
            color_map.append('skyblue') # Macros
        else:
            color_map.append('salmon') # Gates

    # Create labels from node names
    labels = {node_id: data['name'] for node_id, data in G.nodes(data=True)}
    
    # Create labels for edges (showing the qubit)
    edge_labels = {
        (u, v): d['name'] for u, v, d in G.edges(data=True)
    }

    # --- 4. Draw the Graph ---
    print("Drawing graph...")
    
    plt.figure(figsize=(18, 10)) # Make the plot larger
    
    # Draw the nodes
    nx.draw_networkx_nodes(
        G,
        pos,
        node_size=3000,
        node_color=color_map,
        alpha=0.9
    )
    
    # Draw the edges
    nx.draw_networkx_edges(
        G,
        pos,
        node_size=3000,
        arrowstyle='-|>',
        arrowsize=20,
        edge_color='gray',
        connectionstyle='arc3,rad=0.1' #Slightly curve parallel edges
    )
    
    # Draw node labels
    nx.draw_networkx_labels(
        G,
        pos,
        labels,
        font_size=10,
        font_weight='bold'
    )
    
    # Draw edge labels
    nx.draw_networkx_edge_labels(
        G,
        pos,
        edge_labels=edge_labels,
        font_color='black',
        font_size=8
    )

    plt.title("Quantum Circuit Dependency Graph", size=20)
    plt.xlabel("Circuit Layer (Depth)", size=15)
    plt.ylabel("Qubit Index", size=15)
    
    # Set Y-axis labels to be positive qubit numbers
    ax = plt.gca()
    # Get all unique Y positions
    y_ticks = sorted(list(set(p[1] for p in pos.values())))
    if y_ticks:
        ax.set_yticks(y_ticks)
        ax.set_yticklabels([str(abs(y)) for y in y_ticks])
    
    # Turn off the axis box
    plt.box(False)
    # Ensure all layers are shown on x-axis
    max_layer = max(d.get('layer', 0) for _, d in G.nodes(data=True))
    plt.xticks(range(max_layer + 1))
    
    plt.grid(axis='x', linestyle='--', alpha=0.5) # Add gridlines for layers
    plt.tight_layout()
    
    # Save the figure
    output_filename = "circuit_graph.png"
    plt.savefig(output_filename)
    print(f"Graph saved to {output_filename}")
    
    # Show the plot
    plt.show()


# --- Main execution ---
if __name__ == "__main__":
    visualize_circuit_graph("circuit_graph.json")