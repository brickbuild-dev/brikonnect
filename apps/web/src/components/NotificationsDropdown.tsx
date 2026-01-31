import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { apiFetch } from '../lib/api'
import { handleApiError } from '../lib/error-handler'

type Notification = {
  id: string
  title: string
  body?: string | null
  read_at?: string | null
}

export function NotificationsDropdown() {
  const [open, setOpen] = useState(false)
  const { data, refetch } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => apiFetch<Notification[]>('/notifications'),
    refetchInterval: 30000
  })

  const unreadCount = data?.filter((n) => !n.read_at).length ?? 0

  const markRead = async (notificationId: string) => {
    try {
      await apiFetch(`/notifications/${notificationId}/read`, { method: 'POST' })
      await refetch()
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error(handleApiError(error))
    }
  }

  return (
    <div className="relative">
      <button
        className="relative rounded-md border px-2 py-1 text-xs text-slate-600 dark:border-slate-700 dark:text-slate-200"
        onClick={() => setOpen((prev) => !prev)}
      >
        Notifications
        {unreadCount ? (
          <span className="ml-2 rounded-full bg-slate-900 px-2 py-0.5 text-[10px] text-white dark:bg-slate-100 dark:text-slate-900">
            {unreadCount}
          </span>
        ) : null}
      </button>
      {open ? (
        <div className="absolute right-0 z-10 mt-2 w-72 rounded-md border bg-white p-3 shadow-lg dark:border-slate-700 dark:bg-slate-900">
          <h4 className="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
            Notifications
          </h4>
          <div className="mt-2 space-y-2">
            {data?.length ? (
              data.slice(0, 5).map((notification) => (
                <button
                  key={notification.id}
                  className="w-full rounded-md border px-2 py-2 text-left text-xs text-slate-700 dark:border-slate-700 dark:text-slate-200"
                  onClick={() => void markRead(notification.id)}
                >
                  <div className="font-medium">{notification.title}</div>
                  {notification.body ? (
                    <div className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
                      {notification.body}
                    </div>
                  ) : null}
                </button>
              ))
            ) : (
              <div className="text-xs text-slate-500 dark:text-slate-400">
                No notifications
              </div>
            )}
          </div>
        </div>
      ) : null}
    </div>
  )
}
