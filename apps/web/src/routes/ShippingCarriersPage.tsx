import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { apiFetch } from '../lib/api'
import { Skeleton } from '../components/Skeleton'

type Carrier = {
  id: string
  carrier_code: string
  is_enabled: boolean
}

export function ShippingCarriersPage() {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['shipping', 'carriers'],
    queryFn: () => apiFetch<Carrier[]>('/shipping/carriers')
  })
  const [carrierCode, setCarrierCode] = useState('sendcloud')
  const [message, setMessage] = useState<string | null>(null)

  const handleAdd = async () => {
    setMessage(null)
    await apiFetch('/shipping/carriers', {
      method: 'POST',
      body: JSON.stringify({
        carrier_code: carrierCode,
        credentials: {},
        is_enabled: true
      })
    })
    await refetch()
    setMessage('Carrier saved')
  }

  if (isLoading) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-24 w-full" />
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold">Shipping carriers</h1>
      <div className="mt-4 flex flex-wrap items-center gap-2">
        <select
          className="rounded-md border px-3 py-2 text-sm"
          value={carrierCode}
          onChange={(event) => setCarrierCode(event.target.value)}
        >
          <option value="sendcloud">SendCloud</option>
          <option value="shipstation">ShipStation</option>
          <option value="pirateship">PirateShip</option>
          <option value="dhl">DHL</option>
          <option value="postnl">PostNL</option>
        </select>
        <button className="rounded-md bg-slate-900 px-3 py-2 text-sm text-white" onClick={handleAdd}>
          Add carrier
        </button>
        {message ? <span className="text-xs text-emerald-600">{message}</span> : null}
      </div>

      <div className="mt-6 space-y-3">
        {data?.map((carrier) => (
          <div key={carrier.id} className="rounded-lg border bg-white p-3 text-sm">
            <div className="font-medium text-slate-700">{carrier.carrier_code}</div>
            <div className="mt-1 text-xs text-slate-500">
              {carrier.is_enabled ? 'Enabled' : 'Disabled'}
            </div>
          </div>
        ))}
        {!data?.length ? <p className="text-sm text-slate-500">No carriers configured.</p> : null}
      </div>
    </div>
  )
}
