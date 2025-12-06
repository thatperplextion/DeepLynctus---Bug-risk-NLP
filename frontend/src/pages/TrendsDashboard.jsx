import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { GlassCard, Loader } from '../components/ui'
import { API_URL } from '../services/api'

// Simple sparkline chart component
function Sparkline({ data, color = '#10b981', height = 40 }) {
  if (!data || data.length < 2) return null
  
  const max = Math.max(...data)
  const min = Math.min(...data)
  const range = max - min || 1
  
  const width = 120
  const points = data.map((value, i) => {
    const x = (i / (data.length - 1)) * width
    const y = height - ((value - min) / range) * (height - 4) - 2
    return `${x},${y}`
  }).join(' ')

  return (
    <svg width={width} height={height} className="opacity-80">
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Gradient area */}
      <defs>
        <linearGradient id={`gradient-${color}`} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon
        points={`0,${height} ${points} ${width},${height}`}
        fill={`url(#gradient-${color})`}
      />
    </svg>
  )
}

// Trend indicator
function TrendIndicator({ value, inverted = false }) {
  if (value === undefined || value === null) return null
  
  const isPositive = inverted ? value < 0 : value > 0
  const isNeutral = Math.abs(value) < 1
  
  return (
    <span className={`inline-flex items-center gap-1 text-sm font-medium ${
      isNeutral ? 'text-gray-500' :
      isPositive ? 'text-emerald-400' : 'text-red-400'
    }`}>
      {isNeutral ? '→' : isPositive ? '↑' : '↓'}
      {Math.abs(value).toFixed(1)}%
    </span>
  )
}

// Simple bar chart
function BarChart({ data, height = 200 }) {
  if (!data || data.length === 0) return null
  
  const max = Math.max(...data.map(d => d.value))
  
  return (
    <div className="flex items-end justify-between gap-2" style={{ height }}>
      {data.map((item, i) => (
        <div key={i} className="flex-1 flex flex-col items-center gap-2">
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: `${(item.value / max) * 100}%` }}
            transition={{ duration: 0.5, delay: i * 0.05 }}
            className="w-full rounded-t-md"
            style={{ 
              backgroundColor: item.color || '#10b981',
              minHeight: 4
            }}
          />
          <span className="text-xs text-gray-500 truncate w-full text-center">
            {item.label}
          </span>
        </div>
      ))}
    </div>
  )
}

