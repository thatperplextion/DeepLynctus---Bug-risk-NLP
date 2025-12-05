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
  
  // Primary uses blob style with next-level 3D animations
  if (variant === 'primary') {
    return (
      <motion.button
        onClick={onClick}
        className={`btn-blob-3d btn-ripple ${sizes[size]} ${className}`}
        whileHover={{ 
          scale: 1.08,
          y: -5,
          rotateX: 5,
          rotateY: -5,
          transition: { type: 'spring', stiffness: 300, damping: 15 }
        }}
        whileTap={{ 
          scale: 0.92, 
          y: 2,
          rotateX: 0,
          rotateY: 0,
        }}
        initial={{ opacity: 0, y: 20, scale: 0.9 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.4, type: 'spring' }}
        style={{ transformStyle: 'preserve-3d', perspective: 1000 }}
      >
        {/* Shine effect */}
        <motion.div 
          className="absolute inset-0 rounded-2xl overflow-hidden pointer-events-none"
          initial={{ opacity: 0 }}
          whileHover={{ opacity: 1 }}
        >
          <motion.div
            className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent"
            initial={{ x: '-100%' }}
            whileHover={{ x: '100%' }}
            transition={{ duration: 0.6, ease: 'easeInOut' }}
          />
        </motion.div>
        
        <motion.span 
          className="relative z-10 flex items-center justify-center gap-2"
          whileHover={{ 
            textShadow: '0 0 20px rgba(255,255,255,0.8)',
          }}
        >
          {children}
        </motion.span>
      </motion.button>
    )
  }
  
  if (variant === 'secondary') {
    return (
      <motion.button
        onClick={onClick}
        className={`btn-magnetic-3d btn-ripple ${sizes[size]} ${className}`}
        whileHover={{ 
          scale: 1.05,
          boxShadow: '0 15px 35px rgba(6, 182, 212, 0.25), inset 0 0 30px rgba(6, 182, 212, 0.1)',
          transition: { type: 'spring', stiffness: 300, damping: 15 }
        }}
        whileTap={{ scale: 0.95 }}
      >
        <span className="relative z-10">{children}</span>
      </motion.button>
    )
  }
  
  // Danger variant
  return (
    <motion.button
      whileHover={{ 
        scale: 1.08, 
        y: -3,
        boxShadow: '0 15px 40px rgba(239, 68, 68, 0.5)' 
      }}
      whileTap={{ scale: 0.95, y: 0 }}
      onClick={onClick}
      className={`${sizes[size]} bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-600 hover:to-orange-600 rounded-xl font-semibold text-white shadow-lg transition-all duration-300 btn-ripple ${className}`}
    >
      {children}
    </motion.button>
  )
}

export function ThinButton({ children, onClick, className = '', active = false }) {
  return (
    <motion.button
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
      className={`btn-thin ${active ? 'active' : ''} ${className}`}
    >
      {children}
    </motion.button>
  )
}

export function GlassInput({ value, onChange, placeholder, className = '', icon }) {
  return (
    <motion.div 
      className={`search-glass-container relative ${className}`}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover="hover"
    >
      {/* Animated border glow */}
      <motion.div 
        className="absolute inset-0 rounded-xl opacity-0 pointer-events-none"
        style={{
          background: 'linear-gradient(90deg, transparent, rgba(6, 182, 212, 0.3), transparent)',
          backgroundSize: '200% 100%',
        }}
        variants={{
          hover: { 
            opacity: 1,
            backgroundPosition: ['0% 0%', '200% 0%'],
            transition: { duration: 1.5, repeat: Infinity, ease: 'linear' }
          }
        }}
      />
      
      {/* Floating particles inside on hover */}
      <motion.div 
        className="absolute inset-0 overflow-hidden rounded-xl pointer-events-none"
        variants={{ hover: { opacity: 1 } }}
        initial={{ opacity: 0 }}
      >
        {[...Array(5)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-1 h-1 bg-cyan-400/40 rounded-full"
            style={{ left: `${20 + i * 15}%`, bottom: '20%' }}
            variants={{
              hover: {
                y: [0, -30, 0],
                opacity: [0, 1, 0],
                transition: { duration: 2, delay: i * 0.2, repeat: Infinity }
              }
            }}
          />
        ))}
      </motion.div>

      {icon && (
        <motion.span 
          className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 z-10"
          variants={{
            hover: { 
              scale: 1.2, 
              rotate: [0, -10, 10, 0],
              color: '#22d3ee',
              transition: { duration: 0.4 }
            }
          }}
        >
          {icon}
        </motion.span>
      )}
      <input
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className={`search-glass-input w-full ${icon ? 'pl-12' : 'pl-4'} pr-4 py-3.5`}
      />
    </motion.div>
  )
}

export function StatCard({ label, value, icon, trend, color = 'purple', delay = 0 }) {
  const colors = {
    purple: 'from-teal-500 to-cyan-500',
    pink: 'from-pink-500 to-rose-500',
    blue: 'from-sky-500 to-blue-500',
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
        className="w-12 h-12 border-4 border-cyan-500/30 border-t-cyan-500 rounded-full"
      />
    </div>
  )
}
