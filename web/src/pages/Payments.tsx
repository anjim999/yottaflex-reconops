import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Badge, Card, ErrorBox, IdLink, KV, Loading, PageHeader, Table } from '../components/ui'
import { qs, useApi } from '../lib/api'
import { label, money, when } from '../lib/format'

function Search() {
  const [q, setQ] = useState('')
  const nav = useNavigate()
  const results = useApi<any[]>(`/api/payments${qs(q ? { q } : { flagged: true })}`)
  return (
    <Card pad={false} title={q ? 'Search results' : 'Payments with issues'} subtitle={q ? undefined : 'Start here, or search by payment, customer or merchant id.'}
      action={<input value={q} onChange={(e) => setQ(e.target.value)} placeholder="PAY-…, CUS-… or MER-…" className="w-64 rounded-lg border border-slate-200 px-2.5 py-1.5 text-sm outline-none focus:border-indigo-300 focus:ring-4 focus:ring-indigo-100" />}>
      <ErrorBox error={results.error} />
      <Table rowKey="payment_id" rows={results.data ?? []} onRow={(r) => nav(`/payments/${r.payment_id}`)} cols={[
        { key: 'payment_id', header: 'Payment', render: (r) => <span className="id">{r.payment_id}</span> },
        { key: 'status', header: 'Status', render: (r) => <Badge value={r.status} /> },
        { key: 'amount', header: 'Amount', className: 'text-right tabular-nums', render: (r) => money(r.amount_minor, r.currency) },
        { key: 'merchant_id', header: 'Merchant', render: (r) => <span className="id">{r.merchant_id}</span> },
        { key: 'created_at', header: 'Created', render: (r) => when(r.created_at) },
      ]} />
    </Card>
  )
}

function Timeline({ id }: { id: string }) {
  const { data: d, error, loading } = useApi(`/api/payments/${id}`)
  if (error) return <ErrorBox error={error} />
  if (loading || !d) return <Loading />
  const o = d.order
  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-4">
        <div className="rounded-2xl border border-slate-200/80 bg-white p-5 md:col-span-2">
          <div className="id text-slate-500">{o.payment_id}</div>
          <div className="mt-1 text-2xl font-semibold tabular-nums">{money(o.amount_minor, o.currency)}</div>
          <div className="mt-2 flex items-center gap-2 text-sm"><Badge value={o.status} /><span className="text-slate-500">{label(o.payment_method)} · {o.customer_ref}</span></div>
        </div>
        <div className="rounded-2xl border border-slate-200/80 bg-white p-5 text-sm"><div className="text-slate-500">Captured</div><div className="text-lg font-semibold tabular-nums">{money(o.captured_amount_minor, o.currency)}</div></div>
        <div className="rounded-2xl border border-slate-200/80 bg-white p-5 text-sm"><div className="text-slate-500">Refunded</div><div className="text-lg font-semibold tabular-nums">{money(o.refunded_amount_minor, o.currency)}</div></div>
      </div>

      {d.exceptions.length > 0 && (
        <div className="rounded-2xl border border-rose-200 bg-rose-50/70 p-5 text-sm">
          <div className="mb-2 font-medium text-rose-800">Issues on this payment</div>
          {d.exceptions.map((x: any) => (
            <div key={x.exception_id} className="flex flex-wrap items-center gap-2 py-1">
              <Badge value={x.severity} /><span className="font-medium">{label(x.exception_type)}</span><Badge value={x.status} />
              <span className="text-rose-900/70">{x.description}</span>
            </div>
          ))}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Order status history" subtitle="Append-only; each change cites the event that caused it.">
          <ol className="relative ml-1.5 space-y-4 border-l border-slate-200 pl-5 text-sm">
            {d.status_history.map((h: any) => (
              <li key={h.history_id}>
                <span className="absolute -left-[6.5px] mt-1.5 h-3 w-3 rounded-full border-2 border-white bg-indigo-500 ring-1 ring-indigo-200" />
                <div className="flex items-center gap-2"><Badge value={h.to_status} /><span className="text-xs text-slate-500">{when(h.changed_at)}</span></div>
                {h.cause_event_id && <div className="text-xs text-slate-400">caused by <IdLink id={h.cause_event_id} /></div>}
              </li>
            ))}
          </ol>
        </Card>
        <Card title="Merchant">
          <KV data={d.merchant} keys={['merchant_id', 'legal_name', 'country', 'settlement_currency', 'risk_tier', 'settlement_delay_days']} />
          <div className="mt-4 border-t border-slate-100 pt-3">
            <div className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">Fee schedule (effective-dated)</div>
            {d.fee_schedules.map((f: any) => (
              <div key={f.fee_schedule_id} className="flex justify-between py-0.5 text-sm"><span className="text-slate-600">v{f.version} · {f.effective_from} → {f.effective_to ?? 'current'}</span><span className="num">{(f.fee_rate_bps / 100).toFixed(2)}% + {money(f.fixed_fee_minor, d.merchant.settlement_currency)}</span></div>
            ))}
          </div>
        </Card>
      </div>

      <Card pad={false} title="Processor events" subtitle="Deduplicated by event id; re-delivered webhooks are counted but ignored.">
        <Table rowKey="event_id" rows={d.events} cols={[
          { key: 'event_id', header: 'Event', render: (r) => <IdLink id={r.event_id} /> },
          { key: 'event_type', header: 'Type' },
          { key: 'amount', header: 'Amount', className: 'text-right tabular-nums', render: (r) => money(r.amount_minor, r.currency) },
          { key: 'occurred_at', header: 'Occurred', render: (r) => when(r.occurred_at) },
          { key: 'deliveries', header: 'Deliveries', render: (r) => {
            const n = d.deliveries.filter((x: any) => x.event_id === r.event_id).length
            return n > 1 ? <span className="text-amber-700">{n} (duplicate ignored)</span> : n
          } },
        ]} />
      </Card>

      <Card pad={false} title="Settlement" subtitle="Fee from the merchant fee schedule in force on the capture date.">
        <Table rowKey="settlement_line_id" rows={d.settlement_lines} cols={[
          { key: 'settlement_line_id', header: 'Line', render: (r) => <IdLink id={r.settlement_line_id} /> },
          { key: 'line_type', header: 'Type' },
          { key: 'gross', header: 'Gross', className: 'text-right tabular-nums', render: (r) => money(r.gross_minor, r.currency) },
          { key: 'fee', header: 'Fee', className: 'text-right tabular-nums', render: (r) => money(r.fee_minor, r.currency) },
          { key: 'net', header: 'Net', className: 'text-right tabular-nums', render: (r) => money(r.net_minor, r.currency) },
          { key: 'batch_id', header: 'Batch', render: (r) => <IdLink id={r.batch_id} /> },
          { key: 'date', header: 'Settled', render: (r) => d.batches.find((b: any) => b.batch_id === r.batch_id)?.settlement_date ?? '—' },
        ]} />
      </Card>
    </div>
  )
}

export default function Payments() {
  const { id } = useParams()
  return (
    <>
      <PageHeader eyebrow="Customer / account holder" title={id ? 'Payment timeline' : 'Payment lookup'} subtitle="One payment followed across the order, processor events, webhooks, settlement and fees — with any issue explained." />
      {id ? <Timeline id={id} /> : <Search />}
    </>
  )
}
