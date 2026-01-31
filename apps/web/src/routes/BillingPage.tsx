import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'

import { apiFetch } from '../lib/api'
import { Skeleton } from '../components/Skeleton'

type BillingStatus = {
  current_version: string
  has_brikick_discount: boolean
  current_rate: string
  billing_status: string
  current_month_gmv: string
  current_month_estimated_fee: string
}

export function BillingPage() {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['billing', 'status'],
    queryFn: () => apiFetch<BillingStatus>('/billing/status')
  })
  const [version, setVersion] = useState('full')
  const [message, setMessage] = useState<string | null>(null)

  useEffect(() => {
    if (data?.current_version) {
      setVersion(data.current_version)
    }
  }, [data])

  const handleUpdate = async () => {
    setMessage(null)
    await apiFetch('/billing/version', {
      method: 'POST',
      body: JSON.stringify({ version })
    })
    await refetch()
    setMessage('Version updated')
  }

  if (isLoading || !data) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-24 w-full" />
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold">Billing</h1>
      <p className="mt-1 text-sm text-slate-500">Status: {data.billing_status}</p>

      <div className="mt-6 rounded-lg border bg-white p-4">
        <div className="grid gap-4 text-sm text-slate-600 md:grid-cols-2">
          <div>
            <div className="text-xs uppercase text-slate-400">Current version</div>
            <div className="mt-1 text-base font-medium text-slate-900">{data.current_version}</div>
          </div>
          <div>
            <div className="text-xs uppercase text-slate-400">Current rate</div>
            <div className="mt-1 text-base font-medium text-slate-900">{data.current_rate}</div>
          </div>
          <div>
            <div className="text-xs uppercase text-slate-400">GMV this month</div>
            <div className="mt-1 text-base font-medium text-slate-900">{data.current_month_gmv}</div>
          </div>
          <div>
            <div className="text-xs uppercase text-slate-400">Estimated fee</div>
            <div className="mt-1 text-base font-medium text-slate-900">
              {data.current_month_estimated_fee}
            </div>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          <select
            className="rounded-md border px-3 py-2 text-sm"
            value={version}
            onChange={(event) => setVersion(event.target.value)}
          >
            <option value="lite">Lite</option>
            <option value="full">Full</option>
          </select>
          <button className="rounded-md bg-slate-900 px-3 py-2 text-sm text-white" onClick={handleUpdate}>
            Update version
          </button>
          {message ? <span className="text-xs text-emerald-600">{message}</span> : null}
        </div>
      </div>

      <div className="mt-6 flex flex-wrap gap-3 text-sm">
        <Link to="/billing/invoices" className="rounded-md border px-3 py-2 text-slate-600">
          View invoices
        </Link>
        <Link to="/billing/payment-methods" className="rounded-md border px-3 py-2 text-slate-600">
          Payment methods
        </Link>
      </div>
    </div>
  )
}
