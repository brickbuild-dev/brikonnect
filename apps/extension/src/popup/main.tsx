import React, { useEffect, useState } from 'react'
import ReactDOM from 'react-dom/client'

import { getAuth, logout } from '../shared/auth'

function PopupApp() {
  const [authenticated, setAuthenticated] = useState(false)

  useEffect(() => {
    void getAuth().then((auth) => setAuthenticated(Boolean(auth)))
  }, [])

  return (
    <div style={{ padding: 12, fontFamily: 'sans-serif', width: 240 }}>
      <h1 style={{ fontSize: 14, fontWeight: 600 }}>Brikonnect</h1>
      <p style={{ fontSize: 12, color: '#64748b' }}>
        {authenticated ? 'Signed in' : 'Sign in from the side panel.'}
      </p>
      {authenticated ? (
        <button style={{ marginTop: 8 }} onClick={() => void logout()}>
          Logout
        </button>
      ) : null}
    </div>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <PopupApp />
  </React.StrictMode>
)
