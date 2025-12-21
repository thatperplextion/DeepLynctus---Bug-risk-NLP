import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts'
import { GlassCard, GradientButton, RiskBadge, Loader } from '../components/ui'

export default function ComparisonView({ projectId }) {
  const [scans, setScans] = useState([])
  const [selectedCurrent, setSelectedCurrent] = useState(null)
  const [selectedPrevious, setSelectedPrevious] = useState(null)
  const [comparisonData, setComparisonData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Fetch scan history
  useEffect(() => {
    if (!projectId || projectId === 'demo') return
    
    const fetchScans = async () => {
      try {
        const response = await fetch(
          `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/comparison/${projectId}/history?limit=20`
        )
        const data = await response.json()
        setScans(data.scans || [])
        if (data.scans?.length >= 2) {
          setSelectedCurrent(data.scans[0]._id)
          setSelectedPrevious(data.scans[1]._id)
        }
      } catch (err) {
        setError('Failed to load scan history')
        console.error(err)
      }
    }
    
    fetchScans()
  }, [projectId])

  // Fetch comparison data
  useEffect(() => {
    if (!projectId || !selectedCurrent || !selectedPrevious) return
    if (selectedCurrent === selectedPrevious) return

    const fetchComparison = async () => {
      setLoading(true)
      setError(null)
      try {
        const response = await fetch(
          `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/comparison/${projectId}/compare?current_scan=${selectedCurrent}&previous_scan=${selectedPrevious}`
        )
        const data = await response.json()
        setComparisonData(data)
      } catch (err) {
        setError('Failed to load comparison data')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchComparison()
  }, [projectId, selectedCurrent, selectedPrevious])

  if (!projectId || projectId === 'demo') {
    return (
      <GlassCard>
        <p className="text-gray-400">Select a project to view comparison data</p>
      </GlassCard>
    )
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'critical': return 'bg-red-500/20 border-red-500/50 text-red-400'
      case 'warning': return 'bg-orange-500/20 border-orange-500/50 text-orange-400'
      case 'regressed': return 'bg-yellow-500/20 border-yellow-500/50 text-yellow-400'
      case 'healthy': return 'bg-green-500/20 border-green-500/50 text-green-400'
      default: return 'bg-gray-500/20 border-gray-500/50 text-gray-400'
    }
  }

  const getTrendArrow = (value) => {
    if (value > 0) return '📈'
    if (value < 0) return '📉'
    return '→'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-teal-400 bg-clip-text text-transparent">
          Scan Comparison & Regression Detection
        </h1>
        <p className="text-gray-400 mt-2">Compare two scans to see what's improved and what's regressed</p>
      </motion.div>

      {/* Scan Selection */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <GlassCard>
          <h3 className="text-lg font-semibold text-cyan-400 mb-3">Current Scan</h3>
          <select
            value={selectedCurrent || ''}
            onChange={(e) => setSelectedCurrent(e.target.value)}
            className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-cyan-400"
          >
            <option value="">Select current scan</option>
            {scans.map((scan) => (
              <option key={scan._id} value={scan._id}>
                {new Date(scan.timestamp).toLocaleString()}
              </option>
            ))}
          </select>
        </GlassCard>

        <GlassCard>
          <h3 className="text-lg font-semibold text-orange-400 mb-3">Previous Scan</h3>
          <select
            value={selectedPrevious || ''}
            onChange={(e) => setSelectedPrevious(e.target.value)}
            className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-orange-400"
          >
            <option value="">Select previous scan</option>
            {scans.map((scan) => (
              <option key={scan._id} value={scan._id}>
                {new Date(scan.timestamp).toLocaleString()}
              </option>
            ))}
          </select>
        </GlassCard>
      </motion.div>

      {error && (
        <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4 text-red-400">
          {error}
        </div>
      )}

      {loading && (
        <div className="flex justify-center py-8">
          <Loader />
        </div>
      )}

      <AnimatePresence>
        {comparisonData && !loading && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
            
            {/* Health Status */}
            {comparisonData.health_status && (
              <GlassCard className={`border ${getStatusColor(comparisonData.health_status.status)}`}>
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold">{comparisonData.health_status.message}</h3>
                  </div>
                </div>
              </GlassCard>
            )}

            {/* Metrics Overview */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <GlassCard>
                <p className="text-gray-400 text-sm">Risk Change</p>
                <p className="text-2xl font-bold text-cyan-400">
                  {getTrendArrow(comparisonData.metrics.avg_risk_change)} {Math.abs(comparisonData.metrics.avg_risk_change).toFixed(1)}%
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {comparisonData.metrics.previous_avg_risk.toFixed(1)}% → {comparisonData.metrics.current_avg_risk.toFixed(1)}%
                </p>
              </GlassCard>

              <GlassCard>
                <p className="text-gray-400 text-sm">New Issues</p>
                <p className="text-2xl font-bold text-red-400">{comparisonData.regressions.new_issues}</p>
                <p className="text-xs text-gray-500 mt-1">
                  Critical: +{comparisonData.regressions.critical_change}
                </p>
              </GlassCard>

              <GlassCard>
                <p className="text-gray-400 text-sm">Fixed Issues</p>
                <p className="text-2xl font-bold text-green-400">{comparisonData.improvements.fixed_issues}</p>
                <p className="text-xs text-gray-500 mt-1">
                  Critical: -{comparisonData.improvements.critical_fixed}
                </p>
              </GlassCard>

              <GlassCard>
                <p className="text-gray-400 text-sm">Files Changed</p>
                <p className="text-2xl font-bold text-purple-400">{comparisonData.metrics.files_with_changes}</p>
                <p className="text-xs text-gray-500 mt-1">
                  out of {comparisonData.metrics.files_analyzed_current}
                </p>
              </GlassCard>
            </div>

            {/* Regression vs Improvement */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <GlassCard>
                <h3 className="text-lg font-semibold text-red-400 mb-4">🔴 Regressions Detected</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center p-3 bg-red-500/10 rounded-lg border border-red-500/30">
                    <span className="text-gray-300">New Issues Found</span>
                    <span className="text-xl font-bold text-red-400">{comparisonData.regressions.new_issues}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-orange-500/10 rounded-lg border border-orange-500/30">
                    <span className="text-gray-300">Critical Issues Increase</span>
                    <span className="text-xl font-bold text-orange-400">+{comparisonData.regressions.critical_change}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-orange-500/10 rounded-lg border border-orange-500/30">
                    <span className="text-gray-300">High Priority Increase</span>
                    <span className="text-xl font-bold text-orange-400">+{comparisonData.regressions.high_change}</span>
                  </div>
                </div>
              </GlassCard>

              <GlassCard>
                <h3 className="text-lg font-semibold text-green-400 mb-4">🟢 Improvements Made</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center p-3 bg-green-500/10 rounded-lg border border-green-500/30">
                    <span className="text-gray-300">Issues Fixed</span>
                    <span className="text-xl font-bold text-green-400">{comparisonData.improvements.fixed_issues}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-emerald-500/10 rounded-lg border border-emerald-500/30">
                    <span className="text-gray-300">Critical Issues Fixed</span>
                    <span className="text-xl font-bold text-emerald-400">{comparisonData.improvements.critical_fixed}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-teal-500/10 rounded-lg border border-teal-500/30">
                    <span className="text-gray-300">Overall Quality</span>
                    <span className="text-xl font-bold text-teal-400">
                      {comparisonData.metrics.avg_risk_change < 0 ? '↗️' : '↘️'} Improved
                    </span>
                  </div>
                </div>
              </GlassCard>
            </div>

            {/* Files with Biggest Changes */}
            {comparisonData.files_changed?.length > 0 && (
              <GlassCard>
                <h3 className="text-lg font-semibold text-cyan-400 mb-4">📊 Files with Biggest Changes</h3>
                <div className="space-y-2 max-h-80 overflow-y-auto">
                  {comparisonData.files_changed.map((file, idx) => (
                    <div key={idx} className={`p-3 rounded-lg border ${
                      file.status === 'regressed' 
                        ? 'bg-red-500/10 border-red-500/30' 
                        : 'bg-green-500/10 border-green-500/30'
                    }`}>
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <p className="text-white font-mono text-sm break-all">{file.path}</p>
                          <p className="text-xs text-gray-400 mt-1">
                            Risk: {file.previous_risk.toFixed(0)}% → {file.current_risk.toFixed(0)}%
                          </p>
                        </div>
                        <div className="text-right ml-3">
                          <span className={`font-bold text-lg ${
                            file.status === 'regressed' ? 'text-red-400' : 'text-green-400'
                          }`}>
                            {file.status === 'regressed' ? '+' : '−'}{Math.abs(file.risk_change).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </GlassCard>
            )}

          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
