import React from 'react'
import { motion } from 'framer-motion'

export function GlassCard({ children, className = '', hover = true, glow = false, delay = 0 }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      whileHover={hover ? { scale: 1.02, y: -5 } : {}}
      className={`glass rounded-2xl p-6 ${hover ? 'glass-hover cursor-pointer' : ''} ${glow ? 'glow' : ''} ${className}`}
    >
      {children}
    </motion.div>
  )
}

export function GradientButton({ children, onClick, className = '', size = 'md', variant = 'primary' }) {
  const sizes = {
    sm: 'px-4 py-2 text-sm',
    md: 'px-6 py-3 text-base',
    lg: 'px-8 py-4 text-lg'
  }
  const variants = {
    primary: 'bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 hover:from-indigo-600 hover:via-purple-600 hover:to-pink-600',
    secondary: 'bg-white/10 hover:bg-white/20 border border-white/20',
    danger: 'bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-600 hover:to-orange-600'
  }
  return (
    <motion.button
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
      className={`${sizes[size]} ${variants[variant]} rounded-xl font-semibold text-white shadow-lg transition-all duration-300 ${className}`}
    >
      {children}
    </motion.button>
  )
}

export function GlassInput({ value, onChange, placeholder, className = '', icon }) {
  return (
    <div className={`relative ${className}`}>
      {icon && <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">{icon}</span>}
      <input
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className={`w-full glass rounded-xl ${icon ? 'pl-12' : 'pl-4'} pr-4 py-3 bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500/50 focus:ring-2 focus:ring-purple-500/20 transition-all duration-300`}
      />
    </div>
  )
}

export function StatCard({ label, value, icon, trend, color = 'purple', delay = 0 }) {
  const colors = {
    purple: 'from-purple-500 to-indigo-500',
    pink: 'from-pink-500 to-rose-500',
    blue: 'from-blue-500 to-cyan-500',
    green: 'from-emerald-500 to-teal-500',
    orange: 'from-orange-500 to-amber-500',
    red: 'from-red-500 to-rose-500'
  }
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, delay }}
      className="glass rounded-2xl p-6 glass-hover"
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-400 text-sm font-medium">{label}</p>
          <p className={`text-3xl font-bold mt-1 bg-gradient-to-r ${colors[color]} bg-clip-text text-transparent`}>{value}</p>
          {trend && (
            <p className={`text-sm mt-1 ${trend > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
              {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}%
            </p>
          )}
        </div>
        <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${colors[color]} flex items-center justify-center text-2xl shadow-lg`}>
          {icon}
        </div>
      </div>
    </motion.div>
  )
}

export function RiskBadge({ tier }) {
  const styles = {
    Critical: 'bg-red-500/20 text-red-400 border-red-500/30',
    High: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    Medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    Low: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
  }
  return (
    <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${styles[tier] || styles.Low}`}>
      {tier}
    </span>
  )
}

export function ProgressRing({ value, size = 120, strokeWidth = 10, color = '#8b5cf6' }) {
  const radius = (size - strokeWidth) / 2
  const circumference = radius * 2 * Math.PI
  const offset = circumference - (value / 100) * circumference
  
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="rgba(255,255,255,0.1)"
          strokeWidth={strokeWidth}
          fill="none"
        />
        <motion.circle
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1, ease: 'easeOut' }}
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth={strokeWidth}
          fill="none"
          strokeDasharray={circumference}
          strokeLinecap="round"
          style={{ filter: `drop-shadow(0 0 10px ${color})` }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-2xl font-bold">{value}</span>
      </div>
    </div>
  )
}

export function Loader() {
  return (
    <div className="flex items-center justify-center py-12">
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
        className="w-12 h-12 border-4 border-purple-500/30 border-t-purple-500 rounded-full"
      />
    </div>
  )
}
