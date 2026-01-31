import { FormEvent, useState } from 'react'
import { useNavigate } from '@tanstack/react-router'

import { useAuth } from '../lib/auth'

export function LoginPage() {
  const navigate = useNavigate()
  const { login, user } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login(email, password)
      await navigate({ to: '/' })
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  if (user) {
    return (
      <div className="mx-auto mt-20 max-w-md rounded-lg border bg-white p-6 shadow-sm">
        <h1 className="text-xl font-semibold">Already signed in</h1>
        <p className="mt-2 text-sm text-slate-600">You are already authenticated.</p>
        <button
          className="mt-4 w-full rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white"
          onClick={() => navigate({ to: '/' })}
        >
          Go to dashboard
        </button>
      </div>
    )
  }

  return (
    <div className="mx-auto mt-20 max-w-md rounded-lg border bg-white p-6 shadow-sm">
      <h1 className="text-xl font-semibold">Sign in to Brikonnect</h1>
      <p className="mt-1 text-sm text-slate-600">Use your tenant credentials.</p>
      <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
        <div>
          <label className="text-sm font-medium text-slate-700">Email</label>
          <input
            type="email"
            className="mt-2 w-full rounded-md border px-3 py-2 text-sm"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </div>
        <div>
          <label className="text-sm font-medium text-slate-700">Password</label>
          <input
            type="password"
            className="mt-2 w-full rounded-md border px-3 py-2 text-sm"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </div>
        {error ? <div className="text-sm text-red-600">{error}</div> : null}
        <button
          type="submit"
          className="w-full rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white"
          disabled={loading}
        >
          {loading ? 'Signing in...' : 'Sign in'}
        </button>
      </form>
    </div>
  )
}
