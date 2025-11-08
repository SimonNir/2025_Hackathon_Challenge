import { useState, useCallback, useEffect } from 'react';
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

const initialNodes = [
  // Top level: q0, q1, q2
  { id: 'q0', type: 'circle', position: { x: 0, y: 0 }, data: { label: 'q0' } },
  { id: 'q1', type: 'circle', position: { x: 150, y: 0 }, data: { label: 'q1' } },
  { id: 'q2', type: 'circle', position: { x: 300, y: 0 }, data: { label: 'q2' } },
  // Nodes flowing downwards
  { id: 'h1', type: 'custom', position: { x: 0, y: 150 }, data: { label: 'H' } },
  // Group containing cx1, u31, cx2, u32
  { 
    id: 'group1', 
    type: 'group', 
    position: { x: 0, y: 250 }, 
    style: { width: 200, height: 480 },
    data: { label: 'CRZ(pi/2)' }
  },
  { id: 'cx1', type: 'custom', position: { x: 10, y: 40 }, parentId: 'group1', extent: 'parent', data: { label: 'CX' } },
  { id: 'u31', type: 'custom', position: { x: 10, y: 140 }, parentId: 'group1', extent: 'parent', data: { label: 'U3' } },
  { id: 'cx2', type: 'custom', position: { x: 10, y: 240 }, parentId: 'group1', extent: 'parent', data: { label: 'CX' } },
  { id: 'u32', type: 'custom', position: { x: 10, y: 440 }, parentId: 'group1', extent: 'parent', data: { label: 'U3' } },
  { id: 'h2', type: 'custom', position: { x: 0, y: 700 }, data: { label: 'H' } },
  // Group containing cx3, u33, cx4, u34
  { 
    id: 'group2', 
    type: 'group', 
    position: { x: 0, y: 750 }, 
    style: { width: 200, height: 380 },
    data: { label: 'CRZ(pi/4)' }
  },
  { id: 'cx3', type: 'custom', position: { x: 10, y: 40 }, parentId: 'group2', extent: 'parent', data: { label: 'CX' } },
  { id: 'u33', type: 'custom', position: { x: 10, y: 140 }, parentId: 'group2', extent: 'parent', data: { label: 'U3' } },
  { id: 'cx4', type: 'custom', position: { x: 10, y: 240 }, parentId: 'group2', extent: 'parent', data: { label: 'CX' } },
  { id: 'u34', type: 'custom', position: { x: 10, y: 340 }, parentId: 'group2', extent: 'parent', data: { label: 'U3' } },
  // Group containing cx5, u35, cx6, u36
  { 
    id: 'group3', 
    type: 'group', 
    position: { x: 0, y: 1150 }, 
    style: { width: 200, height: 480 },
    data: { label: 'CRZ(pi/2)' }
  },
  { id: 'cx5', type: 'custom', position: { x: 10, y: 40 }, parentId: 'group3', extent: 'parent', data: { label: 'CX' } },
  { id: 'u35', type: 'custom', position: { x: 10, y: 140 }, parentId: 'group3', extent: 'parent', data: { label: 'U3' } },
  { id: 'cx6', type: 'custom', position: { x: 10, y: 240 }, parentId: 'group3', extent: 'parent', data: { label: 'CX' } },
  { id: 'u36', type: 'custom', position: { x: 10, y: 440 }, parentId: 'group3', extent: 'parent', data: { label: 'U3' } },
  { id: 'h3', type: 'custom', position: { x: 0, y: 1630 }, data: { label: 'H' } },
];

