import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import { Link } from 'react-router-dom'
import { Badge, Card, ErrorBox, Loading, PageHeader, StackBar, Stat, Table } from '../components/ui'
import { useApi } from '../lib/api'
import { label, money, num, pct } from '../lib/format'

const WORKFLOW = [
  { key: 'OPEN', color: '#0ea5e9' }, { key: 'IN_REVIEW', color: '#8b5cf6' },
  { key: 'ESCALATED', color: '#f43f5e' }, { key: 'RESOLVED', color: '#10b981' },
]
const COVERAGE = [
  { key: 'MATCHED', color: 'bg-emerald-500', label: 'Matched' }, { key: 'PARTIAL', color: 'bg-amber-400', label: 'Partial' },
  { key: 'EXCEPTION', color: 'bg-rose-500', label: 'Exception' }, { key: 'IN_TRANSIT', color: 'bg-sky-400', label: 'In transit' },
  { key: 'OUT_OF_PERIOD', color: 'bg-slate-400', label: 'Out of period' }, { key: 'OUT_OF_SCOPE', color: 'bg-slate-200', label: 'Out of scope' },
]
const SEV_BAR: Record<string, string> = { CRITICAL: 'bg-rose-500', HIGH: 'bg-orange-400', MEDIUM: 'bg-amber-400', LOW: 'bg-slate-300' }
const ICON = {
  link: 'M10 14a4 4 0 005.7 0l3-3a4 4 0 00-5.7-5.7l-1 1M14 10a4 4 0 00-5.7 0l-3 3a4 4 0 005.7 5.7l1-1',
  bank: 'M3 10l9-6 9 6M5 10v8m4-8v8m6-8v8m4-8v8M3 20h18',
  target: 'M12 21a9 9 0 100-18 9 9 0 000 18zm0-5a4 4 0 100-8 4 4 0 000 8zm0-3a1 1 0 100-2 1 1 0 000 2z',
  alert: 'M12 9v4m0 4h.01M10.3 3.9L1.8 18a2 2 0 001.7 3h17a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z',
}

function FlowNode({ title, value, sub, tone = 'slate' }: { title: string; value: number; sub: string; tone?: 'slate' | 'indigo' | 'emerald' }) {
  const ring = { slate: 'border-slate-200', indigo: 'border-indigo-200 bg-indigo-50/40', emerald: 'border-emerald-200 bg-emerald-50/50' }[tone]
  return (
    <div className={`min-w-0 flex-1 rounded-xl border p-4 ${ring}`}>
      <div className="text-[11px] font-medium uppercase tracking-wider text-slate-500">{title}</div>
      <div className="mt-1 text-2xl font-semibold tracking-tight text-slate-900 num">{num(value)}</div>
      <div className="mt-1 text-xs text-slate-500">{sub}</div>
    </div>
  )
}

function FlowArrow({ rate, note, bad }: { rate: string; note?: string; bad?: number }) {
  return (
    <div className="flex shrink-0 flex-col items-center justify-center px-1 py-2 lg:w-28">
      <div className="text-xs font-semibold text-emerald-600 num">{rate}</div>
      <svg viewBox="0 0 80 12" className="my-1 hidden h-3 w-20 text-slate-300 lg:block"><path d="M0 6h74m-6-5l7 5-7 5" fill="none" stroke="currentColor" strokeWidth="1.5" /></svg>
      <svg viewBox="0 0 12 24" className="my-1 h-5 w-3 text-slate-300 lg:hidden"><path d="M6 0v20m-5-6l5 7 5-7" fill="none" stroke="currentColor" strokeWidth="1.5" /></svg>
      {bad ? <Link to="/exceptions?status=" className="text-[11px] font-medium text-rose-600 hover:underline">{bad} exceptions</Link>
        : <span className="text-[11px] text-slate-400">{note ?? 'no breaks'}</span>}
    </div>
  )
}

