import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'

import { apiFetch } from '../lib/api'

type InventoryItem = {
  id: string
  item_type: string
  item_no: string
  condition: string
  qty_available: number
  unit_price: string | null
  version: number
}

export function InventoryPage() {
  const [search, setSearch] = useState('')
  const [importJob, setImportJob] = useState<string | null>(null)
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['inventory', search],
    queryFn: () =>
      apiFetch<InventoryItem[]>(
        `/inventory${search ? `?q=${encodeURIComponent(search)}` : ''}`
      )
  })

  const handleImport = async () => {
    const job = await apiFetch<{ id: string }>('/inventory/import', { method: 'POST' })
    setImportJob(job.id)
  }

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Inventory</h1>
        <button
          className="rounded-md border px-3 py-2 text-sm"
          onClick={() => void handleImport()}
        >
          Run import
        </button>
      </div>
      {importJob ? (
        <p className="mt-2 text-xs text-slate-500">Import job: {importJob}</p>
      ) : null}
      <div className="mt-4 flex items-center gap-2">
        <input
          className="w-64 rounded-md border px-3 py-2 text-sm"
          placeholder="Search by part number or description"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <button
          className="rounded-md bg-slate-900 px-3 py-2 text-sm text-white"
          onClick={() => void refetch()}
        >
          Filter
        </button>
      </div>

      {isLoading ? (
        <div className="mt-6 text-sm text-slate-500">Loading inventory...</div>
      ) : (
        <div className="mt-6 overflow-hidden rounded-lg border bg-white">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Item</th>
                <th className="px-4 py-3">Condition</th>
                <th className="px-4 py-3">Qty</th>
                <th className="px-4 py-3">Price</th>
              </tr>
            </thead>
            <tbody>
              {data?.map((item) => (
                <tr key={item.id} className="border-t">
                  <td className="px-4 py-3">
                    <Link to={`/inventory/${item.id}`} className="font-medium text-slate-900">
                      {item.item_no}
                    </Link>
                    <div className="text-xs text-slate-500">{item.item_type}</div>
                  </td>
                  <td className="px-4 py-3">{item.condition}</td>
                  <td className="px-4 py-3">{item.qty_available}</td>
                  <td className="px-4 py-3">{item.unit_price ?? '-'}</td>
                </tr>
              ))}
              {!data?.length ? (
                <tr>
                  <td className="px-4 py-4 text-sm text-slate-500" colSpan={4}>
                    No inventory items found.
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
