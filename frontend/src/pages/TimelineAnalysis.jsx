import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { GlassCard, Loader } from '../components/ui'

export default function TimelineAnalysis({ projectId }) {
  const [timelineData, setTimelineData] = useState(null)
  const [roiData, setRoiData] = useState(null)
  const [days, setDays] = useState(90)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Fetch timeline data
  useEffect(() => {
    if (!projectId || projectId === 'demo') return

    const fetchTimeline = async () => {
      setLoading(true)
      setError(null)
      try {
        const [timelineRes, roiRes] = await Promise.all([
          fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/comparison/${projectId}/timeline?days=${days}`),
          fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/comparison/${projectId}/roi?days=${days}`)
        ])

        const timelineJson = await timelineRes.json()
        const roiJson = await roiRes.json()

        setTimelineData(timelineJson)
        setRoiData(roiJson)
      } catch (err) {
        setError('Failed to load timeline data')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchTimeline()
  }, [projectId, days])

  if (!projectId || projectId === 'demo') {
    return (
      <GlassCard>
        <p className="text-gray-400">Select a project to view timeline analysis</p>
      </GlassCard>
    )
  }

  const chartData = timelineData?.timeline || []
  const summary = timelineData?.summary || {}

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="glass rounded-lg p-3 border border-white/20">
          <p className="text-sm text-gray-300">{new Date(payload[0].payload.timestamp).toLocaleDateString()}</p>
          <p className="text-cyan-400 font-semibold">Quality: {payload[0].value.toFixed(1)}%</p>
          <p className="text-orange-400 text-sm">Issues: {payload[1]?.value || 0}</p>
        </div>
      )
    }
    return null
  }

  const getTrendColor = (value) => {
    if (value > 0) return 'text-green-400'
    if (value < 0) return 'text-red-400'
    return 'text-gray-400'
  }

  const getTrendArrow = (value) => {
    if (value > 0) return '↗️'
    if (value < 0) return '↘️'
    return '→'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-teal-400 bg-clip-text text-transparent">
          Timeline & ROI Analysis
        </h1>
        <p className="text-gray-400 mt-2">Track code quality improvements and measure ROI over time</p>

        {/* Days Filter */}
        <div className="flex gap-2 mt-4">
          {[30, 60, 90, 180].map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-4 py-2 rounded-lg transition ${
                days === d
                  ? 'bg-cyan-500 text-white'
                  : 'bg-white/10 text-gray-300 hover:bg-white/20'
              }`}
            >
              {d} days
            </button>
          ))}
        </div>
      </motion.div>

      {error && (
        <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4 text-red-400">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-12">
          <Loader />
        </div>
      ) : (
        <>
          {/* Summary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <GlassCard>
              <p className="text-gray-400 text-sm">Current Quality Score</p>
              <p className="text-3xl font-bold text-cyan-400">{summary.current_quality?.toFixed(1) || 'N/A'}%</p>
              <p className={`text-sm font-semibold mt-2 ${getTrendColor(summary.quality_trend)}`}>
                {getTrendArrow(summary.quality_trend)} {Math.abs(summary.quality_trend || 0).toFixed(1)}%
              </p>
            </GlassCard>

            <GlassCard>
              <p className="text-gray-400 text-sm">Quality Range</p>
              <p className="text-2xl font-bold text-purple-400">
                {summary.quality_range?.min?.toFixed(1) || 'N/A'}% - {summary.quality_range?.max?.toFixed(1) || 'N/A'}%
              </p>
              <p className="text-xs text-gray-500 mt-2">Best to worst in period</p>
            </GlassCard>

            <GlassCard>
              <p className="text-gray-400 text-sm">Issues Trend</p>
              <p className={`text-3xl font-bold ${summary.issues_trend < 0 ? 'text-green-400' : 'text-red-400'}`}>
                {getTrendArrow(summary.issues_trend)} {summary.current_issues || 0}
              </p>
              <p className="text-xs text-gray-500 mt-2">Net change: {summary.issues_trend > 0 ? '+' : ''}{summary.issues_trend || 0}</p>
            </GlassCard>

            <GlassCard>
              <p className="text-gray-400 text-sm">Trend Direction</p>
              <p className="text-2xl font-bold">
                {summary.trend_direction === 'up' ? '📈' : summary.trend_direction === 'down' ? '📉' : '→'}
              </p>
              <p className="text-sm text-gray-400 capitalize mt-2">{summary.trend_direction || 'stable'}</p>
            </GlassCard>
          </div>

          {/* Quality Score Timeline */}
          {chartData.length > 0 && (
            <GlassCard>
              <h3 className="text-lg font-semibold text-cyan-400 mb-4">📊 Quality Score Over Time</h3>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="qualityGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                  <XAxis
                    dataKey="timestamp"
                    tickFormatter={(value) => new Date(value).toLocaleDateString()}
                    stroke="rgba(255,255,255,0.5)"
                  />
                  <YAxis stroke="rgba(255,255,255,0.5)" />
                  <Tooltip content={<CustomTooltip />} />
                  <Area
                    type="monotone"
                    dataKey="quality_score"
                    stroke="#06b6d4"
                    fillOpacity={1}
                    fill="url(#qualityGradient)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </GlassCard>
          )}

          {/* Issues Over Time */}
          {chartData.length > 0 && (
            <GlassCard>
              <h3 className="text-lg font-semibold text-orange-400 mb-4">🐛 Issues Trend</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                  <XAxis
                    dataKey="timestamp"
                    tickFormatter={(value) => new Date(value).toLocaleDateString()}
                    stroke="rgba(255,255,255,0.5)"
                  />
                  <YAxis stroke="rgba(255,255,255,0.5)" />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Bar dataKey="total_issues" fill="#f97316" name="Total Issues" />
                  <Bar dataKey="critical_issues" fill="#ef4444" name="Critical Issues" />
                  <Bar dataKey="high_issues" fill="#eab308" name="High Priority" />
                </BarChart>
              </ResponsiveContainer>
            </GlassCard>
          )}

          {/* ROI Metrics */}
          {roiData?.improvements && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <GlassCard className="border border-green-500/30 bg-green-500/5">
                <h3 className="text-2xl font-bold text-green-400 mb-4">💰 ROI Metrics ({days} days)</h3>

                {roiData.status === 'insufficient_data' ? (
                  <p className="text-gray-400">{roiData.message}</p>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-green-500/10 rounded-lg p-4 border border-green-500/30">
                      <p className="text-gray-300 text-sm mb-2">Issues Fixed</p>
                      <p className="text-4xl font-bold text-green-400">{roiData.improvements.issues_fixed}</p>
                      <p className="text-sm text-green-300 mt-2">Critical: {roiData.improvements.critical_issues_fixed}</p>
                    </div>

                    <div className="bg-blue-500/10 rounded-lg p-4 border border-blue-500/30">
                      <p className="text-gray-300 text-sm mb-2">Estimated Cost Savings</p>
                      <p className="text-4xl font-bold text-blue-400">{roiData.roi_metrics.estimated_cost_savings}</p>
                      <p className="text-sm text-blue-300 mt-2">Bug prevention value</p>
                    </div>

                    <div className="bg-purple-500/10 rounded-lg p-4 border border-purple-500/30">
                      <p className="text-gray-300 text-sm mb-2">Developer Hours Saved</p>
                      <p className="text-4xl font-bold text-purple-400">{roiData.roi_metrics.developer_hours_saved}</p>
                      <p className="text-sm text-purple-300 mt-2">Time saved on bug fixes</p>
                    </div>

                    <div className="bg-cyan-500/10 rounded-lg p-4 border border-cyan-500/30">
                      <p className="text-gray-300 text-sm mb-2">Quality Improvement</p>
                      <p className="text-4xl font-bold text-cyan-400">
                        {roiData.improvements.quality_improvement_percent.toFixed(1)}%
                      </p>
                      <p className="text-sm text-cyan-300 mt-2">
                        {roiData.improvements.quality_score_previous.toFixed(1)}% → {roiData.improvements.quality_score_current.toFixed(1)}%
                      </p>
                    </div>

                    <div className="md:col-span-2 bg-gradient-to-r from-emerald-500/10 to-teal-500/10 rounded-lg p-4 border border-emerald-500/30">
                      <p className="text-gray-300 text-sm mb-2">ROI Score</p>
                      <p className="text-3xl font-bold text-emerald-400">{roiData.roi_score}</p>
                      <p className="text-sm text-gray-400 mt-2">Overall effectiveness of code quality improvements</p>
                    </div>
                  </div>
                )}
              </GlassCard>
            </motion.div>
          )}
        </>
      )}
    </div>
  )
}
