import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { GlassCard, Loader } from '../components/ui'
import { API_URL } from '../services/api'

// Message bubble component
function MessageBubble({ message, isUser }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-emerald-600/80 text-white rounded-br-sm'
            : 'bg-white/10 text-gray-200 rounded-bl-sm'
        }`}
      >
        {/* Markdown-like formatting */}
        <div className="text-sm leading-relaxed whitespace-pre-wrap">
          {formatMessage(message.content)}
        </div>
        <div className={`text-xs mt-2 ${isUser ? 'text-emerald-200/70' : 'text-gray-500'}`}>
          {message.timestamp ? new Date(message.timestamp).toLocaleTimeString() : ''}
        </div>
      </div>
    </motion.div>
  )
}

// Simple markdown-like formatting
function formatMessage(content) {
  if (!content) return ''
  
  // Split by code blocks and format
  const parts = content.split(/```(\w+)?\n?([\s\S]*?)```/g)
  
  return parts.map((part, i) => {
    // Code blocks (every 3rd element starting from index 2)
    if (i % 3 === 2) {
      return (
        <pre key={i} className="bg-black/30 rounded-lg p-3 my-2 overflow-x-auto text-xs">
          <code>{part}</code>
        </pre>
      )
    }
    
    // Skip language identifier
    if (i % 3 === 1) return null
    
    // Regular text with inline formatting
    return (
      <span key={i}>
        {part.split(/(\*\*[^*]+\*\*)/g).map((segment, j) => {
          if (segment.startsWith('**') && segment.endsWith('**')) {
            return <strong key={j}>{segment.slice(2, -2)}</strong>
          }
          // Handle backticks for inline code
          return segment.split(/(`[^`]+`)/g).map((subseg, k) => {
            if (subseg.startsWith('`') && subseg.endsWith('`')) {
              return (
                <code key={k} className="bg-black/30 px-1.5 py-0.5 rounded text-emerald-300">
                  {subseg.slice(1, -1)}
                </code>
              )
            }
            return subseg
          })
        })}
      </span>
    )
  })
}

// Typing indicator
function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex items-center gap-2 text-gray-500 text-sm"
    >
      <div className="flex gap-1">
        {[0, 1, 2].map(i => (
          <motion.div
            key={i}
            className="w-2 h-2 bg-emerald-500 rounded-full"
            animate={{ y: [0, -5, 0] }}
            transition={{
              duration: 0.6,
              repeat: Infinity,
              delay: i * 0.1
            }}
          />
        ))}
      </div>
      <span>Deep Lynctus is thinking...</span>
    </motion.div>
  )
}

// Quick action buttons
function QuickActions({ onAction }) {
  const actions = [
    { label: '📊 Quality Score', message: "What's my code quality score?" },
    { label: '⚠️ Risky Files', message: 'Which files are most risky?' },
    { label: '🔧 How to Fix', message: 'How can I fix the critical issues?' },
    { label: '📈 Improvements', message: 'What improvements do you suggest?' }
  ]

  return (
    <div className="flex flex-wrap gap-2 mb-4">
      {actions.map((action, i) => (
        <motion.button
          key={i}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => onAction(action.message)}
          className="px-3 py-1.5 bg-white/5 hover:bg-white/10 rounded-full 
                     text-sm text-gray-400 hover:text-white transition-all
                     border border-white/10 hover:border-emerald-500/30"
        >
          {action.label}
        </motion.button>
      ))}
    </div>
  )
}

export default function ChatBot({ projectId }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [isOpen, setIsOpen] = useState(true)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  // Add welcome message on mount
  useEffect(() => {
    if (projectId && projectId !== 'demo' && messages.length === 0) {
      setMessages([{
        role: 'assistant',
        content: `👋 **Hello! I'm Deep Lynctus AI**

I'm your intelligent code review assistant. I've analyzed your project and I'm ready to help you understand:

🔍 **Your Code Quality** - Ask about scores, metrics, and issues
⚠️ **Risk Areas** - Find out which files need attention
🔧 **How to Fix** - Get suggestions for improvements
📈 **Best Practices** - Learn coding standards

Just type your question below or use the quick actions!`,
        timestamp: new Date().toISOString()
      }])
    }
  }, [projectId])

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async (messageText) => {
    if (!messageText.trim() || loading) return
    
    const userMessage = {
      role: 'user',
      content: messageText,
      timestamp: new Date().toISOString()
    }
    
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await fetch(`${API_URL}/chat/${projectId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: messageText })
      })

      if (!response.ok) throw new Error('Failed to get response')
      
      const data = await response.json()
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.response,
        timestamp: data.timestamp
      }])
    } catch (err) {
      console.error('Chat error:', err)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: "I'm having trouble connecting. Please try again in a moment.",
        timestamp: new Date().toISOString()
      }])
    }
    
    setLoading(false)
    inputRef.current?.focus()
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  const clearChat = async () => {
    try {
      await fetch(`${API_URL}/chat/${projectId}`, { method: 'DELETE' })
    } catch (err) {
      console.error('Failed to clear chat:', err)
    }
    setMessages([])
  }

  if (!projectId || projectId === 'demo') {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center py-16"
      >
        <div className="text-6xl mb-4">🤖</div>
        <h2 className="text-xl font-semibold text-gray-300 mb-2">
          AI Code Assistant
        </h2>
        <p className="text-gray-500">
          Analyze a repository to chat with Deep Lynctus AI
        </p>
      </motion.div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="h-[calc(100vh-200px)] flex flex-col"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 
                          flex items-center justify-center text-xl shadow-lg shadow-emerald-500/20">
            🤖
          </div>
          <div>
            <h2 className="font-semibold text-white">Deep Lynctus AI</h2>
            <p className="text-xs text-emerald-400">Code Review Assistant</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={clearChat}
            className="px-3 py-1.5 text-sm text-gray-400 hover:text-white 
                       bg-white/5 hover:bg-white/10 rounded-lg transition-all"
          >
            Clear Chat
          </button>
        </div>
      </div>

      {/* Chat Container */}
      <GlassCard className="flex-1 flex flex-col overflow-hidden p-0">
        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          <AnimatePresence>
            {messages.map((msg, i) => (
              <MessageBubble
                key={i}
                message={msg}
                isUser={msg.role === 'user'}
              />
            ))}
          </AnimatePresence>
          
          {loading && (
            <div className="pl-2">
              <TypingIndicator />
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Quick Actions */}
        {messages.length <= 1 && (
          <div className="px-4 pb-2">
            <QuickActions onAction={sendMessage} />
          </div>
        )}

        {/* Input Area */}
        <div className="p-4 border-t border-white/10">
          <div className="relative flex items-center gap-2">
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask me anything about your code..."
                rows={1}
                className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl
                           text-white placeholder-gray-500 resize-none
                           focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/20
                           transition-all"
                style={{ minHeight: '48px', maxHeight: '120px' }}
              />
            </div>
            
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => sendMessage(input)}
              disabled={!input.trim() || loading}
              className={`p-3 rounded-xl transition-all ${
                input.trim() && !loading
                  ? 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-lg shadow-emerald-500/20'
                  : 'bg-white/10 text-gray-500'
              }`}
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                        d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              )}
            </motion.button>
          </div>
          
          <p className="text-xs text-gray-600 mt-2 text-center">
            Press Enter to send • Shift+Enter for new line
          </p>
        </div>
      </GlassCard>
    </motion.div>
  )
}