const initialEdges = [
  // Directed edge chain from q2 through h1, cx1, u31, cx2, u32, cx3, u33, cx4, u34
  { 
    id: 'q2-h1', 
    source: 'q2', 
    sourceHandle: 'bottom-source',
    target: 'h1', 
    targetHandle: 'top-target-2',
    label: 'q2',
    markerEnd: { type: 'arrowclosed', color: '#2ecc71' },
    style: { stroke: '#2ecc71', strokeWidth: 2 }
  },
  { 
    id: 'h1-cx1', 
    source: 'h1', 
    sourceHandle: 'bottom-source-2',
    target: 'cx1', 
    targetHandle: 'top-target-2',
    label: 'q2',
    markerEnd: { type: 'arrowclosed', color: '#2ecc71' },
    style: { stroke: '#2ecc71', strokeWidth: 2 }
  },
  { 
    id: 'cx1-u31', 
    source: 'cx1', 
    sourceHandle: 'bottom-source-2',
    target: 'u31', 
    targetHandle: 'top-target-2',
    label: 'q2',
    markerEnd: { type: 'arrowclosed', color: '#2ecc71' },
    style: { stroke: '#2ecc71', strokeWidth: 2 }
  },
  { 
    id: 'u31-cx2', 
    source: 'u31', 
    sourceHandle: 'bottom-source-2',
    target: 'cx2', 
    targetHandle: 'top-target-2',
    label: 'q2',
    markerEnd: { type: 'arrowclosed', color: '#2ecc71' },
    style: { stroke: '#2ecc71', strokeWidth: 2 }
  },
  { 
    id: 'cx2-u32', 
    source: 'cx2', 
    sourceHandle: 'bottom-source-2',
    target: 'u32', 
    targetHandle: 'top-target-2',
    label: 'q2',
    markerEnd: { type: 'arrowclosed', color: '#2ecc71' },
    style: { stroke: '#2ecc71', strokeWidth: 2 }
  },
  { 
    id: 'u32-cx3', 
    source: 'u32', 
    sourceHandle: 'bottom-source-2',
    target: 'cx3', 
    targetHandle: 'top-target-2',
    label: 'q2',
    markerEnd: { type: 'arrowclosed', color: '#2ecc71' },
    style: { stroke: '#2ecc71', strokeWidth: 2 }
  },
  { 
    id: 'cx3-u33', 
    source: 'cx3', 
    sourceHandle: 'bottom-source-2',
    target: 'u33', 
    targetHandle: 'top-target-2',
    label: 'q2',
    markerEnd: { type: 'arrowclosed', color: '#2ecc71' },
    style: { stroke: '#2ecc71', strokeWidth: 2 }
  },
  { 
    id: 'u33-cx4', 
    source: 'u33', 
    sourceHandle: 'bottom-source-2',
    target: 'cx4', 
    targetHandle: 'top-target-2',
    label: 'q2',
    markerEnd: { type: 'arrowclosed', color: '#2ecc71' },
    style: { stroke: '#2ecc71', strokeWidth: 2 }
  },
  { 
    id: 'cx4-u34', 
    source: 'cx4', 
    sourceHandle: 'bottom-source-2',
    target: 'u34', 
    targetHandle: 'top-target-2',
    label: 'q2',
    markerEnd: { type: 'arrowclosed', color: '#2ecc71' },
    style: { stroke: '#2ecc71', strokeWidth: 2 }
  },
  // Directed edge chain from q1 through cx1, cx2, h2, cx5, u35, cx6, u36
  { 
    id: 'q1-cx1', 
    source: 'q1', 
    sourceHandle: 'bottom-source',
    target: 'cx1', 
    targetHandle: 'top-target-1',
    label: 'q1',
    markerEnd: { type: 'arrowclosed', color: '#3a86ff' },
    style: { stroke: '#3a86ff', strokeWidth: 2 }
  },
  { 
    id: 'cx1-cx2', 
    source: 'cx1', 
    sourceHandle: 'bottom-source-1',
    target: 'cx2', 
    targetHandle: 'top-target-1',
    label: 'q1',
    markerEnd: { type: 'arrowclosed', color: '#3a86ff' },
    style: { stroke: '#3a86ff', strokeWidth: 2 }
  },
  { 
    id: 'cx2-h2', 
    source: 'cx2', 
    sourceHandle: 'bottom-source-1',
    target: 'h2', 
    targetHandle: 'top-target-2',
    label: 'q1',
    markerEnd: { type: 'arrowclosed', color: '#3a86ff' },
    style: { stroke: '#3a86ff', strokeWidth: 2 }
  },
  { 
    id: 'h2-cx5', 
    source: 'h2', 
    sourceHandle: 'bottom-source-2',
    target: 'cx5', 
    targetHandle: 'top-target-2',
    label: 'q1',
    markerEnd: { type: 'arrowclosed', color: '#3a86ff' },
    style: { stroke: '#3a86ff', strokeWidth: 2 }
  },
  { 
    id: 'cx5-u35', 
    source: 'cx5', 
    sourceHandle: 'bottom-source-2',
    target: 'u35', 
    targetHandle: 'top-target-2',
    label: 'q1',
    markerEnd: { type: 'arrowclosed', color: '#3a86ff' },
    style: { stroke: '#3a86ff', strokeWidth: 2 }
  },
  { 
    id: 'u35-cx6', 
    source: 'u35', 
    sourceHandle: 'bottom-source-2',
    target: 'cx6', 
    targetHandle: 'top-target-2',
    label: 'q1',
    markerEnd: { type: 'arrowclosed', color: '#3a86ff' },
    style: { stroke: '#3a86ff', strokeWidth: 2 }
  },
  { 
    id: 'cx6-u36', 
    source: 'cx6', 
    sourceHandle: 'bottom-source-2',
    target: 'u36', 
    targetHandle: 'top-target-2',
    label: 'q1',
    markerEnd: { type: 'arrowclosed', color: '#3a86ff' },
    style: { stroke: '#3a86ff', strokeWidth: 2 }
  },
  // Directed edge chain from q0 through cx3, cx4, cx5, cx6, h3
  { 
    id: 'q0-cx3', 
    source: 'q0', 
    sourceHandle: 'bottom-source',
    target: 'cx3', 
    targetHandle: 'top-target-1',
    label: 'q0',
    markerEnd: { type: 'arrowclosed', color: '#ffa500' },
    style: { stroke: '#ffa500', strokeWidth: 2 }
  },
  { 
    id: 'cx3-cx4', 
    source: 'cx3', 
    sourceHandle: 'bottom-source-1',
    target: 'cx4', 
    targetHandle: 'top-target-1',
    label: 'q0',
    markerEnd: { type: 'arrowclosed', color: '#ffa500' },
    style: { stroke: '#ffa500', strokeWidth: 2 }
  },
  { 
    id: 'cx4-cx5', 
    source: 'cx4', 
    sourceHandle: 'bottom-source-1',
    target: 'cx5', 
    targetHandle: 'top-target-1',
    label: 'q0',
    markerEnd: { type: 'arrowclosed', color: '#ffa500' },
    style: { stroke: '#ffa500', strokeWidth: 2 }
  },
  { 
    id: 'cx5-cx6', 
    source: 'cx5', 
    sourceHandle: 'bottom-source-1',
    target: 'cx6', 
    targetHandle: 'top-target-1',
    label: 'q0',
    markerEnd: { type: 'arrowclosed', color: '#ffa500' },
    style: { stroke: '#ffa500', strokeWidth: 2 }
  },
  { 
    id: 'cx6-h3', 
    source: 'cx6', 
    sourceHandle: 'bottom-source-1',
    target: 'h3', 
    targetHandle: 'top-target-2',
    label: 'q0',
    markerEnd: { type: 'arrowclosed', color: '#ffa500' },
    style: { stroke: '#ffa500', strokeWidth: 2 }
  }
];

