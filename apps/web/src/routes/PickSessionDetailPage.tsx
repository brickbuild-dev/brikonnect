import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useParams } from '@tanstack/react-router'

import { apiFetch } from '../lib/api'
import { Skeleton } from '../components/Skeleton'

type PickSession = {
  id: string
  status: string
  total_orders: number
  total_items: number
  picked_items: number
}

type RouteItem = {
  order_line_id: string
  order_id: string
  item_no: string
  qty_ordered: number
  location_code?: string | null
}

type PickEvent = {
  id: string
  event_type: string
  qty: number
  location_code?: string | null
}

export function PickSessionDetailPage() {
  const { sessionId } = useParams({ from: '/picker/$sessionId' })
  const [message, setMessage] = useState<string | null>(null)

  const sessionQuery = useQuery({
    queryKey: ['pick-session', sessionId],
    queryFn: () => apiFetch<PickSession>(`/picker/sessions/${sessionId}`)
  })
  const routeQuery = useQuery({
    queryKey: ['pick-session', sessionId, 'route'],
    queryFn: () => apiFetch<RouteItem[]>(`/picker/sessions/${sessionId}/route`)
  })
  const eventsQuery = useQuery({
    queryKey: ['pick-session', sessionId, 'events'],
    queryFn: () => apiFetch<PickEvent[]>(`/picker/sessions/${sessionId}/events`)
  })

  const updateStatus = async (status: string) => {
    await apiFetch(`/picker/sessions/${sessionId}`, {
      method: 'PATCH',
      body: JSON.stringify({ status })
    })
    setMessage(`Session marked ${status}`)
    await sessionQuery.refetch()
  }

  const recordPick = async (item: RouteItem, eventType: 'PICKED' | 'MISSING') => {
    await apiFetch(`/picker/sessions/${sessionId}/pick`, {
      method: 'POST',
      body: JSON.stringify({
        order_line_id: item.order_line_id,
        event_type: eventType,
        qty: item.qty_ordered,
        location_code: item.location_code
      })
    })
    await sessionQuery.refetch()
    await eventsQuery.refetch()
  }

  if (sessionQuery.isLoading || !sessionQuery.data) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-24 w-full" />
      </div>
    )
  }

  const session = sessionQuery.data

  return (
    <div>
      <h1 className="text-2xl font-semibold">Pick Session</h1>
      <p className="mt-1 text-sm text-slate-500">Status: {session.status}</p>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <button
          className="rounded-md border px-3 py-2 text-sm"
          onClick={() => void updateStatus('ACTIVE')}
        >
          Start picking
        </button>
        <button
          className="rounded-md border px-3 py-2 text-sm"
          onClick={() => void updateStatus('COMPLETED')}
        >
          Complete session
        </button>
        {message ? <span className="text-xs text-emerald-600">{message}</span> : null}
      </div>

      <div className="mt-6 overflow-x-auto rounded-lg border bg-white">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Item</th>
              <th className="px-4 py-3">Location</th>
              <th className="px-4 py-3">Qty</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {routeQuery.data?.map((item) => (
              <tr key={item.order_line_id} className="border-t">
                <td className="px-4 py-3">{item.item_no}</td>
                <td className="px-4 py-3">{item.location_code ?? '-'}</td>
                <td className="px-4 py-3">{item.qty_ordered}</td>
                <td className="px-4 py-3 space-x-2">
                  <button
                    className="rounded-md bg-slate-900 px-3 py-1 text-xs text-white"
                    onClick={() => void recordPick(item, 'PICKED')}
                  >
                    Picked
                  </button>
                  <button
                    className="rounded-md border px-3 py-1 text-xs"
                    onClick={() => void recordPick(item, 'MISSING')}
                  >
                    Missing
                  </button>
                </td>
              </tr>
            ))}
            {!routeQuery.data?.length ? (
              <tr>
                <td className="px-4 py-4 text-sm text-slate-500" colSpan={4}>
                  No route items yet.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>

      <div className="mt-6 rounded-lg border bg-white p-4">
        <h2 className="text-sm font-medium text-slate-700">Pick Events</h2>
        <ul className="mt-2 space-y-2 text-sm text-slate-600">
          {eventsQuery.data?.map((event) => (
            <li key={event.id}>
              {event.event_type} · {event.qty} · {event.location_code ?? '-'}
            </li>
          ))}
          {!eventsQuery.data?.length ? <li>No events yet.</li> : null}
        </ul>
      </div>
    </div>
  )
}
