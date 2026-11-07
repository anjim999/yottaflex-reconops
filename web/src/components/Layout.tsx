import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useApi } from '../lib/api'

export type Role = 'OPS_ANALYST' | 'RISK_REVIEWER'
const RoleCtx = createContext<{ role: Role; setRole: (r: Role) => void }>({ role: 'OPS_ANALYST', setRole: () => {} })
export const useRole = () => useContext(RoleCtx)

const NAV = [
  { section: 'Monitor', items: [
    { to: '/', label: 'Overview', icon: 'M4 13h6V4H4zm10 7h6v-9h-6zM4 20h6v-4H4zm10-16v4h6V4z' },
    { to: '/trace', label: 'Trace explorer', icon: 'M10.5 17a6.5 6.5 0 100-13 6.5 6.5 0 000 13zm4.5-2l5 5' },
  ] },
  { section: 'Work queues', items: [
    { to: '/exceptions', label: 'Exception queue', hint: 'Operations analyst', icon: 'M4 6h16M4 12h16M4 18h10' },
    { to: '/risk', label: 'Risk & compliance', hint: 'Risk reviewer', icon: 'M12 3l8 4v5c0 5-3.5 8-8 9-4.5-1-8-4-8-9V7z' },
  ] },
  { section: 'Lookup', items: [
    { to: '/payments', label: 'Payment lookup', hint: 'Customer / account holder', icon: 'M3 6h18v12H3zM3 10h18M7 15h3' },
  ] },
  { section: 'Platform', items: [
    { to: '/admin', label: 'System admin', hint: 'Administrator', icon: 'M12 15a3 3 0 100-6 3 3 0 000 6zm7.4-3a7.4 7.4 0 00-.1-1.2l2-1.6-2-3.4-2.4 1a7 7 0 00-2-1.2L14.5 3h-5l-.4 2.6a7 7 0 00-2 1.2l-2.4-1-2 3.4 2 1.6a7.4 7.4 0 000 2.4l-2 1.6 2 3.4 2.4-1a7 7 0 002 1.2l.4 2.6h5l.4-2.6a7 7 0 002-1.2l2.4 1 2-3.4-2-1.6c.1-.4.1-.8.1-1.2z' },
  ] },
]

export function Icon({ d, className = 'h-4 w-4' }: { d: string; className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={`${className} shrink-0`} fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d={d} />
    </svg>
  )
}

export function RoleProvider({ children }: { children: ReactNode }) {
  const [role, setRole] = useState<Role>(() => {
    try { return (localStorage.getItem('role') as Role) || 'OPS_ANALYST' } catch { return 'OPS_ANALYST' }
  })
  useEffect(() => { try { localStorage.setItem('role', role) } catch { /* storage unavailable */ } }, [role])
  return <RoleCtx.Provider value={{ role, setRole }}>{children}</RoleCtx.Provider>
}

function GlobalSearch() {
  const [q, setQ] = useState('')
  const nav = useNavigate()
  function go(e: React.FormEvent) {
    e.preventDefault()
    const id = q.trim().toUpperCase()
    if (!id) return
    nav(id.startsWith('PAY-') ? `/payments/${id}` : id.startsWith('EXC-') ? `/exceptions?id=${id}&status=` : `/trace/${id}`)
    setQ('')
  }
  return (
    <form onSubmit={go} className="relative w-full max-w-md">
      <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-slate-400"><Icon d="M10.5 17a6.5 6.5 0 100-13 6.5 6.5 0 000 13zm4.5-2l5 5" /></span>
      <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Jump to any ID — PAY-, EVT-, STL-, SET-, BANK-, EXC-…"
        className="w-full rounded-lg border border-slate-200 bg-slate-50 py-2 pl-9 pr-3 text-sm outline-none transition focus:border-indigo-300 focus:bg-white focus:ring-4 focus:ring-indigo-100" />
    </form>
  )
}

function RoleSwitch() {
  const { role, setRole } = useRole()
  const opts: [Role, string][] = [['OPS_ANALYST', 'Ops analyst'], ['RISK_REVIEWER', 'Risk reviewer']]
  return (
    <div className="flex items-center gap-2">
      <span className="hidden text-xs text-slate-500 lg:inline">Acting as</span>
      <div className="flex rounded-lg bg-slate-100 p-0.5">
        {opts.map(([r, l]) => (
          <button key={r} onClick={() => setRole(r)}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition ${role === r ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}>{l}</button>
        ))}
      </div>
    </div>
  )
}

export default function Layout() {
  const { data: health } = useApi<{ backend: string; scale: string }>('/api/health')
  const [open, setOpen] = useState(false)

  return (
    <div className="flex min-h-full">
      <aside className={`fixed inset-y-0 left-0 z-30 flex w-64 flex-col bg-slate-950 text-slate-300 transition-transform md:sticky md:top-0 md:h-screen md:translate-x-0 ${open ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex h-16 items-center gap-3 px-5">
          <img src="/favicon.svg" className="h-8 w-8" alt="" />
          <div>
            <div className="text-[15px] font-semibold tracking-tight text-white">ReconOps</div>
            <div className="text-[11px] text-slate-500">YottaFlex · Payment reconciliation</div>
          </div>
        </div>
        <nav className="flex-1 space-y-5 overflow-y-auto px-3 py-4">
          {NAV.map((g) => (
            <div key={g.section}>
              <div className="px-3 pb-1.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">{g.section}</div>
              {g.items.map((n) => (
                <NavLink key={n.to} to={n.to} end={n.to === '/'} onClick={() => setOpen(false)}
                  className={({ isActive }) => `group flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition ${isActive ? 'bg-indigo-500/15 text-white' : 'hover:bg-white/5 hover:text-white'}`}>
                  {({ isActive }) => (<>
                    <span className={isActive ? 'text-indigo-400' : 'text-slate-500 group-hover:text-slate-300'}><Icon d={n.icon} /></span>
                    <span className="min-w-0">
                      <span className="block font-medium">{n.label}</span>
                      {'hint' in n && n.hint && <span className="block truncate text-[11px] text-slate-500">{n.hint}</span>}
                    </span>
                  </>)}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
        <div className="border-t border-white/5 p-4 text-[11px] text-slate-500">
          <div className="flex items-center gap-2">
            <span className={`h-2 w-2 rounded-full ${health ? 'bg-emerald-400 shadow-[0_0_8px] shadow-emerald-400/60' : 'bg-slate-600'}`} />
            {health ? <span><span className="text-slate-300">{health.backend === 'postgres' ? 'PostgreSQL' : 'SQLite'}</span> · {health.scale} dataset</span> : 'connecting…'}
          </div>
          <div className="mt-1">Seed 20261022 · synthetic data</div>
        </div>
      </aside>
      {open && <div className="fixed inset-0 z-20 bg-slate-900/40 md:hidden" onClick={() => setOpen(false)} />}

      <div className="min-w-0 flex-1">
        <header className="sticky top-0 z-10 flex h-16 items-center gap-3 border-b border-slate-200 bg-white/85 px-4 backdrop-blur md:px-8">
          <button onClick={() => setOpen(true)} className="rounded-md p-2 text-slate-600 hover:bg-slate-100 md:hidden" aria-label="Open menu">
            <Icon d="M4 6h16M4 12h16M4 18h16" className="h-5 w-5" />
          </button>
          <GlobalSearch />
          <div className="ml-auto"><RoleSwitch /></div>
        </header>
        <main className="mx-auto max-w-[1400px] p-4 md:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
