import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { getMetrics, getRisks, queueGithubRepo, startScan, exportReport } from '../services/api'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, AreaChart, Area } from 'recharts'
import { GlassCard, GradientButton, GlassInput, StatCard, RiskBadge, ProgressRing, Loader } from '../components/ui'

const COLORS = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#3b82f6', '#8b5cf6', '#ec4899']

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="glass rounded-lg p-3 border border-white/20">
        <p className="text-sm text-gray-300">{label}</p>
        <p className="text-lg font-bold text-cyan-400">{payload[0].value}</p>
      </div>
    )
  }
  return null
}

export default function Overview({ projectId: parentProjectId, onFileSelect, onProjectChange }) {
  const [projectId, setProjectId] = useState(parentProjectId || '')
  const [metrics, setMetrics] = useState([])
  const [risks, setRisks] = useState([])
  const [summary, setSummary] = useState({ avg_risk: 0, high: 0, critical: 0 })
  const [sourceRef, setSourceRef] = useState('')
  const [loading, setLoading] = useState(false)
  const [scanned, setScanned] = useState(false)
  const [scanStatus, setScanStatus] = useState('')
  const [hasPreviousScan, setHasPreviousScan] = useState(false)

  const updateProjectId = (newId) => {
    setProjectId(newId)
    localStorage.setItem('codesensex_project', newId)
    if (onProjectChange) {
      onProjectChange(newId)
    }
  }

  const loadData = async (pid) => {
    const id = pid || projectId
    if (!id || id === 'demo') return
    
    setLoading(true)
    try {
      const m = await getMetrics(id, 50, 'cyclomatic_max:-1')
      const r = await getRisks(id, undefined, 10)
      setMetrics(m.metrics || [])
      setRisks(r.items || [])
      setSummary(r.summary || { avg_risk: 0, high: 0, critical: 0 })
      setScanned(true)
      setProjectId(id)
      if (onProjectChange) {
        onProjectChange(id)
      }
    } catch (err) {
      console.error('Load data error:', err)
    } finally {
      setLoading(false)
    }
  }

  // Sync with parent projectId and load data if we have a valid project
  useEffect(() => {
    if (parentProjectId && parentProjectId !== 'demo' && parentProjectId !== '') {
      setProjectId(parentProjectId)
      // If parent has a projectId but we don't have data, load it
      if (metrics.length === 0 && !loading) {
        loadData(parentProjectId)
      }
    }
  }, [parentProjectId])

  // Check if there's a previous scan on mount (but don't auto-load)
  useEffect(() => {
    const savedProjectId = localStorage.getItem('codesensex_project')
    if (savedProjectId && savedProjectId !== 'demo' && savedProjectId !== '') {
      setHasPreviousScan(true)
    }
  }, [])

  const loadPreviousScan = async () => {
    const savedProjectId = localStorage.getItem('codesensex_project')
    if (savedProjectId && savedProjectId !== 'demo' && savedProjectId !== '') {
      await loadData(savedProjectId)
    }
  }

  const queueAndScan = async () => {
    if (!sourceRef || !sourceRef.trim()) {
      setScanStatus('Please enter a GitHub URL')
      setTimeout(() => setScanStatus(''), 3000)
      return
    }
    
    setLoading(true)
    setScanStatus('Queuing repository...')
    try {
      console.log('Queueing repo:', sourceRef)
      const queued = await queueGithubRepo(sourceRef.trim())
      console.log('Queue response:', queued)
      
      if (queued.error) {
        throw new Error(queued.error)
      }
      
      if (queued.project_id) {
        updateProjectId(queued.project_id)
        setScanStatus('Cloning and analyzing repository... This may take 1-2 minutes.')
        
        console.log('Starting scan for project:', queued.project_id)
        const scanResult = await startScan(queued.project_id)
        console.log('Scan result:', scanResult)
        
        if (scanResult.error) {
          throw new Error(scanResult.error)
        }
        
        const filesFound = scanResult.files_analyzed || scanResult.summary?.total_files || 0
        const smellsFound = scanResult.smells_found || scanResult.summary?.total_smells || 0
        
        setScanStatus(`✓ Found ${filesFound} files, ${smellsFound} issues. Loading results...`)
        await loadData(queued.project_id)
        setScanStatus(`✓ Analysis complete! ${filesFound} files analyzed.`)
        setTimeout(() => setScanStatus(''), 5000)
      } else {
        throw new Error('No project ID returned')
      }
    } catch (err) {
      console.error('Scan error:', err)
      setScanStatus(`❌ Error: ${err.message}`)
      setTimeout(() => setScanStatus(''), 8000)
    } finally {
      setLoading(false)
    }
  }

  const handleExportReport = async () => {
    if (!projectId || projectId === 'demo') {
      alert('Please scan a repository first before exporting.')
      return
    }
    try {
      const blob = await exportReport(projectId, ['summary', 'risks', 'smells'])
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `codesensex-report-${projectId}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Export failed:', err)
      alert('Export failed. Please try again.')
    }
  }

  const riskByFolder = risks.map(r => ({
    folder: r.path.split('/').slice(0, -1).join('/') || '/',
    risk: r.risk_score
  }))

  const smellDistribution = [
    { name: 'Critical', value: summary.critical || 0, fill: '#ef4444' },
    { name: 'High', value: summary.high || 0, fill: '#f97316' },
    { name: 'Medium', value: Math.max(0, risks.length - ((summary.critical || 0) + (summary.high || 0))), fill: '#eab308' }
  ].filter(d => d.value > 0)

  const qualityScore = Math.max(0, 100 - (summary.avg_risk || 0))

  return (
    <div className="space-y-6">
      {/* Hero Section - Clean & Focused */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="text-center py-6"
      >
        <h1 className="text-4xl md:text-5xl font-bold text-[var(--text-primary)] mb-3">
          Code<span className="text-[var(--accent-primary)]">Sense</span>X
        </h1>
        <p className="text-[var(--text-secondary)] text-base max-w-xl mx-auto">
          Intelligent Code Quality & Bug Risk Analyzer powered by AI + NLP
        </p>
      </motion.div>

      {/* Input Section - Clean card */}
      <GlassCard className="max-w-3xl mx-auto" delay={0.1}>
        <div className="flex flex-col md:flex-row gap-3">
          <GlassInput
            value={sourceRef}
            onChange={e => setSourceRef(e.target.value)}
            placeholder="Enter GitHub URL or paste repo link..."
            className="flex-1"
            icon="🔗"
          />
          <div className="flex gap-2">
            <GradientButton onClick={queueAndScan} size="md">
              🚀 Scan Repository
            </GradientButton>
            {scanned && (
              <GradientButton onClick={() => loadData(projectId)} variant="secondary" size="md">
                🔄 Refresh
              </GradientButton>
            )}
          </div>
        </div>
        <div className="mt-3 flex items-center gap-4 text-sm text-[var(--text-secondary)] flex-wrap">
          {projectId && <span>Project: <code className="text-[var(--accent-tertiary)] px-2 py-0.5 rounded-md bg-[var(--accent-primary)]/10 font-mono text-xs">{projectId}</code></span>}
          {scanned && <span className="text-[var(--accent-primary)] flex items-center gap-1.5"><span className="inline-block w-1.5 h-1.5 rounded-full bg-[var(--accent-primary)]"></span> Scanned</span>}
          {scanStatus && <span className="text-amber-400">{scanStatus}</span>}
          {hasPreviousScan && !scanned && (
            <button 
              onClick={loadPreviousScan}
              className="text-[var(--accent-primary)] hover:text-[var(--accent-tertiary)] transition-colors flex items-center gap-1.5 text-sm"
            >
              ← Load previous scan results
            </button>
          )}
        </div>
      </GlassCard>

      {loading && (
        <div className="text-center py-12">
          <Loader />
          {scanStatus && <p className="mt-4 text-[var(--text-secondary)]">{scanStatus}</p>}
        </div>
      )}

      {/* Empty State - Clean & focused */}
      {!scanned && !loading && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="text-center py-20"
        >
          <div className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-[var(--bg-secondary)] border border-[var(--border-subtle)] flex items-center justify-center text-3xl">
            🔍
          </div>
          <h3 className="text-xl font-semibold text-[var(--text-primary)] mb-2">No Repository Scanned</h3>
          <p className="text-[var(--text-secondary)] max-w-md mx-auto mb-8 text-sm">
            Enter a GitHub repository URL above and click "Scan Repository" to analyze code quality, detect bugs, and get AI-powered refactoring suggestions.
          </p>
          <div className="flex flex-col items-center gap-3">
            <p className="text-xs text-[var(--text-muted)] uppercase tracking-wide">Supported formats</p>
            <div className="flex flex-wrap justify-center gap-2">
              <code className="px-3 py-1.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-[var(--text-secondary)] text-xs font-mono">https://github.com/user/repo</code>
              <code className="px-3 py-1.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-[var(--text-secondary)] text-xs font-mono">github.com/user/repo</code>
              <code className="px-3 py-1.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-[var(--text-secondary)] text-xs font-mono">user/repo</code>
            </div>
          </div>
        </motion.div>
      )}

      <AnimatePresence>
        {scanned && !loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-6"
          >
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard label="Quality Score" value={`${qualityScore}%`} icon="⭐" color="purple" delay={0.1} />
              <StatCard label="Files Analyzed" value={metrics.length} icon="📁" color="blue" delay={0.2} />
              <StatCard label="Critical Issues" value={summary.critical} icon="🔥" color="red" delay={0.3} />
              <StatCard label="High Risk" value={summary.high} icon="⚠️" color="orange" delay={0.4} />
            </div>

            {/* Main Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Risk Heatmap / Top Files */}
              <GlassCard delay={0.2}>
                <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                  <span className="text-2xl">🎯</span> Top Risky Files
                </h2>
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={risks} layout="vertical" barSize={20}>
                      <XAxis type="number" stroke="#6b7280" />
                      <YAxis dataKey="path" type="category" width={120} tick={{ fill: '#9ca3af', fontSize: 12 }} />
                      <Tooltip content={<CustomTooltip />} />
                      <Bar
                        dataKey="risk_score"
                        radius={[0, 8, 8, 0]}
                        fill="url(#riskGradient)"
                      />
                      <defs>
                        <linearGradient id="riskGradient" x1="0" y1="0" x2="1" y2="0">
                          <stop offset="0%" stopColor="#ef4444" />
                          <stop offset="100%" stopColor="#f97316" />
                        </linearGradient>
                      </defs>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </GlassCard>

              {/* Complexity Chart */}
              <GlassCard delay={0.3}>
                <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                  <span className="text-2xl">📊</span> Complexity Distribution
                </h2>
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={metrics}>
                      <defs>
                        <linearGradient id="complexityGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#06b6d4" stopOpacity={0.8} />
                          <stop offset="100%" stopColor="#06b6d4" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <XAxis dataKey="path" hide />
                      <YAxis stroke="#6b7280" />
                      <Tooltip content={<CustomTooltip />} />
                      <Area
                        type="monotone"
                        dataKey="cyclomatic_max"
                        stroke="#06b6d4"
                        strokeWidth={3}
                        fill="url(#complexityGradient)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </GlassCard>
            </div>

            {/* Second Row */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Quality Gauge */}
              <GlassCard delay={0.4} className="flex flex-col items-center justify-center">
                <h2 className="text-xl font-bold mb-6">Code Quality</h2>
                <ProgressRing
                  value={qualityScore}
                  size={160}
                  strokeWidth={12}
                  color={qualityScore > 70 ? '#22c55e' : qualityScore > 40 ? '#eab308' : '#ef4444'}
                />
                <p className="mt-4 text-gray-400">
                  {qualityScore > 70 ? 'Excellent' : qualityScore > 40 ? 'Needs Improvement' : 'Critical'}
                </p>
              </GlassCard>

              {/* Smell Distribution */}
              <GlassCard delay={0.5}>
                <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                  <span className="text-2xl">🧪</span> Issue Breakdown
                </h2>
                <div className="h-56">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={smellDistribution}
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={80}
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {smellDistribution.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="flex justify-center gap-4 mt-2">
                  {smellDistribution.map((d, i) => (
                    <div key={i} className="flex items-center gap-2 text-sm">
                      <span className="w-3 h-3 rounded-full" style={{ backgroundColor: d.fill }}></span>
                      <span className="text-gray-400">{d.name}</span>
                    </div>
                  ))}
                </div>
              </GlassCard>

              {/* Risk by Folder */}
              <GlassCard delay={0.6}>
                <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                  <span className="text-2xl">📂</span> Risk by Folder
                </h2>
                <div className="h-56">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={riskByFolder}>
                      <XAxis dataKey="folder" stroke="#6b7280" tick={{ fill: '#9ca3af', fontSize: 11 }} />
                      <YAxis stroke="#6b7280" />
                      <Tooltip content={<CustomTooltip />} />
                      <Bar dataKey="risk" radius={[8, 8, 0, 0]} fill="url(#folderGradient)" />
                      <defs>
                        <linearGradient id="folderGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#f97316" />
                          <stop offset="100%" stopColor="#ea580c" />
                        </linearGradient>
                      </defs>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </GlassCard>
            </div>

            {/* Metrics Table */}
            <GlassCard delay={0.7}>
              <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                <span className="text-2xl">📋</span> File Metrics
              </h2>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-white/10">
                      <th className="text-left py-4 px-4 text-gray-400 font-medium">File Path</th>
                      <th className="text-right py-4 px-4 text-gray-400 font-medium">LOC</th>
                      <th className="text-right py-4 px-4 text-gray-400 font-medium">Complexity</th>
                      <th className="text-center py-4 px-4 text-gray-400 font-medium">Risk</th>
                    </tr>
                  </thead>
                  <tbody>
                    {metrics.map((m, i) => {
                      const risk = risks.find(r => r.path === m.path)
                      return (
                        <motion.tr
                          key={i}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 0.1 * i }}
                          onClick={() => onFileSelect && onFileSelect({ ...m, ...risk })}
                          className="border-b border-white/5 hover:bg-white/5 transition-colors cursor-pointer"
                        >
                          <td className="py-4 px-4">
                            <span className="text-cyan-400">📄</span>
                            <span className="ml-2">{m.path}</span>
                          </td>
                          <td className="text-right py-4 px-4 font-mono text-gray-300">{m.loc}</td>
                          <td className="text-right py-4 px-4">
                            <span className={`font-mono ${m.cyclomatic_max > 10 ? 'text-red-400' : m.cyclomatic_max > 5 ? 'text-yellow-400' : 'text-emerald-400'}`}>
                              {m.cyclomatic_max}
                            </span>
                          </td>
                          <td className="text-center py-4 px-4">
                            {risk && <RiskBadge tier={risk.tier} />}
                          </td>
                        </motion.tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </GlassCard>

            {/* Technical Debt Estimate */}
            <GlassCard delay={0.8} glow>
              <div className="flex flex-col md:flex-row items-center justify-between gap-6">
                <div>
                  <h2 className="text-2xl font-bold gradient-text mb-2">Technical Debt Estimate</h2>
                  <p className="text-gray-400">Based on complexity, code smells, and risk factors</p>
                </div>
                <div className="text-center">
                  <p className="text-5xl font-black text-white">{Math.round(summary.avg_risk * 0.8 + metrics.length * 0.5)}h</p>
                  <p className="text-gray-400 text-sm mt-1">Estimated remediation time</p>
                </div>
                <GradientButton size="lg" onClick={handleExportReport}>
                  📥 Export Report
                </GradientButton>
              </div>
            </GlassCard>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Empty State */}
      {!scanned && !loading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-20"
        >
          <div className="text-8xl mb-6 animate-float">🔍</div>
          <h2 className="text-2xl font-bold text-gray-300 mb-2">Ready to Analyze</h2>
          <p className="text-gray-500 max-w-md mx-auto">
            Enter a GitHub repository URL above and click "Scan Repository" to begin the analysis.
          </p>
        </motion.div>
      )}
    </div>
  )
}
