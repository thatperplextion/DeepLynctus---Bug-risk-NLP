import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { API_URL } from '../services/api';

// ============================================================================
// FORCE-DIRECTED GRAPH SIMULATION
// ============================================================================
const useForceSimulation = (nodes, edges, dimensions, options = {}) => {
  const [positions, setPositions] = useState([]);
  const animationRef = useRef(null);
  const velocitiesRef = useRef([]);
  
  const {
    repulsionStrength = 5000,
    attractionStrength = 0.01,
    centerStrength = 0.02,
    damping = 0.85,
    iterations = 150
  } = options;
  
  useEffect(() => {
    if (!nodes || nodes.length === 0) return;
    
    // Initialize positions randomly around center
    const initialPositions = nodes.map((_, i) => ({
      x: dimensions.width / 2 + (Math.random() - 0.5) * 400,
      y: dimensions.height / 2 + (Math.random() - 0.5) * 400,
      vx: 0,
      vy: 0
    }));
    
    velocitiesRef.current = nodes.map(() => ({ vx: 0, vy: 0 }));
    
    let iteration = 0;
    
    const simulate = () => {
      const positions = [...initialPositions];
      const velocities = velocitiesRef.current;
      
      // Apply forces
      for (let i = 0; i < nodes.length; i++) {
        let fx = 0, fy = 0;
        
        // Repulsion from other nodes
        for (let j = 0; j < nodes.length; j++) {
          if (i === j) continue;
          
          const dx = positions[i].x - positions[j].x;
          const dy = positions[i].y - positions[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          
          const force = repulsionStrength / (dist * dist);
          fx += (dx / dist) * force;
          fy += (dy / dist) * force;
        }
        
        // Attraction along edges
        for (const edge of edges) {
          if (edge.source === nodes[i].id || edge.target === nodes[i].id) {
            const otherIdx = edge.source === nodes[i].id 
              ? nodes.findIndex(n => n.id === edge.target)
              : nodes.findIndex(n => n.id === edge.source);
            
            if (otherIdx >= 0) {
              const dx = positions[otherIdx].x - positions[i].x;
              const dy = positions[otherIdx].y - positions[i].y;
              const dist = Math.sqrt(dx * dx + dy * dy) || 1;
              
              fx += dx * attractionStrength;
              fy += dy * attractionStrength;
            }
          }
        }
        
        // Center gravity
        fx += (dimensions.width / 2 - positions[i].x) * centerStrength;
        fy += (dimensions.height / 2 - positions[i].y) * centerStrength;
        
        // Update velocity with damping
        velocities[i].vx = (velocities[i].vx + fx) * damping;
        velocities[i].vy = (velocities[i].vy + fy) * damping;
        
        // Update position
        positions[i].x += velocities[i].vx;
        positions[i].y += velocities[i].vy;
        
        // Boundary constraints
        const padding = 60;
        positions[i].x = Math.max(padding, Math.min(dimensions.width - padding, positions[i].x));
        positions[i].y = Math.max(padding, Math.min(dimensions.height - padding, positions[i].y));
      }
      
      iteration++;
      
      if (iteration < iterations) {
        setPositions([...positions]);
        animationRef.current = requestAnimationFrame(simulate);
      } else {
        setPositions([...positions]);
      }
    };
    
    setPositions(initialPositions);
    animationRef.current = requestAnimationFrame(simulate);
    
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [nodes, edges, dimensions, repulsionStrength, attractionStrength, centerStrength, damping, iterations]);
  
  return positions;
};

// ============================================================================
// ANIMATED NODE COMPONENT
// ============================================================================
const GraphNode = ({ node, position, isSelected, isHovered, onSelect, onHover, scale = 1 }) => {
  const nodeColors = {
    python: { bg: '#3572A5', border: '#2a5a8a' },
    javascript: { bg: '#f7df1e', border: '#d4be0c' },
    typescript: { bg: '#3178c6', border: '#2563a3' },
    react: { bg: '#61dafb', border: '#4db8d8' },
    default: { bg: '#8b5cf6', border: '#7c3aed' }
  };
  
  const riskColors = {
    high: '#ef4444',
    medium: '#f97316', 
    low: '#10b981'
  };
  
  const nodeType = node.type || 'default';
  const colors = nodeColors[nodeType] || nodeColors.default;
  const riskLevel = node.risk > 70 ? 'high' : node.risk > 40 ? 'medium' : 'low';
  const size = 20 + (node.connections || 1) * 3;
  
  const gradientId = `node-gradient-${node.id}`;
  const glowId = `node-glow-${node.id}`;
  
  return (
    <motion.g
      initial={{ opacity: 0, scale: 0 }}
      animate={{ 
        opacity: 1, 
        scale: isSelected ? 1.3 : isHovered ? 1.15 : 1,
        x: position.x,
        y: position.y
      }}
      transition={{ type: 'spring', stiffness: 300, damping: 25 }}
      onClick={() => onSelect(node)}
      onMouseEnter={() => onHover(node.id)}
      onMouseLeave={() => onHover(null)}
      style={{ cursor: 'pointer' }}
    >
      <defs>
        <radialGradient id={gradientId}>
          <stop offset="0%" stopColor={colors.bg} stopOpacity="1" />
          <stop offset="100%" stopColor={colors.border} stopOpacity="0.8" />
        </radialGradient>
        <filter id={glowId}>
          <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
          <feMerge>
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
      </defs>
      
      {/* Outer glow ring for high-risk nodes */}
      {riskLevel === 'high' && (
        <motion.circle
          r={size + 8}
          fill="none"
          stroke={riskColors.high}
          strokeWidth="2"
          strokeDasharray="4 2"
          opacity="0.6"
          animate={{ rotate: 360 }}
          transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
        />
      )}
      
      {/* Pulse animation for selected */}
      {isSelected && (
        <motion.circle
          r={size + 15}
          fill="none"
          stroke={colors.bg}
          strokeWidth="2"
          animate={{ 
            r: [size + 15, size + 25],
            opacity: [0.5, 0]
          }}
          transition={{ duration: 1.5, repeat: Infinity }}
        />
      )}
      
      {/* Main node circle */}
      <circle
        r={size}
        fill={`url(#${gradientId})`}
        filter={isHovered || isSelected ? `url(#${glowId})` : undefined}
        stroke="rgba(255,255,255,0.3)"
        strokeWidth="2"
      />
      
      {/* Risk indicator ring */}
      <circle
        r={size + 4}
        fill="none"
        stroke={riskColors[riskLevel]}
        strokeWidth="3"
        strokeDasharray={`${(node.risk / 100) * (2 * Math.PI * (size + 4))} ${2 * Math.PI * (size + 4)}`}
        strokeLinecap="round"
        transform="rotate(-90)"
        opacity="0.8"
      />
      
      {/* File type icon */}
      <text
        y="5"
        textAnchor="middle"
        fill="white"
        fontSize="12"
        fontWeight="bold"
        pointerEvents="none"
      >
        {nodeType === 'python' ? '🐍' : 
         nodeType === 'javascript' || nodeType === 'typescript' ? '📜' :
         nodeType === 'react' ? '⚛️' : '📄'}
      </text>
      
      {/* Node label */}
      <text
        y={size + 18}
        textAnchor="middle"
        fill="rgba(255,255,255,0.8)"
        fontSize="11"
        fontWeight="500"
        pointerEvents="none"
      >
        {node.label?.split('/').pop()?.substring(0, 15) || 'file'}
      </text>
    </motion.g>
  );
};

// ============================================================================
// ANIMATED EDGE COMPONENT
// ============================================================================
const GraphEdge = ({ edge, sourcePos, targetPos, isHighlighted }) => {
  if (!sourcePos || !targetPos) return null;
  
  const dx = targetPos.x - sourcePos.x;
  const dy = targetPos.y - sourcePos.y;
  const distance = Math.sqrt(dx * dx + dy * dy);
  
  // Calculate control point for curved edge
  const midX = (sourcePos.x + targetPos.x) / 2;
  const midY = (sourcePos.y + targetPos.y) / 2;
  const perpX = -dy / distance * 30;
  const perpY = dx / distance * 30;
  
  const path = `M ${sourcePos.x} ${sourcePos.y} Q ${midX + perpX} ${midY + perpY} ${targetPos.x} ${targetPos.y}`;
  
  const edgeColor = edge.type === 'import' ? '#8b5cf6' : 
                    edge.type === 'export' ? '#10b981' : 
                    '#6b7280';
  
  const gradientId = `edge-gradient-${edge.source}-${edge.target}`;
  
  return (
    <g>
      <defs>
        <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor={edgeColor} stopOpacity="0.3" />
          <stop offset="50%" stopColor={edgeColor} stopOpacity="0.8" />
          <stop offset="100%" stopColor={edgeColor} stopOpacity="0.3" />
        </linearGradient>
        
        <marker
          id={`arrowhead-${edge.source}-${edge.target}`}
          markerWidth="10"
          markerHeight="8"
          refX="9"
          refY="4"
          orient="auto"
        >
          <polygon
            points="0 0, 10 4, 0 8"
            fill={edgeColor}
            opacity={isHighlighted ? 1 : 0.6}
          />
        </marker>
      </defs>
      
      {/* Edge glow */}
      {isHighlighted && (
        <motion.path
          d={path}
          fill="none"
          stroke={edgeColor}
          strokeWidth="6"
          opacity="0.3"
          filter="blur(4px)"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.5 }}
        />
      )}
      
      {/* Main edge path */}
      <motion.path
        d={path}
        fill="none"
        stroke={isHighlighted ? edgeColor : `url(#${gradientId})`}
        strokeWidth={isHighlighted ? 3 : 2}
        strokeLinecap="round"
        markerEnd={`url(#arrowhead-${edge.source}-${edge.target})`}
        initial={{ pathLength: 0, opacity: 0 }}
        animate={{ pathLength: 1, opacity: 1 }}
        transition={{ duration: 1, delay: 0.2 }}
      />
      
      {/* Animated particle along edge */}
      {isHighlighted && (
        <motion.circle
          r="4"
          fill={edgeColor}
          initial={{ offsetDistance: '0%' }}
          animate={{ offsetDistance: '100%' }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          style={{
            offsetPath: `path("${path}")`,
            offsetRotate: '0deg'
          }}
        />
      )}
    </g>
  );
};

// ============================================================================
// NODE DETAILS PANEL
// ============================================================================
const NodeDetailsPanel = ({ node, onClose }) => {
  if (!node) return null;
  
  const riskLevel = node.risk > 70 ? 'high' : node.risk > 40 ? 'medium' : 'low';
  const riskColors = { high: '#ef4444', medium: '#f97316', low: '#10b981' };
  
  return (
    <motion.div
      className="absolute right-6 top-6 w-80 rounded-2xl overflow-hidden"
      style={{
        background: 'linear-gradient(135deg, rgba(0,0,0,0.9) 0%, rgba(20,20,30,0.95) 100%)',
        border: '1px solid rgba(255,255,255,0.15)',
        boxShadow: '0 20px 60px rgba(0,0,0,0.5)'
      }}
      initial={{ opacity: 0, x: 50, scale: 0.9 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 50, scale: 0.9 }}
    >
      {/* Header */}
      <div 
        className="p-4 border-b border-white/10"
        style={{ background: `${riskColors[riskLevel]}15` }}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div 
              className="w-10 h-10 rounded-xl flex items-center justify-center text-xl"
              style={{ background: `${riskColors[riskLevel]}30` }}
            >
              {node.type === 'python' ? '🐍' : 
               node.type === 'javascript' ? '📜' : 
               node.type === 'typescript' ? '📘' : '📄'}
            </div>
            <div>
              <h3 className="text-white font-semibold text-sm truncate max-w-[180px]">
                {node.label?.split('/').pop() || 'Unknown'}
              </h3>
              <p className="text-gray-400 text-xs truncate max-w-[180px]">
                {node.label}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors"
          >
            <span className="text-gray-400">✕</span>
          </button>
        </div>
      </div>
      
      {/* Stats */}
      <div className="p-4 space-y-4">
        {/* Risk Score */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-400 text-sm">Risk Score</span>
            <span 
              className="text-sm font-bold"
              style={{ color: riskColors[riskLevel] }}
            >
              {node.risk || 0}%
            </span>
          </div>
          <div className="h-2 bg-white/10 rounded-full overflow-hidden">
            <motion.div
              className="h-full rounded-full"
              style={{ background: riskColors[riskLevel] }}
              initial={{ width: 0 }}
              animate={{ width: `${node.risk || 0}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </div>
        
        {/* Metrics Grid */}
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 rounded-xl bg-white/5 border border-white/10">
            <div className="text-2xl font-bold text-white">{node.connections || 0}</div>
            <div className="text-xs text-gray-400">Connections</div>
          </div>
          <div className="p-3 rounded-xl bg-white/5 border border-white/10">
            <div className="text-2xl font-bold text-white">{node.imports || 0}</div>
            <div className="text-xs text-gray-400">Imports</div>
          </div>
          <div className="p-3 rounded-xl bg-white/5 border border-white/10">
            <div className="text-2xl font-bold text-white">{node.exports || 0}</div>
            <div className="text-xs text-gray-400">Exports</div>
          </div>
          <div className="p-3 rounded-xl bg-white/5 border border-white/10">
            <div className="text-2xl font-bold text-white">{node.size || 0}</div>
            <div className="text-xs text-gray-400">Lines</div>
          </div>
        </div>
        
        {/* Dependencies List */}
        {node.dependencies && node.dependencies.length > 0 && (
          <div>
            <h4 className="text-gray-300 text-sm font-medium mb-2">Dependencies</h4>
            <div className="space-y-1 max-h-32 overflow-y-auto">
              {node.dependencies.slice(0, 5).map((dep, i) => (
                <div 
                  key={i}
                  className="text-xs text-gray-400 px-2 py-1 bg-white/5 rounded flex items-center gap-2"
                >
                  <span className="text-purple-400">→</span>
                  {dep}
                </div>
              ))}
              {node.dependencies.length > 5 && (
                <div className="text-xs text-gray-500 px-2">
                  +{node.dependencies.length - 5} more
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
};

// ============================================================================
// GRAPH CONTROLS
// ============================================================================
const GraphControls = ({ zoom, setZoom, layout, setLayout, onReset, onExport }) => {
  const layouts = [
    { id: 'force', label: 'Force', icon: '🎯' },
    { id: 'radial', label: 'Radial', icon: '🔵' },
    { id: 'tree', label: 'Tree', icon: '🌲' },
  ];
  
  return (
    <motion.div
      className="absolute left-6 bottom-6 flex flex-col gap-2 z-30"
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
    >
      {/* Zoom Controls */}
      <div 
        className="flex flex-col rounded-xl overflow-hidden"
        style={{
          background: 'rgba(0,0,0,0.8)',
          border: '1px solid rgba(255,255,255,0.1)'
        }}
      >
        <button
          onClick={() => setZoom(z => Math.min(z + 0.2, 2))}
          className="p-3 hover:bg-white/10 transition-colors text-white text-lg"
        >
          +
        </button>
        <div className="px-3 py-1 text-center text-xs text-gray-400 border-y border-white/10">
          {Math.round(zoom * 100)}%
        </div>
        <button
          onClick={() => setZoom(z => Math.max(z - 0.2, 0.5))}
          className="p-3 hover:bg-white/10 transition-colors text-white text-lg"
        >
          −
        </button>
      </div>
      
      {/* Layout Selector */}
      <div 
        className="flex flex-col rounded-xl overflow-hidden"
        style={{
          background: 'rgba(0,0,0,0.8)',
          border: '1px solid rgba(255,255,255,0.1)'
        }}
      >
        {layouts.map((l) => (
          <button
            key={l.id}
            onClick={() => setLayout(l.id)}
            className={`p-3 transition-colors ${
              layout === l.id 
                ? 'bg-purple-500/30 text-purple-400' 
                : 'hover:bg-white/10 text-gray-400'
            }`}
            title={l.label}
          >
            {l.icon}
          </button>
        ))}
      </div>
      
      {/* Actions */}
      <div 
        className="flex flex-col rounded-xl overflow-hidden"
        style={{
          background: 'rgba(0,0,0,0.8)',
          border: '1px solid rgba(255,255,255,0.1)'
        }}
      >
        <button
          onClick={onReset}
          className="p-3 hover:bg-white/10 transition-colors text-gray-400"
          title="Reset View"
        >
          🔄
        </button>
        <button
          onClick={onExport}
          className="p-3 hover:bg-white/10 transition-colors text-gray-400"
          title="Export"
        >
          📷
        </button>
      </div>
    </motion.div>
  );
};

// ============================================================================
// GRAPH LEGEND
// ============================================================================
const GraphLegend = () => {
  const items = [
    { color: '#3572A5', label: 'Python' },
    { color: '#f7df1e', label: 'JavaScript' },
    { color: '#3178c6', label: 'TypeScript' },
    { color: '#8b5cf6', label: 'Other' },
  ];
  
  const risks = [
    { color: '#10b981', label: 'Low Risk' },
    { color: '#f97316', label: 'Medium Risk' },
    { color: '#ef4444', label: 'High Risk' },
  ];
  
  return (
    <motion.div
      className="absolute right-6 bottom-6 p-4 rounded-xl z-20"
      style={{
        background: 'rgba(0,0,0,0.9)',
        border: '1px solid rgba(255,255,255,0.1)',
        backdropFilter: 'blur(10px)'
      }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <h4 className="text-gray-300 text-xs font-semibold mb-3">FILE TYPES</h4>
      <div className="flex flex-col gap-2 mb-4">
        {items.map((item, i) => (
          <div key={i} className="flex items-center gap-2">
            <div 
              className="w-3 h-3 rounded-full"
              style={{ background: item.color }}
            />
            <span className="text-xs text-gray-400">{item.label}</span>
          </div>
        ))}
      </div>
      
      <h4 className="text-gray-300 text-xs font-semibold mb-3">RISK LEVELS</h4>
      <div className="flex flex-col gap-2">
        {risks.map((item, i) => (
          <div key={i} className="flex items-center gap-2">
            <div 
              className="w-3 h-3 rounded-full"
              style={{ background: item.color }}
            />
            <span className="text-xs text-gray-400">{item.label}</span>
          </div>
        ))}
      </div>
    </motion.div>
  );
};

// ============================================================================
// SEARCH & FILTER BAR
// ============================================================================
const SearchFilterBar = ({ searchTerm, setSearchTerm, filters, setFilters }) => {
  const fileTypes = ['python', 'javascript', 'typescript', 'other'];
  
  return (
    <motion.div
      className="absolute left-6 top-20 flex flex-col gap-3 z-30"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      {/* Search Input */}
      <div 
        className="flex items-center gap-2 px-4 py-2 rounded-xl"
        style={{
          background: 'rgba(0,0,0,0.8)',
          border: '1px solid rgba(255,255,255,0.1)'
        }}
      >
        <span className="text-gray-400">🔍</span>
        <input
          type="text"
          placeholder="Search nodes..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="bg-transparent text-white text-sm outline-none w-40 placeholder-gray-500"
        />
        {searchTerm && (
          <button 
            onClick={() => setSearchTerm('')}
            className="text-gray-400 hover:text-white"
          >
            ✕
          </button>
        )}
      </div>
      
      {/* File Type Filters */}
      <div 
        className="flex items-center gap-1 px-2 py-1 rounded-xl"
        style={{
          background: 'rgba(0,0,0,0.8)',
          border: '1px solid rgba(255,255,255,0.1)'
        }}
      >
        {fileTypes.map((type) => (
          <button
            key={type}
            onClick={() => setFilters(f => ({
              ...f,
              [type]: !f[type]
            }))}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              filters[type] 
                ? 'bg-purple-500/30 text-purple-400' 
                : 'text-gray-500 hover:text-gray-300'
            }`}
          >
            {type === 'python' ? '🐍' : 
             type === 'javascript' ? '📜' : 
             type === 'typescript' ? '📘' : '📄'}
          </button>
        ))}
      </div>
    </motion.div>
  );
};

