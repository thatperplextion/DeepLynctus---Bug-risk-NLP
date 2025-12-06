import React, { useState } from 'react'
import { createRoot } from 'react-dom/client'
import { motion, AnimatePresence } from 'framer-motion'
import './index.css'
import Overview from './pages/Overview'
import FileDetail from './pages/FileDetail'
import CodeSmells from './pages/CodeSmells'
import Heatmap from './pages/Heatmap'
import DependencyGraph from './pages/DependencyGraph'
import TrendsDashboard from './pages/TrendsDashboard'
import ChatBot from './pages/ChatBot'
import BackendStatus from './components/BackendStatus'

const NAV_ITEMS = [
  { id: 'overview', label: 'Overview', icon: '📊' },
  { id: 'heatmap', label: 'Heatmap', icon: '🗺️' },
  { id: 'smells', label: 'Smells', icon: '🧪' },
  { id: 'dependencies', label: 'Graph', icon: '🔗' },
  { id: 'trends', label: 'Trends', icon: '📈' },
  { id: 'chat', label: 'AI Chat', icon: '🤖' }
]

function App(){
  const [currentPage, setCurrentPage] = useState('overview')
  const [selectedFile, setSelectedFile] = useState(null)
  const [projectId, setProjectId] = useState('')  // Start empty, only set after scan

  const handleFileSelect = (file) => {
    setSelectedFile(file)
    setCurrentPage('file-detail')
  }

  const handleBackFromFile = () => {
    setSelectedFile(null)
    setCurrentPage('overview')
  }

  const handleProjectChange = (newProjectId) => {
    setProjectId(newProjectId)
    localStorage.setItem('deeplynctus_project', newProjectId)
  }

  return (
    <div className="min-h-screen p-4 md:p-8 lg:p-10 max-w-7xl mx-auto relative">
      {/* Floating Orbs Background Animation */}
      <div className="floating-orbs">
        <div className="orb orb-1"></div>
        <div className="orb orb-2"></div>
        <div className="orb orb-3"></div>
      </div>
      
      {/* Header - Clean GitHub/ChatGPT style with glass effect */}
      <motion.header
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="flex items-center justify-between mb-8 pb-4 px-6 py-4 rounded-2xl glass-header relative"
      >
        <div className="flex items-center gap-3">
          <div 
            onClick={() => { setCurrentPage('overview'); setSelectedFile(null); }}
            className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center text-lg cursor-pointer hover:scale-105 transition-all shadow-lg shadow-emerald-500/20"
          >
            🧠
          </div>
          <span className="text-lg font-semibold text-[var(--text-primary)] tracking-tight">Deep Lynctus</span>
        </div>

        {/* Navigation - Premium glass with animated border */}
        <nav className="hidden md:flex items-center gap-1.5 nav-glass-container nav-animated-border rounded-xl px-1.5 py-1.5">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              onClick={() => { setCurrentPage(item.id); setSelectedFile(null); }}
              className={`nav-btn-fast ${
                currentPage === item.id ? 'active' : ''
              }`}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="relative z-10">{item.label}</span>
            </button>
          ))}
        </nav>

        <BackendStatus />
      </motion.header>

      {/* Main Content */}
      <main>
        <AnimatePresence mode="wait">
          {currentPage === 'overview' && (
            <motion.div
              key="overview"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
            >
              <Overview projectId={projectId} onFileSelect={handleFileSelect} onProjectChange={handleProjectChange} />
            </motion.div>
          )}
          {currentPage === 'file-detail' && selectedFile && (
            <motion.div
              key="file-detail"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
            >
              <FileDetail file={selectedFile} onBack={handleBackFromFile} projectId={projectId} />
            </motion.div>
          )}
          {currentPage === 'heatmap' && (
            <motion.div
              key="heatmap"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
            >
              <Heatmap projectId={projectId} onFileSelect={handleFileSelect} />
            </motion.div>
          )}
          {currentPage === 'smells' && (
            <motion.div
              key="smells"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
            >
              <CodeSmells projectId={projectId} onFileSelect={handleFileSelect} />
            </motion.div>
          )}
          {currentPage === 'dependencies' && (
            <motion.div
              key="dependencies"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
            >
              <DependencyGraph projectId={projectId} />
            </motion.div>
          )}
          {currentPage === 'trends' && (
            <motion.div
              key="trends"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
            >
              <TrendsDashboard projectId={projectId} />
            </motion.div>
          )}
          {currentPage === 'chat' && (
            <motion.div
              key="chat"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
            >
              <ChatBot projectId={projectId} />
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Footer */}
      <motion.footer
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 }}
        className="mt-16 text-center text-gray-500 text-sm"
      >
        <p>Deep Lynctus • Powered by AI + NLP</p>
      </motion.footer>
    </div>
  )
}

createRoot(document.getElementById('root')).render(<App />)
