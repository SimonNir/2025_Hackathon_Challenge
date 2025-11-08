import { useState, useCallback } from 'react';
import { ReactFlow, applyNodeChanges, applyEdgeChanges, addEdge, Handle, Position } from '@xyflow/react';
import '@xyflow/react/dist/style.css';

// Custom node component to ensure labels are visible
function CustomNode({ data }) {
  return (
    <div style={{ 
      background: '#fff', 
      border: '1px solid #1a192b', 
      borderRadius: '3px', 
      padding: '10px',
      color: '#222',
      fontSize: '12px',
      minWidth: '100px',
      textAlign: 'center'
    }}>
      {/* Three handles on top */}
      <Handle type="target" position={Position.Top} id="top-target-1" style={{ left: '20%' }} />
      <Handle type="target" position={Position.Top} id="top-target-2" style={{ left: '50%' }} />
      <Handle type="target" position={Position.Top} id="top-target-3" style={{ left: '80%' }} />
      
      <div>{data.label}</div>
      
      {/* Three handles on bottom */}
      <Handle type="source" position={Position.Bottom} id="bottom-source-1" style={{ left: '20%' }} />
      <Handle type="source" position={Position.Bottom} id="bottom-source-2" style={{ left: '50%' }} />
      <Handle type="source" position={Position.Bottom} id="bottom-source-3" style={{ left: '80%' }} />
      
      {/* Also add source handles on top and target handles on bottom for flexibility */}
      <Handle type="source" position={Position.Top} id="top-source-1" style={{ left: '20%' }} />
      <Handle type="source" position={Position.Top} id="top-source-2" style={{ left: '50%' }} />
      <Handle type="source" position={Position.Top} id="top-source-3" style={{ left: '80%' }} />
      <Handle type="target" position={Position.Bottom} id="bottom-target-1" style={{ left: '20%' }} />
      <Handle type="target" position={Position.Bottom} id="bottom-target-2" style={{ left: '50%' }} />
      <Handle type="target" position={Position.Bottom} id="bottom-target-3" style={{ left: '80%' }} />
    </div>
  );
}

// Circle node component - only one output at bottom
function CircleNode({ data }) {
  return (
    <div style={{ 
      width: '80px',
      height: '80px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      position: 'relative'
    }}>
      {/* Circle shape */}
      <div style={{
        width: '70px',
        height: '70px',
        background: '#fff',
        border: '2px solid #1a192b',
        borderRadius: '50%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative'
      }}>
        <div style={{
          color: '#222',
          fontSize: '12px',
          fontWeight: 'bold',
          textAlign: 'center'
        }}>
          {data.label}
        </div>
      </div>
      
      {/* Single output handle at bottom center */}
      <Handle type="source" position={Position.Bottom} id="bottom-source" />
      {/* Single input handle at top center */}
      <Handle type="target" position={Position.Top} id="top-target" />
    </div>
  );
}

// Custom group node component to display label
function GroupNode({ data, style }) {
  return (
    <div style={{
      ...style,
      background: 'rgba(240, 240, 240, 0.3)',
      border: '2px solid #1a192b',
      borderRadius: '5px',
      position: 'relative',
      paddingTop: '30px'
    }}>
      {data.label && (
        <div style={{
          position: 'absolute',
          top: '5px',
          left: '10px',
          color: '#222',
          fontSize: '14px',
          fontWeight: 'bold',
          background: '#fff',
          padding: '4px 10px',
          borderRadius: '3px',
          border: '2px solid #1a192b',
          zIndex: 10,
          whiteSpace: 'nowrap'
        }}>
          {data.label}
        </div>
      )}
    </div>
  );
}

const nodeTypes = {
  custom: CustomNode,
  circle: CircleNode,
  group: GroupNode,
};

