import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Play, Pause, AlertTriangle, Eye } from 'lucide-react'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001'

export default function LiveMonitoring() {
  // Component state
  const [monitoringActive, setMonitoringActive] = useState(false)
  const [liveData, setLiveData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Get auth token from storage
  const getAuthToken = () => {
    return localStorage.getItem('token') || sessionStorage.getItem('token')
  }

  // Helper to make authenticated API calls
  const fetchWithAuth = async (endpoint, options = {}) => {
    try {
      const token = getAuthToken()
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : '',
          ...(options.headers || {})
        }
      })

      if (!response.ok) {
        throw new Error(`API Error ${response.status}`)
      }

      return response.json()
    } catch (err) {
      console.error("LiveMonitoring API error:", err.message)
      throw err
    }
  }

  // Auto-refresh live data every 3 seconds when monitoring is active
  useEffect(() => {
    let interval = null

    if (monitoringActive) {
      const fetchData = async () => {
        try {
          const data = await fetchWithAuth('/api/monitoring/live-data')
          setLiveData(data)
          setError(null)
        } catch (err) {
          setError("Live data not available.")
        }
      }

      fetchData()
      interval = setInterval(fetchData, 3000)
    }

    return () => interval && clearInterval(interval)
  }, [monitoringActive])

  // Check monitoring status on component mount
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const data = await fetchWithAuth('/api/monitoring/status')
        setMonitoringActive(data.active || false)
      } catch {
        setMonitoringActive(false)
      }
    }
    checkStatus()
  }, [])

  // Start monitoring handler
  const startMonitoring = async () => {
    try {
      setLoading(true)
      await fetchWithAuth('/api/monitoring/start', { method: 'POST' })
      setMonitoringActive(true)
      setError(null)
    } catch {
      setError("Monitoring start failed. Backend endpoint missing.")
    } finally {
      setLoading(false)
    }
  }

  // Stop monitoring handler
  const stopMonitoring = async () => {
    try {
      setLoading(true)
      await fetchWithAuth('/api/monitoring/stop', { method: 'POST' })
      setMonitoringActive(false)
      setLiveData(null)
    } catch {
      setError("Monitoring stop failed.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 space-y-6">
      {/* Page header with title and controls */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Live Monitoring</h1>
          <p className="text-muted-foreground">
            Real-time biometric authentication activity
          </p>
        </div>

        <div className="flex items-center space-x-4">
          {lastUpdate && (
            <p className="text-sm text-muted-foreground">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </p>
          )}

          <Badge variant={monitoringActive ? 'default' : 'secondary'}>
            {monitoringActive ? 'Active' : 'Inactive'}
          </Badge>

          <Button
            onClick={monitoringActive ? stopMonitoring : startMonitoring}
            disabled={loading}
            variant={monitoringActive ? 'destructive' : 'default'}
          >
            {monitoringActive ? (
              <>
                <Pause className="w-4 h-4 mr-2" /> Stop Monitoring
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" /> Start Monitoring
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Error message display */}
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Show message when monitoring is inactive */}
      {!monitoringActive && (
        <Alert>
          <Eye className="h-4 w-4" />
          <AlertDescription>
            Monitoring is not active. Click "Start Monitoring" to enable.
          </AlertDescription>
        </Alert>
      )}

      {/* Main metrics grid - shows when monitoring is active and data is available */}
      {monitoringActive && liveData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Active Sessions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{liveData.active_sessions_count}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Auth Rate</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{liveData.authentication_rate}%</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Anomaly Rate</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">{liveData.anomaly_rate}%</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Keystroke Samples</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{liveData.recent_keystroke_samples}</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Loading state while waiting for first data fetch */}
      {monitoringActive && !liveData && (
        <p className="text-center text-muted-foreground py-8">
          Waiting for live data...
        </p>
      )}
    </div>
  )
}
