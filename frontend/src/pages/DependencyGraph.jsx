import React, { useState, useEffect, useRef, useCallback } from 'react'
import { motion } from 'framer-motion'
import { GlassCard, Loader } from '../components/ui'
import { API_URL } from '../services/api'

// Node colors based on file type
const TYPE_COLORS = {
  python: '#3776ab',
  javascript: '#f7df1e',
  typescript: '#3178c6',
  css: '#264de4',
  html: '#e34c26',
  json: '#5a5a5a',
  external: '#8b5cf6',
  default: '#10b981'
}

// Risk colors for nodes
const RISK_COLORS = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#22c55e'
}

function getRiskLevel(score) {
  if (score >= 80) return 'critical'
  if (score >= 60) return 'high'
  if (score >= 40) return 'medium'
  return 'low'
}

export default function DependencyGraph({ projectId }) {
  const [graphData, setGraphData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selectedNode, setSelectedNode] = useState(null)
  const [viewMode, setViewMode] = useState('type') // 'type' or 'risk'
  const svgRef = useRef(null)
  const [dimensions, setDimensions] = useState({ width: 900, height: 600 })

  useEffect(() => {
    if (projectId && projectId !== 'demo') {
      loadDependencies()
    }
  }, [projectId])

  const loadDependencies = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`${API_URL}/dependencies/${projectId}`)
      if (!response.ok) throw new Error('Failed to load dependencies')
      const data = await response.json()
      setGraphData(data)
    } catch (err) {
      console.error('Failed to load dependencies:', err)
      setError(err.message)
    }
    setLoading(false)
  }

  // Simple force-directed layout simulation
  const simulateForces = useCallback((nodes, links) => {
    const centerX = dimensions.width / 2
    const centerY = dimensions.height / 2
    
    // Initialize positions
    nodes.forEach((node, i) => {
      const angle = (2 * Math.PI * i) / nodes.length
      const radius = Math.min(dimensions.width, dimensions.height) * 0.35
      node.x = centerX + radius * Math.cos(angle)
      node.y = centerY + radius * Math.sin(angle)
      node.vx = 0
      node.vy = 0
    })

    // Create node map for quick lookup
    const nodeMap = new Map(nodes.map(n => [n.id, n]))

    // Run simulation iterations
    for (let iter = 0; iter < 100; iter++) {
      // Repulsion between all nodes
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[j].x - nodes[i].x
          const dy = nodes[j].y - nodes[i].y
          const dist = Math.sqrt(dx * dx + dy * dy) || 1
          const force = 1000 / (dist * dist)
          const fx = (dx / dist) * force
          const fy = (dy / dist) * force
          nodes[i].vx -= fx
          nodes[i].vy -= fy
          nodes[j].vx += fx
          nodes[j].vy += fy
        }
      }

      // Attraction along links
      links.forEach(link => {
        const source = nodeMap.get(link.source)
        const target = nodeMap.get(link.target)
        if (source && target) {
          const dx = target.x - source.x
          const dy = target.y - source.y
          const dist = Math.sqrt(dx * dx + dy * dy) || 1
          const force = dist * 0.01
          const fx = (dx / dist) * force
          const fy = (dy / dist) * force
          source.vx += fx
          source.vy += fy
          target.vx -= fx
          target.vy -= fy
        }
      })

      // Center gravity
      nodes.forEach(node => {
        node.vx += (centerX - node.x) * 0.01
        node.vy += (centerY - node.y) * 0.01
      })

      // Apply velocity with damping
      nodes.forEach(node => {
        node.x += node.vx * 0.5
        node.y += node.vy * 0.5
        node.vx *= 0.9
        node.vy *= 0.9
        // Keep in bounds
        node.x = Math.max(50, Math.min(dimensions.width - 50, node.x))
        node.y = Math.max(50, Math.min(dimensions.height - 50, node.y))
      })
    }

    return { nodes, links }
  }, [dimensions])

  // Process graph data
  const processedGraph = React.useMemo(() => {
    if (!graphData?.nodes) return null
    const nodes = graphData.nodes.map(n => ({ ...n }))
    const links = graphData.links.map(l => ({ ...l }))
    return simulateForces(nodes, links)
  }, [graphData, simulateForces])

  const getNodeColor = (node) => {
    if (viewMode === 'risk') {
      const riskLevel = getRiskLevel(node.risk || 0)
      return RISK_COLORS[riskLevel]
    }
    return TYPE_COLORS[node.type] || TYPE_COLORS.default
  }

  const getNodeRadius = (node) => {
    const base = 8
    const connections = graphData?.links?.filter(
      l => l.source === node.id || l.target === node.id
    ).length || 0
    return base + Math.min(connections * 2, 12)
  }

  if (!projectId || projectId === 'demo') {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center py-16"
      >
        <div className="text-6xl mb-4">🔗</div>
        <h2 className="text-xl font-semibold text-gray-300 mb-2">
          Dependency Graph
        </h2>
        <p className="text-gray-500">
          Analyze a repository to see file dependencies
        </p>
      </motion.div>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader />
        <span className="ml-3 text-gray-400">Building dependency graph...</span>
      </div>
    )
  }

  if (error) {
    return (
      <GlassCard className="p-6 text-center">
        <div className="text-4xl mb-3">⚠️</div>
        <p className="text-gray-400">{error}</p>
        <button 
          onClick={loadDependencies}
          className="btn-primary-fast mt-4"
        >
          Retry
        </button>
      </GlassCard>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Header Controls */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-white flex items-center gap-2">
            <span className="text-2xl">🔗</span>
            Dependency Graph
          </h2>
          <p className="text-gray-500 text-sm mt-1">
            {graphData?.nodes?.length || 0} files • {graphData?.links?.length || 0} connections
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          {/* View Mode Toggle */}
          <div className="glass-card p-1 flex rounded-lg">
            <button
              onClick={() => setViewMode('type')}
              className={`px-3 py-1.5 rounded-md text-sm transition-all ${
                viewMode === 'type' 
                  ? 'bg-emerald-500/20 text-emerald-400' 
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              By Type
            </button>
            <button
              onClick={() => setViewMode('risk')}
              className={`px-3 py-1.5 rounded-md text-sm transition-all ${
                viewMode === 'risk' 
                  ? 'bg-emerald-500/20 text-emerald-400' 
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              By Risk
            </button>
          </div>
          
          <button 
            onClick={loadDependencies}
            className="btn-primary-fast text-sm"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Graph Container */}
      <GlassCard className="p-0 overflow-hidden">
        <div className="relative" style={{ height: dimensions.height }}>
          <svg
            ref={svgRef}
            width="100%"
            height={dimensions.height}
            className="cursor-move"
          >
            <defs>
              {/* Gradient definitions for links */}
              <linearGradient id="linkGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="rgba(16, 185, 129, 0.4)" />
                <stop offset="100%" stopColor="rgba(16, 185, 129, 0.1)" />
              </linearGradient>
              {/* Glow filter */}
              <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                <feMerge>
                  <feMergeNode in="coloredBlur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>
            </defs>

            {/* Links */}
            <g className="links">
              {processedGraph?.links?.map((link, i) => {
                const source = processedGraph.nodes.find(n => n.id === link.source)
                const target = processedGraph.nodes.find(n => n.id === link.target)
                if (!source || !target) return null
                
                return (
                  <line
                    key={i}
                    x1={source.x}
                    y1={source.y}
                    x2={target.x}
                    y2={target.y}
                    stroke="url(#linkGradient)"
                    strokeWidth={link.type === 'import' ? 2 : 1}
                    strokeOpacity={selectedNode ? 
                      (selectedNode.id === link.source || selectedNode.id === link.target ? 1 : 0.2) 
                      : 0.6
                    }
                    className="transition-opacity duration-300"
                  />
                )
              })}
            </g>

            {/* Nodes */}
            <g className="nodes">
              {processedGraph?.nodes?.map((node, i) => {
                const isSelected = selectedNode?.id === node.id
                const isConnected = selectedNode && graphData?.links?.some(
                  l => (l.source === selectedNode.id && l.target === node.id) ||
                       (l.target === selectedNode.id && l.source === node.id)
                )
                const dimmed = selectedNode && !isSelected && !isConnected

                return (
                  <g
                    key={node.id}
                    transform={`translate(${node.x}, ${node.y})`}
                    onClick={() => setSelectedNode(isSelected ? null : node)}
                    className="cursor-pointer"
                    style={{ opacity: dimmed ? 0.3 : 1 }}
                  >
                    {/* Node glow */}
                    <circle
                      r={getNodeRadius(node) + 4}
                      fill={getNodeColor(node)}
                      opacity={isSelected ? 0.3 : 0}
                      filter="url(#glow)"
                      className="transition-opacity duration-300"
                    />
                    {/* Node circle */}
                    <circle
                      r={getNodeRadius(node)}
                      fill={getNodeColor(node)}
                      stroke={isSelected ? '#fff' : 'rgba(255,255,255,0.2)'}
                      strokeWidth={isSelected ? 2 : 1}
                      className="transition-all duration-300 hover:stroke-white"
                    />
                    {/* Node label */}
                    <text
                      y={getNodeRadius(node) + 14}
                      textAnchor="middle"
                      fill={dimmed ? '#666' : '#999'}
                      fontSize="10"
                      className="pointer-events-none"
                    >
                      {node.name.length > 15 ? node.name.slice(0, 15) + '...' : node.name}
                    </text>
                  </g>
                )
              })}
            </g>
          </svg>

          {/* Legend */}
          <div className="absolute bottom-4 left-4 glass-card p-3">
            <p className="text-xs text-gray-500 mb-2 font-medium">
              {viewMode === 'type' ? 'File Types' : 'Risk Levels'}
            </p>
            <div className="flex flex-wrap gap-3">
              {viewMode === 'type' ? (
                <>
                  {Object.entries(TYPE_COLORS).slice(0, 5).map(([type, color]) => (
                    <div key={type} className="flex items-center gap-1.5">
                      <div 
                        className="w-3 h-3 rounded-full" 
                        style={{ backgroundColor: color }}
                      />
                      <span className="text-xs text-gray-400 capitalize">{type}</span>
                    </div>
                  ))}
                </>
              ) : (
                <>
                  {Object.entries(RISK_COLORS).map(([level, color]) => (
                    <div key={level} className="flex items-center gap-1.5">
                      <div 
                        className="w-3 h-3 rounded-full" 
                        style={{ backgroundColor: color }}
                      />
                      <span className="text-xs text-gray-400 capitalize">{level}</span>
                    </div>
                  ))}
                </>
              )}
            </div>
          </div>
        </div>
      </GlassCard>

      {/* Selected Node Details */}
      {selectedNode && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <GlassCard className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-medium text-white flex items-center gap-2">
                  <span 
                    className="w-3 h-3 rounded-full" 
                    style={{ backgroundColor: getNodeColor(selectedNode) }}
                  />
                  {selectedNode.name}
                </h3>
                <p className="text-sm text-gray-500 mt-1">{selectedNode.id}</p>
              </div>
              <button
                onClick={() => setSelectedNode(null)}
                className="text-gray-500 hover:text-white"
              >
                ✕
              </button>
            </div>
            
            <div className="grid grid-cols-3 gap-4 mt-4">
              <div className="text-center p-3 bg-white/5 rounded-lg">
                <div className="text-xl font-semibold text-emerald-400">
                  {selectedNode.metrics?.lines || 0}
                </div>
                <div className="text-xs text-gray-500">Lines</div>
              </div>
              <div className="text-center p-3 bg-white/5 rounded-lg">
                <div className="text-xl font-semibold text-blue-400">
                  {selectedNode.metrics?.complexity || 0}
                </div>
                <div className="text-xs text-gray-500">Complexity</div>
              </div>
              <div className="text-center p-3 bg-white/5 rounded-lg">
                <div className={`text-xl font-semibold ${
                  selectedNode.risk >= 60 ? 'text-red-400' : 
                  selectedNode.risk >= 40 ? 'text-yellow-400' : 'text-emerald-400'
                }`}>
                  {selectedNode.risk || 0}%
                </div>
                <div className="text-xs text-gray-500">Risk</div>
              </div>
            </div>
            
            {/* Connected files */}
            <div className="mt-4">
              <p className="text-sm text-gray-500 mb-2">Connected Files:</p>
              <div className="flex flex-wrap gap-2">
                {graphData?.links
                  ?.filter(l => l.source === selectedNode.id || l.target === selectedNode.id)
                  .slice(0, 8)
                  .map((link, i) => {
                    const connectedId = link.source === selectedNode.id ? link.target : link.source
                    const connectedNode = graphData.nodes.find(n => n.id === connectedId)
                    return (
                      <span
                        key={i}
                        onClick={() => setSelectedNode(connectedNode)}
                        className="px-2 py-1 bg-white/5 rounded text-xs text-gray-400 
                                   hover:bg-white/10 cursor-pointer transition-colors"
                      >
                        {connectedNode?.name || connectedId}
                      </span>
                    )
                  })}
              </div>
            </div>
          </GlassCard>
        </motion.div>
      )}
    </motion.div>
  )
}
