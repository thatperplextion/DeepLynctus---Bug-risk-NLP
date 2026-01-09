import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { API_URL } from '../services/api'

export default function ProjectComparison() {
  const [projects, setProjects] = useState([])
  const [projectA, setProjectA] = useState('')
  const [projectB, setProjectB] = useState('')
  const [comparison, setComparison] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchProjects()
  }, [])

  const fetchProjects = async () => {
    try {
      const res = await fetch(`${API_URL}/projects/compare/list`)
      const data = await res.json()
      setProjects(data.projects || [])
    } catch (err) {
      console.error('Failed to fetch projects:', err)
    }
  }

  const handleCompare = async () => {
    if (!projectA || !projectB) {
      setError('Please select both projects to compare')
      return
    }

    if (projectA === projectB) {
      setError('Please select two different projects')
      return
    }

    setLoading(true)
    setError('')
    
    try {
      const res = await fetch(`${API_URL}/projects/compare/${projectA}/vs/${projectB}`)
      const data = await res.json()
      setComparison(data)
    } catch (err) {
      setError('Failed to compare projects: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  const getWinnerColor = (winner) => {
    if (winner === 'project_a') return 'text-cyan-400'
    if (winner === 'project_b') return 'text-purple-400'
    return 'text-yellow-400'
  }

  const getWinnerEmoji = (winner) => {
    if (winner === 'project_a') return '🏆'
    if (winner === 'project_b') return '🏆'
    return '🤝'
  }

  const getDiffColor = (better) => {
    if (better === 'a') return 'text-cyan-400'
    if (better === 'b') return 'text-purple-400'
    return 'text-gray-400'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <h1 className="text-4xl font-bold mb-2">
          <span className="gradient-text">Project Comparison</span>
        </h1>
        <p className="text-gray-400">Compare code quality between two projects</p>
      </motion.div>

      {/* Project Selection */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card-animated p-6"
      >
        <div className="grid md:grid-cols-2 gap-4">
          {/* Project A Selector */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Project A
            </label>
            <select
              value={projectA}
              onChange={(e) => setProjectA(e.target.value)}
              className="w-full px-4 py-3 rounded-xl bg-[var(--glass-bg)] border border-white/10 text-white focus:outline-none focus:border-cyan-400"
            >
              <option value="">Select Project A...</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          {/* Project B Selector */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Project B
            </label>
            <select
              value={projectB}
              onChange={(e) => setProjectB(e.target.value)}
              className="w-full px-4 py-3 rounded-xl bg-[var(--glass-bg)] border border-white/10 text-white focus:outline-none focus:border-purple-400"
            >
              <option value="">Select Project B...</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <button
          onClick={handleCompare}
          disabled={loading || !projectA || !projectB}
          className="mt-4 w-full px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-purple-600 text-white font-medium hover:shadow-lg hover:shadow-cyan-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Comparing...' : 'Compare Projects ⚖️'}
        </button>

        {error && (
          <p className="mt-3 text-red-400 text-sm text-center">{error}</p>
        )}
      </motion.div>

      {/* Comparison Results */}
      {comparison && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          {/* Winner Banner */}
          <div className="glass-card-animated p-6 text-center">
            <div className="text-6xl mb-3">{getWinnerEmoji(comparison.winner.winner)}</div>
            <h2 className={`text-3xl font-bold ${getWinnerColor(comparison.winner.winner)}`}>
              {comparison.winner.summary}
            </h2>
            <p className="text-gray-400 mt-2">
              Score: {comparison.winner.score_a} vs {comparison.winner.score_b}
            </p>
          </div>

          {/* Side by Side Comparison */}
          <div className="grid md:grid-cols-2 gap-4">
            {/* Project A Card */}
            <div className="glass-card-animated p-6 border-2 border-cyan-500/30">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-cyan-400">
                  {comparison.project_a.name}
                </h3>
                {comparison.winner.winner === 'project_a' && (
                  <span className="text-2xl">🏆</span>
                )}
              </div>
              
              <div className="space-y-3">
                <MetricRow
                  label="Quality Score"
                  value={`${comparison.project_a.summary.quality_score}%`}
                  color="cyan"
                />
                <MetricRow
                  label="Total Files"
                  value={comparison.project_a.summary.total_files}
                  color="cyan"
                />
                <MetricRow
                  label="Total LOC"
                  value={comparison.project_a.summary.total_loc.toLocaleString()}
                  color="cyan"
                />
                <MetricRow
                  label="Avg Complexity"
                  value={comparison.project_a.summary.avg_complexity}
                  color="cyan"
                />
                <MetricRow
                  label="Critical Issues"
                  value={comparison.project_a.summary.critical_issues}
                  color="red"
                />
                <MetricRow
                  label="High Issues"
                  value={comparison.project_a.summary.high_issues}
                  color="orange"
                />
                <MetricRow
                  label="Total Issues"
                  value={comparison.project_a.summary.total_issues}
                  color="yellow"
                />
              </div>
            </div>

            {/* Project B Card */}
            <div className="glass-card-animated p-6 border-2 border-purple-500/30">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-purple-400">
                  {comparison.project_b.name}
                </h3>
                {comparison.winner.winner === 'project_b' && (
                  <span className="text-2xl">🏆</span>
                )}
              </div>
              
              <div className="space-y-3">
                <MetricRow
                  label="Quality Score"
                  value={`${comparison.project_b.summary.quality_score}%`}
                  color="purple"
                />
                <MetricRow
                  label="Total Files"
                  value={comparison.project_b.summary.total_files}
                  color="purple"
                />
                <MetricRow
                  label="Total LOC"
                  value={comparison.project_b.summary.total_loc.toLocaleString()}
                  color="purple"
                />
                <MetricRow
                  label="Avg Complexity"
                  value={comparison.project_b.summary.avg_complexity}
                  color="purple"
                />
                <MetricRow
                  label="Critical Issues"
                  value={comparison.project_b.summary.critical_issues}
                  color="red"
                />
                <MetricRow
                  label="High Issues"
                  value={comparison.project_b.summary.high_issues}
                  color="orange"
                />
                <MetricRow
                  label="Total Issues"
                  value={comparison.project_b.summary.total_issues}
                  color="yellow"
                />
              </div>
            </div>
          </div>

          {/* Differences Table */}
          <div className="glass-card-animated p-6">
            <h3 className="text-xl font-bold mb-4">📊 Detailed Differences</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/10">
                    <th className="text-left py-3 px-4">Metric</th>
                    <th className="text-right py-3 px-4">Difference</th>
                    <th className="text-right py-3 px-4">Change %</th>
                    <th className="text-center py-3 px-4">Better</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(comparison.differences).map(([key, diff]) => (
                    <tr key={key} className="border-b border-white/5">
                      <td className="py-3 px-4 text-gray-300">
                        {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </td>
                      <td className={`text-right py-3 px-4 ${getDiffColor(diff.better)}`}>
                        {diff.absolute > 0 ? '+' : ''}{diff.absolute}
                      </td>
                      <td className={`text-right py-3 px-4 ${getDiffColor(diff.better)}`}>
                        {diff.percentage > 0 ? '+' : ''}{diff.percentage}%
                      </td>
                      <td className="text-center py-3 px-4">
                        {diff.better === 'a' && '🔵'}
                        {diff.better === 'b' && '🟣'}
                        {diff.better === 'tie' && '⚪'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Detailed Breakdown */}
          {comparison.detailed_comparison && (
            <div className="grid md:grid-cols-2 gap-4">
              {/* Complexity */}
              {comparison.detailed_comparison.complexity.available && (
                <div className="glass-card-animated p-6">
                  <h4 className="text-lg font-bold mb-3">🧮 Complexity</h4>
                  <div className="space-y-2 text-sm">
                    <p>Max Complexity: <span className="text-cyan-400">{comparison.detailed_comparison.complexity.project_a.max}</span> vs <span className="text-purple-400">{comparison.detailed_comparison.complexity.project_b.max}</span></p>
                    <p>Files Over 10: <span className="text-cyan-400">{comparison.detailed_comparison.complexity.project_a.files_over_10}</span> vs <span className="text-purple-400">{comparison.detailed_comparison.complexity.project_b.files_over_10}</span></p>
                  </div>
                </div>
              )}

              {/* Security */}
              {comparison.detailed_comparison.security.available && (
                <div className="glass-card-animated p-6">
                  <h4 className="text-lg font-bold mb-3">🔒 Security</h4>
                  <div className="space-y-2 text-sm">
                    <p>Security Issues: <span className="text-cyan-400">{comparison.detailed_comparison.security.project_a.security_issues}</span> vs <span className="text-purple-400">{comparison.detailed_comparison.security.project_b.security_issues}</span></p>
                    <p className="text-gray-400">Winner: <span className={comparison.detailed_comparison.security.winner === 'project_a' ? 'text-cyan-400' : comparison.detailed_comparison.security.winner === 'project_b' ? 'text-purple-400' : 'text-yellow-400'}>
                      {comparison.detailed_comparison.security.winner === 'project_a' ? 'Project A 🏆' : comparison.detailed_comparison.security.winner === 'project_b' ? 'Project B 🏆' : 'Tie'}
                    </span></p>
                  </div>
                </div>
              )}
            </div>
          )}
        </motion.div>
      )}

      {/* Empty State */}
      {!comparison && !loading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-12 text-gray-500"
        >
          <div className="text-6xl mb-4">⚖️</div>
          <p>Select two projects above to compare their code quality</p>
        </motion.div>
      )}
    </div>
  )
}

function MetricRow({ label, value, color }) {
  const colorClasses = {
    cyan: 'text-cyan-400',
    purple: 'text-purple-400',
    red: 'text-red-400',
    orange: 'text-orange-400',
    yellow: 'text-yellow-400'
  }

  return (
    <div className="flex justify-between items-center">
      <span className="text-gray-400 text-sm">{label}</span>
      <span className={`font-semibold ${colorClasses[color]}`}>{value}</span>
    </div>
  )
}
