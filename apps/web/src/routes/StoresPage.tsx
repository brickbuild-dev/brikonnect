import { FormEvent, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { apiFetch } from '../lib/api'
import { Skeleton } from '../components/Skeleton'

type Store = {
  id: string
  channel: string
  name: string
  is_primary: boolean
  is_enabled: boolean
  settings?: Record<string, unknown>
}

const CHANNELS = ['bricklink', 'brickowl', 'brikick', 'shopify', 'ebay', 'etsy', 'local']

export function StoresPage() {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['stores'],
    queryFn: () => apiFetch<Store[]>('/stores')
  })

  const [channel, setChannel] = useState(CHANNELS[0])
  const [name, setName] = useState('')
  const [isPrimary, setIsPrimary] = useState(false)
  const [isEnabled, setIsEnabled] = useState(true)
  const [settings, setSettings] = useState('')
  const [status, setStatus] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setStatus(null)
    setError(null)
    let settingsPayload: Record<string, unknown> = {}
    if (settings.trim()) {
      try {
        settingsPayload = JSON.parse(settings)
      } catch (err) {
        setError('Settings must be valid JSON.')
        return
      }
    }
    await apiFetch('/stores', {
      method: 'POST',
      body: JSON.stringify({
        channel,
        name,
        is_primary: isPrimary,
        is_enabled: isEnabled,
        settings: settingsPayload
      })
    })
    setName('')
    setIsPrimary(false)
    setIsEnabled(true)
    setSettings('')
    setStatus('Store created')
    await refetch()
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold">Stores</h1>

      <form className="mt-6 rounded-lg border bg-white p-4" onSubmit={handleSubmit}>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="text-sm font-medium text-slate-700">Channel</label>
            <select
              className="mt-2 w-full rounded-md border px-3 py-2 text-sm"
              value={channel}
              onChange={(event) => setChannel(event.target.value)}
            >
              {CHANNELS.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">Name</label>
            <input
              className="mt-2 w-full rounded-md border px-3 py-2 text-sm"
              value={name}
              onChange={(event) => setName(event.target.value)}
              required
            />
          </div>
        </div>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <label className="flex items-center gap-2 text-sm text-slate-600">
            <input
              type="checkbox"
              checked={isPrimary}
              onChange={(event) => setIsPrimary(event.target.checked)}
            />
            Primary store
          </label>
          <label className="flex items-center gap-2 text-sm text-slate-600">
            <input
              type="checkbox"
              checked={isEnabled}
              onChange={(event) => setIsEnabled(event.target.checked)}
            />
            Enabled
          </label>
        </div>
        <div className="mt-4">
          <label className="text-sm font-medium text-slate-700">Settings (JSON)</label>
          <textarea
            className="mt-2 w-full rounded-md border px-3 py-2 text-sm"
            rows={4}
            value={settings}
            onChange={(event) => setSettings(event.target.value)}
            placeholder='{"mock_inventory":[{"item_type":"PART","item_no":"3001","condition":"NEW","qty_available":5}]}'
          />
        </div>
        <button className="mt-4 rounded-md bg-slate-900 px-4 py-2 text-sm text-white" type="submit">
          Add store
        </button>
        {status ? <p className="mt-2 text-sm text-emerald-600">{status}</p> : null}
        {error ? <p className="mt-2 text-sm text-red-600">{error}</p> : null}
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
                <th className="px-4 py-3">Channel</th>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Primary</th>
                <th className="px-4 py-3">Enabled</th>
                <th className="px-4 py-3">Mock items</th>
              </tr>
            </thead>
            <tbody>
              {data?.map((store) => (
                <tr key={store.id} className="border-t">
                  <td className="px-4 py-3 font-medium text-slate-900">{store.channel}</td>
                  <td className="px-4 py-3">{store.name}</td>
                  <td className="px-4 py-3">{store.is_primary ? 'Yes' : 'No'}</td>
                  <td className="px-4 py-3">{store.is_enabled ? 'Yes' : 'No'}</td>
                  <td className="px-4 py-3 text-slate-500">
                    {Array.isArray(store.settings?.mock_inventory)
                      ? store.settings?.mock_inventory.length
                      : 0}
                  </td>
                </tr>
              ))}
              {!data?.length ? (
                <tr>
                  <td className="px-4 py-4 text-sm text-slate-500" colSpan={5}>
                    No stores created yet.
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
