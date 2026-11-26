import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { api, type Customer, type CustomerCreate } from '../api'
import { ErrorNote, Field, PageHeader, QueryState } from '../components'
import { when } from '../format'

const BLANK: CustomerCreate = { name: '', email: '', phone: '', address: '' }

// Optional fields are sent as "" when empty; the API rejects null.
const clean = (c: CustomerCreate): CustomerCreate => ({
  name: c.name.trim(),
  email: c.email.trim(),
  phone: c.phone.trim(),
  address: c.address.trim(),
})

export default function CustomersPage() {
  const customers = useQuery({ queryKey: ['customers'], queryFn: api.customers.list })
  const [editing, setEditing] = useState<Customer | 'new' | null>(null)
  const [search, setSearch] = useState('')

  const term = search.trim().toLowerCase()
  const visible = customers.data?.filter((c) =>
    `${c.name} ${c.email} ${c.phone}`.toLowerCase().includes(term),
  )

  return (
    <>
      <PageHeader
        title="Customers"
        actions={
          <>
            <input
              type="search"
              className="search"
              placeholder="Search name, email, phone"
              aria-label="Search customers"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            {editing === null && (
              <button className="primary" onClick={() => setEditing('new')}>
                Add customer
              </button>
            )}
          </>
        }
      />

      {editing !== null && (
        <CustomerForm
          key={editing === 'new' ? 'new' : editing.id}
          customer={editing === 'new' ? undefined : editing}
          onDone={() => setEditing(null)}
        />
      )}

      <QueryState
        isLoading={customers.isLoading}
        error={customers.error}
        isEmpty={visible?.length === 0}
        empty={term ? <p>No customers match “{search}”.</p> : <p>No customers yet.</p>}
      >
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Address</th>
                <th>Since</th>
                <th aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {visible?.map((c) => (
                <tr key={c.id}>
                  <td>{c.name}</td>
                  <td>
                    {c.email && <a href={`mailto:${c.email}`}>{c.email}</a>}
                  </td>
                  <td>{c.phone}</td>
                  <td className="muted">{c.address}</td>
                  <td className="muted">{when(c.created_at)}</td>
                  <td className="row-actions">
                    <button className="quiet" onClick={() => setEditing(c)}>
                      Edit
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </QueryState>
    </>
  )
}

function CustomerForm({ customer, onDone }: { customer?: Customer; onDone: () => void }) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState<CustomerCreate>(() =>
    customer
      ? {
          name: customer.name,
          email: customer.email,
          phone: customer.phone,
          address: customer.address,
        }
      : BLANK,
  )
  const set = (key: keyof CustomerCreate) => (e: { target: { value: string } }) =>
    setForm((f) => ({ ...f, [key]: e.target.value }))

  const save = useMutation({
    mutationFn: (data: CustomerCreate) =>
      customer ? api.customers.update(customer.id, data) : api.customers.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] })
      onDone()
    },
  })

  const submit = (event: FormEvent) => {
    event.preventDefault()
    save.mutate(clean(form))
  }

  return (
    <form className="card form" onSubmit={submit}>
      <h2>{customer ? `Edit ${customer.name}` : 'New customer'}</h2>
      <div className="form-grid">
        <Field label="Name" wide>
          <input value={form.name} onChange={set('name')} maxLength={100} required autoFocus />
        </Field>
        <Field label="Email (optional)">
          <input type="email" value={form.email} onChange={set('email')} maxLength={255} />
        </Field>
        <Field label="Phone (optional)">
          <input type="tel" value={form.phone} onChange={set('phone')} maxLength={30} />
        </Field>
        <Field label="Address (optional)" wide>
          <input value={form.address} onChange={set('address')} maxLength={255} />
        </Field>
      </div>
      <div className="form-footer">
        <ErrorNote error={save.error} />
        <div className="page-actions">
          <button type="button" className="quiet" onClick={onDone}>
            Cancel
          </button>
          <button type="submit" className="primary" disabled={save.isPending}>
            {customer ? 'Save changes' : 'Add customer'}
          </button>
        </div>
      </div>
    </form>
  )
}
