import { FormEvent, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { apiFetch } from '../lib/api'
import { Skeleton } from '../components/Skeleton'

type Location = {
  id: string
  code: string
  zone?: string | null
  aisle?: string | null
  shelf?: string | null
  bin?: string | null
}

export function LocationsPage() {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['locations'],
    queryFn: () => apiFetch<Location[]>('/locations')
  })

  const [code, setCode] = useState('')
  const [zone, setZone] = useState('')
  const [aisle, setAisle] = useState('')
  const [status, setStatus] = useState<string | null>(null)

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setStatus(null)
    await apiFetch('/locations', {
      method: 'POST',
      body: JSON.stringify({ code, zone: zone || undefined, aisle: aisle || undefined })
    })
    setCode('')
    setZone('')
    setAisle('')
    setStatus('Location added')
    await refetch()
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold">Locations</h1>

      <form className="mt-6 rounded-lg border bg-white p-4" onSubmit={handleSubmit}>
        <div className="grid gap-4 sm:grid-cols-3">
          <div>
            <label className="text-sm font-medium text-slate-700">Code</label>
            <input
              className="mt-2 w-full rounded-md border px-3 py-2 text-sm"
              value={code}
              onChange={(event) => setCode(event.target.value)}
              required
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">Zone</label>
            <input
              className="mt-2 w-full rounded-md border px-3 py-2 text-sm"
              value={zone}
              onChange={(event) => setZone(event.target.value)}
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">Aisle</label>
            <input
              className="mt-2 w-full rounded-md border px-3 py-2 text-sm"
              value={aisle}
              onChange={(event) => setAisle(event.target.value)}
            />
          </div>
        </div>
        <button className="mt-4 rounded-md bg-slate-900 px-4 py-2 text-sm text-white" type="submit">
          Add location
        </button>
        {status ? <p className="mt-2 text-sm text-emerald-600">{status}</p> : null}
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
                <th className="px-4 py-3">Code</th>
                <th className="px-4 py-3">Zone</th>
                <th className="px-4 py-3">Aisle</th>
              </tr>
            </thead>
            <tbody>
              {data?.map((location) => (
                <tr key={location.id} className="border-t">
                  <td className="px-4 py-3 font-medium text-slate-900">{location.code}</td>
                  <td className="px-4 py-3">{location.zone ?? '-'}</td>
                  <td className="px-4 py-3">{location.aisle ?? '-'}</td>
                </tr>
              ))}
              {!data?.length ? (
                <tr>
                  <td className="px-4 py-4 text-sm text-slate-500" colSpan={3}>
                    No locations created yet.
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
