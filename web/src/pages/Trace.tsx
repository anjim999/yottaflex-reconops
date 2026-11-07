import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Badge, Card, Empty, ErrorBox, IdLink, KV, Loading, PageHeader } from '../components/ui'
import { useApi } from '../lib/api'
import { label, money } from '../lib/format'

const EXAMPLES = ['SET-2026-000001', 'BANK-2026-000001', 'STL-SET-2026-000001-001']

function Result({ id }: { id: string }) {
  const { data: d, error, loading } = useApi(`/api/trace/${id}`)
  if (error) return <ErrorBox error={error} />
  if (loading || !d) return <Loading />
  const groups: Record<string, any[]> = {}
  d.matches.forEach((m: any) => (groups[m.match_id] ??= []).push(m))

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card title={<span className="flex items-center gap-2">{label(d.entity_type)} <span className="id text-slate-500">{d.entity_id}</span></span>}
        action={d.recon_status && <Badge value={d.recon_status.recon_status} />}>
        <KV data={d.record} />
        {d.line_summary && <p className="mt-3 text-xs text-slate-500">{d.line_summary.lines} lines · {d.line_summary.captures} captures · {d.line_summary.refunds} refunds</p>}
        {d.recon_status && <p className="mt-3 text-xs text-slate-500">Decided by: <span className="id">{d.recon_status.reason}</span></p>}
      </Card>
      <div className="space-y-6">
        <Card title={`Reconciliation matches (${Object.keys(groups).length})`}>
          {Object.keys(groups).length === 0 ? <Empty>No match — see exceptions.</Empty> : Object.entries(groups).map(([mid, items]) => {
            const m = items[0]
            return (
              <div key={mid} className="mb-3 rounded-xl border border-slate-200 p-4 text-sm last:mb-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="id">{mid}</span><Badge value={m.status} /><Badge value={m.match_type} raw />
                  <span className="text-xs text-slate-500">{label(m.match_level)} · rule {m.rule_id}</span>
                </div>
                <div className="mt-2 grid grid-cols-2 gap-2">
                  {['LEFT', 'RIGHT'].map((side) => (
                    <div key={side}>
                      <div className="text-[11px] uppercase text-slate-400">{side === 'LEFT' ? 'Expected' : 'Observed'}</div>
                      {items.filter((i) => i.side === side).map((i) => <div key={i.entity_id}><IdLink id={i.entity_id} /></div>)}
                      <div className="tabular-nums text-slate-600">{money(side === 'LEFT' ? m.left_amount_minor : m.right_amount_minor, m.currency)}</div>
                    </div>
                  ))}
                </div>
                {m.difference_minor !== 0 && <div className="mt-1 text-xs text-amber-700">Difference {money(m.difference_minor, m.currency)}</div>}
              </div>
            )
          })}
        </Card>
        <Card title={`Exceptions (${d.exceptions.length})`}>
          {d.exceptions.length === 0 ? <Empty>No exceptions reference this record.</Empty> : d.exceptions.map((x: any) => (
            <div key={x.exception_id} className="mb-2 rounded-xl border border-rose-100 bg-rose-50/40 p-4 text-sm">
              <div className="flex flex-wrap items-center gap-2"><span className="id">{x.exception_id}</span><Badge value={x.severity} /><Badge value={x.status} /></div>
              <div className="mt-1 font-medium">{label(x.exception_type)}</div>
              <div className="text-slate-600">{x.description}</div>
            </div>
          ))}
        </Card>
      </div>
    </div>
  )
}

export default function Trace() {
  const { id } = useParams()
  const nav = useNavigate()
  const [q, setQ] = useState(id ?? '')
  return (
    <>
      <PageHeader eyebrow="Traceability" title="Trace explorer" subtitle="Follow any record — event, settlement line, batch, bank line or webhook delivery — to the records it was matched with and every exception that references it." />
      <form onSubmit={(e) => { e.preventDefault(); q && nav(`/trace/${q.trim()}`) }} className="mb-6 flex flex-wrap gap-2">
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="EVT-…, STL-…, SET-…, BANK-…, DLV-…" className="w-80 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-indigo-300 focus:ring-4 focus:ring-indigo-100" />
        <button className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700">Trace</button>
        <span className="flex items-center gap-2 text-xs text-slate-500">Try: {EXAMPLES.map((e) => <IdLink key={e} id={e} />)}</span>
      </form>
      {id && <Result key={id} id={id} />}
    </>
  )
}
