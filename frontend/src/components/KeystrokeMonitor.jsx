import { useEffect, useRef, useState } from 'react'

/**
 * 🔵 KeystrokeMonitor
 * 
 * Monitors keyboard input and collects keystroke timing data
 * Extracts dwell times, flight times, and pause patterns
 * Sends data to backend for feature extraction and anomaly detection
 */

export function KeystrokeMonitor({ onKeystrokeData, enabled = true }) {
  const keystrokeDataRef = useRef({
    dwell_times: [],
    flight_times: [],
    pause_patterns: [],
    key_presses: [],
    timestamps: []
  })

  const keyDownTimesRef = useRef({})
  const lastKeyUpTimeRef = useRef(null)
  const sessionStartRef = useRef(Date.now())

  useEffect(() => {
    if (!enabled) return

    const handleKeyDown = (event) => {
      const key = event.key
      const timestamp = Date.now()

      // Record key down time
      keyDownTimesRef.current[key] = timestamp

      // Track key press
      keystrokeDataRef.current.key_presses.push(key)
      keystrokeDataRef.current.timestamps.push(timestamp)
    }

    const handleKeyUp = (event) => {
      const key = event.key
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

      // Send keystroke data every 10 key presses
      if (keystrokeDataRef.current.key_presses.length % 10 === 0) {
        sendKeystrokeData()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    document.addEventListener('keyup', handleKeyUp)

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.removeEventListener('keyup', handleKeyUp)
    }
  }, [enabled, onKeystrokeData])

  const sendKeystrokeData = () => {
    if (keystrokeDataRef.current.key_presses.length < 5) {
      return // Need at least 5 key presses
    }

    const totalTime = Date.now() - sessionStartRef.current
    const typingSpeed =
      (keystrokeDataRef.current.key_presses.length / totalTime) * 1000 // keys per second

    const data = {
      dwell_times: keystrokeDataRef.current.dwell_times,
      flight_times: keystrokeDataRef.current.flight_times,
      pause_patterns: keystrokeDataRef.current.pause_patterns,
      typing_speed: typingSpeed,
      key_count: keystrokeDataRef.current.key_presses.length,
      total_time_ms: totalTime
    }

    if (onKeystrokeData) {
      onKeystrokeData(data)
    }
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

  const reset = () => {
    keystrokeDataRef.current = {
      dwell_times: [],
      flight_times: [],
      pause_patterns: [],
      key_presses: [],
      timestamps: []
    }
    keyDownTimesRef.current = {}
    lastKeyUpTimeRef.current = null
    sessionStartRef.current = Date.now()
  }

  return {
    getKeystrokeData,
    reset,
    sendKeystrokeData
  }
}

/**
 * 🔵 KeystrokeStats
 * 
 * Display keystroke statistics during login
 */

export function KeystrokeStats({ keystrokeData }) {
  if (!keystrokeData) {
    return null
  }

  const avgDwell =
    keystrokeData.dwell_times.length > 0
      ? (
          keystrokeData.dwell_times.reduce((a, b) => a + b, 0) /
          keystrokeData.dwell_times.length
        ).toFixed(2)
      : 0

  const avgFlight =
    keystrokeData.flight_times.length > 0
      ? (
          keystrokeData.flight_times.reduce((a, b) => a + b, 0) /
          keystrokeData.flight_times.length
        ).toFixed(2)
      : 0

  return (
    <div className="keystroke-stats">
      <div className="stat-item">
        <span className="stat-label">Avg Dwell Time:</span>
        <span className="stat-value">{avgDwell}ms</span>
      </div>
      <div className="stat-item">
        <span className="stat-label">Avg Flight Time:</span>
        <span className="stat-value">{avgFlight}ms</span>
      </div>
      <div className="stat-item">
        <span className="stat-label">Key Presses:</span>
        <span className="stat-value">{keystrokeData.key_count || 0}</span>
      </div>
      <div className="stat-item">
        <span className="stat-label">Typing Speed:</span>
        <span className="stat-value">
          {keystrokeData.typing_speed?.toFixed(2) || 0} keys/sec
        </span>
      </div>
      <div className="stat-item">
        <span className="stat-label">Pauses Detected:</span>
        <span className="stat-value">{keystrokeData.pause_patterns?.length || 0}</span>
      </div>
    </div>
  )
}
