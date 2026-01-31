import { FormEvent, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useParams } from '@tanstack/react-router'

import { apiFetch } from '../lib/api'

type InventoryItem = {
  id: string
  item_no: string
  item_type: string
  condition: string
  qty_available: number
  remarks?: string | null
  version: number
}

export function InventoryDetailPage() {
  const { itemId } = useParams({ from: '/inventory/$itemId' })
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['inventory', itemId],
    queryFn: () => apiFetch<InventoryItem>(`/inventory/${itemId}`)
  })
  const [qty, setQty] = useState<number | ''>('')
  const [remarks, setRemarks] = useState('')
  const [status, setStatus] = useState<string | null>(null)

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!data) return
    setStatus(null)
    await apiFetch(`/inventory/${itemId}`, {
      method: 'PATCH',
      body: JSON.stringify({
        qty_available: qty === '' ? data.qty_available : qty,
        remarks: remarks || data.remarks,
        version: data.version
      })
    })
    setQty('')
    setRemarks('')
    setStatus('Saved')
    await refetch()
  }

  if (isLoading || !data) {
    return <div className="text-sm text-slate-500">Loading item...</div>
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold">{data.item_no}</h1>
      <p className="mt-1 text-sm text-slate-500">
        {data.item_type} · {data.condition}
      </p>

      <form className="mt-6 space-y-4 rounded-lg border bg-white p-4" onSubmit={handleSubmit}>
        <div>
          <label className="text-sm font-medium text-slate-700">Available Qty</label>
          <input
            type="number"
            className="mt-2 w-full rounded-md border px-3 py-2 text-sm"
            value={qty}
            onChange={(event) => setQty(event.target.value === '' ? '' : Number(event.target.value))}
            placeholder={String(data.qty_available)}
          />
        </div>
        <div>
          <label className="text-sm font-medium text-slate-700">Remarks</label>
          <textarea
            className="mt-2 w-full rounded-md border px-3 py-2 text-sm"
            rows={3}
            value={remarks}
            onChange={(event) => setRemarks(event.target.value)}
            placeholder={data.remarks ?? ''}
          />
        </div>
        <button className="rounded-md bg-slate-900 px-4 py-2 text-sm text-white" type="submit">
          Save
        </button>
        {status ? <p className="text-sm text-emerald-600">{status}</p> : null}
      </form>
    </div>
  )
}
