import { useEffect, useState } from "react"
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableHeader,
  TableRow,
  TableHead,
  TableBody,
  TableCell
} from "@/components/ui/table"
import {
  ArrowDown,
  ArrowUp,
  Download,
  Users,
  Search,
  Loader2,
  Zap,
  Info
} from "lucide-react"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer
} from "recharts"

const API_BASE = "http://localhost:5001/api"

export default function PerUserAnalytics() {
  const [metrics, setMetrics] = useState([])
  const [filtered, setFiltered] = useState([])
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState("")

  const loadMetrics = async () => {
    try {
      setLoading(true)
      // Request all users to ensure we get everyone including new users
      const res = await fetch(`${API_BASE}/analytics/per-user-metrics?per_page=1000`)
      const data = await res.json()

      if (data.success) {
        setMetrics(data.users)
        setFiltered(data.users)
      }
    } catch (e) {
      console.error("Failed to load per-user metrics:", e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadMetrics()
  }, [])

  const searchUsers = (term) => {
    setSearch(term)
    if (!term.trim()) {
      setFiltered(metrics)
      return
    }
    const lowered = term.toLowerCase()
    setFiltered(
      metrics.filter(
        (u) =>
          u.user_name.toLowerCase().includes(lowered) ||
          u.user_email.toLowerCase().includes(lowered)
      )
    )
  }

  const exportUser = (id) => {
    window.open(`${API_BASE}/analytics/export-user/${id}`, "_blank")
  }

  const trainModel = async (userId) => {
    try {
      const response = await fetch(`${API_BASE}/ml/train/${userId}`, {
        method: 'POST'
      })
      const data = await response.json()

      if (response.ok && data.success) {
        const result = data.result
        alert(`Model trained successfully!\nAlgorithm: ${result.best_model}\nAccuracy: ${(result.accuracy * 100).toFixed(2)}%`)
        loadMetrics() // Refresh the data
      } else {
        alert(`Training failed: ${data.error || 'Unknown error'}`)
      }
    } catch (error) {
      alert(`Training error: ${error.message}`)
    }
  }

  return (
    <div className="p-8 space-y-8">
      {/* HEADER */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Users className="w-8 h-8 text-blue-500" />
            Per-User Biometric Analytics
          </h1>
          <p className="text-gray-400">
            Detailed performance of every user's behavioral biometric model.
          </p>
        </div>

        <Button variant="outline" onClick={loadMetrics}>
          {loading && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
          Refresh
        </Button>
      </div>

      {/* SEARCH BAR */}
      <div className="flex items-center w-full max-w-md">
        <Search className="w-5 h-5 absolute ml-3 text-gray-400" />
        <Input
          placeholder="Search by name or email…"
          className="pl-10"
          value={search}
          onChange={(e) => searchUsers(e.target.value)}
        />
      </div>

      {/* CHART SECTION */}
      <Card>
        <CardHeader>
          <CardTitle>User Accuracy Distribution</CardTitle>
          <CardDescription>
            Compare accuracy, FAR, FRR across all trained users
          </CardDescription>
        </CardHeader>
        <CardContent className="h-[320px]">
          {loading ? (
            <p className="text-center text-gray-500">Loading chart…</p>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={filtered}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="user_name" stroke="#9CA3AF" />
                <YAxis stroke="#9CA3AF" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#111827",
                    border: "1px solid #374151",
                    borderRadius: "8px"
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="accuracy"
                  stroke="#3B82F6"
                  strokeWidth={2}
                  name="Accuracy %"
                />
                <Line
                  type="monotone"
                  dataKey="far"
                  stroke="#EF4444"
                  strokeWidth={2}
                  name="FAR %"
                />
                <Line
                  type="monotone"
                  dataKey="frr"
                  stroke="#F59E0B"
                  strokeWidth={2}
                  name="FRR %"
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      {/* TABLE */}
      <Card>
        <CardHeader>
          <CardTitle>Per-User Model Performance</CardTitle>
          <CardDescription>
            Accuracy, FAR, FRR, EER and training samples for each user.
          </CardDescription>
        </CardHeader>

        <CardContent>
          <div className="overflow-auto rounded-lg border border-gray-700">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>User</TableHead>
                  <TableHead>Accuracy</TableHead>
                  <TableHead>FAR</TableHead>
                  <TableHead>FRR</TableHead>
                  <TableHead>EER</TableHead>
                  <TableHead>Samples / Split</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>

              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan="8" className="text-center py-6">
                      <Loader2 className="w-6 h-6 animate-spin mx-auto" />
                    </TableCell>
                  </TableRow>
                ) : filtered.length === 0 ? (
                  <TableRow>
                    <TableCell
                      colSpan="8"
                      className="text-center py-6 text-gray-500"
                    >
                      No users found.
                    </TableCell>
                  </TableRow>
                ) : (
                  filtered.map((u) => (
                    <TableRow key={u.user_id}>
                      <TableCell>
                        <div>
                          <p className="font-semibold text-white">
                            {u.user_name}
                          </p>
                          <p className="text-gray-400 text-sm">{u.user_email}</p>
                        </div>
                      </TableCell>

                      <TableCell>
                        {u.has_model ? (
                          <Badge>{u.accuracy}%</Badge>
                        ) : (
                          <Badge variant="outline">No Model</Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        {u.has_model ? (
                          <Badge variant="destructive">{u.far}%</Badge>
                        ) : (
                          <Badge variant="outline">—</Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        {u.has_model ? (
                          <Badge variant="secondary">{u.frr}%</Badge>
                        ) : (
                          <Badge variant="outline">—</Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        {u.has_model ? (
                          <Badge className="bg-purple-600">{u.eer}%</Badge>
                        ) : (
                          <Badge variant="outline">—</Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        {u.has_model ? (
                          <div className="space-y-1">
                            <div className="font-semibold">{u.training_samples} total</div>
                            {u.split_info && (
                              <div className="text-xs text-gray-400">
                                Train: {u.split_info.train} | Val: {u.split_info.validation} | Test: {u.split_info.test}
                              </div>
                            )}
                          </div>
                        ) : (
                          <div>
                            <div className="font-semibold">{u.training_samples} collected</div>
                            {u.training_samples >= 10 && (
                              <Badge variant="default" className="mt-1">Ready to train</Badge>
                            )}
                            {u.training_samples < 10 && u.training_samples > 0 && (
                              <Badge variant="outline" className="mt-1">Need {10 - u.training_samples} more</Badge>
                            )}
                          </div>
                        )}
                      </TableCell>

                      <TableCell>
                        {u.model_trained_at ? (
                          <div className="space-y-1">
                            <Badge variant="default">Trained</Badge>
                            <div className="text-xs text-gray-400">
                              {new Date(u.model_trained_at).toLocaleDateString()}
                            </div>
                          </div>
                        ) : u.training_samples >= 10 ? (
                          <Badge variant="secondary">Ready</Badge>
                        ) : (
                          <Badge variant="outline">Collecting ({u.training_samples}/10)</Badge>
                        )}
                      </TableCell>

                      <TableCell>
                        <div className="flex gap-2">
                          {!u.has_model && u.training_samples >= 10 && (
                            <Button
                              size="sm"
                              variant="default"
                              onClick={() => trainModel(u.user_id)}
                            >
                              <Zap className="w-4 h-4 mr-1" />
                              Train
                            </Button>
                          )}
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => exportUser(u.user_id)}
                          >
                            <Download className="w-4 h-4 mr-1" />
                            Export
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
