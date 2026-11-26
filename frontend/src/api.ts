// Types mirror the Pydantic schemas in app/models.py. Decimal fields arrive as strings
// (e.g. "24.50") so money never passes through floating point on the way in.

export type OrderStatus = 'created' | 'paid' | 'in_progress' | 'ready' | 'completed' | 'cancelled'

export const ORDER_STATUSES: OrderStatus[] = [
  'created',
  'paid',
  'in_progress',
  'ready',
  'completed',
  'cancelled',
]

export interface Product {
  id: number
  code: string
  name: string
  description: string | null
  price: string
  is_active: boolean
  created_at: string
}

export interface ProductCreate {
  code: string
  name: string
  description?: string | null
  price: string
  is_active?: boolean
}

export type ProductUpdate = Partial<Pick<Product, 'name' | 'description' | 'price' | 'is_active'>>

export interface Customer {
  id: number
  name: string
  email: string // "" when not on file
  phone: string // "" when not on file
  address: string // "" when not on file
  created_at: string
}

export type CustomerCreate = Omit<Customer, 'id' | 'created_at'>
export type CustomerUpdate = Partial<CustomerCreate>

export interface OrderLine {
  id: number
  product_id: number
  quantity: number
  unit_price: string
}

export interface Order {
  id: number
  customer_id: number
  status: OrderStatus
  notes: string | null
  created_at: string
  lines: OrderLine[]
  total: string
}

export interface OrderCreate {
  customer_id: number
  notes?: string | null
  lines: { product_id: number; quantity: number }[]
}

export type Weekday = 'sun' | 'mon' | 'tue' | 'wed' | 'thu' | 'fri' | 'sat'

export const WEEKDAYS: Weekday[] = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat']

export interface StandingOrderLine {
  id: number
  product_id: number
  quantity: number
}

export interface StandingOrder {
  id: number
  customer_id: number
  days: Weekday[] // Sunday-first, no duplicates, at least one
  notes: string | null
  is_active: boolean
  created_at: string
  lines: StandingOrderLine[]
}

export interface StandingOrderCreate {
  customer_id: number
  days: Weekday[]
  lines: { product_id: number; quantity: number }[]
  notes?: string | null
  is_active?: boolean
}

// The customer can't be changed after creation. `lines`, when sent, replaces all lines.
export type StandingOrderUpdate = Partial<Omit<StandingOrderCreate, 'customer_id'>>

export class ApiError extends Error {
  readonly status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

// FastAPI returns {detail: "message"} for HTTPException and
// {detail: [{loc, msg}, ...]} for request validation errors.
function describeError(body: unknown, fallback: string): string {
  const detail = (body as { detail?: unknown } | null)?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((d: { loc?: unknown[]; msg?: string }) => {
        const field = d.loc?.filter((part) => part !== 'body').join('.')
        return field ? `${field}: ${d.msg}` : d.msg
      })
      .join('; ')
  }
  return fallback
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...init,
    headers: init?.body ? { 'Content-Type': 'application/json' } : undefined,
  })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new ApiError(response.status, describeError(body, `${response.status} ${response.statusText}`))
  }
  return response.status === 204 ? (undefined as T) : response.json()
}

const send = (method: string, body?: unknown): RequestInit => ({
  method,
  body: body === undefined ? undefined : JSON.stringify(body),
})

// The API caps page size at 200; that's plenty for a single bakery's working set.
export const api = {
  products: {
    list: () => request<Product[]>('/products?limit=200'),
    create: (data: ProductCreate) => request<Product>('/products', send('POST', data)),
    update: (id: number, data: ProductUpdate) => request<Product>(`/products/${id}`, send('PATCH', data)),
    remove: (id: number) => request<void>(`/products/${id}`, send('DELETE')),
  },
  customers: {
    list: () => request<Customer[]>('/customers?limit=200'),
    create: (data: CustomerCreate) => request<Customer>('/customers', send('POST', data)),
    update: (id: number, data: CustomerUpdate) => request<Customer>(`/customers/${id}`, send('PATCH', data)),
  },
  orders: {
    list: (status?: OrderStatus) =>
      request<Order[]>(`/orders?limit=200${status ? `&status=${status}` : ''}`),
    create: (data: OrderCreate) => request<Order>('/orders', send('POST', data)),
    setStatus: (id: number, status: OrderStatus) =>
      request<Order>(`/orders/${id}/status`, send('PATCH', { status })),
  },
  standingOrders: {
    list: () => request<StandingOrder[]>('/standing-orders?limit=200'),
    create: (data: StandingOrderCreate) => request<StandingOrder>('/standing-orders', send('POST', data)),
    update: (id: number, data: StandingOrderUpdate) =>
      request<StandingOrder>(`/standing-orders/${id}`, send('PATCH', data)),
    remove: (id: number) => request<void>(`/standing-orders/${id}`, send('DELETE')),
  },
}
