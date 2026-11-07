import { createContext, useCallback, useContext, useState, type ReactNode } from 'react'

type Toast = { id: number; text: string; tone: 'ok' | 'err' }
const Ctx = createContext<(text: string, tone?: 'ok' | 'err') => void>(() => {})
export const useToast = () => useContext(Ctx)

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<Toast[]>([])
  const push = useCallback((text: string, tone: 'ok' | 'err' = 'ok') => {
    const id = Date.now() + Math.random()
    setItems((t) => [...t, { id, text, tone }])
    setTimeout(() => setItems((t) => t.filter((x) => x.id !== id)), 3500)
  }, [])
  return (
    <Ctx.Provider value={push}>
      {children}
      <div className="pointer-events-none fixed bottom-5 right-5 z-50 space-y-2">
        {items.map((t) => (
          <div key={t.id} role="status"
            className={`toast-in pointer-events-auto flex items-center gap-2 rounded-lg px-4 py-3 text-sm font-medium text-white shadow-lg ${t.tone === 'ok' ? 'bg-slate-900' : 'bg-rose-600'}`}>
            <span className={`h-2 w-2 rounded-full ${t.tone === 'ok' ? 'bg-emerald-400' : 'bg-white'}`} />
            {t.text}
          </div>
        ))}
      </div>
    </Ctx.Provider>
  )
}
