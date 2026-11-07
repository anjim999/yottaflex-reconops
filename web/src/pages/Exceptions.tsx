import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import ExceptionPanel from '../components/ExceptionPanel'
import { Badge, Card, ErrorBox, IdLink, Loading, PageHeader, SEVERITY_BORDER, Table } from '../components/ui'
import { qs, useApi, type Exception } from '../lib/api'
import { label, money, when } from '../lib/format'

const PAGE = 20
const TABS = [
  { value: 'OPEN,IN_REVIEW,ESCALATED', label: 'Unresolved' }, { value: 'OPEN', label: 'Open' },
  { value: 'IN_REVIEW', label: 'In review' }, { value: 'ESCALATED', label: 'Escalated' },
  { value: 'RESOLVED', label: 'Resolved' }, { value: '', label: 'All' },
]

export function ExceptionQueue({ owner, defaultStatus }: { owner?: string; defaultStatus: string }) {
  const [params, setParams] = useSearchParams()
  const status = params.get('status') ?? defaultStatus
  const type = params.get('type') ?? ''
  const severity = params.get('severity') ?? ''
  const q = params.get('q') ?? ''
  const page = Number(params.get('page') ?? 0)
  const [selected, setSelected] = useState<string | null>(params.get('id'))
  const facets = useApi(`/api/exceptions/facets`)
  const list = useApi<{ total: number; items: Exception[] }>(
    `/api/exceptions${qs({ owner, status, type, severity, q: q || params.get('id'), limit: PAGE, offset: page * PAGE })}`)

  const set = (k: string, v: string) => {
    const p = new URLSearchParams(params)
    p.set(k, v)
    if (!v && k !== 'status') p.delete(k)
    if (k !== 'page') p.delete('page')
    p.delete('id')
    setParams(p, { replace: true })
  }
  const types: string[] = (facets.data?.exception_type ?? []).map((f: any) => f.value)
  const total = list.data?.total ?? 0
  const sel = 'rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-sm text-slate-700 outline-none focus:border-indigo-300 focus:ring-4 focus:ring-indigo-100'

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_400px]">
      <Card pad={false}>
        <div className="flex flex-wrap items-center gap-1 border-b border-slate-100 px-4 pt-3">
          {TABS.map((t) => (
            <button key={t.label} onClick={() => set('status', t.value)}
              className={`-mb-px border-b-2 px-3 pb-2.5 text-sm font-medium transition ${status === t.value ? 'border-indigo-600 text-indigo-700' : 'border-transparent text-slate-500 hover:text-slate-800'}`}>
              {t.label}
            </button>
          ))}
        </div>
        <div className="flex flex-wrap items-center gap-2 px-4 py-3">
          <input value={q} onChange={(e) => set('q', e.target.value)} placeholder="Search id, record, description…" className={`${sel} w-64`} />
          <select value={type} onChange={(e) => set('type', e.target.value)} className={sel}>
            <option value="">All types</option>
            {types.map((v) => <option key={v} value={v}>{label(v)}</option>)}
          </select>
          <select value={severity} onChange={(e) => set('severity', e.target.value)} className={sel}>
            <option value="">All severities</option>
            {['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((v) => <option key={v} value={v}>{label(v)}</option>)}
          </select>
          <span className="ml-auto text-xs text-slate-500 num">{total.toLocaleString()} exceptions</span>
        </div>
        <ErrorBox error={list.error} />
        {list.loading && !list.data ? <div className="p-5"><Loading /></div> : (
          <Table<Exception> rowKey="exception_id" rows={list.data?.items ?? []} selected={selected} onRow={(r) => setSelected(r.exception_id)}
            accent={(r) => SEVERITY_BORDER[r.severity]} cols={[
              { key: 'exception_id', header: 'Exception', render: (r) => <span className="id text-slate-600">{r.exception_id}</span> },
              { key: 'exception_type', header: 'Type', render: (r) => <span className="font-medium text-slate-800">{label(r.exception_type)}</span> },
              { key: 'severity', header: 'Severity', render: (r) => <Badge value={r.severity} /> },
              { key: 'status', header: 'Status', render: (r) => <Badge value={r.status} /> },
              { key: 'entity_id', header: 'Record', render: (r) => <IdLink id={r.entity_id} /> },
              { key: 'amount', header: 'Amount', className: 'text-right num', render: (r) => money(r.amount_minor, r.currency) },
              { key: 'status_changed_at', header: 'Updated', className: 'whitespace-nowrap', render: (r) => <span className="text-xs text-slate-500">{when(r.status_changed_at)}</span> },
            ]} />
        )}
        <div className="flex items-center justify-between border-t border-slate-100 px-5 py-3 text-sm text-slate-500">
          <span>Page {page + 1} of {Math.max(1, Math.ceil(total / PAGE))}</span>
          <div className="flex gap-2">
            <button disabled={page === 0} onClick={() => set('page', String(page - 1))} className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 hover:bg-slate-50 disabled:opacity-40">Previous</button>
            <button disabled={(page + 1) * PAGE >= total} onClick={() => set('page', String(page + 1))} className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 hover:bg-slate-50 disabled:opacity-40">Next</button>
          </div>
        </div>
      </Card>
      <div className="xl:sticky xl:top-24 xl:self-start">
        <Card>
          {selected ? <ExceptionPanel key={selected} id={selected} onChange={list.reload} onClose={() => setSelected(null)} />
            : (
              <div className="flex flex-col items-center px-6 py-12 text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-indigo-50 text-indigo-500">
                  <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth={1.8}><path d="M9 12h6m-6 4h6M7 3h7l5 5v11a2 2 0 01-2 2H7a2 2 0 01-2-2V5a2 2 0 012-2z" /></svg>
                </div>
                <div className="mt-3 text-sm font-medium text-slate-700">Select an exception</div>
                <div className="mt-1 text-xs text-slate-500">See the linked records, append-only history and available actions.</div>
              </div>
            )}
        </Card>
      </div>
    </div>
  )
}

export default function Exceptions() {
  return (
    <>
      <PageHeader eyebrow="Operations analyst" title="Exception queue"
        subtitle="Every unmatched or partial record lands here. Start a review, resolve with a recorded resolution, or escalate to risk — each action appends a history row; nothing is overwritten." />
      <ExceptionQueue owner="OPS_ANALYST" defaultStatus="OPEN,IN_REVIEW,ESCALATED" />
    </>
  )
}