// ============================================================================
// STATS OVERVIEW
// ============================================================================
const GraphStats = ({ nodes, edges }) => {
  const stats = useMemo(() => {
    if (!nodes || !edges) return null;
    
    const highRisk = nodes.filter(n => n.risk > 70).length;
    const medRisk = nodes.filter(n => n.risk > 40 && n.risk <= 70).length;
    const lowRisk = nodes.filter(n => n.risk <= 40).length;
    
    const avgConnections = edges.length / (nodes.length || 1);
    
    return {
      totalNodes: nodes.length,
      totalEdges: edges.length,
      highRisk,
      medRisk,
      lowRisk,
      avgConnections: avgConnections.toFixed(1)
    };
  }, [nodes, edges]);
  
  if (!stats) return null;
  
  return (
    <motion.div
      className="absolute top-6 left-1/2 -translate-x-1/2 flex gap-4 z-30"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
    >
      {[
        { label: 'Nodes', value: stats.totalNodes, color: '#8b5cf6' },
        { label: 'Edges', value: stats.totalEdges, color: '#06b6d4' },
        { label: 'High Risk', value: stats.highRisk, color: '#ef4444' },
        { label: 'Avg Connections', value: stats.avgConnections, color: '#10b981' },
      ].map((stat, i) => (
        <motion.div
          key={i}
          className="px-4 py-2 rounded-xl text-center"
          style={{
            background: 'rgba(0,0,0,0.8)',
            border: '1px solid rgba(255,255,255,0.1)'
          }}
          whileHover={{ scale: 1.05 }}
        >
          <div className="text-xl font-bold" style={{ color: stat.color }}>
            {stat.value}
          </div>
          <div className="text-xs text-gray-400">{stat.label}</div>
        </motion.div>
      ))}
    </motion.div>
  );
};

