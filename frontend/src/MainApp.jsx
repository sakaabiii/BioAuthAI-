import { useState } from 'react'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'

function MainApp() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [currentUser, setCurrentUser] = useState(null)
  const [sessionId, setSessionId] = useState(null)

  const handleLoginSuccess = (user, confidenceScore, session) => {
    setCurrentUser(user)
    setSessionId(session)
    setIsAuthenticated(true)
    console.log('Login successful:', user, 'Confidence:', confidenceScore)
  }

  const handleLogout = () => {
    // Call logout API
    fetch('http://localhost:5001/api/auth/logout', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: currentUser?.id,
        session_id: sessionId
      })
    }).catch(err => console.error('Logout error:', err))

    // Clear state
    setIsAuthenticated(false)
    setCurrentUser(null)
    setSessionId(null)
  }

  if (!isAuthenticated) {
    return <Login onLoginSuccess={handleLoginSuccess} />
  }

  return <Dashboard currentUser={currentUser} onLogout={handleLogout} />
}

export default MainApp
