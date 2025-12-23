import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Users, RefreshCw, TrendingUp, TrendingDown, Target, Shield } from 'lucide-react'
import { Progress } from '@/components/ui/progress'

const API_BASE_URL = 'http://localhost:5001'

export function PerUserMetrics() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const fetchMetrics = async () => {
    try {
      setRefreshing(true)
      const response = await fetch(`${API_BASE_URL}/api/analytics/per-user-metrics`)
      const data = await response.json()
      
      if (data.success) {
        setUsers(data.users)
      }
    } catch (error) {
      console.error('Error fetching per-user metrics:', error)
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

  const getMetricBadge = (value, isError = false) => {
    if (isError) {
      if (value < 5) return 'default'
      if (value < 10) return 'secondary'
      return 'destructive'
    } else {
      if (value >= 95) return 'default'
      if (value >= 85) return 'secondary'
      return 'destructive'
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    const date = new Date(dateString)
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="w-5 h-5" />
            Per-User Biometric Metrics
          </CardTitle>
          <CardDescription>Loading user metrics from database...</CardDescription>
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
              <Users className="w-5 h-5" />
              Per-User Biometric Metrics
            </CardTitle>
            <CardDescription>
              Individual FAR, FRR, EER and accuracy for {users.length} users with trained models
            </CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchMetrics}
            disabled={refreshing}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {users.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No users with trained models found
          </div>
        ) : (
          <div className="space-y-6">
            {/* Summary Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 border rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Target className="w-4 h-4 text-muted-foreground" />
                  <span className="text-xs font-medium text-muted-foreground">Avg Accuracy</span>
                </div>
                <div className="text-2xl font-bold">
                  {(users.reduce((sum, u) => sum + u.accuracy, 0) / users.length).toFixed(2)}%
                </div>
              </div>
              <div className="p-4 border rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="w-4 h-4 text-muted-foreground" />
                  <span className="text-xs font-medium text-muted-foreground">Avg FAR</span>
                </div>
                <div className="text-2xl font-bold">
                  {(users.reduce((sum, u) => sum + u.far, 0) / users.length).toFixed(2)}%
                </div>
              </div>
              <div className="p-4 border rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingDown className="w-4 h-4 text-muted-foreground" />
                  <span className="text-xs font-medium text-muted-foreground">Avg FRR</span>
                </div>
                <div className="text-2xl font-bold">
                  {(users.reduce((sum, u) => sum + u.frr, 0) / users.length).toFixed(2)}%
                </div>
              </div>
              <div className="p-4 border rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Shield className="w-4 h-4 text-muted-foreground" />
                  <span className="text-xs font-medium text-muted-foreground">Avg EER</span>
                </div>
                <div className="text-2xl font-bold">
                  {(users.reduce((sum, u) => sum + u.eer, 0) / users.length).toFixed(2)}%
                </div>
              </div>
            </div>

            {/* Detailed Table */}
            <div className="border rounded-lg overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>User</TableHead>
                    <TableHead className="text-center">Accuracy</TableHead>
                    <TableHead className="text-center">FAR</TableHead>
                    <TableHead className="text-center">FRR</TableHead>
                    <TableHead className="text-center">EER</TableHead>
                    <TableHead className="text-center">Samples</TableHead>
                    <TableHead>Model Trained</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users.map((user) => (
                    <TableRow key={user.user_id}>
                      <TableCell>
                        <div className="flex flex-col">
                          <span className="font-medium">{user.user_name}</span>
                          <span className="text-xs text-muted-foreground">{user.user_email}</span>
                          <Badge variant="outline" className="w-fit mt-1 text-xs">
                            {user.user_role}
                          </Badge>
                        </div>
                      </TableCell>
                      <TableCell className="text-center">
                        <div className="flex flex-col items-center gap-1">
                          <span className={`text-lg font-bold ${getMetricColor(user.accuracy, false)}`}>
                            {user.accuracy}%
                          </span>
                          <Progress value={user.accuracy} className="h-1 w-16" />
                        </div>
                      </TableCell>
                      <TableCell className="text-center">
                        <div className="flex flex-col items-center gap-1">
                          <Badge variant={getMetricBadge(user.far, true)} className="text-xs">
                            {user.far}%
                          </Badge>
                          <span className="text-xs text-muted-foreground">Lower is better</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-center">
                        <div className="flex flex-col items-center gap-1">
                          <Badge variant={getMetricBadge(user.frr, true)} className="text-xs">
                            {user.frr}%
                          </Badge>
                          <span className="text-xs text-muted-foreground">Lower is better</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-center">
                        <div className="flex flex-col items-center gap-1">
                          <Badge variant={getMetricBadge(user.eer, true)} className="text-xs">
                            {user.eer}%
                          </Badge>
                          <span className="text-xs text-muted-foreground">Crossover</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-center">
                        <span className="font-medium">{user.training_samples}</span>
                      </TableCell>
                      <TableCell>
                        <span className="text-xs text-muted-foreground">
                          {formatDate(user.model_trained_at)}
                        </span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            {/* Legend */}
            <div className="p-4 bg-muted rounded-lg">
              <h4 className="text-sm font-semibold mb-2">Metric Definitions:</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-muted-foreground">
                <div><strong>FAR (False Acceptance Rate)</strong>: % of imposters incorrectly accepted</div>
                <div><strong>FRR (False Rejection Rate)</strong>: % of genuine users incorrectly rejected</div>
                <div><strong>EER (Equal Error Rate)</strong>: Point where FAR = FRR (optimal threshold)</div>
                <div><strong>Accuracy</strong>: Overall correct authentication rate</div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
