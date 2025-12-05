import React, { useState } from 'react'
import { createRoot } from 'react-dom/client'
import { motion, AnimatePresence } from 'framer-motion'
import './index.css'
import Overview from './pages/Overview'
import FileDetail from './pages/FileDetail'
import CodeSmells from './pages/CodeSmells'
import Heatmap from './pages/Heatmap'
import BackendStatus from './components/BackendStatus'

const NAV_ITEMS = [
  { id: 'overview', label: 'Overview', icon: '📊' },
  { id: 'heatmap', label: 'Heatmap', icon: '🗺️' },
  { id: 'smells', label: 'Code Smells', icon: '🧪' }
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
    localStorage.setItem('codesensex_project', newProjectId)
  }

  return (
    <div className="min-h-screen p-6 md:p-10">
      {/* Floating orbs background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-cyan-500/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 right-1/3 w-64 h-64 bg-sky-500/10 rounded-full blur-3xl animate-pulse delay-500"></div>
      </div>

      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between mb-8"
      >
        <div className="flex items-center gap-3">
          <div 
            onClick={() => { setCurrentPage('overview'); setSelectedFile(null); }}
            className="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-500 via-cyan-500 to-sky-500 flex items-center justify-center text-xl shadow-lg glow cursor-pointer hover:scale-110 transition-transform"
          >
            🧠
          </div>
          <span className="text-xl font-bold gradient-text">CodeSenseX</span>
        </div>

        {/* Navigation - Optimized for performance */}
        <nav className="hidden md:flex items-center gap-2 nav-glass-container rounded-full px-4 py-2.5">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              onClick={() => { setCurrentPage(item.id); setSelectedFile(null); }}
              className={`nav-btn-fast ${
                currentPage === item.id ? 'active' : ''
              }`}
            >
              <span className="nav-icon mr-2">{item.icon}</span>
              <span>{item.label}</span>
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
        </AnimatePresence>
      </main>

      {/* Footer */}
      <motion.footer
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 }}
        className="mt-16 text-center text-gray-500 text-sm"
      >
        <p>Powered by AI + NLP • Built for better code</p>
      </motion.footer>
    </div>
  )
}

createRoot(document.getElementById('root')).render(<App />)
