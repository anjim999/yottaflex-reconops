const EXP: Record<string, number> = { USD: 2, EUR: 2, GBP: 2, INR: 2, JPY: 0 }
const SYMBOL: Record<string, string> = { USD: '$', EUR: '€', GBP: '£', INR: '₹', JPY: '¥' }

/** Integer minor units -> "€1,234.56". */
export function money(minor: number | null | undefined, ccy: string | null | undefined) {
  if (minor === null || minor === undefined || !ccy) return '—'
  const exp = EXP[ccy] ?? 2
  const v = Number(minor) / 10 ** exp
  const s = Math.abs(v).toLocaleString('en-US', { minimumFractionDigits: exp, maximumFractionDigits: exp })
  return `${v < 0 ? '−' : ''}${SYMBOL[ccy] ?? ''}${s}${SYMBOL[ccy] ? '' : ' ' + ccy}`
}

export function when(ts: string | null | undefined) {
  if (!ts) return '—'
  const d = new Date(ts)
  if (isNaN(d.getTime())) return ts
  return d.toISOString().replace('T', ' ').slice(0, ts.length > 10 ? 16 : 10)
}

export const pct = (v: number | undefined | null, digits = 1) =>
  v === undefined || v === null ? '—' : `${(v * 100).toFixed(digits)}%`

export const num = (v: number | undefined | null) => (v === undefined || v === null ? '—' : v.toLocaleString('en-US'))

export const label = (s: string | null | undefined) =>
  (s ?? '').toLowerCase().replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase())
