import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { label } from '../lib/format'

export function Card({ title, subtitle, action, children, className = '', pad = true }: {
  title?: ReactNode; subtitle?: ReactNode; action?: ReactNode; children: ReactNode; className?: string; pad?: boolean
}) {
  return (
    <section className={`rounded-2xl border border-slate-200/80 bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)] ${className}`}>
      {(title || action) && (
        <header className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-5 py-3.5">
          <div>
            {title && <h2 className="text-[13px] font-semibold text-slate-800">{title}</h2>}
            {subtitle && <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>}
          </div>
          {action}
        </header>
      )}
      <div className={pad ? 'p-5' : ''}>{children}</div>
    </section>
  )
}

const ACCENT = {
  indigo: 'bg-indigo-50 text-indigo-600', emerald: 'bg-emerald-50 text-emerald-600',
  amber: 'bg-amber-50 text-amber-600', rose: 'bg-rose-50 text-rose-600', sky: 'bg-sky-50 text-sky-600', slate: 'bg-slate-100 text-slate-600',
}

export function Stat({ label: l, value, hint, icon, accent = 'indigo' }: {
  label: string; value: ReactNode; hint?: ReactNode; icon?: string; accent?: keyof typeof ACCENT
}) {
  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
      <div className="flex items-start justify-between gap-3">
        <div className="text-[12px] font-medium text-slate-500">{l}</div>
        {icon && (
          <span className={`flex h-8 w-8 items-center justify-center rounded-lg ${ACCENT[accent]}`}>
            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"><path d={icon} /></svg>
          </span>
        )}
      </div>
      <div className="mt-2 text-[26px] font-semibold leading-none tracking-tight text-slate-900 num">{value}</div>
      {hint && <div className="mt-2 text-xs text-slate-500">{hint}</div>}
    </div>
  )
}

const TONES: Record<string, string> = {
  CRITICAL: 'bg-rose-50 text-rose-700 ring-rose-600/20', HIGH: 'bg-orange-50 text-orange-700 ring-orange-600/20',
  MEDIUM: 'bg-amber-50 text-amber-700 ring-amber-600/20', LOW: 'bg-slate-50 text-slate-600 ring-slate-500/20',
  OPEN: 'bg-sky-50 text-sky-700 ring-sky-600/20', IN_REVIEW: 'bg-violet-50 text-violet-700 ring-violet-600/20',
  ESCALATED: 'bg-rose-50 text-rose-700 ring-rose-600/20', RESOLVED: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  MATCHED: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20', PARTIAL: 'bg-amber-50 text-amber-700 ring-amber-600/20',
  EXCEPTION: 'bg-rose-50 text-rose-700 ring-rose-600/20', IN_TRANSIT: 'bg-sky-50 text-sky-700 ring-sky-600/20',
  PASS: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20', FAIL: 'bg-rose-50 text-rose-700 ring-rose-600/20',
  CAPTURED: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20', REFUNDED: 'bg-slate-50 text-slate-600 ring-slate-500/20',
  PARTIALLY_REFUNDED: 'bg-amber-50 text-amber-700 ring-amber-600/20', FAILED: 'bg-rose-50 text-rose-700 ring-rose-600/20',
  AUTHORIZED: 'bg-sky-50 text-sky-700 ring-sky-600/20', VOIDED: 'bg-slate-50 text-slate-600 ring-slate-500/20',
}
const DOT: Record<string, string> = { CRITICAL: 'bg-rose-500', HIGH: 'bg-orange-500', MEDIUM: 'bg-amber-500', LOW: 'bg-slate-400' }

