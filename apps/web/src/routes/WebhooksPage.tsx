import { FormEvent, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { apiFetch } from '../lib/api'
import { Skeleton } from '../components/Skeleton'

type Webhook = {
  id: string
  url: string
  events: string[]
  is_enabled: boolean
}

export function WebhooksPage() {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['webhooks'],
    queryFn: () => apiFetch<Webhook[]>('/webhooks')
  })

  const [url, setUrl] = useState('')
  const [events, setEvents] = useState('')
  const [status, setStatus] = useState<string | null>(null)

  const handleCreate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const eventsList = events
      .split(',')
      .map((value) => value.trim())
      .filter(Boolean)
    await apiFetch('/webhooks', {
      method: 'POST',
      body: JSON.stringify({ url, events: eventsList })
    })
    setUrl('')
    setEvents('')
    setStatus('Webhook created')
    await refetch()
  }

  const handleTest = async (id: string) => {
    await apiFetch(`/webhooks/${id}/test`, { method: 'POST' })
    setStatus('Test event queued')
  }

  const handleDelete = async (id: string) => {
    await apiFetch(`/webhooks/${id}`, { method: 'DELETE' })
    setStatus('Webhook deleted')
    await refetch()
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold">Webhooks</h1>

      <form className="mt-4 rounded-lg border bg-white p-4" onSubmit={handleCreate}>
        <label className="text-sm font-medium text-slate-700">Webhook URL</label>
        <input
          className="mt-2 w-full rounded-md border px-3 py-2 text-sm"
          value={url}
          onChange={(event) => setUrl(event.target.value)}
          placeholder="https://example.com/webhook"
        />
        <label className="mt-4 block text-sm font-medium text-slate-700">Events (comma separated)</label>
        <input
          className="mt-2 w-full rounded-md border px-3 py-2 text-sm"
          value={events}
          onChange={(event) => setEvents(event.target.value)}
          placeholder="order.created, inventory.updated"
        />
        <button className="mt-4 rounded-md bg-slate-900 px-4 py-2 text-sm text-white" type="submit">
          Create webhook
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
                <th className="px-4 py-3">URL</th>
                <th className="px-4 py-3">Events</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {data?.map((hook) => (
                <tr key={hook.id} className="border-t">
                  <td className="px-4 py-3">{hook.url}</td>
                  <td className="px-4 py-3">{hook.events.join(', ')}</td>
                  <td className="px-4 py-3 space-x-2">
                    <button
                      className="rounded-md border px-2 py-1 text-xs"
                      onClick={() => void handleTest(hook.id)}
                    >
                      Test
                    </button>
                    <button
                      className="rounded-md border px-2 py-1 text-xs"
                      onClick={() => void handleDelete(hook.id)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
              {!data?.length ? (
                <tr>
                  <td className="px-4 py-4 text-sm text-slate-500" colSpan={3}>
                    No webhooks configured.
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
