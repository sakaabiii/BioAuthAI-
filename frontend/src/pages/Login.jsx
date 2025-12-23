import { useState, useRef } from 'react'
import './Login.css'

const BACKEND_URL = 'http://localhost:5001/api'

function Login({ onLoginSuccess }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [keystrokeStats, setKeystrokeStats] = useState(null)

  // Keystroke collection refs
  const keystrokeDataRef = useRef({
    dwell_times: [],
    flight_times: [],
    pause_patterns: [],
    key_presses: []
  })
  const keyDownTimesRef = useRef({})
  const lastKeyUpTimeRef = useRef(null)
  const sessionStartRef = useRef(Date.now())

  // Keystroke event handlers
  const handleKeyDown = (e) => {
    const key = e.key
    const timestamp = Date.now()

    // Record key down time
    keyDownTimesRef.current[key] = timestamp

    // Track key press
    keystrokeDataRef.current.key_presses.push(key)
  }

  const handleKeyUp = (e) => {
    const key = e.key
    const timestamp = Date.now()

    // Calculate dwell time (key hold duration)
    if (keyDownTimesRef.current[key]) {
      const dwellTime = timestamp - keyDownTimesRef.current[key]
      keystrokeDataRef.current.dwell_times.push(dwellTime)
      delete keyDownTimesRef.current[key]
    }

    // Calculate flight time (gap between keys)
    if (lastKeyUpTimeRef.current !== null) {
      const flightTime = timestamp - lastKeyUpTimeRef.current
      keystrokeDataRef.current.flight_times.push(flightTime)

      // Detect pauses (flight times > 200ms)
      if (flightTime > 200) {
        keystrokeDataRef.current.pause_patterns.push(flightTime)
      }
    }

    lastKeyUpTimeRef.current = timestamp

    // Update stats display
    updateKeystrokeStats()
  }

  const updateKeystrokeStats = () => {
    const totalTime = Date.now() - sessionStartRef.current
    const typingSpeed =
      (keystrokeDataRef.current.key_presses.length / totalTime) * 1000 // keys per second

    setKeystrokeStats({
      dwell_times: keystrokeDataRef.current.dwell_times,
      flight_times: keystrokeDataRef.current.flight_times,
      pause_patterns: keystrokeDataRef.current.pause_patterns,
      typing_speed: typingSpeed,
      key_count: keystrokeDataRef.current.key_presses.length,
      total_time_ms: totalTime
    })
  }

  const getKeystrokeData = () => {
    const totalTime = Date.now() - sessionStartRef.current
    const typingSpeed =
      (keystrokeDataRef.current.key_presses.length / totalTime) * 1000

    return {
      dwell_times: keystrokeDataRef.current.dwell_times,
      flight_times: keystrokeDataRef.current.flight_times,
      pause_patterns: keystrokeDataRef.current.pause_patterns,
      typing_speed: typingSpeed,
      key_count: keystrokeDataRef.current.key_presses.length,
      total_time_ms: totalTime
    }
  }

  const resetKeystrokeData = () => {
    keystrokeDataRef.current = {
      dwell_times: [],
      flight_times: [],
      pause_patterns: [],
      key_presses: []
    }
    keyDownTimesRef.current = {}
    lastKeyUpTimeRef.current = null
    sessionStartRef.current = Date.now()
    setKeystrokeStats(null)
  }

  const getDeviceInfo = () => {
    return {
      device_id: localStorage.getItem('device_id') || generateDeviceId(),
      device_name: navigator.userAgent.split('(')[1]?.split(')')[0] || 'Unknown',
      device_type: getDeviceType(),
      browser: getBrowserName(),
      os_name: getOSName()
    }
  }

  const generateDeviceId = () => {
    const id = 'device_' + Math.random().toString(36).substring(2, 11)
    localStorage.setItem('device_id', id)
    return id
  }

  const getDeviceType = () => {
    const ua = navigator.userAgent
    if (/mobile|android|iphone|ipad|phone/i.test(ua.toLowerCase())) {
      return 'mobile'
    }
    if (/tablet|ipad/i.test(ua.toLowerCase())) {
      return 'tablet'
    }
    return 'desktop'
  }

  const getBrowserName = () => {
    const ua = navigator.userAgent
    if (ua.indexOf('Firefox') > -1) return 'Firefox'
    if (ua.indexOf('Chrome') > -1) return 'Chrome'
    if (ua.indexOf('Safari') > -1) return 'Safari'
    if (ua.indexOf('Edge') > -1) return 'Edge'
    return 'Unknown'
  }

  const getOSName = () => {
    const ua = navigator.userAgent
    if (ua.indexOf('Windows') > -1) return 'Windows'
    if (ua.indexOf('Mac') > -1) return 'macOS'
    if (ua.indexOf('Linux') > -1) return 'Linux'
    if (ua.indexOf('Android') > -1) return 'Android'
    if (ua.indexOf('iOS') > -1) return 'iOS'
    return 'Unknown'
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      // Validate input
      if (!email || !password) {
        setError('Email and password are required')
        setLoading(false)
        return
      }

      // Get keystroke data
      const keystrokeData = getKeystrokeData()

      // Validate keystroke data
      if (keystrokeData.key_count < 5) {
        setError('Please type more characters to enable keystroke authentication')
        setLoading(false)
        return
      }

      // Prepare login payload
      const loginPayload = {
        email: email.toLowerCase().trim(),
        password: password,
        keystroke_data: keystrokeData,
        device_info: getDeviceInfo()
      }

      // Send login request
      const response = await fetch(`${BACKEND_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(loginPayload)
      })

      const data = await response.json()

      if (response.ok && data.success) {
        // Login successful
        console.log(' Login successful:', data)

        // Store session
        localStorage.setItem('user_id', data.user.id)
        localStorage.setItem('user_email', data.user.email)
        localStorage.setItem('session_id', data.session_id)
        localStorage.setItem('confidence_score', data.confidence)

        // Notify parent component
        if (onLoginSuccess) {
          onLoginSuccess(data.user, data.confidence, data.session_id)
        }

        // Reset form
        resetKeystrokeData()
        setEmail('')
        setPassword('')
      } else {
        // Login failed
        setError(data.error || 'Login failed')
        console.error(' Login error:', data)

        // If anomaly detected, show warning
        if (data.anomaly) {
          setError(
            `Anomaly detected! Confidence: ${(data.confidence * 100).toFixed(1)}%`
          )
        }
      }
    } catch (err) {
      setError('Network error: ' + err.message)
      console.error('Login error:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <div className="login-logo">
            <img src="/bioauthai-logo.png" alt="BioAuthAI Logo" className="logo-image" />
          </div>
          <h1>BioAuthAI</h1>
          <p>Behavioral Biometric Authentication</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          {/* Email Field */}
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onKeyDown={handleKeyDown}
              onKeyUp={handleKeyUp}
              placeholder="Enter your email"
              disabled={loading}
              required
            />
          </div>

          {/* Password Field */}
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={handleKeyDown}
              onKeyUp={handleKeyUp}
              placeholder="Enter your password"
              disabled={loading}
              required
            />
          </div>

          {/* Keystroke Stats Display */}
          {keystrokeStats && keystrokeStats.key_count > 0 && (
            <div className="keystroke-stats">
              <div className="stat-row">
                <span className="stat-label">Keys Pressed:</span>
                <span className="stat-value">{keystrokeStats.key_count}</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Avg Dwell:</span>
                <span className="stat-value">
                  {keystrokeStats.dwell_times.length > 0
                    ? (
                        keystrokeStats.dwell_times.reduce((a, b) => a + b, 0) /
                        keystrokeStats.dwell_times.length
                      ).toFixed(0)
                    : 0}
                  ms
                </span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Avg Flight:</span>
                <span className="stat-value">
                  {keystrokeStats.flight_times.length > 0
                    ? (
                        keystrokeStats.flight_times.reduce((a, b) => a + b, 0) /
                        keystrokeStats.flight_times.length
                      ).toFixed(0)
                    : 0}
                  ms
                </span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Typing Speed:</span>
                <span className="stat-value">
                  {keystrokeStats.typing_speed.toFixed(1)} keys/sec
                </span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Pauses:</span>
                <span className="stat-value">{keystrokeStats.pause_patterns.length}</span>
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && <div className="error-message">{error}</div>}

          {/* Submit Button */}
          <button type="submit" disabled={loading} className="login-button">
            {loading ? 'Authenticating...' : 'Login'}
          </button>
        </form>
      </div>

      {/* Info Panel */}
      <div className="info-panel">
        <h3>🔍 How It Works</h3>
        <ul>
          <li>
            <strong>Keystroke Monitoring:</strong> Your typing patterns are captured in real-time
          </li>
          <li>
            <strong>Feature Extraction:</strong> 21 behavioral features are extracted from your
            keystrokes
          </li>
          <li>
            <strong>Anomaly Detection:</strong> ML models detect unusual typing patterns
          </li>
        </ul>
      </div>
    </div>
  )
}

export default Login