export default function Overview() {
  const { data, error, loading } = useApi('/api/summary')
  if (error) return <ErrorBox error={error} />
  if (loading || !data) return <Card><Loading rows={8} /></Card>
  const f = data.flow
  const k = data.metrics?.kpis ?? {}
  const det: any[] = data.metrics?.detection ?? []
  const total = det.find((d) => d.exception_type === 'ALL (micro)') ?? {}
  const live: Record<string, number> = Object.fromEntries(data.exceptions_by_status.map((r: any) => [r.k, r.n]))
  const allEx = Object.values(live).reduce((a, b) => a + b, 0)
  const unresolved = allEx - (live.RESOLVED ?? 0)

  const types: Record<string, { type: string; severity: string; total: number; open: number }> = {}
  data.exceptions_by_type_status.forEach((r: any) => {
    const t = (types[r.exception_type] ??= { type: r.exception_type, severity: r.severity, total: 0, open: 0 })
    t.total += r.n
    if (r.status !== 'RESOLVED') t.open += r.n
  })
  const typeRows = Object.values(types).sort((a, b) => b.total - a.total)
  const maxT = Math.max(...typeRows.map((t) => t.total), 1)

  const coverage: Record<string, Record<string, number>> = {}
  const RECONCILED = ['PROCESSOR_EVENT', 'SETTLEMENT_LINE', 'SETTLEMENT_BATCH', 'BANK_LINE']
  data.item_status.filter((r: any) => RECONCILED.includes(r.item_type))
    .sort((a: any, b: any) => RECONCILED.indexOf(a.item_type) - RECONCILED.indexOf(b.item_type))
    .forEach((r: any) => ((coverage[r.item_type] ??= {})[r.recon_status] = r.n))
  const cfg = data.run_config

  return (
    <>
      <PageHeader eyebrow="Reconciliation run" title="Overview"
        subtitle="Payment instructions, processor events, settlement batches and bank statements — reconciled, with every break raised as an exception.">
        {cfg && (
          <div className="flex flex-wrap gap-2 text-xs">
            {[`Seed ${cfg.seed}`, `${cfg.period.settlement_start} → ${cfg.period.settlement_end}`,
              `Tolerance ±${cfg.rules.amount_tolerance_minor} minor unit`, `Date window ${cfg.rules.date_window_days}d`].map((c) => (
              <span key={c} className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-slate-600">{c}</span>
            ))}
          </div>
        )}
      </PageHeader>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Stat label="Event → settlement match" value={pct(k.event_settlement_match_rate, 2)} icon={ICON.link} accent="emerald"
          hint={`${num(f.events_matched)} of ${num(f.events_matched + f.events_exception)} due events settled exactly once`} />
        <Stat label="Batch → bank match" value={pct(k.batch_bank_match_rate, 1)} icon={ICON.bank} accent="indigo"
          hint={`${num(f.batches_matched)} of ${num(f.batches)} payouts reconciled · ${pct(k.amount_match_rate, 1)} by value`} />
        <Stat label="Detection precision / recall" value={`${(total.precision ?? 0).toFixed(2)} / ${(total.recall ?? 0).toFixed(2)}`} icon={ICON.target} accent="emerald"
          hint={`${num(total.true_positive)} of ${num(total.expected)} labelled anomalies · ${num(total.false_positive)} false positives`} />
        <Stat label="Unresolved exceptions" value={num(unresolved)} icon={ICON.alert} accent={unresolved ? 'amber' : 'emerald'}
          hint={<><Link to="/exceptions" className="text-indigo-600 hover:underline">{num((live.OPEN ?? 0) + (live.IN_REVIEW ?? 0))} with ops</Link> · <Link to="/risk" className="text-indigo-600 hover:underline">{num(live.ESCALATED ?? 0)} with risk</Link></>} />
      </div>

      <Card className="mt-6" title="Money flow" subtitle="How records move from payment instruction to cash in the bank, and where they break.">
        <div className="flex flex-col items-stretch lg:flex-row lg:items-center">
          <FlowNode title="Payment orders" value={f.orders} sub={`${num(f.captured_orders)} captured`} />
          <FlowArrow rate={`${num(f.settleable_events)}`} note="captures + refunds" bad={0} />
          <FlowNode title="Processor events" value={f.settleable_events} sub={`${num(f.events_pending)} in transit / prior period · ${num(f.duplicate_webhooks)} duplicate webhooks ignored`} />
          <FlowArrow rate={pct(k.event_settlement_match_rate, 2)} bad={f.events_exception + f.lines_exception} />
          <FlowNode title="Settlement lines" value={f.lines} sub={`in ${num(f.batches)} batches, fees deducted`} tone="indigo" />
          <FlowArrow rate={pct(k.batch_bank_match_rate, 1)} bad={f.batches_exception} />
          <FlowNode title="Bank payouts" value={f.bank_in_scope} sub={`${num(f.bank_matched)} matched · ${num(f.bank_out_of_scope)} unrelated lines out of scope`} tone="emerald" />
        </div>
      </Card>

      <div className="mt-6 grid gap-6 xl:grid-cols-5">
        <Card className="xl:col-span-3" title="Exceptions by type" subtitle="Bar length on a square-root scale so rare, high-severity breaks stay visible.">
          <div className="space-y-3">
            {typeRows.map((t) => (
              <Link key={t.type} to={`/exceptions?type=${t.type}&status=`} className="group grid grid-cols-[minmax(0,180px)_1fr_auto] items-center gap-3">
                <span className="truncate text-sm text-slate-700 group-hover:text-indigo-700">{label(t.type)}</span>
                <span className="h-2 rounded-full bg-slate-100">
                  <span className={`block h-2 rounded-full ${SEV_BAR[t.severity]}`} style={{ width: `${Math.max(Math.sqrt(t.total / maxT) * 100, 3)}%` }} />
                </span>
                <span className="w-24 text-right text-xs text-slate-500 num"><b className="text-slate-800">{num(t.total)}</b>{t.open ? ` · ${t.open} open` : ''}</span>
              </Link>
            ))}
          </div>
          <div className="mt-4 flex flex-wrap gap-3 text-[11px] text-slate-500">
            {Object.entries(SEV_BAR).map(([s, c]) => <span key={s} className="flex items-center gap-1.5"><span className={`h-2 w-2 rounded-full ${c}`} />{label(s)}</span>)}
          </div>
        </Card>

        <Card className="xl:col-span-2" title="Exception workflow" subtitle="Status derived from append-only history.">
          <div className="flex items-center gap-6">
            <div className="relative h-40 w-40 shrink-0">
              <ResponsiveContainer>
                <PieChart>
                  <Pie data={WORKFLOW.map((w) => ({ name: label(w.key), value: live[w.key] ?? 0, color: w.color }))} dataKey="value"
                    innerRadius={52} outerRadius={72} paddingAngle={2} stroke="none" isAnimationActive={false}>
                    {WORKFLOW.map((w) => <Cell key={w.key} fill={w.color} />)}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
              <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-xl font-semibold num">{pct(allEx ? (live.RESOLVED ?? 0) / allEx : 0, 0)}</span>
                <span className="text-[11px] text-slate-500">resolved</span>
              </div>
            </div>
            <ul className="flex-1 space-y-2 text-sm">
              {WORKFLOW.map((w) => (
                <li key={w.key} className="flex items-center justify-between">
                  <span className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-sm" style={{ background: w.color }} />{label(w.key)}</span>
                  <span className="font-medium num">{num(live[w.key] ?? 0)}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="mt-5 border-t border-slate-100 pt-4">
            <div className="mb-2 text-xs font-medium text-slate-500">Open exposure</div>
            {data.open_exception_amounts.length ? (
              <div className="flex flex-wrap gap-2">
                {data.open_exception_amounts.map((r: any) => (
                  <span key={r.currency} className="rounded-lg bg-slate-50 px-2.5 py-1.5 text-xs"><b className="num">{money(r.amount_minor, r.currency)}</b> <span className="text-slate-500">· {r.n}</span></span>
                ))}
              </div>
            ) : <span className="text-sm text-slate-400">No open exposure.</span>}
          </div>
        </Card>
      </div>

      <Card className="mt-6" title="Reconciliation coverage" subtitle="Every in-scope record ends with exactly one status — nothing is silently dropped.">
        <div className="space-y-4">
          {Object.entries(coverage).map(([type, s]) => {
            const n = Object.values(s).reduce((a, b) => a + b, 0)
            return (
              <div key={type} className="grid grid-cols-1 items-center gap-2 md:grid-cols-[180px_1fr_260px]">
                <div className="text-sm font-medium text-slate-700">{label(type)} <span className="font-normal text-slate-400 num">· {num(n)}</span></div>
                <StackBar parts={COVERAGE.map((c) => ({ key: c.key, value: s[c.key] ?? 0, color: c.color, label: c.label }))} />
                <div className="flex flex-wrap gap-x-3 text-xs text-slate-500 md:justify-end">
                  {COVERAGE.filter((c) => s[c.key]).map((c) => <span key={c.key} className="flex items-center gap-1"><span className={`h-2 w-2 rounded-full ${c.color}`} />{num(s[c.key])}</span>)}
                </div>
              </div>
            )
          })}
        </div>
        <div className="mt-4 flex flex-wrap gap-3 border-t border-slate-100 pt-3 text-[11px] text-slate-500">
          {COVERAGE.map((c) => <span key={c.key} className="flex items-center gap-1.5"><span className={`h-2 w-2 rounded-full ${c.color}`} />{c.label}</span>)}
        </div>
      </Card>

      <div className="mt-6 grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2" pad={false} title="Anomaly detection vs ground truth" subtitle="Engine never reads ground truth; scored afterwards on (exception type, record id).">
          <Table rowKey="exception_type" rows={det} cols={[
            { key: 'exception_type', header: 'Exception type', render: (r) => r.exception_type.startsWith('ALL') ? <b>All types (micro)</b> : label(r.exception_type) },
            { key: 'expected', header: 'Expected', className: 'text-right num', render: (r) => num(r.expected) },
            { key: 'true_positive', header: 'Caught', className: 'text-right num', render: (r) => num(r.true_positive) },
            { key: 'false_positive', header: 'False +', className: 'text-right num' },
            { key: 'false_negative', header: 'Missed', className: 'text-right num' },
            { key: 'precision', header: 'Precision', className: 'text-right num', render: (r) => r.precision.toFixed(2) },
            { key: 'recall', header: 'Recall', className: 'text-right num', render: (r) => <span className="font-semibold text-emerald-600">{r.recall.toFixed(2)}</span> },
          ]} />
        </Card>
        <Card pad={false} title="Labelled normal cases" subtitle="Tricky but valid — must match, not raise.">
          <Table rowKey="issue_type" rows={data.metrics?.normal_case_decisions ?? []} cols={[
            { key: 'issue_type', header: 'Case', render: (r) => <div><div>{label(r.issue_type)}</div><div className="text-[11px] text-slate-400">{label(r.expected_decision)}</div></div> },
            { key: 'cases', header: 'n', className: 'text-right num', render: (r) => num(r.cases) },
            { key: 'accuracy', header: '', className: 'text-right', render: (r) => <Badge value={r.accuracy === 1 ? 'PASS' : 'FAIL'} /> },
          ]} />
        </Card>
      </div>
    </>
  )
}
