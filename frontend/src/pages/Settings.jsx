import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Slider } from '@/components/ui/slider'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { 
  Settings as SettingsIcon, 
  Shield, 
  Bell, 
  Database, 
  Cpu, 
  Mail,
  Save,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Users,
  Lock
} from 'lucide-react'

// 🔥 FIXED: DEFAULT EXPORT REQUIRED
export default function Settings() {
  const [settings, setSettings] = useState({
    // Security Settings
    farThreshold: [0.05],
    frrThreshold: [0.10],
    anomalyThreshold: [0.85],
    sessionTimeout: [30],
    maxFailedAttempts: [3],
    enableMFA: true,
    enableGeolocation: true,
    enableDeviceFingerprinting: true,

    // ML Model Settings
    modelRetrainingInterval: [7],
    minKeystrokesForProfile: [1000],
    dataRetentionDays: [90],
    enableAutoRetraining: true,
    enableDataDriftDetection: true,

    // Alert Settings
    enableEmailAlerts: true,
    enableSlackAlerts: false,
    alertCooldown: [5],
    highPriorityThreshold: [0.90],

    // System Settings
    logLevel: 'INFO',
    enableAuditLogging: true,
    backupFrequency: 'daily',
    enableMaintenanceMode: false,

    // Notification Settings
    emailServer: 'smtp.company.com',
    emailPort: '587',
    emailUsername: 'bioauthai@company.com',
    slackWebhook: '',

    // Performance Settings
    maxConcurrentSessions: [1000],
    cacheTimeout: [300],
    enablePerformanceMonitoring: true
  })

  const [isSaving, setIsSaving] = useState(false)
  const [lastSaved, setLastSaved] = useState(new Date())

  const handleSettingChange = (key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }))
  }

  const handleSave = async () => {
    setIsSaving(true)
    await new Promise(resolve => setTimeout(resolve, 1000))
    setLastSaved(new Date())
    setIsSaving(false)
  }

  const handleReset = () => {
    setSettings({
      farThreshold: [0.05],
      frrThreshold: [0.10],
      anomalyThreshold: [0.85],
      sessionTimeout: [30],
      maxFailedAttempts: [3],
      enableMFA: true,
      enableGeolocation: true,
      enableDeviceFingerprinting: true,
      modelRetrainingInterval: [7],
      minKeystrokesForProfile: [1000],
      dataRetentionDays: [90],
      enableAutoRetraining: true,
      enableDataDriftDetection: true,
      enableEmailAlerts: true,
      enableSlackAlerts: false,
      alertCooldown: [5],
      highPriorityThreshold: [0.90],
      logLevel: 'INFO',
      enableAuditLogging: true,
      backupFrequency: 'daily',
      enableMaintenanceMode: false,
      emailServer: 'smtp.company.com',
      emailPort: '587',
      emailUsername: 'bioauthai@company.com',
      slackWebhook: '',
      maxConcurrentSessions: [1000],
      cacheTimeout: [300],
      enablePerformanceMonitoring: true
    })
  }

  return (
    <div className="p-6 space-y-6">
      {/* HEADER */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">System Settings</h1>
          <p className="text-muted-foreground">
            Configure BioAuthAI system parameters and preferences
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <p className="text-sm text-muted-foreground">
            Last saved: {lastSaved.toLocaleString()}
          </p>
          <Button variant="outline" onClick={handleReset}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Reset to Defaults
          </Button>
          <Button onClick={handleSave} disabled={isSaving}>
            <Save className="w-4 h-4 mr-2" />
            {isSaving ? 'Saving...' : 'Save Changes'}
          </Button>
        </div>
      </div>

      <Tabs defaultValue="security" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="security">
            <Shield className="w-4 h-4 mr-2" />
            Security
          </TabsTrigger>
          <TabsTrigger value="ml">
            <Cpu className="w-4 h-4 mr-2" />
            ML Models
          </TabsTrigger>
          <TabsTrigger value="alerts">
            <Bell className="w-4 h-4 mr-2" />
            Alerts
          </TabsTrigger>
          <TabsTrigger value="system">
            <Database className="w-4 h-4 mr-2" />
            System
          </TabsTrigger>
          <TabsTrigger value="notifications">
            <Mail className="w-4 h-4 mr-2" />
            Notifications
          </TabsTrigger>
        </TabsList>

        {/* SECURITY SETTINGS TAB */}
        <TabsContent value="security" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Authentication Thresholds</CardTitle>
              <CardDescription>Configure security thresholds for ML model authentication</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>FAR Threshold (False Accept Rate)</Label>
                  <span className="text-sm text-muted-foreground">{(settings.farThreshold[0] * 100).toFixed(1)}%</span>
                </div>
                <Slider
                  value={settings.farThreshold}
                  onValueChange={(value) => handleSettingChange('farThreshold', value)}
                  max={0.5}
                  step={0.01}
                  className="w-full"
                />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>FRR Threshold (False Reject Rate)</Label>
                  <span className="text-sm text-muted-foreground">{(settings.frrThreshold[0] * 100).toFixed(1)}%</span>
                </div>
                <Slider
                  value={settings.frrThreshold}
                  onValueChange={(value) => handleSettingChange('frrThreshold', value)}
                  max={0.5}
                  step={0.01}
                  className="w-full"
                />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Anomaly Detection Threshold</Label>
                  <span className="text-sm text-muted-foreground">{(settings.anomalyThreshold[0] * 100).toFixed(1)}%</span>
                </div>
                <Slider
                  value={settings.anomalyThreshold}
                  onValueChange={(value) => handleSettingChange('anomalyThreshold', value)}
                  max={1.0}
                  step={0.01}
                  min={0.5}
                  className="w-full"
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Session Security</CardTitle>
              <CardDescription>Configure session and access controls</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Session Timeout (minutes)</Label>
                  <span className="text-sm text-muted-foreground">{settings.sessionTimeout[0]}</span>
                </div>
                <Slider
                  value={settings.sessionTimeout}
                  onValueChange={(value) => handleSettingChange('sessionTimeout', value)}
                  max={120}
                  step={5}
                  min={5}
                  className="w-full"
                />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Max Failed Login Attempts</Label>
                  <span className="text-sm text-muted-foreground">{settings.maxFailedAttempts[0]}</span>
                </div>
                <Slider
                  value={settings.maxFailedAttempts}
                  onValueChange={(value) => handleSettingChange('maxFailedAttempts', value)}
                  max={10}
                  step={1}
                  min={1}
                  className="w-full"
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Multi-Factor Authentication</Label>
                  <p className="text-sm text-muted-foreground">Require MFA for all users</p>
                </div>
                <Switch
                  checked={settings.enableMFA}
                  onCheckedChange={(checked) => handleSettingChange('enableMFA', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Geolocation Tracking</Label>
                  <p className="text-sm text-muted-foreground">Track user login locations</p>
                </div>
                <Switch
                  checked={settings.enableGeolocation}
                  onCheckedChange={(checked) => handleSettingChange('enableGeolocation', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Device Fingerprinting</Label>
                  <p className="text-sm text-muted-foreground">Identify user devices</p>
                </div>
                <Switch
                  checked={settings.enableDeviceFingerprinting}
                  onCheckedChange={(checked) => handleSettingChange('enableDeviceFingerprinting', checked)}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ML MODELS TAB */}
        <TabsContent value="ml" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Model Training Settings</CardTitle>
              <CardDescription>Configure ML model training parameters</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Auto-Retraining Interval (days)</Label>
                  <span className="text-sm text-muted-foreground">{settings.modelRetrainingInterval[0]}</span>
                </div>
                <Slider
                  value={settings.modelRetrainingInterval}
                  onValueChange={(value) => handleSettingChange('modelRetrainingInterval', value)}
                  max={30}
                  step={1}
                  min={1}
                  className="w-full"
                />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Minimum Keystrokes for Profile</Label>
                  <span className="text-sm text-muted-foreground">{settings.minKeystrokesForProfile[0]}</span>
                </div>
                <Slider
                  value={settings.minKeystrokesForProfile}
                  onValueChange={(value) => handleSettingChange('minKeystrokesForProfile', value)}
                  max={5000}
                  step={100}
                  min={100}
                  className="w-full"
                />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Data Retention (days)</Label>
                  <span className="text-sm text-muted-foreground">{settings.dataRetentionDays[0]}</span>
                </div>
                <Slider
                  value={settings.dataRetentionDays}
                  onValueChange={(value) => handleSettingChange('dataRetentionDays', value)}
                  max={365}
                  step={30}
                  min={30}
                  className="w-full"
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Auto-Retraining</Label>
                  <p className="text-sm text-muted-foreground">Automatically retrain models periodically</p>
                </div>
                <Switch
                  checked={settings.enableAutoRetraining}
                  onCheckedChange={(checked) => handleSettingChange('enableAutoRetraining', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Data Drift Detection</Label>
                  <p className="text-sm text-muted-foreground">Monitor typing profile changes</p>
                </div>
                <Switch
                  checked={settings.enableDataDriftDetection}
                  onCheckedChange={(checked) => handleSettingChange('enableDataDriftDetection', checked)}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ALERTS TAB */}
        <TabsContent value="alerts" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Alert Configuration</CardTitle>
              <CardDescription>Configure security alert settings</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Email Alerts</Label>
                  <p className="text-sm text-muted-foreground">Send security alerts via email</p>
                </div>
                <Switch
                  checked={settings.enableEmailAlerts}
                  onCheckedChange={(checked) => handleSettingChange('enableEmailAlerts', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Slack Alerts</Label>
                  <p className="text-sm text-muted-foreground">Send alerts to Slack channel</p>
                </div>
                <Switch
                  checked={settings.enableSlackAlerts}
                  onCheckedChange={(checked) => handleSettingChange('enableSlackAlerts', checked)}
                />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Alert Cooldown (minutes)</Label>
                  <span className="text-sm text-muted-foreground">{settings.alertCooldown[0]}</span>
                </div>
                <Slider
                  value={settings.alertCooldown}
                  onValueChange={(value) => handleSettingChange('alertCooldown', value)}
                  max={60}
                  step={5}
                  min={1}
                  className="w-full"
                />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>High Priority Threshold</Label>
                  <span className="text-sm text-muted-foreground">{(settings.highPriorityThreshold[0] * 100).toFixed(1)}%</span>
                </div>
                <Slider
                  value={settings.highPriorityThreshold}
                  onValueChange={(value) => handleSettingChange('highPriorityThreshold', value)}
                  max={1.0}
                  step={0.05}
                  min={0.5}
                  className="w-full"
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* SYSTEM TAB */}
        <TabsContent value="system" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>System Configuration</CardTitle>
              <CardDescription>General system settings</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label>Log Level</Label>
                <Select value={settings.logLevel} onValueChange={(value) => handleSettingChange('logLevel', value)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="DEBUG">DEBUG</SelectItem>
                    <SelectItem value="INFO">INFO</SelectItem>
                    <SelectItem value="WARNING">WARNING</SelectItem>
                    <SelectItem value="ERROR">ERROR</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Backup Frequency</Label>
                <Select value={settings.backupFrequency} onValueChange={(value) => handleSettingChange('backupFrequency', value)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="hourly">Hourly</SelectItem>
                    <SelectItem value="daily">Daily</SelectItem>
                    <SelectItem value="weekly">Weekly</SelectItem>
                    <SelectItem value="monthly">Monthly</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Audit Logging</Label>
                  <p className="text-sm text-muted-foreground">Track admin actions</p>
                </div>
                <Switch
                  checked={settings.enableAuditLogging}
                  onCheckedChange={(checked) => handleSettingChange('enableAuditLogging', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Maintenance Mode</Label>
                  <p className="text-sm text-muted-foreground text-orange-600">System will be unavailable to users</p>
                </div>
                <Switch
                  checked={settings.enableMaintenanceMode}
                  onCheckedChange={(checked) => handleSettingChange('enableMaintenanceMode', checked)}
                />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Max Concurrent Sessions</Label>
                  <span className="text-sm text-muted-foreground">{settings.maxConcurrentSessions[0]}</span>
                </div>
                <Slider
                  value={settings.maxConcurrentSessions}
                  onValueChange={(value) => handleSettingChange('maxConcurrentSessions', value)}
                  max={10000}
                  step={100}
                  min={100}
                  className="w-full"
                />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Cache Timeout (seconds)</Label>
                  <span className="text-sm text-muted-foreground">{settings.cacheTimeout[0]}</span>
                </div>
                <Slider
                  value={settings.cacheTimeout}
                  onValueChange={(value) => handleSettingChange('cacheTimeout', value)}
                  max={3600}
                  step={60}
                  min={60}
                  className="w-full"
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Performance Monitoring</Label>
                  <p className="text-sm text-muted-foreground">Track API performance metrics</p>
                </div>
                <Switch
                  checked={settings.enablePerformanceMonitoring}
                  onCheckedChange={(checked) => handleSettingChange('enablePerformanceMonitoring', checked)}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* NOTIFICATIONS TAB */}
        <TabsContent value="notifications" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Email Configuration</CardTitle>
              <CardDescription>Configure email notification settings</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>SMTP Server</Label>
                <Input
                  value={settings.emailServer}
                  onChange={(e) => handleSettingChange('emailServer', e.target.value)}
                  placeholder="smtp.company.com"
                />
              </div>

              <div className="space-y-2">
                <Label>SMTP Port</Label>
                <Input
                  value={settings.emailPort}
                  onChange={(e) => handleSettingChange('emailPort', e.target.value)}
                  placeholder="587"
                  type="number"
                />
              </div>

              <div className="space-y-2">
                <Label>Email Username</Label>
                <Input
                  value={settings.emailUsername}
                  onChange={(e) => handleSettingChange('emailUsername', e.target.value)}
                  placeholder="bioauthai@company.com"
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Slack Configuration</CardTitle>
              <CardDescription>Configure Slack integration</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Slack Webhook URL</Label>
                <Textarea
                  value={settings.slackWebhook}
                  onChange={(e) => handleSettingChange('slackWebhook', e.target.value)}
                  placeholder="https://hooks.slack.com/services/..."
                  rows={3}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
