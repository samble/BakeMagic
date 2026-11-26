import type { ReactNode } from 'react'
import type { OrderStatus } from './api'
import { STATUS_LABELS } from './format'

export function StatusBadge({ status }: { status: OrderStatus }) {
  return <span className={`badge badge-${status}`}>{STATUS_LABELS[status]}</span>
}

export function ErrorNote({ error }: { error: unknown }) {
  if (!error) return null
  const message = error instanceof Error ? error.message : String(error)
  return (
    <p className="error" role="alert">
      {message}
    </p>
  )
}

export function PageHeader({ title, actions }: { title: string; actions?: ReactNode }) {
  return (
    <div className="page-header">
      <h1>{title}</h1>
      {actions && <div className="page-actions">{actions}</div>}
    </div>
  )
}

export function Field({ label, children, wide }: { label: string; children: ReactNode; wide?: boolean }) {
  return (
    <label className={wide ? 'field field-wide' : 'field'}>
      <span>{label}</span>
      {children}
    </label>
  )
}

// Shows loading / error / empty states so each page only renders the happy path.
export function QueryState({
  isLoading,
  error,
  isEmpty,
  empty,
  children,
}: {
  isLoading: boolean
  error: unknown
  isEmpty: boolean
  empty: ReactNode
  children: ReactNode
}) {
  if (isLoading) return <p className="muted">Loading…</p>
  if (error) return <ErrorNote error={error} />
  if (isEmpty) return <div className="empty">{empty}</div>
  return <>{children}</>
}
