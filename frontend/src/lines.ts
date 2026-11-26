// Draft line items for the order and standing order forms (see LineEditor).

import type { Product } from './api'
import { toCents } from './format'

export interface DraftLine {
  key: number
  productId: string
  quantity: string
}

let nextLineKey = 1
export const blankLine = (productId = '', quantity = '1'): DraftLine => ({
  key: nextLineKey++,
  productId,
  quantity,
})

/** The line's value in cents at current prices, or 0 if it's incomplete or invalid. */
export function lineCents(line: DraftLine, products: Product[]): number {
  const price = products.find((p) => String(p.id) === line.productId)?.price
  const qty = Number(line.quantity)
  return price && Number.isInteger(qty) && qty > 0 ? toCents(price) * qty : 0
}
