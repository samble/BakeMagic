import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router'
import { api } from '../api'
import { ErrorNote, Field, PageHeader } from '../components'
import { fromCents, money, toCents } from '../format'

interface DraftLine {
  key: number
  productId: string
  quantity: string
}

let nextKey = 1
const blankLine = (): DraftLine => ({ key: nextKey++, productId: '', quantity: '1' })

export default function NewOrderPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const customers = useQuery({ queryKey: ['customers'], queryFn: api.customers.list })
  const products = useQuery({ queryKey: ['products'], queryFn: api.products.list })

  const [customerId, setCustomerId] = useState('')
  const [notes, setNotes] = useState('')
  const [lines, setLines] = useState<DraftLine[]>(() => [blankLine()])

  const activeProducts = products.data?.filter((p) => p.is_active) ?? []
  const priceOf = (productId: string) => activeProducts.find((p) => String(p.id) === productId)?.price

  const updateLine = (key: number, patch: Partial<DraftLine>) =>
    setLines((current) => current.map((l) => (l.key === key ? { ...l, ...patch } : l)))

  const lineCents = (line: DraftLine) => {
    const price = priceOf(line.productId)
    const qty = Number(line.quantity)
    return price && Number.isInteger(qty) && qty > 0 ? toCents(price) * qty : 0
  }
  const totalCents = lines.reduce((sum, l) => sum + lineCents(l), 0)
  const validLines = lines.filter((l) => lineCents(l) > 0)
  const canSubmit = customerId !== '' && validLines.length > 0 && validLines.length === lines.length

  const createOrder = useMutation({
    mutationFn: api.orders.create,
    onSuccess: (order) => {
      queryClient.invalidateQueries({ queryKey: ['orders'] })
      navigate(`/orders?highlight=${order.id}`)
    },
  })

  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (!canSubmit) return
    createOrder.mutate({
      customer_id: Number(customerId),
      notes: notes.trim() || null,
      lines: lines.map((l) => ({ product_id: Number(l.productId), quantity: Number(l.quantity) })),
    })
  }

  if (customers.isLoading || products.isLoading) return <p className="muted">Loading…</p>
  if (customers.error || products.error) return <ErrorNote error={customers.error ?? products.error} />

  const missing = [
    customers.data?.length === 0 && <Link key="c" to="/customers">add a customer</Link>,
    activeProducts.length === 0 && <Link key="p" to="/products">add a product</Link>,
  ].filter(Boolean)
  if (missing.length) {
    return (
      <>
        <PageHeader title="New order" />
        <div className="empty">
          <p>
            Before taking an order, {missing.length === 2 ? <>{missing[0]} and {missing[1]}</> : missing[0]}.
          </p>
        </div>
      </>
    )
  }

  return (
    <>
      <PageHeader title="New order" />
      <form className="card form" onSubmit={submit}>
        <div className="form-grid">
          <Field label="Customer">
            <select value={customerId} onChange={(e) => setCustomerId(e.target.value)} required>
              <option value="">Choose a customer…</option>
              {customers.data?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.first_name} {c.last_name} — {c.email}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Notes (optional)">
            <input value={notes} maxLength={255} onChange={(e) => setNotes(e.target.value)} placeholder="Pickup Saturday, write “Happy Birthday”" />
          </Field>
        </div>

        <fieldset className="line-editor">
          <legend>Items</legend>
          {lines.map((line, index) => (
            <div className="line" key={line.key}>
              <select
                aria-label={`Product for item ${index + 1}`}
                value={line.productId}
                onChange={(e) => updateLine(line.key, { productId: e.target.value })}
                required
              >
                <option value="">Choose a product…</option>
                {activeProducts.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({money(p.price)})
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
              <span className="num line-total">{lineCents(line) ? money(fromCents(lineCents(line))) : '—'}</span>
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
          ))}
          <button type="button" className="quiet" onClick={() => setLines((current) => [...current, blankLine()])}>
            + Add item
          </button>
        </fieldset>

        <div className="form-footer">
          <div className="total">
            Total <strong>{money(fromCents(totalCents))}</strong>
          </div>
          <div className="page-actions">
            <Link to="/orders" className="button quiet">
              Cancel
            </Link>
            <button type="submit" className="primary" disabled={!canSubmit || createOrder.isPending}>
              {createOrder.isPending ? 'Placing…' : 'Place order'}
            </button>
          </div>
        </div>
        <ErrorNote error={createOrder.error} />
      </form>
    </>
  )
}
