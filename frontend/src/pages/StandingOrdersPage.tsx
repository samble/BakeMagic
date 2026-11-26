import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState, type FormEvent } from 'react'
import { Link } from 'react-router'
import { api, WEEKDAYS, type Product, type StandingOrder, type Weekday } from '../api'
import { ErrorNote, Field, LineEditor, PageHeader, QueryState } from '../components'
import { DAY_LABELS, DAY_SHORT, fromCents, money, toCents } from '../format'
import { blankLine, lineCents, type DraftLine } from '../lines'

export default function StandingOrdersPage() {
  const standingOrders = useQuery({ queryKey: ['standing-orders'], queryFn: api.standingOrders.list })
  const customers = useQuery({ queryKey: ['customers'], queryFn: api.customers.list })
  const products = useQuery({ queryKey: ['products'], queryFn: api.products.list })

  const [editing, setEditing] = useState<StandingOrder | 'new' | null>(null)
  const [dayFilter, setDayFilter] = useState<Weekday | null>(null)

  const customerName = useMemo(() => {
    const names = new Map(customers.data?.map((c) => [c.id, c.name]))
    return (id: number) => names.get(id) ?? `Customer #${id}`
  }, [customers.data])

  const productById = useMemo(() => new Map(products.data?.map((p) => [p.id, p])), [products.data])

  const visible = standingOrders.data?.filter((s) => !dayFilter || s.days.includes(dayFilter))

  return (
    <>
      <PageHeader
        title="Standing orders"
        actions={
          editing === null && (
            <button className="primary" onClick={() => setEditing('new')}>
              Add standing order
            </button>
          )
        }
      />

      {editing !== null && (
        <StandingOrderForm
          key={editing === 'new' ? 'new' : editing.id}
          standingOrder={editing === 'new' ? undefined : editing}
          onDone={() => setEditing(null)}
        />
      )}

      <div className="chips" role="group" aria-label="Filter by day">
        <button className={!dayFilter ? 'chip active' : 'chip'} onClick={() => setDayFilter(null)}>
          Every day
        </button>
        {WEEKDAYS.map((day) => (
          <button
            key={day}
            className={dayFilter === day ? 'chip active' : 'chip'}
            onClick={() => setDayFilter(day)}
            aria-label={DAY_LABELS[day]}
          >
            {DAY_SHORT[day]}
          </button>
        ))}
      </div>

      <QueryState
        isLoading={standingOrders.isLoading}
        error={standingOrders.error}
        isEmpty={visible?.length === 0}
        empty={
          dayFilter ? (
            <p>No standing orders on {DAY_LABELS[dayFilter]}s.</p>
          ) : (
            <p>No standing orders yet. Add one for customers who order the same thing every week.</p>
          )
        }
      >
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Customer</th>
                <th>Days</th>
                <th>Items</th>
                <th className="num">Each delivery</th>
                <th>Status</th>
                <th aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {visible?.map((s) => (
                <StandingOrderRow
                  key={s.id}
                  standingOrder={s}
                  customerName={customerName(s.customer_id)}
                  productById={productById}
                  onEdit={() => setEditing(s)}
                />
              ))}
            </tbody>
          </table>
        </div>
      </QueryState>
    </>
  )
}

function StandingOrderRow({
  standingOrder: s,
  customerName,
  productById,
  onEdit,
}: {
  standingOrder: StandingOrder
  customerName: string
  productById: Map<number, Product>
  onEdit: () => void
}) {
  const queryClient = useQueryClient()
  const onSuccess = () => queryClient.invalidateQueries({ queryKey: ['standing-orders'] })
  const toggle = useMutation({
    mutationFn: () => api.standingOrders.update(s.id, { is_active: !s.is_active }),
    onSuccess,
  })
  const remove = useMutation({ mutationFn: () => api.standingOrders.remove(s.id), onSuccess })

  // Estimated at today's prices; the real order will use prices on the day it's created.
  const cents = s.lines.reduce((sum, l) => {
    const price = productById.get(l.product_id)?.price
    return sum + (price ? toCents(price) * l.quantity : 0)
  }, 0)
  const error = toggle.error ?? remove.error

  return (
    <>
      <tr className={s.is_active ? undefined : 'inactive'}>
        <td>
          {customerName}
          {s.notes && <div className="muted small">“{s.notes}”</div>}
        </td>
        <td>
          <DayPills days={s.days} />
        </td>
        <td>
          {s.lines.map((l) => (
            <div key={l.id}>
              {l.quantity} × {productById.get(l.product_id)?.name ?? `Product #${l.product_id}`}
            </div>
          ))}
        </td>
        <td className="num">{money(fromCents(cents))}</td>
        <td>
          <span className={s.is_active ? 'badge badge-ready' : 'badge badge-completed'}>
            {s.is_active ? 'Active' : 'Paused'}
          </span>
        </td>
        <td className="row-actions">
          <button className="quiet" onClick={onEdit}>
            Edit
          </button>
          <button className="quiet" disabled={toggle.isPending} onClick={() => toggle.mutate()}>
            {s.is_active ? 'Pause' : 'Resume'}
          </button>
          <button
            className="danger-quiet"
            disabled={remove.isPending}
            onClick={() => {
              if (confirm(`Delete the standing order for ${customerName}? Orders already created are kept.`)) {
                remove.mutate()
              }
            }}
          >
            Delete
          </button>
        </td>
      </tr>
      {error && (
        <tr className="error-row">
          <td colSpan={6}>
            <ErrorNote error={error} />
          </td>
        </tr>
      )}
    </>
  )
}

