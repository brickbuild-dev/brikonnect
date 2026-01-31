import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'

import { apiFetch } from '../lib/api'

type Order = {
  id: string
  external_order_id: string
  status: string
  buyer_name?: string | null
  grand_total?: string | null
}

export function OrdersPage() {
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['orders', search, status],
    queryFn: () => {
      const params = new URLSearchParams()
      if (search) params.set('q', search)
      if (status) params.set('status', status)
      const qs = params.toString()
      return apiFetch<Order[]>(`/orders${qs ? `?${qs}` : ''}`)
    }
  })

  return (
    <div>
      <h1 className="text-2xl font-semibold">Orders</h1>
      <div className="mt-4 flex flex-wrap items-center gap-2">
        <input
          className="w-60 rounded-md border px-3 py-2 text-sm"
          placeholder="Search order or buyer"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <select
          className="rounded-md border px-3 py-2 text-sm"
          value={status}
          onChange={(event) => setStatus(event.target.value)}
        >
          <option value="">All statuses</option>
          <option value="NEW">NEW</option>
          <option value="PENDING">PENDING</option>
          <option value="PICKING">PICKING</option>
          <option value="PACKING">PACKING</option>
          <option value="READY">READY</option>
          <option value="SHIPPED">SHIPPED</option>
          <option value="DELIVERED">DELIVERED</option>
          <option value="COMPLETED">COMPLETED</option>
          <option value="CANCELLED">CANCELLED</option>
          <option value="REFUNDED">REFUNDED</option>
        </select>
        <button
          className="rounded-md bg-slate-900 px-3 py-2 text-sm text-white"
          onClick={() => void refetch()}
        >
          Filter
        </button>
      </div>

      {isLoading ? (
        <div className="mt-6 text-sm text-slate-500">Loading orders...</div>
      ) : (
        <div className="mt-6 overflow-hidden rounded-lg border bg-white">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Order</th>
                <th className="px-4 py-3">Buyer</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Total</th>
              </tr>
            </thead>
            <tbody>
              {data?.map((order) => (
                <tr key={order.id} className="border-t">
                  <td className="px-4 py-3">
                    <Link to={`/orders/${order.id}`} className="font-medium text-slate-900">
                      {order.external_order_id}
                    </Link>
                  </td>
                  <td className="px-4 py-3">{order.buyer_name ?? '-'}</td>
                  <td className="px-4 py-3">{order.status}</td>
                  <td className="px-4 py-3">{order.grand_total ?? '-'}</td>
                </tr>
              ))}
              {!data?.length ? (
                <tr>
                  <td className="px-4 py-4 text-sm text-slate-500" colSpan={4}>
                    No orders found.
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
