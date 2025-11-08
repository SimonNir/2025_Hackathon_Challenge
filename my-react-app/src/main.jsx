import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import Circuit2 from './Circuit2.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Circuit2 />
  </StrictMode>,
)