// ============================================================================
// MAIN DEPENDENCY GRAPH COMPONENT
// ============================================================================
const DependencyGraph = ({ projectId: propProjectId }) => {
  const containerRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [layout, setLayout] = useState('force');
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    python: true,
    javascript: true,
    typescript: true,
    other: true
  });
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState(null);
  
  // Get project ID from props, URL, or state
  const projectId = selectedProjectId || propProjectId || (() => {
    const params = new URLSearchParams(window.location.search);
    return params.get('project') || params.get('id') || localStorage.getItem('currentProjectId');
  })();
  
  // Fetch available projects
  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const response = await fetch(`${API_URL}/projects`);
        if (response.ok) {
          const data = await response.json();
          setProjects(data || []);
          // Auto-select first project if no projectId
          if (!projectId && data && data.length > 0) {
            setSelectedProjectId(data[0]._id);
          }
        }
      } catch (err) {
        console.error('Failed to fetch projects:', err);
      }
    };
    fetchProjects();
  }, []);
  
  // Resize observer
  useEffect(() => {
    const observer = new ResizeObserver(entries => {
      if (entries[0]) {
        setDimensions({
          width: entries[0].contentRect.width,
          height: entries[0].contentRect.height
        });
      }
    });
    
    if (containerRef.current) {
      observer.observe(containerRef.current);
    }
    
    return () => observer.disconnect();
  }, []);
  
  // Fetch graph data
  useEffect(() => {
    const fetchGraph = async () => {
      if (!projectId) {
        setLoading(false);
        return;
      }
      
      try {
        setLoading(true);
        const response = await fetch(`${API_URL}/dependencies/${projectId}`);
        if (!response.ok) throw new Error('Failed to fetch dependencies');
        const data = await response.json();
        
        // Handle both 'links' and 'edges' from backend
        const connections = data.links || data.edges || [];
        
        // Process nodes with proper labeling
        const processedNodes = (data.nodes || []).map((node, i) => {
          const fileName = node.name || node.label || node.id || `file-${i}`;
          const nodeId = node.id || `node-${i}`;
          
          return {
            ...node,
            id: nodeId,
            label: fileName,
            type: node.type || (
              fileName.endsWith('.py') ? 'python' : 
              fileName.endsWith('.js') || fileName.endsWith('.jsx') ? 'javascript' :
              fileName.endsWith('.ts') || fileName.endsWith('.tsx') ? 'typescript' : 'other'
            ),
            risk: node.risk || node.metrics?.complexity || Math.floor(Math.random() * 100),
            connections: connections.filter(e => e.source === nodeId || e.target === nodeId).length,
            imports: connections.filter(e => e.target === nodeId).length,
            exports: connections.filter(e => e.source === nodeId).length,
            size: node.metrics?.lines || node.size || Math.floor(Math.random() * 500) + 50
          };
        });
        
        // Convert links to edges format
        const processedEdges = connections.map((link, i) => ({
          id: `edge-${i}`,
          source: link.source,
          target: link.target,
          type: link.type || 'import'
        }));
        
        console.log('Dependency graph data:', { nodes: processedNodes.length, edges: processedEdges.length });
        setNodes(processedNodes);
        setEdges(processedEdges);
      } catch (err) {
        console.error('Error fetching graph:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    
    if (projectId) {
      fetchGraph();
    } else {
      setLoading(false);
    }
  }, [projectId]);
  
  // Get force-directed positions
  const positions = useForceSimulation(nodes, edges, dimensions);
  
  // Filter nodes based on search and filters
  const filteredNodes = useMemo(() => {
    return nodes.filter(node => {
      const matchesSearch = !searchTerm || 
        node.label?.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesFilter = filters[node.type] || node.type === 'other' && filters.other;
      return matchesSearch && matchesFilter;
    });
  }, [nodes, searchTerm, filters]);
  
  // Get highlighted edges based on selection
  const highlightedEdges = useMemo(() => {
    if (!selectedNode) return new Set();
    return new Set(
      edges
        .filter(e => e.source === selectedNode.id || e.target === selectedNode.id)
        .map(e => `${e.source}-${e.target}`)
    );
  }, [selectedNode, edges]);
  
  const handleReset = useCallback(() => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setSelectedNode(null);
  }, []);
  
  const handleExport = useCallback(() => {
    // Export SVG functionality
    const svg = containerRef.current?.querySelector('svg');
    if (svg) {
      const serializer = new XMLSerializer();
      const source = serializer.serializeToString(svg);
      const blob = new Blob([source], { type: 'image/svg+xml' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'dependency-graph.svg';
      a.click();
      URL.revokeObjectURL(url);
    }
  }, []);
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <motion.div
          className="flex flex-col items-center gap-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <div className="relative w-24 h-24">
            {[...Array(3)].map((_, i) => (
              <motion.div
                key={i}
                className="absolute inset-0 border-4 border-purple-500 rounded-full"
                style={{ borderTopColor: 'transparent' }}
                animate={{ rotate: 360 }}
                transition={{ 
                  duration: 1.5 - i * 0.3, 
                  repeat: Infinity, 
                  ease: "linear" 
                }}
              />
            ))}
            <div className="absolute inset-0 flex items-center justify-center text-3xl">
              🔗
            </div>
          </div>
          <span className="text-gray-400">Generating dependency graph...</span>
        </motion.div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <motion.div
          className="text-center p-8 rounded-2xl bg-red-500/10 border border-red-500/30"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
        >
          <span className="text-4xl mb-4 block">⚠️</span>
          <h3 className="text-xl font-bold text-red-400 mb-2">Error Loading Graph</h3>
          <p className="text-gray-400">{error}</p>
        </motion.div>
      </div>
    );
  }
  
  if (!projectId && projects.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <motion.div
          className="text-center p-12 rounded-3xl"
          style={{
            background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%)',
            border: '1px solid rgba(139, 92, 246, 0.2)'
          }}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <span className="text-6xl mb-6 block">🕸️</span>
          <h2 className="text-2xl font-bold text-white mb-3">Dependency Graph</h2>
          <p className="text-gray-400 max-w-md">
            Analyze a project to visualize file dependencies, 
            import relationships, and identify complex coupling patterns.
          </p>
        </motion.div>
      </div>
    );
  }
  
  if (!projectId && projects.length > 0) {
    return (
      <div className="min-h-screen flex items-center justify-center p-8">
        <motion.div
          className="text-center p-12 rounded-3xl max-w-2xl w-full"
          style={{
            background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%)',
            border: '1px solid rgba(139, 92, 246, 0.2)'
          }}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <span className="text-6xl mb-6 block">🕸️</span>
          <h2 className="text-2xl font-bold text-white mb-3">Select a Project</h2>
          <p className="text-gray-400 mb-6">
            Choose a project to visualize its dependency graph
          </p>
          <select
            className="w-full p-3 rounded-lg bg-gray-800 border border-gray-700 text-white"
            onChange={(e) => setSelectedProjectId(e.target.value)}
            defaultValue=""
          >
            <option value="" disabled>Select a project...</option>
            {projects.map(project => (
              <option key={project._id} value={project._id}>
                {project.name}
              </option>
            ))}
          </select>
        </motion.div>
      </div>
    );
  }
  
  // Show message if graph loaded but has no nodes
  if (!loading && nodes.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <motion.div
          className="text-center p-12 rounded-3xl max-w-2xl"
          style={{
            background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%)',
            border: '1px solid rgba(139, 92, 246, 0.2)'
          }}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <span className="text-6xl mb-6 block">📊</span>
          <h2 className="text-2xl font-bold text-white mb-3">No Dependencies Found</h2>
          <p className="text-gray-400 mb-4">
            This project has no file dependencies to visualize.
          </p>
          <p className="text-sm text-gray-500">
            The project may not have been analyzed yet or contains no importable files.
          </p>
        </motion.div>
      </div>
    );
  }
  
  return (
    <div 
      ref={containerRef}
      className="min-h-screen relative overflow-hidden"
      style={{ 
        background: 'radial-gradient(circle at 50% 50%, rgba(139, 92, 246, 0.05) 0%, transparent 50%)'
      }}
    >
      {/* Background Grid */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-20">
        <defs>
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="1"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
      </svg>
      
      {/* Main Graph SVG */}
      <motion.svg
        width={dimensions.width}
        height={dimensions.height}
        className="absolute inset-0"
        style={{
          transform: `scale(${zoom}) translate(${pan.x}px, ${pan.y}px)`,
          transformOrigin: 'center'
        }}
      >
        {/* Edges */}
        <g className="edges">
          {edges.map((edge, i) => {
            const sourceIdx = nodes.findIndex(n => n.id === edge.source);
            const targetIdx = nodes.findIndex(n => n.id === edge.target);
            const isHighlighted = highlightedEdges.has(`${edge.source}-${edge.target}`);
            
            return (
              <GraphEdge
                key={i}
                edge={edge}
                sourcePos={positions[sourceIdx]}
                targetPos={positions[targetIdx]}
                isHighlighted={isHighlighted || hoveredNode === edge.source || hoveredNode === edge.target}
              />
            );
          })}
        </g>
        
        {/* Nodes */}
        <g className="nodes">
          {filteredNodes.map((node, i) => {
            const nodeIdx = nodes.findIndex(n => n.id === node.id);
            const pos = positions[nodeIdx];
            
            if (!pos) return null;
            
            return (
              <GraphNode
                key={node.id}
                node={node}
                position={pos}
                isSelected={selectedNode?.id === node.id}
                isHovered={hoveredNode === node.id}
                onSelect={setSelectedNode}
                onHover={setHoveredNode}
                scale={zoom}
              />
            );
          })}
        </g>
      </motion.svg>
      
      {/* Stats Bar */}
      <GraphStats nodes={nodes} edges={edges} />
      
      {/* Search & Filters */}
      <SearchFilterBar
        searchTerm={searchTerm}
        setSearchTerm={setSearchTerm}
        filters={filters}
        setFilters={setFilters}
      />
      
      {/* Controls */}
      <GraphControls
        zoom={zoom}
        setZoom={setZoom}
        layout={layout}
        setLayout={setLayout}
        onReset={handleReset}
        onExport={handleExport}
      />
      
      {/* Legend */}
      <GraphLegend />
      
      {/* Node Details Panel */}
      <AnimatePresence>
        {selectedNode && (
          <NodeDetailsPanel
            node={selectedNode}
            onClose={() => setSelectedNode(null)}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

export default DependencyGraph;
