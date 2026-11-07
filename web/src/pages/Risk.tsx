import { Badge, Card, ErrorBox, IdLink, PageHeader, Table } from '../components/ui'
import { useApi } from '../lib/api'
import { label, money, when } from '../lib/format'
import { ExceptionQueue } from './Exceptions'

export default function Risk() {
  const audit = useApi<any[]>('/api/audit?limit=150')
  const res = useApi<any[]>('/api/resolutions?limit=150')
  return (
    <>
      <PageHeader eyebrow="Risk / compliance reviewer" title="Risk & compliance"
        subtitle="Currency mismatches, refunds before capture and over-refunds are owned by risk. Segregation of duties: only a risk reviewer can resolve them — the API rejects anyone else with 403." />
      <ExceptionQueue owner="RISK_REVIEWER" defaultStatus="OPEN,IN_REVIEW,ESCALATED" />
      <div className="mt-6 grid gap-6 2xl:grid-cols-2">
        <Card pad={false} title="Audit trail" subtitle="Who changed what, when — every row is immutable.">
          <ErrorBox error={audit.error} />
          <div className="max-h-[520px] overflow-y-auto">
            <Table rowKey="history_id" rows={audit.data ?? []} cols={[
              { key: 'changed_at', header: 'When', className: 'whitespace-nowrap', render: (r) => <span className="text-xs text-slate-500">{when(r.changed_at)}</span> },
              { key: 'actor_role', header: 'Actor', className: 'whitespace-nowrap', render: (r) => label(r.actor_role) },
              { key: 'transition', header: 'Transition', render: (r) => <span className="flex items-center gap-1.5">{r.from_status ? <Badge value={r.from_status} /> : <span className="text-xs text-slate-400">created</span>}<span className="text-slate-300">→</span><Badge value={r.to_status} /></span> },
              { key: 'exception_type', header: 'Exception', render: (r) => <div><div className="text-slate-700">{label(r.exception_type)}</div><div className="id text-slate-400">{r.exception_id}</div></div> },
              { key: 'entity_id', header: 'Record', render: (r) => <IdLink id={r.entity_id} /> },
            ]} />
          </div>
        </Card>
        <Card pad={false} title="Resolutions & financial adjustments" subtitle="Recorded separately from the exception — never edited in place.">
          <ErrorBox error={res.error} />
          <div className="max-h-[520px] overflow-y-auto">
            <Table rowKey="resolution_id" rows={res.data ?? []} cols={[
              { key: 'resolved_at', header: 'When', className: 'whitespace-nowrap', render: (r) => <span className="text-xs text-slate-500">{when(r.resolved_at)}</span> },
              { key: 'resolution_type', header: 'Resolution', render: (r) => <div><div className="text-slate-700">{label(r.resolution_type)}</div><div className="text-[11px] text-slate-400">{label(r.exception_type)}</div></div> },
              { key: 'resolved_by_role', header: 'By', className: 'whitespace-nowrap', render: (r) => label(r.resolved_by_role) },
              { key: 'adj', header: 'Adjustment', className: 'text-right num', render: (r) => money(r.adjustment_amount_minor, r.currency) },
              { key: 'entity_id', header: 'Record', render: (r) => <IdLink id={r.entity_id} /> },
            ]} />
          </div>
        </Card>
      </div>
    </>
  )
}
