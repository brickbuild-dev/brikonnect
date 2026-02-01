import { apiFetch } from '../shared/api'
import { refreshAuth } from '../shared/auth'

type NotificationItem = {
  id: string
  title: string
  body?: string | null
  read_at?: string | null
  dismissed_at?: string | null
}

const REFRESH_ALARM = 'brikonnect-refresh'
const NOTIFICATION_ALARM = 'brikonnect-notifications'
const NOTIFIED_KEY = 'notifiedIds'
const UNREAD_COUNT_KEY = 'unreadCount'

function formatBadge(count: number) {
  if (count <= 0) return ''
  if (count > 99) return '99+'
  return String(count)
}

async function updateBadge(count: number) {
  await chrome.action.setBadgeText({ text: formatBadge(count) })
  await chrome.action.setBadgeBackgroundColor({ color: '#0f172a' })
  await chrome.storage.local.set({ [UNREAD_COUNT_KEY]: count })
}

async function refreshToken() {
  await refreshAuth()
}

async function pollNotifications() {
  const auth = await refreshAuth()
  if (!auth) {
    await updateBadge(0)
    return
  }

  try {
    const notifications = await apiFetch<NotificationItem[]>('/notifications', {}, auth.accessToken)
    const unread = notifications.filter(
      (item) => !item.read_at && !item.dismissed_at
    )
    await updateBadge(unread.length)

    const stored = await chrome.storage.local.get(NOTIFIED_KEY)
    const notified = new Set<string>((stored[NOTIFIED_KEY] as string[] | undefined) ?? [])

    const newItems = unread.filter((item) => !notified.has(item.id))
    for (const item of newItems) {
      await chrome.notifications.create(`brikonnect-${item.id}`, {
        type: 'basic',
        iconUrl: 'assets/icons/icon-128.png',
        title: item.title,
        message: item.body ?? 'You have a new update.',
        priority: 0
      })
      notified.add(item.id)
    }

    const trimmed = Array.from(notified).slice(-50)
    await chrome.storage.local.set({ [NOTIFIED_KEY]: trimmed })
  } catch (error) {
    console.error('Notification polling failed', error)
  }
}

chrome.runtime.onInstalled.addListener(() => {
  chrome.alarms.create(REFRESH_ALARM, { periodInMinutes: 5 })
  chrome.alarms.create(NOTIFICATION_ALARM, { periodInMinutes: 2 })
  void refreshToken()
  void pollNotifications()
})

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === REFRESH_ALARM) {
    void refreshToken()
  }
  if (alarm.name === NOTIFICATION_ALARM) {
    void pollNotifications()
  }
})

chrome.runtime.onStartup.addListener(() => {
  void refreshToken()
  void pollNotifications()
})
