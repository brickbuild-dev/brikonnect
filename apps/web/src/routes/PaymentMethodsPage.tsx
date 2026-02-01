import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { apiFetch } from '../lib/api'
import { Skeleton } from '../components/Skeleton'

type PaymentMethod = {
  id: string
  method_type: string
  card_last4?: string | null
  card_brand?: string | null
  is_default: boolean
}

export function PaymentMethodsPage() {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['billing', 'payment-methods'],
    queryFn: () => apiFetch<PaymentMethod[]>('/billing/payment-methods')
  })
  const [message, setMessage] = useState<string | null>(null)

  const handleAdd = async () => {
    setMessage(null)
    await apiFetch('/billing/payment-methods', {
      method: 'POST',
      body: JSON.stringify({
        method_type: 'stripe',
        stripe_payment_method_id: `pm_${Date.now()}`,
        card_last4: '4242',
        card_brand: 'visa',
        is_default: true
      })
    })
    await refetch()
    setMessage('Payment method added')
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
      <h1 className="text-2xl font-semibold">Payment methods</h1>
      <button className="mt-4 rounded-md bg-slate-900 px-3 py-2 text-sm text-white" onClick={handleAdd}>
        Add method
      </button>
      {message ? <p className="mt-2 text-sm text-emerald-600">{message}</p> : null}
      <div className="mt-6 space-y-3">
        {data?.map((method) => (
          <div key={method.id} className="rounded-lg border bg-white p-3 text-sm">
            <div className="font-medium text-slate-700">{method.method_type}</div>
            <div className="mt-1 text-xs text-slate-500">
              {method.card_brand?.toUpperCase()} •••• {method.card_last4 ?? '----'}
            </div>
            {method.is_default ? <div className="mt-2 text-xs text-emerald-600">Default</div> : null}
          </div>
        ))}
        {!data?.length ? <p className="text-sm text-slate-500">No methods yet.</p> : null}
      </div>
    </div>
  )
}