// Function to parse JSON and convert to React Flow format
function parseCircuitData(circuitData) {
  const nodes = [];
  const edges = [];
  
  // Color palette for qubits (supports up to 40 qubits with distinct colors)
  // Generated to maximize visual distinction across the color spectrum
  const colorPalette = [
    '#ff6b6b', // 0: coral red
    '#4ecdc4', // 1: turquoise
    '#45b7d1', // 2: sky blue
    '#f9ca24', // 3: yellow
    '#6c5ce7', // 4: purple
    '#a29bfe', // 5: light purple
    '#fd79a8', // 6: pink
    '#fdcb6e', // 7: peach
    '#e17055', // 8: salmon
    '#00b894', // 9: mint green
    '#00cec9', // 10: cyan
    '#0984e3', // 11: blue
    '#55efc4', // 12: aqua
    '#74b9ff', // 13: light blue
    '#ff7675', // 14: light red
    '#ffa502', // 15: orange
    '#2ed573', // 16: green
    '#ff6348', // 17: tomato
    '#5352ed', // 18: indigo
    '#ff4757', // 19: red
    '#5f27cd', // 20: violet
    '#00d2d3', // 21: teal
    '#ff9ff3', // 22: magenta
    '#54a0ff', // 23: bright blue
    '#c44569', // 24: rose
    '#feca57', // 25: gold
    '#48dbfb', // 26: cyan blue
    '#1dd1a1', // 27: emerald
    '#3742fa', // 28: royal blue
    '#2f3542', // 29: dark gray-blue
    '#ff3838', // 30: bright red
    '#ff9f43', // 31: orange
    '#10ac84', // 32: green
    '#ee5a6f', // 33: rose red
    '#0abde3', // 34: bright cyan
    '#ffd32a', // 35: bright yellow
    '#ff6b81', // 36: pink red
    '#c7ecee', // 37: pale blue
    '#ffa8b6', // 38: light pink
    '#a8e6cf', // 39: light green
  ];
  
  const getQubitColor = (qubitId) => {
    const index = parseInt(qubitId);
    return colorPalette[index % colorPalette.length];
  };
  
  // Step 1: Extract qubits and calculate dynamic positions
  const initNodes = circuitData.nodes.filter(n => n.type === 'init');
  initNodes.sort((a, b) => parseInt(a.qubits[0]) - parseInt(b.qubits[0]));
  
  const qubitXPositions = {};
  const qubitSpacing = 400; // Increased from 250 to 400 for even more horizontal separation
  const qubitColors = {};
  
  // Create qubit nodes and calculate x positions
  initNodes.forEach((initNode, index) => {
    const qubitId = initNode.qubits[0];
    const x = index * qubitSpacing;
    qubitXPositions[qubitId] = x;
    qubitColors[qubitId] = getQubitColor(qubitId);
    
    // Create qubit node (circle type)
    nodes.push({
      id: `q${qubitId}`,
      type: 'circle',
      position: { x, y: 0 },
      data: { label: `q${qubitId}` }
    });
  });
  
  // Step 2: Build graph structure to determine gate positions
  const gateNodes = circuitData.nodes.filter(n => n.type === 'gate');
  const gatePositions = {};
  const gatesInGroups = new Set();
  
  // Collect gates that will be in groups
  if (circuitData.macros) {
    circuitData.macros.forEach((macro) => {
      if (macro.gate_ids && Array.isArray(macro.gate_ids)) {
        macro.gate_ids.forEach(gid => gatesInGroups.add(gid));
      }
    });
  }
  
  // Build edge graph to determine gate depths
  const edgesByTarget = {};
  const edgesBySource = {};
  
  circuitData.edges.forEach(edge => {
    const source = edge['from-node'];
    const target = edge['to-node'];
    
    if (!edgesByTarget[target]) {
      edgesByTarget[target] = [];
    }
    edgesByTarget[target].push(edge);
    
    if (!edgesBySource[source]) {
      edgesBySource[source] = [];
    }
    edgesBySource[source].push(edge);
  });
  
  // Map init/end nodes to qubit IDs
  const nodeIdToQubitId = {};
  initNodes.forEach(initNode => {
    const qubitId = initNode.qubits[0];
    nodeIdToQubitId[initNode.id] = `q${qubitId}`;
  });
  
  // Build a graph structure for topological sorting
  const graph = {}; // nodeId -> [neighborIds]
  const inDegree = {}; // nodeId -> number of incoming edges
  
  // Initialize graph and inDegree for all gates
  gateNodes.forEach(gate => {
    graph[gate.id] = [];
    inDegree[gate.id] = 0;
  });
  
  // Build graph from all edges (including qubit-to-gate and gate-to-gate)
  circuitData.edges.forEach(edge => {
    let sourceId = edge['from-node'];
    let targetId = edge['to-node'];
    
    // Convert init nodes to qubit IDs, but keep gate IDs as-is
    if (nodeIdToQubitId[sourceId]) {
      sourceId = nodeIdToQubitId[sourceId];
    }
    
    // Check if target is a gate
    const targetGate = gateNodes.find(g => g.id === targetId);
    
    if (targetGate) {
      // Target is a gate - count incoming edges
      if (!inDegree[targetId]) {
        inDegree[targetId] = 0;
      }
      
      // If source is also a gate, add to graph
      const sourceGate = gateNodes.find(g => g.id === sourceId);
      if (sourceGate) {
        if (!graph[sourceId]) graph[sourceId] = [];
        graph[sourceId].push(targetId);
        inDegree[targetId]++;
      } else {
        // Source is a qubit - this gate has no incoming gate edges
        // inDegree stays 0 (or is already 0)
      }
    }
  });
  
  // Topological sort to ensure proper ordering
  const gateDepths = {};
  const queue = [];
  const processed = new Set();
  
  // Initialize with gates that have no incoming gate edges (connected directly to qubits)
  gateNodes.forEach(gate => {
    if (inDegree[gate.id] === 0) {
      gateDepths[gate.id] = 1;
      queue.push({ gateId: gate.id, depth: 1 });
      processed.add(gate.id);
    }
  });
  
  // Process gates in topological order
  while (queue.length > 0) {
    const { gateId, depth } = queue.shift();
    
    // Process all neighbors
    if (graph[gateId]) {
      graph[gateId].forEach(neighborId => {
        if (!processed.has(neighborId)) {
          inDegree[neighborId]--;
          if (inDegree[neighborId] === 0) {
            gateDepths[neighborId] = depth + 1;
            queue.push({ gateId: neighborId, depth: depth + 1 });
            processed.add(neighborId);
          } else {
            // Update depth if this path is longer
            gateDepths[neighborId] = Math.max(gateDepths[neighborId] || 0, depth + 1);
          }
        }
      });
    }
  }
  
  // For any gates not processed, assign depth based on layer or default
  gateNodes.forEach(gate => {
    if (!gateDepths[gate.id]) {
      gateDepths[gate.id] = gate.layer || 1;
    }
  });
  
  // Ensure proper ordering: if A -> B, then depth(A) < depth(B)
  // Do a final pass to ensure all edges respect depth ordering
  let changed = true;
  let iterations = 0;
  while (changed && iterations < 10) {
    changed = false;
    circuitData.edges.forEach(edge => {
      let sourceId = edge['from-node'];
      let targetId = edge['to-node'];
      
      if (nodeIdToQubitId[sourceId]) {
        sourceId = nodeIdToQubitId[sourceId];
      }
      
      const sourceGate = gateNodes.find(g => g.id === sourceId);
      const targetGate = gateNodes.find(g => g.id === targetId);
      
      if (sourceGate && targetGate) {
        const sourceDepth = gateDepths[sourceId] || 1;
        const targetDepth = gateDepths[targetId] || 1;
        
        if (sourceDepth >= targetDepth) {
          gateDepths[targetId] = sourceDepth + 1;
          changed = true;
        }
      }
    });
    iterations++;
  }
  
  // Position gates by depth with proper spacing
  const layerHeight = 250; // Increased from 200 to 250 for even more vertical separation
  const baseY = 150;
  const gatesByLayer = {};
  
  gateNodes.forEach(gate => {
    const depth = gateDepths[gate.id] || 1;
    if (!gatesByLayer[depth]) {
      gatesByLayer[depth] = [];
    }
    gatesByLayer[depth].push(gate);
  });
  
  // Position gates within each layer with proper horizontal spacing
  Object.keys(gatesByLayer).sort((a, b) => parseInt(a) - parseInt(b)).forEach(layer => {
    const layerGates = gatesByLayer[layer];
    const y = baseY + parseInt(layer) * layerHeight;
    
    // Track x positions used in this layer to avoid overlaps
    const xPositionsUsed = new Set();
    const horizontalOffset = 200; // Additional horizontal spacing for overlapping gates (increased from 120 to 200)
    
    layerGates.forEach((gate) => {
      // Find the leftmost qubit for this gate
      const qubitIndices = gate.qubits.map(q => parseInt(q)).sort((a, b) => a - b);
      const leftmostQubit = qubitIndices[0];
      let x = qubitXPositions[leftmostQubit.toString()] || 0;
      
      // Check if this x position is already used, if so, add offset
      let offset = 0;
      while (xPositionsUsed.has(x + offset)) {
        offset += horizontalOffset;
      }
      x = x + offset;
      xPositionsUsed.add(x);
      
      gatePositions[gate.id] = { x, y };
      
      // Create non-grouped gate nodes
      if (!gatesInGroups.has(gate.id)) {
        nodes.push({
          id: gate.id,
          type: 'custom',
          position: { x, y },
          data: { label: gate.name.toUpperCase() }
        });
      }
    });
  });
  
  // Step 3: Create groups using gate_ids from macros
  if (circuitData.macros) {
    circuitData.macros.forEach((macro, macroIndex) => {
      if (macro.gate_ids && Array.isArray(macro.gate_ids) && macro.gate_ids.length > 0) {
        const groupGates = macro.gate_ids.filter(gid => gatePositions[gid]);
        
        if (groupGates.length > 0) {
          // Calculate group bounds based on gate positions
          const groupX = Math.min(...groupGates.map(gid => gatePositions[gid].x));
          const groupY = Math.min(...groupGates.map(gid => gatePositions[gid].y));
          const groupMaxY = Math.max(...groupGates.map(gid => gatePositions[gid].y));
          
          // Calculate group height dynamically with more padding
          const gateSpacing = 180; // Space between gates (increased from 150 to 180)
          const topPadding = 60; // Space for label at top (increased from 50 to 60)
          const bottomPadding = 50; // Space at bottom
          const groupHeight = (groupGates.length - 1) * gateSpacing + topPadding + bottomPadding + 100; // 100 for gate height
          
          // Create group node with larger width
          const groupId = `group${macroIndex + 1}`;
          const groupNode = {
            id: groupId,
            type: 'group',
            position: { x: groupX, y: groupY - 40 }, // Adjusted to account for label space
            style: { width: 300, height: groupHeight }, // Increased width from 200 to 300
            data: { label: macro.name }
          };
          nodes.push(groupNode);
          
          // Create gate nodes as children of the group with more spacing
          let relativeY = topPadding + 10; // Start position within group (space for label + extra padding)
          groupGates.forEach((gateId) => {
            const gate = gateNodes.find(g => g.id === gateId);
            if (gate) {
              nodes.push({
                id: gateId,
                type: 'custom',
                parentId: groupId,
                extent: 'parent',
                position: { x: 20, y: relativeY }, // Increased x from 10 to 20 for more horizontal space
                data: { label: gate.name.toUpperCase() }
              });
              relativeY += gateSpacing; // Space between gates (increased from 100px)
            }
          });
        }
      }
    });
  }
  
  // Step 4: Create edges with proper colors and handles
  let edgeCounter = 0;
  
  // Track handle usage for each node to ensure different handles are used
  const sourceHandleUsage = {}; // nodeId -> Set of used source handles
  const targetHandleUsage = {}; // nodeId -> Set of used target handles
  const nodeEntryHandle = {}; // nodeId_qubitId -> handle index used when entering (for correspondence)
  const qubitHandleMap = {}; // qubitId -> preferred handle index (1, 2, or 3) to keep edges aligned
  
  // Helper function to determine preferred handle index based on qubit position
  const getPreferredHandleIndex = (qubitId, allQubits) => {
    const qubitIndex = parseInt(qubitId);
    const sortedQubits = allQubits.map(q => parseInt(q)).sort((a, b) => a - b);
    const positionInSorted = sortedQubits.indexOf(qubitIndex);
    
    // Map position to handle: leftmost -> 1, middle -> 2, rightmost -> 3
    if (sortedQubits.length === 1) return 2; // Middle if only one
    if (sortedQubits.length === 2) {
      return positionInSorted === 0 ? 1 : 3; // Left or right
    }
    // For 3+ qubits, distribute: left -> 1, middle -> 2, right -> 3
    if (positionInSorted === 0) return 1; // Leftmost
    if (positionInSorted === sortedQubits.length - 1) return 3; // Rightmost
    return 2; // Middle
  };
  
  // Helper function to get source handle based on entry handle for a specific qubit
  const getSourceHandle = (node, qubitId, entryHandleIndex, allQubits) => {
    if (node.type === 'circle') {
      return 'bottom-source'; // Circle nodes only have one source handle
    }
    
    // Use the same handle index as the entry handle for this qubit
    if (entryHandleIndex !== undefined && entryHandleIndex !== null) {
      const handle = `bottom-source-${entryHandleIndex}`;
      if (!sourceHandleUsage[node.id]) {
        sourceHandleUsage[node.id] = new Set();
      }
      sourceHandleUsage[node.id].add(handle);
      return handle;
    }
    
    // If no entry handle, try to use preferred handle for this qubit
    if (!qubitHandleMap[qubitId]) {
      qubitHandleMap[qubitId] = getPreferredHandleIndex(qubitId, allQubits);
    }
    const preferredIndex = qubitHandleMap[qubitId];
    
    if (!sourceHandleUsage[node.id]) {
      sourceHandleUsage[node.id] = new Set();
    }
    
    // Try preferred handle first
    const preferredHandle = `bottom-source-${preferredIndex}`;
    if (!sourceHandleUsage[node.id].has(preferredHandle)) {
      sourceHandleUsage[node.id].add(preferredHandle);
      return preferredHandle;
    }
    
    // If preferred is taken, find next available
    for (let i = 1; i <= 3; i++) {
      const handle = `bottom-source-${i}`;
      if (!sourceHandleUsage[node.id].has(handle)) {
        sourceHandleUsage[node.id].add(handle);
        return handle;
      }
    }
    
    return 'bottom-source-1';
  };
  
  const getTargetHandle = (node, qubitId, allQubits) => {
    if (node.type === 'circle') {
      return 'top-target'; // Circle nodes only have one target handle
    }
    
    if (!targetHandleUsage[node.id]) {
      targetHandleUsage[node.id] = new Set();
    }
    
    // Try to use preferred handle for this qubit to keep edges aligned
    if (!qubitHandleMap[qubitId]) {
      qubitHandleMap[qubitId] = getPreferredHandleIndex(qubitId, allQubits);
    }
    const preferredIndex = qubitHandleMap[qubitId];
    
    // Try preferred handle first
    const preferredHandle = `top-target-${preferredIndex}`;
    if (!targetHandleUsage[node.id].has(preferredHandle)) {
      targetHandleUsage[node.id].add(preferredHandle);
      // Store the handle index for this specific (node, qubit) pair
      const key = `${node.id}_${qubitId}`;
      nodeEntryHandle[key] = preferredIndex;
      return preferredHandle;
    }
    
    // If preferred is taken, try other handles
    for (let i = 1; i <= 3; i++) {
      const handle = `top-target-${i}`;
      if (!targetHandleUsage[node.id].has(handle)) {
        targetHandleUsage[node.id].add(handle);
        // Store the handle index for this specific (node, qubit) pair
        const key = `${node.id}_${qubitId}`;
        nodeEntryHandle[key] = i;
        return handle;
      }
    }
    
    // If all handles are used, use preferred (or 1 if not set)
    const key = `${node.id}_${qubitId}`;
    const finalIndex = preferredIndex || 1;
    nodeEntryHandle[key] = finalIndex;
    return `top-target-${finalIndex}`;
  };
  
  // Get all qubit IDs for handle assignment
  const allQubitIds = initNodes.map(n => n.qubits[0]);
  
  // Calculate entanglement count for each qubit
  // Track how many multi-qubit gates each qubit has passed through
  const qubitEntanglementCount = {}; // qubitId -> entanglement count
  const qubitEdgeEntanglement = {}; // edgeId -> entanglement count for that edge
  
  // Initialize entanglement counts
  allQubitIds.forEach(qubitId => {
    qubitEntanglementCount[qubitId] = 0;
  });
  
  // Process edges in order to track entanglement
  // First, build a map of edges by qubit in order
  const edgesByQubit = {}; // qubitId -> [edges in order]
  allQubitIds.forEach(qubitId => {
    edgesByQubit[qubitId] = [];
  });
  
  circuitData.edges.forEach(edge => {
    const qubitId = edge.qubit;
    if (edgesByQubit[qubitId]) {
      edgesByQubit[qubitId].push(edge);
    }
  });
  
  // Sort edges by layer/depth for each qubit
  allQubitIds.forEach(qubitId => {
    edgesByQubit[qubitId].sort((a, b) => {
      // Get the target gate for each edge
      const targetA = a['to-node'];
      const targetB = b['to-node'];
      const gateA = gateNodes.find(g => g.id === targetA);
      const gateB = gateNodes.find(g => g.id === targetB);
      
      const depthA = gateA ? (gateDepths[gateA.id] || gateA.layer || 0) : 0;
      const depthB = gateB ? (gateDepths[gateB.id] || gateB.layer || 0) : 0;
      
      return depthA - depthB;
    });
  });
  
  // Calculate entanglement for each edge
  allQubitIds.forEach(qubitId => {
    let currentEntanglement = 0;
    
    edgesByQubit[qubitId].forEach(edge => {
      const targetId = edge['to-node'];
      const targetGate = gateNodes.find(g => g.id === targetId);
      
      if (targetGate) {
        // Store entanglement count for this edge (before entering the gate)
        const edgeKey = `${edge['from-node']}_${edge['to-node']}_${qubitId}`;
        qubitEdgeEntanglement[edgeKey] = currentEntanglement;
        
        // Check if this is a multi-qubit gate (more than 1 qubit)
        if (targetGate.qubits && targetGate.qubits.length > 1) {
          // This is an entanglement gate - increment entanglement after exiting
          // The next edge will have the increased entanglement
          currentEntanglement++;
        }
      } else {
        // Not a gate, store current entanglement
        const edgeKey = `${edge['from-node']}_${edge['to-node']}_${qubitId}`;
        qubitEdgeEntanglement[edgeKey] = currentEntanglement;
      }
    });
    
    // Store final entanglement count for the qubit
    qubitEntanglementCount[qubitId] = currentEntanglement;
  });
  
  // Helper function to get stroke width based on entanglement
  const getStrokeWidth = (entanglementCount) => {
    // Base width is 2, increase by 3 for each entanglement to make it more noticeable
    // Cap at a reasonable maximum (e.g., 20)
    return Math.min(2 + (entanglementCount * 3), 20);
  };
  
  // Process existing edges
  circuitData.edges.forEach(edge => {
    // Map source and target IDs
    let sourceId = edge['from-node'];
    let targetId = edge['to-node'];
    
    // Convert init/end nodes to qubit IDs
    if (nodeIdToQubitId[sourceId]) {
      sourceId = nodeIdToQubitId[sourceId];
    }
    if (nodeIdToQubitId[targetId]) {
      targetId = nodeIdToQubitId[targetId];
    }
    
    const sourceNode = nodes.find(n => n.id === sourceId);
    const targetNode = nodes.find(n => n.id === targetId);
    
    if (sourceNode && targetNode) {
      // Get next available handles for this node
      const qubitId = edge.qubit;
      const qubitIndex = parseInt(qubitId);
      
      // Get target handle (entry point) for this qubit
      const targetHandle = getTargetHandle(targetNode, qubitId, allQubitIds);
      
      // Get source handle based on entry handle for this specific qubit
      // Look up the entry handle index for this (node, qubit) pair
      const sourceKey = `${sourceId}_${qubitId}`;
      const entryHandleIndex = nodeEntryHandle[sourceKey];
      const sourceHandle = getSourceHandle(sourceNode, qubitId, entryHandleIndex, allQubitIds);
      
      // Get color for this qubit
      const color = qubitColors[qubitId] || getQubitColor(qubitId);
      
      // Get entanglement count for this edge
      const edgeKey = `${edge['from-node']}_${edge['to-node']}_${qubitId}`;
      const entanglementCount = qubitEdgeEntanglement[edgeKey] || 0;
      const strokeWidth = getStrokeWidth(entanglementCount);
      
      edges.push({
        id: `edge-${edgeCounter++}`,
        source: sourceId,
        target: targetId,
        sourceHandle,
        targetHandle,
        label: `q${qubitId}`,
        markerEnd: { type: 'arrowclosed', color },
        style: { stroke: color, strokeWidth: strokeWidth }
      });
    }
  });
  
  // Step 5: Add measurement nodes at the end of each qubit chain
  const endNodes = circuitData.nodes.filter(n => n.type === 'end');
  const measurementNodes = {};
  const maxLayer = Math.max(...gateNodes.map(g => gateDepths[g.id] || g.layer || 0), 0);
  const measurementY = baseY + (maxLayer + 1) * layerHeight + 150; // Extra 150px spacing before measurements (increased from 100)
  
  // Build a mapping of edges by source (using converted IDs) for finding last nodes
  const edgesBySourceConverted = {};
  edges.forEach(edge => {
    if (!edgesBySourceConverted[edge.source]) {
      edgesBySourceConverted[edge.source] = [];
    }
    edgesBySourceConverted[edge.source].push(edge);
  });
  
  // Find the last node for each qubit
  initNodes.forEach(initNode => {
    const qubitId = initNode.qubits[0];
    const qubitNodeId = `q${qubitId}`;
    const x = qubitXPositions[qubitId] || 0;
    
    // Find the last node for this qubit by following edges
    let lastNodeId = qubitNodeId;
    let currentNode = qubitNodeId;
    let foundNext = true;
    
    while (foundNext) {
      foundNext = false;
      if (edgesBySourceConverted[currentNode]) {
        // Find edges for this qubit
        const qubitEdges = edgesBySourceConverted[currentNode].filter(e => e.label === `q${qubitId}`);
        if (qubitEdges.length > 0) {
          // Take the first edge (assuming they're in order)
          const nextEdge = qubitEdges[0];
          const nextId = nextEdge.target;
          const nextNode = nodes.find(n => n.id === nextId);
          if (nextNode && edgesBySourceConverted[nextId] && edgesBySourceConverted[nextId].some(e => e.label === `q${qubitId}`)) {
            currentNode = nextId;
            lastNodeId = nextId;
            foundNext = true;
          } else if (nextNode) {
            // This is the last node
            lastNodeId = nextId;
            foundNext = false;
          }
        }
      }
    }
    
    // Create measurement node
    const measurementId = `measure_${qubitId}`;
    measurementNodes[qubitId] = measurementId;
    
    nodes.push({
      id: measurementId,
      type: 'circle',
      position: { x, y: measurementY },
      data: { label: `M${qubitId}` }
    });
    
    // Add edge from last node to measurement node
    const lastNode = nodes.find(n => n.id === lastNodeId);
    if (lastNode) {
      const qubitIndex = parseInt(qubitId);
      // Use the entry handle index for this (node, qubit) pair to get corresponding exit handle
      const lastNodeKey = `${lastNodeId}_${qubitId}`;
      const entryHandleIndex = nodeEntryHandle[lastNodeKey];
      const sourceHandle = getSourceHandle(lastNode, qubitId, entryHandleIndex, allQubitIds);
      const color = qubitColors[qubitId] || getQubitColor(qubitId);
      
      // Get final entanglement count for this qubit
      const finalEntanglementCount = qubitEntanglementCount[qubitId] || 0;
      const strokeWidth = getStrokeWidth(finalEntanglementCount);
      
      edges.push({
        id: `edge-${edgeCounter++}`,
        source: lastNodeId,
        target: measurementId,
        sourceHandle,
        targetHandle: 'top-target',
        label: `q${qubitId}`,
        markerEnd: { type: 'arrowclosed', color },
        style: { stroke: color, strokeWidth: strokeWidth }
      });
    }
  });
  
  return { nodes, edges };
}

