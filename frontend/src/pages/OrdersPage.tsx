import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Fragment, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router'
import { api, ORDER_STATUSES, type Order, type OrderStatus } from '../api'
import { ErrorNote, PageHeader, QueryState, StatusBadge } from '../components'
import { isFinished, money, NEXT_STATUS, STATUS_LABELS, when } from '../format'

export default function OrdersPage() {
  const [params, setParams] = useSearchParams()
  const statusFilter = (params.get('status') as OrderStatus | null) ?? undefined
  // A just-created order arrives with ?highlight=<id> so it starts expanded.
  const [openId, setOpenId] = useState<number | null>(() => Number(params.get('highlight')) || null)

  const orders = useQuery({
    queryKey: ['orders', statusFilter ?? 'all'],
    queryFn: () => api.orders.list(statusFilter),
    // Keep showing the current rows while another filter loads, instead of flashing "Loading…".
    placeholderData: keepPreviousData,
  })
  const customers = useQuery({ queryKey: ['customers'], queryFn: api.customers.list })
  const products = useQuery({ queryKey: ['products'], queryFn: api.products.list })

  const customerName = useMemo(() => {
    const names = new Map(customers.data?.map((c) => [c.id, `${c.first_name} ${c.last_name}`]))
    return (id: number) => names.get(id) ?? `Customer #${id}`
  }, [customers.data])

  const productName = useMemo(() => {
    const names = new Map(products.data?.map((p) => [p.id, p.name]))
    return (id: number) => names.get(id) ?? `Product #${id}`
  }, [products.data])

  const setFilter = (status?: OrderStatus) => setParams(status ? { status } : {})

  return (
    <>
      <PageHeader
        title="Orders"
        actions={
          <Link to="/orders/new" className="button primary">
            New order
          </Link>
        }
      />

      <div className="chips" role="group" aria-label="Filter by status">
        <button className={!statusFilter ? 'chip active' : 'chip'} onClick={() => setFilter()}>
          All
        </button>
        {ORDER_STATUSES.map((s) => (
          <button key={s} className={statusFilter === s ? 'chip active' : 'chip'} onClick={() => setFilter(s)}>
            {STATUS_LABELS[s]}
          </button>
        ))}
      </div>

      <QueryState
        isLoading={orders.isLoading}
        error={orders.error}
        isEmpty={orders.data?.length === 0}
        empty={
          statusFilter ? (
            <p>No {STATUS_LABELS[statusFilter].toLowerCase()} orders.</p>
          ) : (
            <p>
              No orders yet. <Link to="/orders/new">Take the first one.</Link>
            </p>
          )
        }
      >
        <div className={orders.isPlaceholderData ? 'table-wrap stale' : 'table-wrap'} aria-busy={orders.isPlaceholderData}>
          <table>
            <thead>
              <tr>
                <th>Order</th>
                <th>Customer</th>
                <th className="num">Items</th>
                <th className="num">Total</th>
                <th>Status</th>
                <th>Placed</th>
              </tr>
            </thead>
            <tbody>
              {orders.data?.map((order) => {
                const open = openId === order.id
                return (
                  <Fragment key={order.id}>
                    <tr
                      className={open ? 'row-button open' : 'row-button'}
                      onClick={() => setOpenId(open ? null : order.id)}
                      aria-expanded={open}
                    >
                      <td className="mono">#{order.id}</td>
                      <td>{customerName(order.customer_id)}</td>
                      <td className="num">{order.lines.reduce((n, l) => n + l.quantity, 0)}</td>
                      <td className="num">{money(order.total)}</td>
                      <td>
                        <StatusBadge status={order.status} />
                      </td>
                      <td className="muted">{when(order.created_at)}</td>
                    </tr>
                    {open && (
                      <tr className="detail-row">
                        <td colSpan={6}>
                          <OrderDetail order={order} productName={productName} />
                        </td>
                      </tr>
                    )}
                  </Fragment>
                )
              })}
            </tbody>
          </table>
        </div>
        {orders.data?.length === 200 && <p className="muted small">Showing the 200 most recent orders.</p>}
      </QueryState>
    </>
  )
}

function OrderDetail({ order, productName }: { order: Order; productName: (id: number) => string }) {
  const queryClient = useQueryClient()
  const changeStatus = useMutation({
    mutationFn: (status: OrderStatus) => api.orders.setStatus(order.id, status),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['orders'] }),
  })
  const next = NEXT_STATUS[order.status]

  return (
    <div className="detail">
      <table className="lines">
        <thead>
          <tr>
            <th>Product</th>
            <th className="num">Qty</th>
            <th className="num">Unit price</th>
            <th className="num">Line total</th>
          </tr>
        </thead>
        <tbody>
          {order.lines.map((line) => (
            <tr key={line.id}>
              <td>{productName(line.product_id)}</td>
              <td className="num">{line.quantity}</td>
              <td className="num">{money(line.unit_price)}</td>
              <td className="num">{money(Number(line.unit_price) * line.quantity)}</td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr>
            <td colSpan={3}>Total</td>
            <td className="num">{money(order.total)}</td>
          </tr>
        </tfoot>
      </table>

      {order.notes && <p className="notes">“{order.notes}”</p>}

      <div className="detail-actions">
        {isFinished(order.status) ? (
          <span className="muted">This order is {STATUS_LABELS[order.status].toLowerCase()} and locked.</span>
        ) : (
          <>
            {next && (
              <button className="primary" disabled={changeStatus.isPending} onClick={() => changeStatus.mutate(next)}>
                Mark as {STATUS_LABELS[next].toLowerCase()}
              </button>
            )}
            <button
              className="danger-quiet"
              disabled={changeStatus.isPending}
              onClick={() => {
                if (confirm(`Cancel order #${order.id}? Cancelled orders can't be reopened.`)) {
                  changeStatus.mutate('cancelled')
                }
              }}
            >
              Cancel order
            </button>
          </>
        )}
        <ErrorNote error={changeStatus.error} />
      </div>
    </div>
  )
}