// All seven days, with the scheduled ones highlighted, so rows line up and scan easily.
function DayPills({ days }: { days: Weekday[] }) {
  return (
    <span className="day-pills" aria-label={days.map((d) => DAY_LABELS[d]).join(', ')}>
      {WEEKDAYS.map((day) => (
        <span key={day} className={days.includes(day) ? 'day-pill on' : 'day-pill'} aria-hidden>
          {DAY_SHORT[day][0]}
        </span>
      ))}
    </span>
  )
}

function StandingOrderForm({ standingOrder, onDone }: { standingOrder?: StandingOrder; onDone: () => void }) {
  const queryClient = useQueryClient()
  const customers = useQuery({ queryKey: ['customers'], queryFn: api.customers.list })
  const products = useQuery({ queryKey: ['products'], queryFn: api.products.list })

  const [customerId, setCustomerId] = useState(standingOrder ? String(standingOrder.customer_id) : '')
  const [days, setDays] = useState<Weekday[]>(standingOrder?.days ?? [])
  const [notes, setNotes] = useState(standingOrder?.notes ?? '')
  const [lines, setLines] = useState<DraftLine[]>(() =>
    standingOrder
      ? standingOrder.lines.map((l) => blankLine(String(l.product_id), String(l.quantity)))
      : [blankLine()],
  )

  // Offer active products, plus any retired ones this standing order still uses so they
  // show up correctly; the API will ask for them to be swapped out on save.
  const usedIds = new Set(standingOrder?.lines.map((l) => l.product_id))
  const choices = products.data?.filter((p) => p.is_active || usedIds.has(p.id)) ?? []

  const toggleDay = (day: Weekday) =>
    setDays((current) =>
      current.includes(day) ? current.filter((d) => d !== day) : WEEKDAYS.filter((d) => d === day || current.includes(d)),
    )

  const totalCents = lines.reduce((sum, l) => sum + lineCents(l, choices), 0)
  const linesValid = lines.every((l) => lineCents(l, choices) > 0)
  const canSubmit = customerId !== '' && days.length > 0 && linesValid

  const save = useMutation({
    mutationFn: () => {
      const body = {
        days,
        notes: notes.trim() || null,
        lines: lines.map((l) => ({ product_id: Number(l.productId), quantity: Number(l.quantity) })),
      }
      return standingOrder
        ? api.standingOrders.update(standingOrder.id, body)
        : api.standingOrders.create({ customer_id: Number(customerId), ...body })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['standing-orders'] })
      onDone()
    },
  })

  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (canSubmit) save.mutate()
  }

  if (customers.isLoading || products.isLoading) return <p className="muted">Loading…</p>
  if (customers.error || products.error) return <ErrorNote error={customers.error ?? products.error} />

  if (!standingOrder && (customers.data?.length === 0 || choices.length === 0)) {
    return (
      <div className="card empty">
        <p>
          A standing order needs a customer and a product. Add some on the{' '}
          <Link to="/customers">Customers</Link> and <Link to="/products">Products</Link> pages first.
        </p>
        <button className="quiet" onClick={onDone}>
          Close
        </button>
      </div>
    )
  }

  return (
    <form className="card form" onSubmit={submit}>
      <h2>{standingOrder ? 'Edit standing order' : 'New standing order'}</h2>
      <div className="form-grid">
        <Field label="Customer">
          <select
            value={customerId}
            onChange={(e) => setCustomerId(e.target.value)}
            disabled={!!standingOrder}
            title={standingOrder ? "The customer can't be changed; create a new standing order instead." : undefined}
            required
          >
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
          <input
            value={notes}
            maxLength={255}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Leave at the back door"
          />
        </Field>
      </div>

      <fieldset className="line-editor">
        <legend>Days</legend>
        <div className="chips" role="group" aria-label="Days of the week">
          {WEEKDAYS.map((day) => (
            <button
              key={day}
              type="button"
              className={days.includes(day) ? 'chip active' : 'chip'}
              aria-pressed={days.includes(day)}
              aria-label={DAY_LABELS[day]}
              onClick={() => toggleDay(day)}
            >
              {DAY_SHORT[day]}
            </button>
          ))}
        </div>
      </fieldset>

      <LineEditor lines={lines} setLines={setLines} products={choices} />

      <div className="form-footer">
        <div className="total">
          Each delivery <strong>{money(fromCents(totalCents))}</strong>
        </div>
        <div className="page-actions">
          <button type="button" className="quiet" onClick={onDone}>
            Cancel
          </button>
          <button type="submit" className="primary" disabled={!canSubmit || save.isPending}>
            {save.isPending ? 'Saving…' : standingOrder ? 'Save changes' : 'Create standing order'}
          </button>
        </div>
      </div>
      {days.length === 0 && <p className="muted small">Pick at least one day.</p>}
      <ErrorNote error={save.error} />
    </form>
  )
}
