import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router'
import { api } from '../api'
import { ErrorNote, Field, LineEditor, PageHeader } from '../components'
import { blankLine, lineCents, type DraftLine } from '../lines'
import { fromCents, money } from '../format'

export default function NewOrderPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const customers = useQuery({ queryKey: ['customers'], queryFn: api.customers.list })
  const products = useQuery({ queryKey: ['products'], queryFn: api.products.list })

  const [customerId, setCustomerId] = useState('')
  const [notes, setNotes] = useState('')
  const [lines, setLines] = useState<DraftLine[]>(() => [blankLine()])

  const activeProducts = products.data?.filter((p) => p.is_active) ?? []
  const totalCents = lines.reduce((sum, l) => sum + lineCents(l, activeProducts), 0)
  const validLines = lines.filter((l) => lineCents(l, activeProducts) > 0)
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
                  {c.name}
                  {c.email && ` — ${c.email}`}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Notes (optional)">
            <input value={notes} maxLength={255} onChange={(e) => setNotes(e.target.value)} placeholder="Pickup Saturday, write “Happy Birthday”" />
          </Field>
        </div>

        <LineEditor lines={lines} setLines={setLines} products={activeProducts} />

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
