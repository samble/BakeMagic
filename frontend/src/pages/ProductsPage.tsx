import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { api, type Product, type ProductCreate, type ProductUpdate } from '../api'
import { ErrorNote, Field, PageHeader, QueryState } from '../components'
import { money } from '../format'

const PRICE_PATTERN = '\\d+(\\.\\d{1,2})?'

export default function ProductsPage() {
  const products = useQuery({ queryKey: ['products'], queryFn: api.products.list })
  const [adding, setAdding] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)

  return (
    <>
      <PageHeader
        title="Products"
        actions={
          !adding && (
            <button className="primary" onClick={() => setAdding(true)}>
              Add product
            </button>
          )
        }
      />

      {adding && <AddProductForm onDone={() => setAdding(false)} />}

      <QueryState
        isLoading={products.isLoading}
        error={products.error}
        isEmpty={products.data?.length === 0}
        empty={<p>No products yet. Add your first bake to start taking orders.</p>}
      >
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Code</th>
                <th>Name</th>
                <th>Description</th>
                <th className="num">Price</th>
                <th>Status</th>
                <th aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {products.data?.map((product) =>
                editingId === product.id ? (
                  <EditProductRow key={product.id} product={product} onDone={() => setEditingId(null)} />
                ) : (
                  <ProductRow key={product.id} product={product} onEdit={() => setEditingId(product.id)} />
                ),
              )}
            </tbody>
          </table>
        </div>
      </QueryState>
    </>
  )
}

function useProductMutations() {
  const queryClient = useQueryClient()
  const refresh = () => queryClient.invalidateQueries({ queryKey: ['products'] })
  return {
    update: useMutation({
      mutationFn: ({ id, data }: { id: number; data: ProductUpdate }) => api.products.update(id, data),
      onSuccess: refresh,
    }),
    remove: useMutation({ mutationFn: api.products.remove, onSuccess: refresh }),
  }
}

function ProductRow({ product, onEdit }: { product: Product; onEdit: () => void }) {
  const { update, remove } = useProductMutations()
  const busy = update.isPending || remove.isPending
  const error = update.error ?? remove.error

  return (
    <>
      <tr className={product.is_active ? undefined : 'inactive'}>
        <td className="mono">{product.code}</td>
        <td>{product.name}</td>
        <td className="muted">{product.description}</td>
        <td className="num">{money(product.price)}</td>
        <td>
          <span className={product.is_active ? 'badge badge-ready' : 'badge badge-cancelled'}>
            {product.is_active ? 'On sale' : 'Retired'}
          </span>
        </td>
        <td className="row-actions">
          <button className="quiet" disabled={busy} onClick={onEdit}>
            Edit
          </button>
          <button
            className="quiet"
            disabled={busy}
            onClick={() => update.mutate({ id: product.id, data: { is_active: !product.is_active } })}
          >
            {product.is_active ? 'Retire' : 'Put on sale'}
          </button>
          <button
            className="danger-quiet"
            disabled={busy}
            onClick={() => {
              if (confirm(`Delete ${product.name}? This can't be undone.`)) remove.mutate(product.id)
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

function EditProductRow({ product, onDone }: { product: Product; onDone: () => void }) {
  const { update } = useProductMutations()
  const [name, setName] = useState(product.name)
  const [description, setDescription] = useState(product.description ?? '')
  const [price, setPrice] = useState(product.price)

  const save = (event: FormEvent) => {
    event.preventDefault()
    update.mutate(
      { id: product.id, data: { name: name.trim(), description: description.trim() || null, price } },
      { onSuccess: onDone },
    )
  }
  const formId = `edit-product-${product.id}`

  return (
    <>
      <tr className="editing">
        <td className="mono">{product.code}</td>
        <td>
          <input form={formId} aria-label="Name" value={name} maxLength={100} required onChange={(e) => setName(e.target.value)} />
        </td>
        <td>
          <input form={formId} aria-label="Description" value={description} maxLength={255} onChange={(e) => setDescription(e.target.value)} />
        </td>
        <td className="num">
          <input form={formId} aria-label="Price" className="price-input" inputMode="decimal" pattern={PRICE_PATTERN} value={price} required onChange={(e) => setPrice(e.target.value)} />
        </td>
        <td />
        <td className="row-actions">
          <form id={formId} onSubmit={save} />
          <button form={formId} type="submit" className="primary" disabled={update.isPending}>
            Save
          </button>
          <button className="quiet" onClick={onDone}>
            Cancel
          </button>
        </td>
      </tr>
      {update.error && (
        <tr className="error-row">
          <td colSpan={6}>
            <ErrorNote error={update.error} />
          </td>
        </tr>
      )}
    </>
  )
}

function AddProductForm({ onDone }: { onDone: () => void }) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState<ProductCreate>({ code: '', name: '', price: '', description: '' })
  const set = (key: keyof ProductCreate) => (e: { target: { value: string } }) =>
    setForm((f) => ({ ...f, [key]: e.target.value }))

  const create = useMutation({
    mutationFn: api.products.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
      onDone()
    },
  })

  const submit = (event: FormEvent) => {
    event.preventDefault()
    create.mutate({
      code: form.code.trim().toUpperCase(),
      name: form.name.trim(),
      price: form.price,
      description: form.description?.trim() || null,
    })
  }

  return (
    <form className="card form" onSubmit={submit}>
      <h2>New product</h2>
      <div className="form-grid">
        <Field label="Code">
          <input value={form.code} onChange={set('code')} maxLength={20} required placeholder="CAKE-CHOC" autoFocus />
        </Field>
        <Field label="Name">
          <input value={form.name} onChange={set('name')} maxLength={100} required placeholder="Chocolate fudge cake" />
        </Field>
        <Field label="Price ($)">
          <input value={form.price} onChange={set('price')} inputMode="decimal" pattern={PRICE_PATTERN} required placeholder="24.50" />
        </Field>
        <Field label="Description (optional)" wide>
          <input value={form.description ?? ''} onChange={set('description')} maxLength={255} />
        </Field>
      </div>
      <div className="form-footer">
        <ErrorNote error={create.error} />
        <div className="page-actions">
          <button type="button" className="quiet" onClick={onDone}>
            Cancel
          </button>
          <button type="submit" className="primary" disabled={create.isPending}>
            Add product
          </button>
        </div>
      </div>
    </form>
  )
}
