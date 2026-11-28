import { useState } from 'react'
import { useSearchParams } from 'react-router'
import { WEEKDAYS } from '../api'
import { PageHeader } from '../components'
import { DAY_LABELS, DAY_SHORT } from '../format'

// Dates here are local calendar days, keyed as "YYYY-MM-DD".
const pad = (n: number) => String(n).padStart(2, '0')
const dayKey = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
const monthKey = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}`

/** The month named by ?month=YYYY-MM, or the current month. */
function parseMonth(value: string | null): Date {
  const match = value?.match(/^(\d{4})-(\d{2})$/)
  if (match) {
    const month = Number(match[2])
    if (month >= 1 && month <= 12) return new Date(Number(match[1]), month - 1, 1)
  }
  const now = new Date()
  return new Date(now.getFullYear(), now.getMonth(), 1)
}

/** Every day shown for a month: whole weeks, Sunday first, padded with days from the
 * months either side. */
function monthGrid(first: Date): Date[] {
  const start = new Date(first.getFullYear(), first.getMonth(), 1 - first.getDay())
  const last = new Date(first.getFullYear(), first.getMonth() + 1, 0)
  const days = Math.ceil((first.getDay() + last.getDate()) / 7) * 7
  return Array.from({ length: days }, (_, i) => new Date(start.getFullYear(), start.getMonth(), start.getDate() + i))
}

const monthTitle = new Intl.DateTimeFormat(undefined, { month: 'long', year: 'numeric' })
const longDate = new Intl.DateTimeFormat(undefined, { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })

export default function CalendarPage() {
  const [params, setParams] = useSearchParams()
  const month = parseMonth(params.get('month'))
  const selected = params.get('day')
  // Fixed when the page opens; fine for a calendar that isn't left open past midnight.
  const [today] = useState(() => dayKey(new Date()))

  const days = monthGrid(month)
  const goTo = (d: Date, day?: string) => setParams(day ? { month: monthKey(d), day } : { month: monthKey(d) })
  const shift = (months: number) => goTo(new Date(month.getFullYear(), month.getMonth() + months, 1))
  const selectedDate = selected ? days.find((d) => dayKey(d) === selected) : undefined

  return (
    <>
      <PageHeader
        title="Calendar"
        actions={
          <div className="month-nav">
            <button className="icon" aria-label="Previous month" onClick={() => shift(-1)}>
              ‹
            </button>
            <h2 className="month-title">{monthTitle.format(month)}</h2>
            <button className="icon" aria-label="Next month" onClick={() => shift(1)}>
              ›
            </button>
            <button className="quiet" onClick={() => goTo(new Date(), today)}>
              Today
            </button>
          </div>
        }
      />

      <div className="calendar" role="grid" aria-label={monthTitle.format(month)}>
        {WEEKDAYS.map((w) => (
          <div key={w} className="calendar-weekday" role="columnheader" aria-label={DAY_LABELS[w]}>
            {DAY_SHORT[w]}
          </div>
        ))}
        {days.map((day) => {
          const key = dayKey(day)
          const classes = [
            'calendar-day',
            day.getMonth() !== month.getMonth() && 'outside',
            key === today && 'today',
            key === selected && 'selected',
          ]
          return (
            <button
              key={key}
              role="gridcell"
              className={classes.filter(Boolean).join(' ')}
              aria-pressed={key === selected}
              aria-label={longDate.format(day)}
              onClick={() => goTo(month, key === selected ? undefined : key)}
            >
              <span className="calendar-date">{day.getDate()}</span>
            </button>
          )
        })}
      </div>

      {selectedDate && (
        <section className="card day-detail" aria-live="polite">
          <h2>{longDate.format(selectedDate)}</h2>
          <p className="muted">Nothing to show for this day yet.</p>
        </section>
      )}
    </>
  )
}
