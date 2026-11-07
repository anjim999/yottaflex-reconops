import { useCallback, useEffect, useState } from 'react'

export type Row = Record<string, any>

export type Exception = {
  exception_id: string
  exception_type: string
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  owner_role: 'SYSTEM' | 'OPS_ANALYST' | 'RISK_REVIEWER'
  entity_type: string
  entity_id: string
  related_ids: string | null
  amount_minor: number | null
  currency: string | null
  rule_id: string
  description: string
  detected_at: string
  status: 'OPEN' | 'IN_REVIEW' | 'ESCALATED' | 'RESOLVED'
  status_changed_at: string
  status_actor: string
}

export type ExceptionDetail = Exception & {
  history: Row[]
  resolution: Row | null
  allowed_actions: ('START_REVIEW' | 'ESCALATE' | 'RESOLVE')[]
  default_resolution: string
}

export async function api<T = any>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, { headers: { 'Content-Type': 'application/json' }, ...init })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? `${res.status} ${res.statusText}`)
  }
  return res.json()
}

export function qs(params: Record<string, string | number | boolean | undefined | null>) {
  const p = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => v !== undefined && v !== null && v !== '' && p.set(k, String(v)))
  const s = p.toString()
  return s ? `?${s}` : ''
}

/** Fetch on mount / when `path` changes. `reload()` refetches. */
export function useApi<T = any>(path: string | null) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [tick, setTick] = useState(0)

  useEffect(() => {
    if (!path) return
    let alive = true
    setLoading(true)
    setError(null)
    api<T>(path)
      .then((d) => alive && setData(d))
      .catch((e) => alive && setError(e.message))
      .finally(() => alive && setLoading(false))
    return () => {
      alive = false
    }
  }, [path, tick])

  const reload = useCallback(() => setTick((t) => t + 1), [])
  return { data, error, loading, reload }
}
