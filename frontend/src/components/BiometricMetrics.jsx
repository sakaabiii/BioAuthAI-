import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { Shield, TrendingDown, TrendingUp, Target, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'

const API_BASE_URL = 'http://localhost:5001'

export function BiometricMetrics() {
  const [metrics, setMetrics] = useState({
    accuracy: 0,
    far: 0,
    frr: 0,
    eer: 0,
    total_models: 0,
    best_accuracy: 0,
    best_far: 0,
    best_frr: 0
  })
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const fetchMetrics = async () => {
    try {
      setRefreshing(true)
      const response = await fetch(`${API_BASE_URL}/api/analytics/biometric-metrics`)
      const data = await response.json()
      
      if (data.success) {
        setMetrics(data.metrics)
      }
    } catch (error) {
      console.error('Error fetching biometric metrics:', error)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    fetchMetrics()
  }, [])

  const getMetricColor = (value, isError = false) => {
    if (isError) {
      // For FAR, FRR, EER - lower is better
      if (value < 5) return 'text-green-600'
      if (value < 10) return 'text-yellow-600'
      return 'text-red-600'
    } else {
      // For accuracy - higher is better
      if (value >= 95) return 'text-green-600'
      if (value >= 85) return 'text-yellow-600'
      return 'text-red-600'
    }
  }

  const getProgressColor = (value, isError = false) => {
    if (isError) {
      if (value < 5) return 'bg-green-600'
      if (value < 10) return 'bg-yellow-600'
      return 'bg-red-600'
    } else {
      if (value >= 95) return 'bg-green-600'
      if (value >= 85) return 'bg-yellow-600'
      return 'bg-red-600'
    }
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5" />
            Biometric Authentication Metrics
          </CardTitle>
          <CardDescription>Loading metrics...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="w-6 h-6 animate-spin text-muted-foreground" />
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Shield className="w-5 h-5" />
              Biometric Authentication Metrics
            </CardTitle>
            <CardDescription>
              FAR, FRR, EER and accuracy from {metrics.total_models} active ML models
            </CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchMetrics}
            disabled={refreshing}
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Accuracy */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Target className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm font-medium">Accuracy</span>
              </div>
              <span className={`text-2xl font-bold ${getMetricColor(metrics.accuracy, false)}`}>
                {metrics.accuracy}%
              </span>
            </div>
            <Progress value={metrics.accuracy} className="h-2" />
            <p className="text-xs text-muted-foreground">
              Best model: {metrics.best_accuracy}%
            </p>
          </div>

          {/* FAR - False Acceptance Rate */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm font-medium">FAR</span>
                <Badge variant="outline" className="text-xs">Lower is better</Badge>
              </div>
              <span className={`text-2xl font-bold ${getMetricColor(metrics.far, true)}`}>
                {metrics.far}%
              </span>
            </div>
            <Progress value={metrics.far} max={20} className="h-2" />
            <p className="text-xs text-muted-foreground">
              False Acceptance Rate • Best: {metrics.best_far}%
            </p>
          </div>

          {/* FRR - False Rejection Rate */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <TrendingDown className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm font-medium">FRR</span>
                <Badge variant="outline" className="text-xs">Lower is better</Badge>
              </div>
              <span className={`text-2xl font-bold ${getMetricColor(metrics.frr, true)}`}>
                {metrics.frr}%
              </span>
            </div>
            <Progress value={metrics.frr} max={20} className="h-2" />
            <p className="text-xs text-muted-foreground">
              False Rejection Rate • Best: {metrics.best_frr}%
            </p>
          </div>

          {/* EER - Equal Error Rate */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm font-medium">EER</span>
                <Badge variant="outline" className="text-xs">Lower is better</Badge>
              </div>
              <span className={`text-2xl font-bold ${getMetricColor(metrics.eer, true)}`}>
                {metrics.eer}%
              </span>
            </div>
            <Progress value={metrics.eer} max={20} className="h-2" />
            <p className="text-xs text-muted-foreground">
              Equal Error Rate (FAR = FRR crossover point)
            </p>
          </div>
        </div>

        {/* Explanation */}
        <div className="mt-6 p-4 bg-muted rounded-lg">
          <h4 className="text-sm font-semibold mb-2">Metric Definitions:</h4>
          <ul className="text-xs text-muted-foreground space-y-1">
            <li><strong>FAR</strong>: Percentage of imposters incorrectly accepted</li>
            <li><strong>FRR</strong>: Percentage of genuine users incorrectly rejected</li>
            <li><strong>EER</strong>: Point where FAR equals FRR (optimal threshold)</li>
            <li><strong>Accuracy</strong>: Overall correct authentication rate</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  )
}
