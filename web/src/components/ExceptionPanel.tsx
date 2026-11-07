import { useState } from 'react'
import { api, useApi, type ExceptionDetail } from '../lib/api'
import { label, money, when } from '../lib/format'
import { useRole } from './Layout'
import { useToast } from './Toast'
import { Badge, ErrorBox, IdLink, Loading } from './ui'

const ACTIONS = {
  START_REVIEW: { text: 'Start review', style: 'border border-slate-300 bg-white text-slate-700 hover:bg-slate-50' },
  ESCALATE: { text: 'Escalate to risk', style: 'border border-rose-200 bg-rose-50 text-rose-700 hover:bg-rose-100' },
  RESOLVE: { text: 'Resolve', style: 'bg-indigo-600 text-white shadow-sm hover:bg-indigo-700' },
}
const ROLE_FOR = { START_REVIEW: 'OPS_ANALYST', ESCALATE: 'OPS_ANALYST' } as const

/** Exception detail with append-only workflow actions. */
export default function ExceptionPanel({ id, onChange, onClose }: { id: string; onChange?: () => void; onClose?: () => void }) {
  const { data: x, error, loading, reload } = useApi<ExceptionDetail>(`/api/exceptions/${id}`)
  const { role } = useRole()
  const toast = useToast()
  const [notes, setNotes] = useState('')
  const [busy, setBusy] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  async function act(action: keyof typeof ACTIONS) {
    setBusy(true)
    setActionError(null)
    try {
      const r = await api<ExceptionDetail>(`/api/exceptions/${id}/actions`, { method: 'POST', body: JSON.stringify({ action, actor_role: role, notes: notes || undefined }) })
      setNotes('')
      toast(`${id} → ${label(r.status)}`)
      reload()
      onChange?.()
    } catch (e: any) {
      setActionError(e.message)
      toast(e.message, 'err')
    } finally {
      setBusy(false)
    }
  }

  if (loading && !x) return <Loading rows={6} />
  if (error) return <ErrorBox error={error} />
  if (!x) return null
  const related = (x.related_ids ?? '').split('|').filter(Boolean)
  const blocked = (a: keyof typeof ACTIONS) =>
    (a in ROLE_FOR && role !== ROLE_FOR[a as 'START_REVIEW']) || (a === 'RESOLVE' && x.owner_role === 'RISK_REVIEWER' && role !== 'RISK_REVIEWER')

  return (
    <div className="space-y-5 text-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="id text-slate-400">{x.exception_id}</div>
          <h3 className="mt-1 text-lg font-semibold tracking-tight text-slate-900">{label(x.exception_type)}</h3>
          <div className="mt-2 flex flex-wrap gap-1.5"><Badge value={x.severity} /><Badge value={x.status} /><Badge value={x.owner_role} /></div>
        </div>
        {onClose && <button onClick={onClose} className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600" aria-label="Close">
          <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth={2}><path d="M6 6l12 12M18 6L6 18" /></svg>
        </button>}
      </div>

      <p className="rounded-xl bg-slate-50 p-3.5 leading-relaxed text-slate-700">{x.description}</p>

      <dl className="grid grid-cols-[max-content_1fr] gap-x-5 gap-y-2">
        <dt className="text-slate-500">Record</dt><dd><IdLink id={x.entity_id} /> <span className="text-xs text-slate-400">{label(x.entity_type)}</span></dd>
        <dt className="text-slate-500">Amount</dt><dd className="font-medium num">{money(x.amount_minor, x.currency)}</dd>
        <dt className="text-slate-500">Rule</dt><dd className="id">{x.rule_id}</dd>
        <dt className="text-slate-500">Detected</dt><dd>{when(x.detected_at)}</dd>
        {related.length > 0 && (<><dt className="text-slate-500">Linked</dt><dd className="flex flex-wrap gap-x-3 gap-y-1">{related.map((r) => <IdLink key={r} id={r} />)}</dd></>)}
      </dl>

      {x.allowed_actions.length > 0 && (
        <div className="rounded-xl border border-indigo-100 bg-gradient-to-b from-indigo-50/70 to-white p-4">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-xs font-semibold text-indigo-900">Take action</span>
            <span className="text-[11px] text-slate-500">as {label(role)}</span>
          </div>
          <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={2} placeholder="Notes — saved with the history row"
            className="w-full rounded-lg border border-slate-200 bg-white p-2.5 text-sm outline-none focus:border-indigo-300 focus:ring-4 focus:ring-indigo-100" />
          <div className="mt-3 flex flex-wrap gap-2">
            {x.allowed_actions.map((a) => (
              <button key={a} disabled={busy || blocked(a)} onClick={() => act(a)} title={blocked(a) ? 'Not permitted for your role (segregation of duties)' : ''}
                className={`rounded-lg px-3.5 py-2 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-40 ${ACTIONS[a].style}`}>
                {ACTIONS[a].text}
              </button>
            ))}
          </div>
          {x.allowed_actions.includes('RESOLVE') && (
            <div className="mt-2.5 text-xs text-slate-500">
              Records resolution <b className="text-slate-700">{label(x.default_resolution)}</b>
              {x.owner_role === 'RISK_REVIEWER' && role !== 'RISK_REVIEWER' && <span className="text-rose-600"> · risk-owned: switch to Risk reviewer to resolve</span>}
            </div>
          )}
          {actionError && <div className="mt-2"><ErrorBox error={actionError} /></div>}
        </div>
      )}

      <div>
        <h4 className="mb-3 text-[11px] font-semibold uppercase tracking-wider text-slate-500">Audit history · append-only</h4>
        <ol className="space-y-0">
          {x.history.map((h, i) => (
            <li key={h.history_id} className="relative flex gap-3 pb-4 last:pb-0">
              {i < x.history.length - 1 && <span className="absolute left-[5px] top-3 h-full w-px bg-slate-200" />}
              <span className="relative mt-1.5 h-[11px] w-[11px] shrink-0 rounded-full border-2 border-white bg-indigo-500 ring-1 ring-indigo-200" />
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2"><Badge value={h.to_status} /><span className="text-xs text-slate-500">{label(h.actor_role)}</span></div>
                <div className="mt-0.5 text-[11px] text-slate-400">{when(h.changed_at)} · <span className="id">{h.history_id}</span></div>
              </div>
            </li>
          ))}
        </ol>
      </div>

      {x.resolution && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50/70 p-4">
          <div className="flex items-center gap-2 font-semibold text-emerald-800">
            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth={2.2}><path d="M5 12l5 5L20 7" /></svg>
            {label(x.resolution.resolution_type)}
          </div>
          <div className="mt-1.5 text-emerald-900">{x.resolution.notes}</div>
          <div className="mt-2 text-xs text-emerald-700">
            <span className="id">{x.resolution.resolution_id}</span> · {label(x.resolution.resolved_by_role)} · {when(x.resolution.resolved_at)} · adjustment <b className="num">{money(x.resolution.adjustment_amount_minor, x.resolution.currency)}</b>
          </div>
        </div>
      )}
    </div>
  )
}