export default function App() {
  const [nodes, setNodes] = useState(initialNodes);
  const [edges, setEdges] = useState(initialEdges);

  // Sync state with initialNodes/initialEdges when they change (for development)
  // Create a string representation that changes when nodes/edges change
  const nodesKey = JSON.stringify(initialNodes.map(n => n.id).sort());
  const edgesKey = JSON.stringify(initialEdges.map(e => e.id).sort());
  
  useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [nodesKey, edgesKey]);

  // Debug: Log nodes to console (you can remove this later)
  console.log('Current nodes:', nodes);
  console.log('Number of nodes:', nodes.length);

  const onNodesChange = useCallback(
    (changes) => setNodes((nodesSnapshot) => applyNodeChanges(changes, nodesSnapshot)),
    [],
  );
  const onEdgesChange = useCallback(
    (changes) => setEdges((edgesSnapshot) => applyEdgeChanges(changes, edgesSnapshot)),
    [],
  );
  const onConnect = useCallback(
    (params) => setEdges((edgesSnapshot) => addEdge({ 
      ...params, 
      markerEnd: { type: 'arrowclosed', color: '#06ffa5' },
      style: { stroke: '#06ffa5', strokeWidth: 2 }
    }, edgesSnapshot)),
    [],
  );

  return (
    <div style={{ width: '100vw', height: '100vh' }}>
      <ReactFlow
        key={nodesKey}
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        fitView
      />
    </div>
  );
}
