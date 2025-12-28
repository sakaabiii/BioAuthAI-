import { useState, useEffect, Suspense, lazy } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Area, AreaChart } from 'recharts'
import { Activity, Users, Shield, AlertTriangle, Monitor, Settings as SettingsIcon, BarChart3, User, RefreshCw } from 'lucide-react'
import './Dashboard.css'

// Lazy load the page components for better performance
const UserManagement = lazy(() => import("../pages/UserManagement.jsx"))
const SecurityAlerts = lazy(() => import("../pages/SecurityAlerts.jsx"))
const Analytics = lazy(() => import("../pages/Analytics.jsx"))
const LiveMonitoring = lazy(() => import("../pages/LiveMonitoring.jsx"))
const Settings = lazy(() => import("../pages/Settings.jsx"))

const BACKEND_URL = 'http://localhost:5001/api'

// Loading fallback component
const PageLoading = ({ title }) => (
  <div className="text-white p-8">
    <div className="flex items-center justify-center h-64">
      <div className="text-center">
        <RefreshCw className="w-12 h-12 animate-spin text-blue-500 mx-auto mb-4" />
        <h2 className="text-xl font-semibold mb-2">Loading {title}...</h2>
        <p className="text-gray-400">Please wait while we load the component</p>
      </div>
    </div>
  </div>
)

