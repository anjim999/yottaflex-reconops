import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Layout, { RoleProvider } from './components/Layout'
import { ToastProvider } from './components/Toast'
import './index.css'
import Admin from './pages/Admin'
import Exceptions from './pages/Exceptions'
import Overview from './pages/Overview'
import Payments from './pages/Payments'
import Risk from './pages/Risk'
import Trace from './pages/Trace'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RoleProvider>
      <ToastProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<Overview />} />
            <Route path="exceptions" element={<Exceptions />} />
            <Route path="risk" element={<Risk />} />
            <Route path="payments" element={<Payments />} />
            <Route path="payments/:id" element={<Payments />} />
            <Route path="trace" element={<Trace />} />
            <Route path="trace/:id" element={<Trace />} />
            <Route path="admin" element={<Admin />} />
          </Route>
        </Routes>
      </BrowserRouter>
      </ToastProvider>
    </RoleProvider>
  </StrictMode>,
)
