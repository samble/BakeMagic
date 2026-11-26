import type { OrderStatus, Weekday } from './api'

const currency = new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD' })
const dateTime = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' })

export const money = (value: string | number) => currency.format(Number(value))

export const when = (iso: string) => dateTime.format(new Date(iso))

export const STATUS_LABELS: Record<OrderStatus, string> = {
  created: 'New',
  paid: 'Paid',
  in_progress: 'Baking',
  ready: 'Ready',
  completed: 'Completed',
  cancelled: 'Cancelled',
}

// The usual path an order takes; the backend accepts any change until an order is finished.
export const NEXT_STATUS: Partial<Record<OrderStatus, OrderStatus>> = {
  created: 'paid',
  paid: 'in_progress',
  in_progress: 'ready',
  ready: 'completed',
}

export const isFinished = (status: OrderStatus) => status === 'completed' || status === 'cancelled'

// Sum line totals in integer cents to avoid floating-point drift.
export const toCents = (value: string | number) => Math.round(Number(value) * 100)
export const fromCents = (cents: number) => (cents / 100).toFixed(2)

export const DAY_LABELS: Record<Weekday, string> = {
  sun: 'Sunday',
  mon: 'Monday',
  tue: 'Tuesday',
  wed: 'Wednesday',
  thu: 'Thursday',
  fri: 'Friday',
  sat: 'Saturday',
}

export const DAY_SHORT: Record<Weekday, string> = {
  sun: 'Sun',
  mon: 'Mon',
  tue: 'Tue',
  wed: 'Wed',
  thu: 'Thu',
  fri: 'Fri',
  sat: 'Sat',
}
