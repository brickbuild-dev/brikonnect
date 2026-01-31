import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { apiFetch } from '../lib/api'

type AuditLog = {
  id: string
  action: string
  entity_type: string
  entity_id?: string | null
  actor_name?: string | null
  created_at?: string | null
}

export function AuditPage() {
  const [entityType, setEntityType] = useState('')
  const [entityId, setEntityId] = useState('')

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['audit', entityType, entityId],
    queryFn: () => {
      const params = new URLSearchParams()
      if (entityType) params.set('entity_type', entityType)
      if (entityId) params.set('entity_id', entityId)
      const qs = params.toString()
      return apiFetch<AuditLog[]>(`/audit${qs ? `?${qs}` : ''}`)
    }
  })

  const handleRevert = async (auditId: string) => {
    await apiFetch(`/audit/${auditId}/revert`, { method: 'POST' })
    await refetch()
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold">Audit Log</h1>
      <div className="mt-4 flex flex-wrap items-center gap-2">
        <input
          className="rounded-md border px-3 py-2 text-sm"
          placeholder="Entity type"
          value={entityType}
          onChange={(event) => setEntityType(event.target.value)}
        />
        <input
          className="rounded-md border px-3 py-2 text-sm"
          placeholder="Entity ID"
          value={entityId}
          onChange={(event) => setEntityId(event.target.value)}
        />
        <button
          className="rounded-md bg-slate-900 px-3 py-2 text-sm text-white"
          onClick={() => void refetch()}
        >
          Filter
        </button>
      </div>

      {isLoading ? (
        <div className="mt-6 text-sm text-slate-500">Loading audit log...</div>
      ) : (
        <div className="mt-6 overflow-hidden rounded-lg border bg-white">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Action</th>
                <th className="px-4 py-3">Entity</th>
                <th className="px-4 py-3">Actor</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {data?.map((log) => (
                <tr key={log.id} className="border-t">
                  <td className="px-4 py-3">{log.action}</td>
                  <td className="px-4 py-3">
                    {log.entity_type} {log.entity_id ?? ''}
                  </td>
                  <td className="px-4 py-3">{log.actor_name ?? '-'}</td>
                  <td className="px-4 py-3">
                    <button
                      className="rounded-md border px-2 py-1 text-xs"
                      onClick={() => void handleRevert(log.id)}
                    >
                      Revert
                    </button>
                  </td>
                </tr>
              ))}
              {!data?.length ? (
                <tr>
                  <td className="px-4 py-4 text-sm text-slate-500" colSpan={4}>
                    No audit logs found.
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
