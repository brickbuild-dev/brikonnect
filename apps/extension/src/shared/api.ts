const API_URL_KEY = 'apiBaseUrl'
export const DEFAULT_API_BASE_URL = 'http://localhost:8000/api/v1'

export async function getApiBaseUrl(): Promise<string> {
  const result = await chrome.storage.local.get(API_URL_KEY)
  const stored = result[API_URL_KEY]
  if (typeof stored === 'string' && stored.trim().length > 0) {
    return stored
  }
  return DEFAULT_API_BASE_URL
}

export async function setApiBaseUrl(url: string) {
  await chrome.storage.local.set({ [API_URL_KEY]: url })
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  accessToken?: string
): Promise<T> {
  const baseUrl = await getApiBaseUrl()
  const response = await fetch(`${baseUrl}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...(options.headers ?? {})
    },
    ...options
  })

  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || `Request failed: ${response.status}`)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}
