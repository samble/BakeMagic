import type { Dispatch, ReactNode, SetStateAction } from 'react'
import type { OrderStatus, Product } from './api'
import { fromCents, money, STATUS_LABELS } from './format'
import { blankLine, lineCents, type DraftLine } from './lines'

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

// ---------- line items (order and standing order forms) ----------

/**
 * Editable list of product + quantity rows. `products` are the choices offered;
 * pass retired products too if existing lines may refer to them.
 */
export function LineEditor({
  lines,
  setLines,
  products,
}: {
  lines: DraftLine[]
  setLines: Dispatch<SetStateAction<DraftLine[]>>
  products: Product[]
}) {
  const updateLine = (key: number, patch: Partial<DraftLine>) =>
    setLines((current) => current.map((l) => (l.key === key ? { ...l, ...patch } : l)))

  return (
    <fieldset className="line-editor">
      <legend>Items</legend>
      {lines.map((line, index) => {
        const cents = lineCents(line, products)
        return (
          <div className="line" key={line.key}>
            <select
              aria-label={`Product for item ${index + 1}`}
              value={line.productId}
              onChange={(e) => updateLine(line.key, { productId: e.target.value })}
              required
            >
              <option value="">Choose a product…</option>
              {products.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({money(p.price)}){p.is_active ? '' : ' — retired'}
                </option>
              ))}
            </select>
            <input
              aria-label={`Quantity for item ${index + 1}`}
              type="number"
              min={1}
              step={1}
              value={line.quantity}
              onChange={(e) => updateLine(line.key, { quantity: e.target.value })}
              required
            />
            <span className="num line-total">{cents ? money(fromCents(cents)) : '—'}</span>
            <button
              type="button"
              className="icon"
              aria-label={`Remove item ${index + 1}`}
              disabled={lines.length === 1}
              onClick={() => setLines((current) => current.filter((l) => l.key !== line.key))}
            >
              ×
            </button>
          </div>
        )
      })}
      <button type="button" className="quiet" onClick={() => setLines((current) => [...current, blankLine()])}>
        + Add item
      </button>
    </fieldset>
  )
}