export function Badge({ value, raw = false }: { value: string | null | undefined; raw?: boolean }) {
  if (!value) return null
  const tone = TONES[value] ?? 'bg-slate-50 text-slate-600 ring-slate-500/20'
  return (
    <span className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2 py-0.5 text-[11px] font-medium ring-1 ring-inset ${tone}`}>
      {DOT[value] && <span className={`h-1.5 w-1.5 rounded-full ${DOT[value]}`} />}
      {raw ? value : label(value)}
    </span>
  )
}

/** Any record id becomes a link into the trace explorer / payment timeline. */
export function IdLink({ id }: { id: string | null | undefined }) {
  if (!id) return <span className="text-slate-400">—</span>
  const to = id.startsWith('PAY-') ? `/payments/${id}` : `/trace/${id}`
  return <Link to={to} onClick={(e) => e.stopPropagation()} className="id text-indigo-600 hover:text-indigo-800 hover:underline">{id}</Link>
}

export function Loading({ rows = 4 }: { rows?: number }) {
  return (
    <div className="space-y-3 p-2" aria-busy>
      {Array.from({ length: rows }).map((_, i) => <div key={i} className="h-4 animate-pulse rounded bg-slate-100" style={{ width: `${90 - i * 12}%` }} />)}
    </div>
  )
}

export function ErrorBox({ error }: { error: string | null }) {
  if (!error) return null
  return <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>
}

export function Empty({ children = 'Nothing here.' }: { children?: ReactNode }) {
  return <div className="px-6 py-10 text-center text-sm text-slate-400">{children}</div>
}

export type Col<T> = { key: string; header: ReactNode; render?: (row: T) => ReactNode; className?: string }

export function Table<T extends Record<string, any> = Record<string, any>>({ rows, cols, onRow, selected, rowKey, accent }: {
  rows: T[]; cols: Col<T>[]; onRow?: (r: T) => void; selected?: string | null; rowKey: string; accent?: (r: T) => string
}) {
  if (!rows.length) return <Empty />
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-[11px] uppercase tracking-wider text-slate-500">
            {cols.map((c) => <th key={c.key} className={`whitespace-nowrap px-3 py-2.5 font-medium first:pl-5 last:pr-5 ${c.className ?? ''}`}>{c.header}</th>)}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {rows.map((r) => (
            <tr key={String(r[rowKey])} onClick={() => onRow?.(r)}
              className={`transition ${onRow ? 'cursor-pointer hover:bg-slate-50' : ''} ${selected === r[rowKey] ? 'bg-indigo-50/70 hover:bg-indigo-50' : ''}`}>
              {cols.map((c, i) => (
                <td key={c.key} className={`px-3 py-2.5 align-middle first:pl-5 last:pr-5 ${c.className ?? ''} ${i === 0 && accent ? `border-l-[3px] ${accent(r)}` : ''}`}>
                  {c.render ? c.render(r) : String(r[c.key] ?? '—')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function KV({ data, keys }: { data: Record<string, any>; keys?: string[] }) {
  return (
    <dl className="grid grid-cols-[max-content_1fr] gap-x-6 gap-y-2 text-sm">
      {(keys ?? Object.keys(data)).map((k) => (
        <div key={k} className="contents">
          <dt className="text-slate-500">{label(k)}</dt>
          <dd className="min-w-0 break-words text-slate-800">
            {typeof data[k] === 'string' && /^(PAY|EVT|DLV|SET|STL|BANK)-/.test(data[k]) ? <IdLink id={data[k]} /> : String(data[k] ?? '—')}
          </dd>
        </div>
      ))}
    </dl>
  )
}

export function PageHeader({ title, subtitle, eyebrow, children }: { title: string; subtitle?: ReactNode; eyebrow?: string; children?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        {eyebrow && <div className="mb-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-indigo-600">{eyebrow}</div>}
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">{title}</h1>
        {subtitle && <p className="mt-1.5 max-w-3xl text-sm text-slate-500">{subtitle}</p>}
      </div>
      {children}
    </div>
  )
}

/** Horizontal 100% stacked bar built from divs (crisp, no chart lib needed). */
export function StackBar({ parts }: { parts: { key: string; value: number; color: string; label: string }[] }) {
  const total = parts.reduce((a, p) => a + p.value, 0) || 1
  return (
    <div className="flex h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
      {parts.filter((p) => p.value > 0).map((p) => (
        <div key={p.key} title={`${p.label}: ${p.value.toLocaleString()}`} className={p.color}
          style={{ width: `${Math.max((p.value / total) * 100, 0.6)}%` }} />
      ))}
    </div>
  )
}

export const SEVERITY_BORDER: Record<string, string> = {
  CRITICAL: 'border-l-rose-500', HIGH: 'border-l-orange-400', MEDIUM: 'border-l-amber-300', LOW: 'border-l-slate-200',
}
