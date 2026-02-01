import { FormEvent, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'

import { apiFetch } from '../lib/api'
import { Skeleton } from '../components/Skeleton'

type PickSession = {
  id: string
  status: string
  total_orders: number
  total_items: number
  picked_items: number
}

export function PickSessionsPage() {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['pick-sessions'],
    queryFn: () => apiFetch<PickSession[]>('/picker/sessions')
  })

  const [orderIdsInput, setOrderIdsInput] = useState('')
  const [status, setStatus] = useState<string | null>(null)

  const handleCreate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const orderIds = orderIdsInput
      .split(',')
      .map((value) => value.trim())
      .filter(Boolean)
    if (!orderIds.length) return
    await apiFetch('/picker/sessions', {
      method: 'POST',
      body: JSON.stringify({ order_ids: orderIds })
    })
    setOrderIdsInput('')
    setStatus('Pick session created')
    await refetch()
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold">Pick Sessions</h1>

      <form className="mt-4 rounded-lg border bg-white p-4" onSubmit={handleCreate}>
        <label className="text-sm font-medium text-slate-700">Order IDs (comma separated)</label>
        <input
          className="mt-2 w-full rounded-md border px-3 py-2 text-sm"
          value={orderIdsInput}
          onChange={(event) => setOrderIdsInput(event.target.value)}
          placeholder="uuid-1, uuid-2"
        />
        <button className="mt-3 rounded-md bg-slate-900 px-4 py-2 text-sm text-white" type="submit">
          Create session
        </button>
        {status ? <p className="mt-2 text-xs text-emerald-600">{status}</p> : null}
      </form>

      {isLoading ? (
        <div className="mt-6 space-y-2">
          <Skeleton className="h-5 w-40" />
          <Skeleton className="h-32 w-full" />
        </div>
      ) : (
        <div className="mt-6 overflow-x-auto rounded-lg border bg-white">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Session</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Orders</th>
                <th className="px-4 py-3">Picked</th>
              </tr>
            </thead>
            <tbody>
              {data?.map((session) => (
                <tr key={session.id} className="border-t">
                  <td className="px-4 py-3">
                    <Link to={`/picker/${session.id}`} className="font-medium text-slate-900">
                      {session.id.slice(0, 8)}...
                    </Link>
                  </td>
                  <td className="px-4 py-3">{session.status}</td>
                  <td className="px-4 py-3">{session.total_orders}</td>
                  <td className="px-4 py-3">
                    {session.picked_items}/{session.total_items}
                  </td>
                </tr>
              ))}
              {!data?.length ? (
                <tr>
                  <td className="px-4 py-4 text-sm text-slate-500" colSpan={4}>
                    No pick sessions yet.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
