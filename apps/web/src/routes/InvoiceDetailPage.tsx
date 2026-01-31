import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useParams } from '@tanstack/react-router'

import { apiFetch } from '../lib/api'
import { Skeleton } from '../components/Skeleton'

type Invoice = {
  id: string
  year_month: string
  total_due: string
  status: string
  currency: string
}

export function InvoiceDetailPage() {
  const { invoiceId } = useParams({ from: '/billing/invoices/$invoiceId' })
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['billing', 'invoices', invoiceId],
    queryFn: () => apiFetch<Invoice>(`/billing/invoices/${invoiceId}`)
  })
  const [message, setMessage] = useState<string | null>(null)

  const handlePay = async () => {
    setMessage(null)
    await apiFetch(`/billing/invoices/${invoiceId}/pay`, {
      method: 'POST',
      body: JSON.stringify({ method: 'stripe' })
    })
    await refetch()
    setMessage('Payment processed')
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
      <h1 className="text-2xl font-semibold">Invoice {data.year_month}</h1>
      <p className="mt-1 text-sm text-slate-500">Status: {data.status}</p>

      <div className="mt-6 rounded-lg border bg-white p-4">
        <div className="text-sm text-slate-600">Total due</div>
        <div className="mt-2 text-2xl font-semibold text-slate-900">
          {data.total_due} {data.currency}
        </div>
        <button className="mt-4 rounded-md bg-slate-900 px-3 py-2 text-sm text-white" onClick={handlePay}>
          Pay now
        </button>
        {message ? <p className="mt-2 text-sm text-emerald-600">{message}</p> : null}
      </div>
    </div>
  )
}
