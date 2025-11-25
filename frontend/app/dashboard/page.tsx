'use client'

import { useEffect, useState } from 'react'
import { MetricsCard } from '@/components/MetricsCard'
import { ProviderChart } from '@/components/ProviderChart'
import { RecentRequests } from '@/components/RecentRequests'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import {
  getStats,
  getCacheStats,
  getRoutingMetrics,
  getHealth,
  type Stats,
  type CacheStats,
  type RoutingMetrics,
  type HealthStatus,
} from '@/lib/api'
import {
  DollarSign,
  Activity,
  Zap,
  Database,
  RefreshCw,
  TrendingUp,
  Server,
  Brain,
} from 'lucide-react'

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [cacheStats, setCacheStats] = useState<CacheStats | null>(null)
  const [routingMetrics, setRoutingMetrics] = useState<RoutingMetrics | null>(null)
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)

      const [statsData, cacheData, routingData, healthData] = await Promise.all([
        getStats().catch(() => null),
        getCacheStats().catch(() => null),
        getRoutingMetrics().catch(() => null),
        getHealth().catch(() => null),
      ])

      setStats(statsData)
      setCacheStats(cacheData)
      setRoutingMetrics(routingData)
      setHealth(healthData)
      setLastUpdated(new Date())
    } catch {
      setError('Failed to fetch data. Is the API server running?')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading && !stats) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto text-primary" />
          <p className="mt-2 text-sm text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  if (error && !stats) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Server className="h-8 w-8 mx-auto text-destructive" />
          <p className="mt-2 text-sm text-destructive">{error}</p>
          <Button onClick={fetchData} className="mt-4" variant="outline">
            <RefreshCw className="mr-2 h-4 w-4" />
            Retry
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Real-time AI cost optimization metrics
          </p>
        </div>
        <div className="flex items-center gap-4">
          {lastUpdated && (
            <span className="text-xs text-muted-foreground">
              Updated {lastUpdated.toLocaleTimeString()}
            </span>
          )}
          <Button onClick={fetchData} variant="outline" size="sm">
            <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Service Status */}
      {health && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Badge variant="success" className="text-xs">
                  {health.status}
                </Badge>
                <span className="text-sm text-muted-foreground">
                  v{health.version}
                </span>
                <span className="text-sm text-muted-foreground">
                  Cache: {health.cache_enabled ? 'Enabled' : 'Disabled'}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Providers:</span>
                {health.providers.map((provider) => (
                  <Badge key={provider} variant="outline" className="capitalize">
                    {provider}
                  </Badge>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricsCard
          title="Total Cost"
          value={stats ? `$${(stats.total_cost_cents / 100).toFixed(2)}` : '$0.00'}
          description="All time spending"
          icon={DollarSign}
        />
        <MetricsCard
          title="Total Requests"
          value={stats?.total_requests.toLocaleString() || '0'}
          description="API calls processed"
          icon={Activity}
        />
        <MetricsCard
          title="Cache Hit Rate"
          value={cacheStats ? `${(cacheStats.hit_rate * 100).toFixed(1)}%` : '0%'}
          description={`${cacheStats?.total_hits.toLocaleString() || 0} cache hits`}
          icon={Zap}
          badge={
            cacheStats && cacheStats.hit_rate > 0.7
              ? { text: 'Excellent', variant: 'success' }
              : cacheStats && cacheStats.hit_rate > 0.4
              ? { text: 'Good', variant: 'warning' }
              : { text: 'Low', variant: 'destructive' }
          }
        />
        <MetricsCard
          title="Routing Accuracy"
          value={
            routingMetrics
              ? `${(routingMetrics.accuracy_rate * 100).toFixed(1)}%`
              : 'N/A'
          }
          description={`${routingMetrics?.total_decisions.toLocaleString() || 0} decisions`}
          icon={Brain}
        />
      </div>

      {/* Secondary Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricsCard
          title="Total Tokens"
          value={stats?.total_tokens.toLocaleString() || '0'}
          description="Tokens processed"
          icon={Database}
        />
        <MetricsCard
          title="Avg Response Time"
          value={stats ? `${stats.avg_response_time_ms.toFixed(0)}ms` : '0ms'}
          description="Average latency"
          icon={TrendingUp}
        />
        <MetricsCard
          title="Cache Entries"
          value={cacheStats?.total_entries.toLocaleString() || '0'}
          description={`${cacheStats?.storage_used_mb.toFixed(2) || 0} MB used`}
          icon={Database}
        />
        <MetricsCard
          title="Avg Confidence"
          value={
            routingMetrics
              ? `${(routingMetrics.avg_confidence * 100).toFixed(0)}%`
              : 'N/A'
          }
          description="Routing confidence"
          icon={Brain}
        />
      </div>

      {/* Charts */}
      <div className="grid gap-4 md:grid-cols-2">
        {stats && (
          <>
            <ProviderChart
              data={stats.requests_by_provider}
              title="Requests by Provider"
              type="requests"
            />
            <ProviderChart
              data={stats.cost_by_provider}
              title="Cost by Provider"
              type="cost"
            />
          </>
        )}
      </div>

      {/* Recent Activity - Placeholder */}
      <RecentRequests requests={[]} />
    </div>
  )
}