function Dashboard({ currentUser, onLogout }) {
  const [currentView, setCurrentView] = useState('dashboard')
  const [lastUpdated, setLastUpdated] = useState(new Date())
  const [dashboardData, setDashboardData] = useState({
    activeSessions: 0,
    authRate: 0,
    securityAlerts: 0,
    registeredUsers: 0,
    sessionChange: 0,
    authChange: 0,
    alertsChange: 0,
    usersChange: 0
  })
  const [authTrendsData, setAuthTrendsData] = useState([])
  const [deviceData, setDeviceData] = useState([])
  const [keystrokeData, setKeystrokeData] = useState([])
  const [securityAlertsData, setSecurityAlertsData] = useState([])
  const [userStats, setUserStats] = useState({})
  const [usersList, setUsersList] = useState([])
  const [isLoading, setIsLoading] = useState(false)

  // ✅ REAL ENDPOINT: Fetch user stats
  const fetchUserStats = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/users/stats`)
      if (response.ok) {
        const data = await response.json()
        setUserStats(data)
        
        setDashboardData(prev => ({
          ...prev,
          activeSessions: data.active_users || 0,
          authRate: data.avg_auth_score || 0,
          registeredUsers: data.total_users || 0,
          usersChange: data.new_users_week || 0
        }))
        return data
      }
    } catch (error) {
      console.error('Failed to fetch user stats:', error)
    }
  }

  // ✅ REAL ENDPOINT: Fetch users list
  const fetchUsers = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/users`)
      if (response.ok) {
        const data = await response.json()
        setUsersList(data)
        return data
      }
    } catch (error) {
      console.error('Failed to fetch users:', error)
    }
  }

  // ✅ REAL ENDPOINT: Fetch keystrokes
  const fetchKeystrokes = async () => {
    try {
      // Add cache-busting timestamp to force fresh data
      const response = await fetch(`${BACKEND_URL}/keystrokes?_t=${Date.now()}`, {
        cache: 'no-store',
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache'
        }
      })
      if (response.ok) {
        const data = await response.json()
        setKeystrokeData(data)

        if (data && data.length > 0) {
          const trends = generateTrendsFromKeystrokes(data)
          setAuthTrendsData(trends)
        }
        return data
      }
    } catch (error) {
      console.error('Failed to fetch keystrokes:', error)
    }
  }

  // ✅ FIXED: Fetch security alerts - extracts alerts array
  const fetchSecurityAlerts = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/alerts`)
      if (response.ok) {
        const data = await response.json()
        
        // Extract only the list of alerts
        const alerts = data.alerts || []
        
        setSecurityAlertsData(alerts)
        
        setDashboardData(prev => ({
          ...prev,
          securityAlerts: alerts.length
        }))
        
        return alerts
      }
    } catch (error) {
      console.error('Failed to fetch security alerts:', error)
    }
  }

  // Generate mock device data
  const generateDeviceData = () => {
    return [
      { name: 'Desktop', value: 45, color: '#3B82F6' },
      { name: 'Laptop', value: 35, color: '#10B981' },
      { name: 'Mobile', value: 20, color: '#F59E0B' }
    ]
  }

  // Generate trends from keystroke data
  const generateTrendsFromKeystrokes = (keystrokes) => {
    if (!keystrokes || keystrokes.length === 0) {
      return [
        { time: '00:00', value: 15 },
        { time: '04:00', value: 8 },
        { time: '08:00', value: 45 },
        { time: '12:00', value: 62 },
        { time: '16:00', value: 48 },
        { time: '20:00', value: 32 }
      ]
    }
    
    const hourlyData = {}
    keystrokes.forEach((k, index) => {
      const hour = Math.floor(index / (keystrokes.length / 6))
      const timeLabels = ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00']
      const time = timeLabels[Math.min(hour, 5)]
      hourlyData[time] = (hourlyData[time] || 0) + 1
    })
    
    return Object.entries(hourlyData).map(([time, value]) => ({ time, value }))
  }

  // Fetch ALL dashboard data
  const fetchDashboardData = async () => {
    setIsLoading(true)
    try {
      await Promise.all([
        fetchUserStats(),
        fetchUsers(),
        fetchKeystrokes(),
        fetchSecurityAlerts()
      ])
      
      setDeviceData(generateDeviceData())
      
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setIsLoading(false)
      setLastUpdated(new Date())
    }
  }

  // Initial data fetch
  useEffect(() => {
    fetchDashboardData()
  }, [])

  // Auto-refresh every 30 seconds for stability
  useEffect(() => {
    const interval = setInterval(() => {
      if (currentView === 'dashboard') {
        fetchDashboardData()
      }
    }, 30000) // 30 seconds - stable refresh rate

    return () => clearInterval(interval)
  }, [currentView])

  const formatTime = (date) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
      timeZone: 'Asia/Bahrain' // Arabia Standard Time (UTC+3)
    })
  }

  const MetricCard = ({ title, value, change, changeLabel, icon: Icon, color = 'blue', loading = false }) => (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-gray-400 text-sm font-medium">{title}</h3>
        <Icon className={`w-5 h-5 text-${color}-400`} />
      </div>
      <div className="space-y-2">
        {loading ? (
          <div className="animate-pulse">
            <div className="h-8 bg-gray-700 rounded w-24 mb-2"></div>
            <div className="h-4 bg-gray-700 rounded w-32"></div>
          </div>
        ) : (
          <>
            <div className="text-3xl font-bold text-white">
              {title === 'Auth Score' ? 
                `${value}%` : 
                typeof value === 'number' ? value.toLocaleString() : value}
            </div>
            {changeLabel && change !== 0 && (
              <div className="flex items-center text-sm">
                <span className={`text-${change > 0 ? 'green' : 'red'}-400 font-medium`}>
                  {change > 0 ? '+' : ''}{change}{changeLabel.includes('%') ? '%' : ''}
                </span>
                <span className="text-gray-500 ml-1">{changeLabel}</span>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )

  const Sidebar = () => (
    <div className="w-64 bg-gray-900 h-screen fixed left-0 top-0 border-r border-gray-700">
      <div className="p-6">
        <div className="flex items-center space-x-3 mb-8">
          <img src="/bioauthai-logo.png" alt="BioAuthAI" className="w-10 h-10" />
          <span className="text-xl font-bold text-white">BioAuthAI</span>
        </div>
        
        <nav className="space-y-2">
          <SidebarItem 
            icon={BarChart3} 
            label="Dashboard" 
            active={currentView === 'dashboard'}
            onClick={() => setCurrentView('dashboard')}
          />
          <SidebarItem 
            icon={Users} 
            label="User Management" 
            active={currentView === 'users'}
            onClick={() => setCurrentView('users')}
          />
          <SidebarItem 
            icon={AlertTriangle} 
            label="Security Alerts" 
            active={currentView === 'alerts'}
            onClick={() => setCurrentView('alerts')}
          />
          <SidebarItem 
            icon={Activity} 
            label="Analytics" 
            active={currentView === 'analytics'}
            onClick={() => setCurrentView('analytics')}
          />
          <SidebarItem 
            icon={Monitor} 
            label="Live Monitoring" 
            active={currentView === 'monitoring'}
            onClick={() => setCurrentView('monitoring')}
          />
          <SidebarItem 
            icon={SettingsIcon} 
            label="Settings" 
            active={currentView === 'settings'}
            onClick={() => setCurrentView('settings')}
          />
        </nav>
      </div>
      
      <div className="absolute bottom-0 left-0 right-0 p-6 border-t border-gray-700">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center">
            <User className="w-4 h-4 text-white" />
          </div>
          <div>
            <div className="text-sm font-medium text-white">Admin User</div>
            <div className="text-xs text-gray-400">admin@bioauthai.com</div>
          </div>
        </div>
      </div>
    </div>
  )

  const SidebarItem = ({ icon: Icon, label, active, onClick }) => (
    <button
      onClick={onClick}
      className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-left transition-colors ${
        active 
          ? 'bg-blue-600 text-white' 
          : 'text-gray-300 hover:bg-gray-800 hover:text-white'
      }`}
    >
      <Icon className="w-5 h-5" />
      <span className="font-medium">{label}</span>
    </button>
  )

  const Header = ({ title, subtitle }) => (
    <div className="flex items-center justify-between mb-8">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">{title}</h1>
        <p className="text-gray-400">{subtitle}</p>
      </div>
      <div className="flex items-center space-x-4">
        <div className="text-sm text-gray-400">
          Last updated: {formatTime(lastUpdated)}
        </div>
        <button 
          onClick={fetchDashboardData}
          className="flex items-center space-x-2 px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition-colors"
          disabled={isLoading}
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          <span>{isLoading ? 'Refreshing...' : 'Refresh'}</span>
        </button>
      </div>
    </div>
  )

  const DashboardView = () => (
    <div className="space-y-8">
      <Header 
        title="Security Dashboard" 
        subtitle="Real-time biometric authentication monitoring and analytics" 
      />
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Active Users"
          value={dashboardData.activeSessions}
          change={dashboardData.sessionChange}
          changeLabel="from last hour"
          icon={Activity}
          color="blue"
          loading={isLoading}
        />
        <MetricCard
          title="Auth Score"
          value={dashboardData.authRate}
          change={dashboardData.authChange}
          changeLabel="from yesterday"
          icon={Shield}
          color="green"
          loading={isLoading}
        />
        <MetricCard
          title="Security Alerts"
          value={dashboardData.securityAlerts}
          change={dashboardData.alertsChange}
          changeLabel="in last 24h"
          icon={AlertTriangle}
          color="red"
          loading={isLoading}
        />
        <MetricCard
          title="Registered Users"
          value={dashboardData.registeredUsers}
          change={dashboardData.usersChange}
          changeLabel="new this week"
          icon={Users}
          color="purple"
          loading={isLoading}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-2">Authentication Activity</h3>
          <p className="text-gray-400 text-sm mb-6">Keystroke activity overview</p>
          {isLoading ? (
            <div className="animate-pulse h-[300px] bg-gray-700 rounded"></div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={authTrendsData}>
                <defs>
                  <linearGradient id="colorAuth" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.1}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="time" stroke="#9CA3AF" />
                <YAxis stroke="#9CA3AF" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1F2937', 
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#F9FAFB'
                  }} 
                />
                <Area 
                  type="monotone" 
                  dataKey="value" 
                  stroke="#3B82F6" 
                  fillOpacity={1} 
                  fill="url(#colorAuth)" 
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-2">Device Distribution</h3>
          <p className="text-gray-400 text-sm mb-6">Authentication requests by device type</p>
          {isLoading ? (
            <div className="animate-pulse h-[300px] bg-gray-700 rounded"></div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={deviceData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={120}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {deviceData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1F2937', 
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#F9FAFB'
                  }} 
                />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Recent Keystrokes Section */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-6">Recent Keystroke Data</h3>
        <div className="space-y-4">
          
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map(i => (
                <div key={i} className="animate-pulse p-4 bg-gray-900 rounded-lg">
                  <div className="h-4 bg-gray-700 rounded w-3/4 mb-2"></div>
                  <div className="h-3 bg-gray-700 rounded w-1/2"></div>
                </div>
              ))}
            </div>
          ) : keystrokeData && keystrokeData.length > 0 ? (
            keystrokeData.slice(-5).reverse().map((item, index) => {
              
              // FIX: Prevent React from rendering objects
              const hasFeatures =
                item.keystroke_features &&
                typeof item.keystroke_features === "object" &&
                Object.keys(item.keystroke_features).length > 0;

              return (
                <div
                  key={index}
                  className="flex items-center justify-between p-4 bg-gray-900 rounded-lg"
                >
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                      <span className="text-white font-medium">
                        User ID: {String(item.user_id || "Unknown")}
                      </span>
                    </div>

                    <div className="text-sm text-gray-400">
                      Session: {String(item.session_id || "N/A")}
                    </div>
                  </div>

                  <div className="text-right">
                    <div className="text-blue-400 font-bold">
                      {hasFeatures ? "✓" : "○"}
                    </div>

                    <div className="text-xs text-gray-500">
                      {item.timestamp
                        ? new Date(item.timestamp + 'Z').toLocaleTimeString('en-US', {
                            hour: '2-digit',
                            minute: '2-digit',
                            second: '2-digit',
                            hour12: false,
                            timeZone: 'Asia/Bahrain'
                          })
                        : "Recent"}
                    </div>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="text-center text-gray-500 py-8">
              No keystroke data available
            </div>
          )}

        </div>
      </div>
    </div>
  )

  const renderCurrentView = () => {
    switch (currentView) {
      case "dashboard":
        return <DashboardView />

      case "users":
        return (
          <Suspense fallback={<PageLoading title="User Management" />}>
            <UserManagement />
          </Suspense>
        )

      case "alerts":
        return (
          <Suspense fallback={<PageLoading title="Security Alerts" />}>
            <SecurityAlerts />
          </Suspense>
        )

      case "analytics":
        return (
          <Suspense fallback={<PageLoading title="Analytics" />}>
            <Analytics />
          </Suspense>
        )

      case "monitoring":
        return (
          <Suspense fallback={<PageLoading title="Live Monitoring" />}>
            <LiveMonitoring />
          </Suspense>
        )

      case "settings":
        return (
          <Suspense fallback={<PageLoading title="Settings" />}>
            <Settings />
          </Suspense>
        )

      default:
        return <DashboardView />
    }
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <Sidebar />
      <div className="ml-64 p-8">
        {renderCurrentView()}
      </div>
    </div>
  )
}

export default Dashboard