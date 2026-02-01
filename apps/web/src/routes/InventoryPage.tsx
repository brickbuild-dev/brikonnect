import { useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'

import { apiFetch, apiUpload } from '../lib/api'
import { Skeleton } from '../components/Skeleton'

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
  const [brickognizeResults, setBrickognizeResults] = useState<
    { item_no: string; confidence: number }[]
  >([])
  const fileInputRef = useRef<HTMLInputElement>(null)
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

  const handleIdentify = async (file: File) => {
    const formData = new FormData()
    formData.append('image', file)
    const result = await apiUpload<{ predictions: { item_no: string; confidence: number }[] }>(
      '/brickognize/identify',
      formData
    )
    setBrickognizeResults(result.predictions)
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
      <div className="mt-4 flex flex-wrap items-center gap-2">
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
        <button
          className="rounded-md border px-3 py-2 text-sm text-slate-600"
          onClick={() => fileInputRef.current?.click()}
        >
          Identify part
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(event) => {
            const file = event.target.files?.[0]
            if (file) {
              void handleIdentify(file)
            }
          }}
        />
      </div>

      {brickognizeResults.length ? (
        <div className="mt-4 rounded-lg border bg-white p-3 text-sm">
          <div className="font-medium text-slate-700">Brickognize results</div>
          <ul className="mt-2 space-y-1 text-slate-600">
            {brickognizeResults.map((prediction) => (
              <li key={prediction.item_no}>
                {prediction.item_no} · {(prediction.confidence * 100).toFixed(1)}%
              </li>
            ))}
          </ul>
        </div>
      ) : null}

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
