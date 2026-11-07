import { useState } from 'react'
import { Badge, Card, ErrorBox, Loading, PageHeader, Stat, Table } from '../components/ui'
import { useApi } from '../lib/api'
import { label, num } from '../lib/format'

const ICON = {
  check: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
  tag: 'M7 7h.01M3 3h8l10 10-8 8L3 11z',
  copy: 'M8 8h11v11H8zM5 16V5h11',
  repeat: 'M4 4v6h6M20 20v-6h-6M5.5 15a7 7 0 0012.2 2.5M18.5 9A7 7 0 006.3 6.5',
}

export default function Admin() {
  const v = useApi('/api/validation')
  const s = useApi('/api/summary')
  const [onlyFlagged, setOnlyFlagged] = useState(false)
  const [cat, setCat] = useState('')
  if (v.error || s.error) return <ErrorBox error={v.error ?? s.error} />
  if (!v.data || !s.data) return <Card><Loading rows={8} /></Card>
  const checks: any[] = v.data.checks
  const failed = checks.filter((c) => c.status === 'FAIL').length
  const labelled = checks.reduce((a, c) => a + Number(c.labelled_anomalies || 0), 0)
  const repro = v.data.reproducibility
  const idem = s.data.metrics?.idempotency ?? {}
  const idemPass = Object.values(idem).filter((x) => x === true).length
  const idemTotal = Object.values(idem).filter((x) => typeof x === 'boolean').length
  const cfg = s.data.run_config
  const cats = [...new Set(checks.map((c) => c.category))]
  const rows = checks.map((c, i) => ({ ...c, key: i }))
    .filter((c) => (!onlyFlagged || c.status === 'FAIL' || Number(c.labelled_anomalies) > 0) && (!cat || c.category === cat))

  return (
    <>
      <PageHeader eyebrow="System administrator" title="Platform health"
        subtitle="Run configuration and the evidence behind it: data validation, reproducibility from a fixed seed, and idempotent ingestion." />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Stat label="Validation checks passed" value={`${num(checks.length - failed)} / ${num(checks.length)}`} icon={ICON.check} accent={failed ? 'rose' : 'emerald'} hint="PK, FK, enums, dates, arithmetic, lifecycle, duplicates" />
        <Stat label="Labelled anomalies (excluded)" value={num(labelled)} icon={ICON.tag} accent="amber" hint="deliberate edge cases, counted not failed" />
        <Stat label="Reproducibility" value={repro?.identical ? 'Identical' : '—'} icon={ICON.copy} accent={repro?.identical ? 'emerald' : 'slate'} hint={`2 runs · ${repro?.files_compared ?? 0} files · SHA-256`} />
        <Stat label="Idempotent replay" value={`${idemPass} / ${idemTotal}`} icon={ICON.repeat} accent="emerald" hint="full webhook feed replayed twice" />
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-3">
        <Card title="Run configuration" subtitle="recon/config.py · run_config.json">
          <pre className="max-h-80 overflow-auto rounded-xl bg-slate-950 p-4 text-xs leading-relaxed text-slate-200">{JSON.stringify({ seed: cfg.seed, scale: cfg.scale, rules: cfg.rules, period: cfg.period, anomaly_counts: cfg.anomaly_counts }, null, 2)}</pre>
        </Card>
        <Card title="Idempotency evidence" subtitle="Engine re-run on the same input, and on a doubled webhook feed.">
          <ul className="divide-y divide-slate-100 text-sm">
            {Object.entries(idem).map(([k, val]) => (
              <li key={k} className="flex items-start justify-between gap-3 py-2.5 first:pt-0">
                <span className="text-slate-600">{label(k)}</span>
                {typeof val === 'boolean' ? <Badge value={val ? 'PASS' : 'FAIL'} /> : <b className="num">{num(val as number)}</b>}
              </li>
            ))}
          </ul>
        </Card>
        <Card title="Source manifest" subtitle="Provenance and checksums">
          <p className="text-sm leading-relaxed text-slate-600">{v.data.manifest.provenance}</p>
          <dl className="mt-4 grid grid-cols-[max-content_1fr] gap-x-4 gap-y-1.5 text-xs">
            <dt className="text-slate-500">Generator</dt><dd>{v.data.manifest.generator_version}</dd>
            <dt className="text-slate-500">Runtime</dt><dd>Python {v.data.manifest.python} · pandas {v.data.manifest.pandas}</dd>
            <dt className="text-slate-500">Files</dt><dd>{v.data.manifest.files?.length} checksummed</dd>
            <dt className="text-slate-500">Command</dt><dd className="id break-all whitespace-normal">{v.data.manifest.command}</dd>
          </dl>
        </Card>
      </div>

      <Card className="mt-6" pad={false} title={`Validation checks · ${rows.length} shown`}
        action={<div className="flex flex-wrap items-center gap-3">
          <select value={cat} onChange={(e) => setCat(e.target.value)} className="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-sm">
            <option value="">All categories</option>
            {cats.map((c) => <option key={c} value={c}>{label(c)}</option>)}
          </select>
          <label className="flex items-center gap-2 text-sm text-slate-600"><input type="checkbox" checked={onlyFlagged} onChange={(e) => setOnlyFlagged(e.target.checked)} className="accent-indigo-600" />Failures or labelled only</label>
        </div>}>
        <div className="max-h-[560px] overflow-y-auto">
          <Table rowKey="key" rows={rows} cols={[
            { key: 'status', header: '', render: (r) => <Badge value={r.status} /> },
            { key: 'category', header: 'Category', className: 'whitespace-nowrap', render: (r) => label(r.category) },
            { key: 'check', header: 'Check', render: (r) => <span className="text-slate-700">{r.check}</span> },
            { key: 'table', header: 'Table', render: (r) => <span className="id text-slate-500">{r.table}</span> },
            { key: 'checked', header: 'Rows', className: 'text-right num', render: (r) => num(Number(r.checked)) },
            { key: 'failures', header: 'Failures', className: 'text-right num' },
            { key: 'labelled_anomalies', header: 'Labelled', className: 'text-right num', render: (r) => Number(r.labelled_anomalies) ? <span className="font-medium text-amber-600">{r.labelled_anomalies}</span> : '0' },
          ]} />
        </div>
      </Card>
    </>
  )
}
