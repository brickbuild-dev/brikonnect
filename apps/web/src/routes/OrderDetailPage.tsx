import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useParams } from '@tanstack/react-router'

import { apiFetch } from '../lib/api'

type OrderLine = {
  id: string
  item_no: string
  item_type: string
  qty_ordered: number
  status: string
}

type Order = {
  id: string
  external_order_id: string
  status: string
  buyer_name?: string | null
  lines: OrderLine[]
}

type StatusEvent = {
  id: string
  from_status?: string | null
  to_status: string
  changed_at?: string | null
  notes?: string | null
}

const STATUS_OPTIONS = [
  'NEW',
  'PENDING',
  'PICKING',
  'PACKING',
  'READY',
  'SHIPPED',
  'DELIVERED',
  'COMPLETED',
  'CANCELLED',
  'REFUNDED'
]

export function OrderDetailPage() {
  const { orderId } = useParams({ from: '/orders/$orderId' })
  const [status, setStatus] = useState('')
  const [statusNote, setStatusNote] = useState('')
  const [message, setMessage] = useState<string | null>(null)

  const orderQuery = useQuery({
    queryKey: ['orders', orderId],
    queryFn: () => apiFetch<Order>(`/orders/${orderId}`)
  })
  const historyQuery = useQuery({
    queryKey: ['orders', orderId, 'history'],
    queryFn: () => apiFetch<StatusEvent[]>(`/orders/${orderId}/history`)
  })

  const handleStatusUpdate = async () => {
    if (!status) return
    setMessage(null)
    await apiFetch(`/orders/${orderId}/status`, {
      method: 'POST',
      body: JSON.stringify({ status, notes: statusNote || undefined })
    })
    setStatus('')
    setStatusNote('')
    setMessage('Status updated')
    await orderQuery.refetch()
    await historyQuery.refetch()
  }

  if (orderQuery.isLoading || !orderQuery.data) {
    return <div className="text-sm text-slate-500">Loading order...</div>
  }

  const order = orderQuery.data

  return (
    <div>
      <h1 className="text-2xl font-semibold">{order.external_order_id}</h1>
      <p className="mt-1 text-sm text-slate-500">{order.buyer_name ?? 'Unknown buyer'}</p>

      <div className="mt-6 rounded-lg border bg-white p-4">
        <div className="text-sm font-medium">Status</div>
        <div className="mt-1 text-sm text-slate-600">Current: {order.status}</div>
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <select
            className="rounded-md border px-3 py-2 text-sm"
            value={status}
            onChange={(event) => setStatus(event.target.value)}
          >
            <option value="">Change status...</option>
            {STATUS_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
          <input
            className="flex-1 rounded-md border px-3 py-2 text-sm"
            placeholder="Notes (optional)"
            value={statusNote}
            onChange={(event) => setStatusNote(event.target.value)}
          />
          <button
            className="rounded-md bg-slate-900 px-3 py-2 text-sm text-white"
            onClick={() => void handleStatusUpdate()}
          >
            Update
          </button>
        </div>
        {message ? <p className="mt-2 text-sm text-emerald-600">{message}</p> : null}
      </div>

      <div className="mt-6 overflow-hidden rounded-lg border bg-white">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Item</th>
              <th className="px-4 py-3">Qty</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {order.lines.map((line) => (
              <tr key={line.id} className="border-t">
                <td className="px-4 py-3">
                  {line.item_no}
                  <div className="text-xs text-slate-500">{line.item_type}</div>
                </td>
                <td className="px-4 py-3">{line.qty_ordered}</td>
                <td className="px-4 py-3">{line.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-6 rounded-lg border bg-white p-4">
        <h2 className="text-sm font-medium text-slate-700">History</h2>
        {historyQuery.isLoading ? (
          <div className="mt-2 text-sm text-slate-500">Loading history...</div>
        ) : (
          <ul className="mt-2 space-y-2 text-sm text-slate-600">
            {historyQuery.data?.map((event) => (
              <li key={event.id}>
                {event.from_status ? `${event.from_status} → ` : ''}
                {event.to_status}
                {event.notes ? ` — ${event.notes}` : ''}
              </li>
            ))}
            {!historyQuery.data?.length ? <li>No history yet.</li> : null}
          </ul>
        )}
      </div>
    </div>
  )
}
