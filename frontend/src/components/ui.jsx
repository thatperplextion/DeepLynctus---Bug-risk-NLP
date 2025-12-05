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
  
  // Optimized buttons using CSS transitions for performance
  if (variant === 'primary') {
    return (
      <button
        onClick={onClick}
        className={`btn-primary-fast ${sizes[size]} ${className}`}
      >
        <span className="relative z-10 flex items-center justify-center gap-2">
          {children}
        </span>
      </button>
    )
  }
  
  if (variant === 'secondary') {
    return (
      <button
        onClick={onClick}
        className={`btn-secondary-fast ${sizes[size]} ${className}`}
      >
        <span className="relative z-10">{children}</span>
      </button>
    )
  }
  
  // Danger variant - optimized with CSS
  return (
    <button
      onClick={onClick}
      className={`${sizes[size]} bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-600 hover:to-orange-600 rounded-xl font-semibold text-white shadow-lg btn-danger-fast ${className}`}
    >
      {children}
    </button>
  )
}

export function ThinButton({ children, onClick, className = '', active = false }) {
  return (
    <button
      onClick={onClick}
      className={`btn-thin-fast ${active ? 'active' : ''} ${className}`}
    >
      {children}
    </button>
  )
}

export function GlassInput({ value, onChange, placeholder, className = '', icon }) {
  return (
    <div className={`search-glass-container-fast relative ${className}`}>
      {icon && (
        <span className="glass-icon absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 z-10">
          {icon}
        </span>
      )}
      <input
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className={`search-glass-input-fast w-full ${icon ? 'pl-12' : 'pl-4'} pr-4 py-3.5`}
      />
    </div>
  )
}

export function StatCard({ label, value, icon, trend, color = 'purple', delay = 0 }) {
  const colors = {
    purple: 'bg-[var(--accent-primary)]',
    pink: 'bg-pink-500',
    blue: 'bg-blue-500',
    green: 'bg-emerald-500',
    orange: 'bg-orange-500',
    red: 'bg-red-500'
  }
  
  const textColors = {
    purple: 'text-[var(--accent-tertiary)]',
    pink: 'text-pink-400',
    blue: 'text-blue-400',
    green: 'text-emerald-400',
    orange: 'text-orange-400',
    red: 'text-red-400'
  }
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay }}
      className="glass rounded-xl p-5 glass-hover"
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-[var(--text-secondary)] text-sm font-medium">{label}</p>
          <p className={`text-2xl font-bold mt-1 ${textColors[color]}`}>{value}</p>
          {trend && (
            <p className={`text-xs mt-1 ${trend > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
              {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}%
            </p>
          )}
        </div>
        <div className={`w-12 h-12 rounded-xl ${colors[color]} flex items-center justify-center text-xl`}>
          {icon}
        </div>
      </div>
    </motion.div>
  )
}

export function RiskBadge({ tier }) {
  const styles = {
    Critical: 'bg-red-500/15 text-red-400 border-red-500/25',
    High: 'bg-orange-500/15 text-orange-400 border-orange-500/25',
    Medium: 'bg-amber-500/15 text-amber-400 border-amber-500/25',
    Low: 'bg-[var(--accent-primary)]/15 text-[var(--accent-tertiary)] border-[var(--accent-primary)]/25'
  }
  return (
    <span className={`px-2.5 py-1 rounded-md text-xs font-medium border ${styles[tier] || styles.Low}`}>
      {tier}
    </span>
  )
}

export function ProgressRing({ value, size = 100, strokeWidth = 8, color = 'var(--accent-primary)' }) {
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
          stroke="var(--border-subtle)"
          strokeWidth={strokeWidth}
          fill="none"
        />
        <motion.circle
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth={strokeWidth}
          fill="none"
          strokeDasharray={circumference}
          strokeLinecap="round"
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-xl font-semibold text-[var(--text-primary)]">{value}</span>
      </div>
    </div>
  )
}

export function Loader() {
  return (
    <div className="flex items-center justify-center py-8">
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 0.8, repeat: Infinity, ease: 'linear' }}
        className="w-8 h-8 border-2 border-[var(--border-default)] border-t-[var(--accent-primary)] rounded-full"
      />
    </div>
  )
}
