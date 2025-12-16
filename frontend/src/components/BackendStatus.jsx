import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { API_URL } from '../services/api'

export default function BackendStatus(){
  const [status, setStatus] = useState('checking')

  useEffect(()=>{
    const check = async () => {
      try{
        const res = await fetch(`${API_URL}/`)
        const json = await res.json()
        if(json && json.status === 'ok') setStatus('ok')
        else setStatus('error')
      }catch(e){
        setStatus('error')
      }
    }
    check()
    const interval = setInterval(check, 10000)
    return () => clearInterval(interval)
  },[])

  const statusConfig = {
    checking: { color: 'bg-yellow-500', text: 'Connecting...', pulse: true },
    ok: { color: 'bg-emerald-500', text: 'Backend Connected', pulse: false },
    error: { color: 'bg-red-500', text: 'Backend Offline', pulse: true }
  }

  const config = statusConfig[status]

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      className="flex items-center gap-2 glass px-4 py-2 rounded-full"
    >
      <span className="relative flex h-3 w-3">
        {config.pulse && (
          <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${config.color} opacity-75`}></span>
        )}
        <span className={`relative inline-flex rounded-full h-3 w-3 ${config.color}`}></span>
      </span>
      <span className="text-sm text-gray-300">{config.text}</span>
    </motion.div>
  )
}
