import React, { useState, useEffect, useMemo } from 'react'
import { motion } from 'framer-motion'
import { getSuggestions, getSmells } from '../services/api'
import { GlassCard, GradientButton, RiskBadge, Loader } from '../components/ui'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    return (
      <div className="glass rounded-lg p-3 border border-white/20">
        <p className="text-sm text-gray-300">{payload[0].payload.feature}</p>
        <p className="text-lg font-bold text-cyan-400">{payload[0].value.toFixed(3)}</p>
      </div>
    )
  }
  return null
}

export default function FileDetail({ file, onBack, projectId }) {
  const [suggestions, setSuggestions] = useState([])
  const [fileSmells, setFileSmells] = useState([])
  const [loadingSmells, setLoadingSmells] = useState(true)
  const [loadingSuggestions, setLoadingSuggestions] = useState(true)

  useEffect(() => {
    const pid = projectId || localStorage.getItem('codesensex_project') || 'demo'
    
    // Load smells for this file
    const loadSmells = async () => {
      setLoadingSmells(true)
      try {
        const smellsData = await getSmells(pid)
        const smells = smellsData.items || []
        // Filter smells for this specific file (handle both / and \ in paths)
        const normalizedFilePath = (file.path || '').replace(/\\/g, '/').toLowerCase()
        const thisFileSmells = smells.filter(s => {
          const smellPath = (s.path || '').replace(/\\/g, '/').toLowerCase()
          return smellPath === normalizedFilePath || smellPath.endsWith(normalizedFilePath)
        })
        setFileSmells(thisFileSmells)
      } catch (err) {
        console.error('Failed to load smells:', err)
        setFileSmells([])
      } finally {
        setLoadingSmells(false)
      }
    }
    
    // Load suggestions
    const loadSuggestions = async () => {
      if (!projectId) {
        setSuggestions([])
        setLoadingSuggestions(false)
        return
      }
      
      setLoadingSuggestions(true)
      try {
        // Encode the path for the API (replace / and \ with _)
        const encodedPath = (file.path || '').replace(/[\/\\]/g, '_')
        const data = await getSuggestions(projectId, encodedPath, 5)
        setSuggestions(data.suggestions || [])
      } catch (err) {
        console.error('Failed to load suggestions:', err)
        setSuggestions([])
      } finally {
        setLoadingSuggestions(false)
      }
    }
    
    loadSmells()
    loadSuggestions()
  }, [file, projectId])

  // Calculate SHAP-like feature importance from actual file metrics
  const shapValues = useMemo(() => {
    const values = []
    
    // Add actual metrics as features if they exist
    if (file.cyclomatic_max) {
      values.push({ feature: 'cyclomatic_max', value: Math.min(file.cyclomatic_max / 50, 1) })
    }
    if (file.churn_30d) {
      values.push({ feature: 'churn_30d', value: Math.min(file.churn_30d / 100, 1) })
    }
    if (file.dup_ratio) {
      values.push({ feature: 'dup_ratio', value: file.dup_ratio })
    }
    if (file.nesting_max) {
      values.push({ feature: 'nesting_max', value: Math.min(file.nesting_max / 10, 1) })
    }
    if (file.loc) {
      values.push({ feature: 'loc', value: Math.min(file.loc / 1000, 1) })
    }
    if (file.fn_count) {
      values.push({ feature: 'fn_count', value: Math.min(file.fn_count / 50, 1) })
    }
    
    // Sort by value descending and take top 5
    return values.sort((a, b) => b.value - a.value).slice(0, 5)
  }, [file])

  const priorityColors = {
    High: 'border-red-500/30 bg-red-500/10',
    Medium: 'border-yellow-500/30 bg-yellow-500/10',
    Low: 'border-emerald-500/30 bg-emerald-500/10'
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: 50 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -50 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <GradientButton onClick={onBack} variant="secondary" size="sm">
            ← Back
          </GradientButton>
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-2">
              <span className="text-cyan-400">📄</span>
              {file.path}
            </h1>
            <p className="text-gray-400 text-sm mt-1">Detailed risk analysis and refactoring suggestions</p>
          </div>
        </div>
        <RiskBadge tier={file.tier || 'Medium'} />
      </div>

      {/* Metrics Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <GlassCard delay={0.1} className="text-center">
          <p className="text-gray-400 text-sm">Risk Score</p>
          <p className="text-3xl font-bold text-red-400">{file.risk_score ?? 'N/A'}</p>
        </GlassCard>
        <GlassCard delay={0.2} className="text-center">
          <p className="text-gray-400 text-sm">Lines of Code</p>
          <p className="text-3xl font-bold text-cyan-400">{file.loc ?? 'N/A'}</p>
        </GlassCard>
        <GlassCard delay={0.3} className="text-center">
          <p className="text-gray-400 text-sm">Complexity</p>
          <p className="text-3xl font-bold text-orange-400">{file.cyclomatic_max ?? 'N/A'}</p>
        </GlassCard>
        <GlassCard delay={0.4} className="text-center">
          <p className="text-gray-400 text-sm">Functions</p>
          <p className="text-3xl font-bold text-emerald-400">{file.fn_count ?? 'N/A'}</p>
        </GlassCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* SHAP Feature Importance */}
        <GlassCard delay={0.3}>
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <span className="text-2xl">📊</span> Risk Attribution (SHAP)
          </h2>
          <p className="text-gray-400 text-sm mb-4">
            Top factors contributing to this file's risk score
          </p>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={shapValues} layout="vertical" barSize={24}>
                <XAxis type="number" stroke="#6b7280" />
                <YAxis dataKey="feature" type="category" width={100} tick={{ fill: '#9ca3af', fontSize: 12 }} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="value" radius={[0, 8, 8, 0]} fill="url(#shapGradient)" />
                <defs>
                  <linearGradient id="shapGradient" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="#14b8a6" />
                    <stop offset="100%" stopColor="#06b6d4" />
                  </linearGradient>
                </defs>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        {/* Code Smells Detected */}
        <GlassCard delay={0.4}>
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <span className="text-2xl">🧪</span> Detected Issues
          </h2>
          {loadingSmells ? (
            <Loader />
          ) : fileSmells.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              <p className="text-4xl mb-2">✅</p>
              <p>No issues detected in this file</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-80 overflow-y-auto">
              {fileSmells.map((smell, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 * i }}
                  className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <span className={`w-2 h-2 rounded-full ${smell.severity >= 4 ? 'bg-red-500' : smell.severity >= 3 ? 'bg-orange-500' : 'bg-yellow-500'}`}></span>
                    <div>
                      <p className="font-medium text-white">{smell.type}</p>
                      <p className="text-sm text-gray-400">Line {smell.line}: {smell.message}</p>
                    </div>
                  </div>
                  <span className="text-sm text-gray-500">Severity {smell.severity}/5</span>
                </motion.div>
              ))}
            </div>
          )}
        </GlassCard>
      </div>

      {/* Refactoring Suggestions */}
      <GlassCard delay={0.5}>
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
          <span className="text-2xl">💡</span> AI Refactoring Suggestions
        </h2>
        {loadingSuggestions ? (
          <Loader />
        ) : suggestions.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <p className="text-4xl mb-2">✨</p>
            <p>No refactoring suggestions at this time</p>
          </div>
        ) : (
          <div className="space-y-4">
            {suggestions.map((s, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 * i }}
                className={`p-4 rounded-xl border ${priorityColors[s.priority] || priorityColors.Medium}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="font-semibold text-white">{s.title}</h3>
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                        s.priority === 'High' ? 'bg-red-500/20 text-red-400' :
                        s.priority === 'Medium' ? 'bg-yellow-500/20 text-yellow-400' :
                        'bg-emerald-500/20 text-emerald-400'
                      }`}>
                        {s.priority}
                      </span>
                    </div>
                    <p className="text-gray-400 text-sm mb-3">{s.rationale}</p>
                    <code className="block p-3 rounded-lg bg-gray-900/50 text-cyan-400 text-sm font-mono">
                      {s.snippet}
                    </code>
                  </div>
                  <div className="text-right ml-4">
                    <p className="text-2xl font-bold text-white">{s.est_hours}h</p>
                    <p className="text-xs text-gray-500">Est. effort</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </GlassCard>
    </motion.div>
  )
}
