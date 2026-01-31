import { useQuery } from '@tanstack/react-query'
import { useParams } from '@tanstack/react-router'

import { apiFetch } from '../lib/api'

type SyncRun = {
  id: string
  status: string
  mode: string
  direction: string
  plan_summary?: { add: number; update: number; remove: number; skip?: number }
  error_message?: string | null
}

type SyncPlanItem = {
  id: string
  action: string
  status: string
  skip_reason?: string | null
  before_state?: Record<string, any> | null
  after_state?: Record<string, any> | null
  changes?: Array<{ field: string; old: any; new: any }>
}

export function SyncRunDetailPage() {
  const { runId } = useParams({ from: '/sync/$runId' })
  const { data: run, refetch: refetchRun } = useQuery({
    queryKey: ['syncRun', runId],
    queryFn: () => apiFetch<SyncRun>(`/sync/runs/${runId}`)
  })
  const { data: plan, refetch: refetchPlan } = useQuery({
    queryKey: ['syncPlan', runId],
    queryFn: () => apiFetch<SyncPlanItem[]>(`/sync/runs/${runId}/plan`)
  })

  const handleApprove = async () => {
    await apiFetch(`/sync/runs/${runId}/approve`, { method: 'POST' })
    await refetchRun()
    await refetchPlan()
  }

  const handleCancel = async () => {
    await apiFetch(`/sync/runs/${runId}/cancel`, { method: 'POST' })
    await refetchRun()
  }

  const renderLabel = (item: SyncPlanItem) => {
    const state = item.after_state ?? item.before_state
    if (!state) return 'Unknown item'
    return `${state.item_no ?? 'Item'} · ${state.condition ?? ''}`
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold">Sync run</h1>
      <p className="mt-1 text-sm text-slate-500">Run ID: {runId}</p>

      {run ? (
        <div className="mt-6 rounded-lg border bg-white p-4">
          <div className="flex flex-wrap gap-4 text-sm text-slate-600">
            <span>Status: {run.status}</span>
            <span>Mode: {run.mode}</span>
            <span>Direction: {run.direction}</span>
            {run.plan_summary ? (
              <span>
                Summary: +{run.plan_summary.add ?? 0} / ~{run.plan_summary.update ?? 0} / -
                {run.plan_summary.remove ?? 0}
              </span>
            ) : null}
          </div>
          {run.error_message ? <p className="mt-2 text-sm text-red-600">{run.error_message}</p> : null}
          <div className="mt-4 flex gap-3">
            {run.status === 'PREVIEW_READY' ? (
              <button className="rounded-md bg-slate-900 px-4 py-2 text-sm text-white" onClick={handleApprove}>
                Approve and apply
              </button>
            ) : null}
            {['PREVIEW_READY', 'APPLYING'].includes(run.status) ? (
              <button className="rounded-md border px-4 py-2 text-sm text-slate-600" onClick={handleCancel}>
                Cancel
              </button>
            ) : null}
          </div>
        </div>
      ) : (
        <div className="mt-6 text-sm text-slate-500">Loading run...</div>
      )}

      <div className="mt-8">
        <h2 className="text-lg font-semibold">Plan items</h2>
        <div className="mt-4 overflow-hidden rounded-lg border bg-white">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Action</th>
                <th className="px-4 py-3">Item</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Changes</th>
              </tr>
            </thead>
            <tbody>
              {plan?.map((item) => (
                <tr key={item.id} className="border-t">
                  <td className="px-4 py-3 font-medium text-slate-900">{item.action}</td>
                  <td className="px-4 py-3">{renderLabel(item)}</td>
                  <td className="px-4 py-3 text-slate-500">
                    {item.status}
                    {item.skip_reason ? ` (${item.skip_reason})` : ''}
                  </td>
                  <td className="px-4 py-3 text-slate-500">
                    {item.changes?.length
                      ? item.changes.map((change) => `${change.field}: ${change.old} → ${change.new}`).join(', ')
                      : '-'}
                  </td>
                </tr>
              ))}
              {!plan?.length ? (
                <tr>
                  <td className="px-4 py-4 text-sm text-slate-500" colSpan={4}>
                    No plan items yet.
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
