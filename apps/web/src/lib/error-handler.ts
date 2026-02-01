export class ApiError extends Error {
  status: number
  payload?: string

  constructor(message: string, status: number, payload?: string) {
    super(message)
    this.status = status
    this.payload = payload
  }
}

export function handleApiError(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'Unexpected error'
}