export default function TrendsDashboard({ projectId }) {
  const [trends, setTrends] = useState(null)
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [timeRange, setTimeRange] = useState('all')

  useEffect(() => {
    if (projectId && projectId !== 'demo') {
      loadTrends()
    }
  }, [projectId])

  const loadTrends = async () => {
    setLoading(true)
    setError(null)
    try {
      const [trendsRes, historyRes] = await Promise.all([
        fetch(`${API_URL}/history/${projectId}/trends`),
        fetch(`${API_URL}/history/${projectId}?limit=30`)
      ])
      
      if (!trendsRes.ok) throw new Error('Failed to load trends')
      
      const trendsData = await trendsRes.json()
      const historyData = await historyRes.json()
      
      setTrends(trendsData)
      setHistory(historyData.scans || [])
    } catch (err) {
      console.error('Failed to load trends:', err)
      setError(err.message)
    }
    setLoading(false)
  }

  // Calculate chart data from history
  const chartData = React.useMemo(() => {
    if (!history.length) return null
    
    const qualityData = history.slice(-10).map(scan => 
      scan.metrics?.quality_score || 0
    )
    
    const issuesData = history.slice(-10).map(scan => 
      scan.metrics?.total_smells || 0
    )
    
    const riskData = history.slice(-10).map(scan => 
      scan.metrics?.avg_risk || 0
    )
    
    // Bar chart data for issue types
    const latestScan = history[0]?.metrics || {}
    const issueTypes = [
      { label: 'Critical', value: latestScan.critical_issues || 0, color: '#ef4444' },
      { label: 'High', value: latestScan.high_issues || 0, color: '#f97316' },
      { label: 'Medium', value: latestScan.medium_issues || 0, color: '#eab308' },
      { label: 'Low', value: latestScan.low_issues || 0, color: '#22c55e' }
    ]
    
    return { qualityData, issuesData, riskData, issueTypes }
  }, [history])

  if (!projectId || projectId === 'demo') {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center py-16"
      >
        <div className="text-6xl mb-4">📈</div>
        <h2 className="text-xl font-semibold text-gray-300 mb-2">
          Historical Trends
        </h2>
        <p className="text-gray-500">
          Analyze a repository to track quality over time
        </p>
      </motion.div>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader />
        <span className="ml-3 text-gray-400">Loading trends...</span>
      </div>
    )
  }

  if (error) {
    return (
      <GlassCard className="p-6 text-center">
        <div className="text-4xl mb-3">⚠️</div>
        <p className="text-gray-400">{error}</p>
        <button 
          onClick={loadTrends}
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
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-white flex items-center gap-2">
            <span className="text-2xl">📈</span>
            Historical Trends
          </h2>
          <p className="text-gray-500 text-sm mt-1">
            {history.length} scans tracked
          </p>
        </div>
        
        <button 
          onClick={loadTrends}
          className="btn-primary-fast text-sm"
        >
          Refresh
        </button>
      </div>

      {/* Trend Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Quality Score Trend */}
        <GlassCard className="p-4">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-gray-500 text-sm">Quality Score</p>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-2xl font-semibold text-emerald-400">
                  {trends?.current?.quality_score?.toFixed(1) || 0}%
                </span>
                <TrendIndicator value={trends?.changes?.quality_score} />
              </div>
            </div>
            <div className="text-3xl opacity-50">📊</div>
          </div>
          <div className="mt-3">
            <Sparkline data={chartData?.qualityData} color="#10b981" />
          </div>
        </GlassCard>

        {/* Total Issues Trend */}
        <GlassCard className="p-4">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-gray-500 text-sm">Total Issues</p>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-2xl font-semibold text-orange-400">
                  {trends?.current?.total_smells || 0}
                </span>
                <TrendIndicator value={trends?.changes?.total_smells} inverted />
              </div>
            </div>
            <div className="text-3xl opacity-50">🐛</div>
          </div>
          <div className="mt-3">
            <Sparkline data={chartData?.issuesData} color="#f97316" />
          </div>
        </GlassCard>

        {/* Average Risk Trend */}
        <GlassCard className="p-4">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-gray-500 text-sm">Average Risk</p>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-2xl font-semibold text-yellow-400">
                  {trends?.current?.avg_risk?.toFixed(1) || 0}%
                </span>
                <TrendIndicator value={trends?.changes?.avg_risk} inverted />
              </div>
            </div>
            <div className="text-3xl opacity-50">⚠️</div>
          </div>
          <div className="mt-3">
            <Sparkline data={chartData?.riskData} color="#eab308" />
          </div>
        </GlassCard>
      </div>

      {/* Issue Distribution */}
      <GlassCard className="p-6">
        <h3 className="font-medium text-white mb-4">Issue Distribution</h3>
        <BarChart data={chartData?.issueTypes} height={160} />
      </GlassCard>

      {/* Scan History Timeline */}
      <GlassCard className="p-6">
        <h3 className="font-medium text-white mb-4">Recent Scans</h3>
        <div className="space-y-3 max-h-80 overflow-y-auto">
          {history.slice(0, 10).map((scan, i) => (
            <motion.div
              key={scan.scan_id || i}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className="flex items-center gap-4 p-3 bg-white/5 rounded-lg hover:bg-white/10 transition-colors"
            >
              {/* Timeline dot */}
              <div className="relative">
                <div className="w-3 h-3 rounded-full bg-emerald-500" />
                {i < history.length - 1 && (
                  <div className="absolute top-3 left-1/2 -translate-x-1/2 w-px h-8 bg-emerald-500/20" />
                )}
              </div>
              
              {/* Scan info */}
              <div className="flex-1 min-w-0">
                <p className="text-sm text-white truncate">
                  Scan #{scan.scan_id?.slice(-6) || i + 1}
                </p>
                <p className="text-xs text-gray-500">
                  {scan.timestamp ? new Date(scan.timestamp).toLocaleString() : 'Unknown'}
                </p>
              </div>
              
              {/* Metrics */}
              <div className="flex items-center gap-4 text-sm">
                <div className="text-right">
                  <span className="text-emerald-400 font-medium">
                    {scan.metrics?.quality_score?.toFixed(0) || 0}%
                  </span>
                  <p className="text-xs text-gray-500">Quality</p>
                </div>
                <div className="text-right">
                  <span className="text-orange-400 font-medium">
                    {scan.metrics?.total_smells || 0}
                  </span>
                  <p className="text-xs text-gray-500">Issues</p>
                </div>
                <div className="text-right">
                  <span className="text-blue-400 font-medium">
                    {scan.metrics?.total_files || 0}
                  </span>
                  <p className="text-xs text-gray-500">Files</p>
                </div>
              </div>
            </motion.div>
          ))}
          
          {history.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <p>No scan history yet</p>
              <p className="text-sm mt-1">Run your first scan to start tracking trends</p>
            </div>
          )}
        </div>
      </GlassCard>

      {/* Insights */}
      {trends && (
        <GlassCard className="p-6">
          <h3 className="font-medium text-white mb-4 flex items-center gap-2">
            <span>💡</span> Insights
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Quality insight */}
            <div className="p-4 bg-white/5 rounded-lg">
              <p className="text-sm text-gray-400">
                {trends.changes?.quality_score > 5 ? (
                  <>
                    <span className="text-emerald-400">Great progress!</span> Your code quality 
                    has improved by {Math.abs(trends.changes.quality_score).toFixed(1)}% since the last scan.
                  </>
                ) : trends.changes?.quality_score < -5 ? (
                  <>
                    <span className="text-red-400">Heads up!</span> Code quality dropped by 
                    {Math.abs(trends.changes.quality_score).toFixed(1)}%. Review recent changes.
                  </>
                ) : (
                  <>
                    <span className="text-blue-400">Stable!</span> Your code quality is 
                    consistent at around {trends.current?.quality_score?.toFixed(0)}%.
                  </>
                )}
              </p>
            </div>
            
            {/* Issues insight */}
            <div className="p-4 bg-white/5 rounded-lg">
              <p className="text-sm text-gray-400">
                {trends.changes?.total_smells < -10 ? (
                  <>
                    <span className="text-emerald-400">Nice work!</span> You've reduced 
                    issues by {Math.abs(trends.changes.total_smells).toFixed(0)}%.
                  </>
                ) : trends.changes?.total_smells > 10 ? (
                  <>
                    <span className="text-orange-400">New issues detected.</span> 
                    {trends.changes.total_smells.toFixed(0)}% more issues than before.
                  </>
                ) : (
                  <>
                    Currently tracking <span className="text-blue-400">
                    {trends.current?.total_smells || 0} issues</span> across your codebase.
                  </>
                )}
              </p>
            </div>
          </div>
        </GlassCard>
      )}
    </motion.div>
  )
}
