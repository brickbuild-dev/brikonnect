import { useQuery } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'

import { apiFetch } from '../lib/api'
import { Skeleton } from '../components/Skeleton'

type Invoice = {
  id: string
  year_month: string
  total_due: string
  status: string
}

export function InvoicesPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['billing', 'invoices'],
    queryFn: () => apiFetch<Invoice[]>('/billing/invoices')
  })

  if (isLoading) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-32 w-full" />
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold">Invoices</h1>
      <div className="mt-6 overflow-x-auto rounded-lg border bg-white">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Month</th>
              <th className="px-4 py-3">Total</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Action</th>
            </tr>
          </thead>
          <tbody>
            {data?.map((invoice) => (
              <tr key={invoice.id} className="border-t">
                <td className="px-4 py-3">{invoice.year_month}</td>
                <td className="px-4 py-3">{invoice.total_due}</td>
                <td className="px-4 py-3">{invoice.status}</td>
                <td className="px-4 py-3">
                  <Link to={`/billing/invoices/${invoice.id}`} className="text-slate-700">
                    View
                  </Link>
                </td>
              </tr>
            ))}
            {!data?.length ? (
              <tr>
                <td className="px-4 py-4 text-sm text-slate-500" colSpan={4}>
                  No invoices yet.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  )
}
