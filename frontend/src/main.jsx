import React from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'

function App(){
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold">CodeSenseX</h1>
      <p className="mt-2">Upload a GitHub repo or ZIP and start a scan.</p>
    </div>
  )
}

createRoot(document.getElementById('root')).render(<App />)
