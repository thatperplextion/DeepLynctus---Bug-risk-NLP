import React from 'react'
import { createRoot } from 'react-dom/client'
import { motion } from 'framer-motion'
import './index.css'
import Overview from './pages/Overview'
import BackendStatus from './components/BackendStatus'

function App(){
  return (
    <div className="min-h-screen p-6 md:p-10">
      {/* Floating orbs background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-pink-500/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 right-1/3 w-64 h-64 bg-indigo-500/20 rounded-full blur-3xl animate-pulse delay-500"></div>
      </div>

      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between mb-8"
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center text-xl shadow-lg glow">
            🧠
          </div>
          <span className="text-xl font-bold gradient-text">CodeSenseX</span>
        </div>
        <BackendStatus />
      </motion.header>

      {/* Main Content */}
      <main>
        <Overview />
      </main>

      {/* Footer */}
      <motion.footer
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 }}
        className="mt-16 text-center text-gray-500 text-sm"
      >
        <p>Powered by AI + NLP • Built with ❤️ for better code</p>
      </motion.footer>
    </div>
  )
}

createRoot(document.getElementById('root')).render(<App />)