export default function Circuit2() {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [circuitData, setCircuitData] = useState(null);
  const [error, setError] = useState(null);

  // Handle file upload
  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = JSON.parse(e.target.result);
        setCircuitData(data);
        const { nodes: parsedNodes, edges: parsedEdges } = parseCircuitData(data);
        setNodes(parsedNodes);
        setEdges(parsedEdges);
        setError(null);
      } catch (err) {
        setError('Invalid JSON file: ' + err.message);
        console.error('Error parsing JSON:', err);
      }
    };
    reader.readAsText(file);
  };

  const onNodesChange = useCallback(
    (changes) => setNodes((nodesSnapshot) => applyNodeChanges(changes, nodesSnapshot)),
    []
  );

  const onEdgesChange = useCallback(
    (changes) => setEdges((edgesSnapshot) => applyEdgeChanges(changes, edgesSnapshot)),
    []
  );

  const onConnect = useCallback(
    (params) => {
      const newEdge = {
        ...params,
        markerEnd: { type: 'arrowclosed', color: '#1a192b' },
        style: { stroke: '#1a192b', strokeWidth: 2 }
      };
      setEdges((edgesSnapshot) => addEdge(newEdge, edgesSnapshot));
    },
    []
  );

  return (
    <div style={{ width: '100vw', height: '100vh', position: 'relative' }}>
      {/* File upload button */}
      <div style={{
        position: 'absolute',
        top: '10px',
        left: '10px',
        zIndex: 1000,
        background: '#fff',
        padding: '10px',
        borderRadius: '5px',
        boxShadow: '0 2px 5px rgba(0,0,0,0.2)'
      }}>
        <div style={{ 
          display: 'block', 
          marginBottom: '10px', 
          fontSize: '14px',
          color: '#333'
        }}>
          Upload your QASM file here to visualize the circuit
        </div>
        <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
          Load Circuit JSON:
        </label>
        <input
          type="file"
          accept=".json"
          onChange={handleFileUpload}
          style={{ fontSize: '12px' }}
        />
        {error && (
          <div style={{ color: 'red', fontSize: '12px', marginTop: '5px' }}>
            {error}
          </div>
        )}
      </div>
      
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
      />
    </div>
  );
}
