import { FormEvent, useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'

import { apiFetch } from '../lib/api'

type Store = {
  id: string
  channel: string
  name: string
  is_primary: boolean
}

type SyncRun = {
  id: string
  status: string
  direction: string
  mode: string
  plan_summary?: { add: number; update: number; remove: number; unmatched?: number; skip?: number }
  created_at?: string
}

export function SyncPage() {
  const { data: stores } = useQuery({
    queryKey: ['stores'],
    queryFn: () => apiFetch<Store[]>('/stores')
  })
  const { data: runs, refetch } = useQuery({
    queryKey: ['syncRuns'],
    queryFn: () => apiFetch<SyncRun[]>('/sync/runs')
  })

  const [sourceId, setSourceId] = useState('')
  const [targetId, setTargetId] = useState('')
  const [allowLargeRemovals, setAllowLargeRemovals] = useState(false)
  const [status, setStatus] = useState<string | null>(null)

  useEffect(() => {
    if (!stores?.length) return
    if (!sourceId) {
      const primary = stores.find((store) => store.is_primary) ?? stores[0]
      setSourceId(primary.id)
    }
    if (!targetId) {
      const fallback = stores.find((store) => !store.is_primary) ?? stores[0]
      setTargetId(fallback.id)
    }
  }, [stores, sourceId, targetId])

  const handlePreview = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setStatus(null)
    if (!sourceId || !targetId) return
    const response = await apiFetch<{ run: SyncRun }>('/sync/preview', {
      method: 'POST',
      body: JSON.stringify({
        source_store_id: sourceId,
        target_store_id: targetId,
        direction: 'SOURCE_TO_TARGET',
        allow_large_removals: allowLargeRemovals
      })
    })
    setStatus(`Preview ready (${response.run.id.slice(0, 8)})`)
    await refetch()
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold">Sync</h1>

      <form className="mt-6 rounded-lg border bg-white p-4" onSubmit={handlePreview}>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="text-sm font-medium text-slate-700">Source store</label>
            <select
              className="mt-2 w-full rounded-md border px-3 py-2 text-sm"
              value={sourceId}
              onChange={(event) => setSourceId(event.target.value)}
            >
              {stores?.map((store) => (
                <option key={store.id} value={store.id}>
                  {store.name} ({store.channel})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">Target store</label>
            <select
              className="mt-2 w-full rounded-md border px-3 py-2 text-sm"
              value={targetId}
              onChange={(event) => setTargetId(event.target.value)}
            >
              {stores?.map((store) => (
                <option key={store.id} value={store.id}>
                  {store.name} ({store.channel})
                </option>
              ))}
            </select>
          </div>
        </div>
        <label className="mt-4 flex items-center gap-2 text-sm text-slate-600">
          <input
            type="checkbox"
            checked={allowLargeRemovals}
            onChange={(event) => setAllowLargeRemovals(event.target.checked)}
          />
          Allow large removals
        </label>
        <button className="mt-4 rounded-md bg-slate-900 px-4 py-2 text-sm text-white" type="submit">
          Create preview
        </button>
        {status ? <p className="mt-2 text-sm text-emerald-600">{status}</p> : null}
      </form>

      <div className="mt-8">
        <h2 className="text-lg font-semibold">Recent runs</h2>
        <div className="mt-4 overflow-x-auto rounded-lg border bg-white">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Mode</th>
                <th className="px-4 py-3">Summary</th>
                <th className="px-4 py-3">Created</th>
                <th className="px-4 py-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {runs?.map((run) => (
                <tr key={run.id} className="border-t">
                  <td className="px-4 py-3 font-medium text-slate-900">{run.status}</td>
                  <td className="px-4 py-3">{run.mode}</td>
                  <td className="px-4 py-3 text-slate-500">
                    {run.plan_summary
                      ? `+${run.plan_summary.add ?? 0} / ~${run.plan_summary.update ?? 0} / -${
                          run.plan_summary.remove ?? 0
                        }`
                      : '-'}
                  </td>
                  <td className="px-4 py-3 text-slate-500">
                    {run.created_at ? new Date(run.created_at).toLocaleString() : '-'}
                  </td>
                  <td className="px-4 py-3">
                    <Link to="/sync/$runId" params={{ runId: run.id }} className="text-slate-700">
                      View
                    </Link>
                  </td>
                </tr>
              ))}
              {!runs?.length ? (
                <tr>
                  <td className="px-4 py-4 text-sm text-slate-500" colSpan={5}>
                    No sync runs yet.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
