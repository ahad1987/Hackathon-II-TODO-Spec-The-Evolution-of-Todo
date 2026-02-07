'use client';

import { useEffect, useState } from 'react';
import { monitoringApi, type MonitoringOverview } from '@/services/api';

export default function MonitoringPanel() {
  const [overview, setOverview] = useState<MonitoringOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const fetchMonitoring = async () => {
    try {
      setError(null);
      const data = await monitoringApi.getOverview();
      setOverview(data);
      setLastUpdate(new Date());
      setLoading(false);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch monitoring data');
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMonitoring();
    const interval = setInterval(fetchMonitoring, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !overview) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 border border-slate-200">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-3 h-3 bg-slate-400 rounded-full animate-pulse" />
          <h2 className="text-lg font-semibold text-slate-900">System Monitoring</h2>
        </div>
        <p className="text-slate-600 text-sm">Loading...</p>
      </div>
    );
  }

  if (error && !overview) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 border border-red-200">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-3 h-3 bg-red-500 rounded-full" />
          <h2 className="text-lg font-semibold text-slate-900">System Monitoring</h2>
        </div>
        <p className="text-red-600 text-sm">{error}</p>
        <button
          onClick={fetchMonitoring}
          className="mt-3 px-4 py-2 bg-red-100 text-red-700 rounded hover:bg-red-200 text-sm"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!overview) return null;

  const healthColor = {
    healthy: 'bg-green-500',
    degraded: 'bg-yellow-500',
    unhealthy: 'bg-red-500',
  }[overview.overall_health];

  const healthText = {
    healthy: 'All Systems Operational',
    degraded: 'Partial Degradation',
    unhealthy: 'Service Disruption',
  }[overview.overall_health];

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200">
      {/* Header */}
      <div className="p-4 border-b border-slate-200">
        <div className="flex items-center gap-2 mb-2">
          <div className={`w-3 h-3 rounded-full ${healthColor} animate-pulse`} />
          <h2 className="text-lg font-semibold text-slate-900">System Monitoring</h2>
        </div>
        <p className="text-xs text-slate-500">
          Updated {lastUpdate.toLocaleTimeString()}
        </p>
      </div>

      {/* Overall Status */}
      <div className="p-4 bg-slate-50 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${healthColor}`} />
          <span className="text-sm font-medium text-slate-900">{healthText}</span>
        </div>
      </div>

      <div className="divide-y divide-slate-200">
        {/* Kafka Status */}
        <div className="p-4">
          <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2 mb-3">
            <span>📊</span>
            Kafka
          </h3>

          <div className="space-y-2">
            <div className="flex items-center justify-between p-2 bg-slate-50 rounded text-xs">
              <span className="text-slate-600">Broker</span>
              <div className="flex items-center gap-2">
                <div className={`w-1.5 h-1.5 rounded-full ${overview.kafka.broker.connected ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="font-medium text-slate-900">{overview.kafka.broker.status}</span>
              </div>
            </div>

            <div className="flex items-center justify-between p-2 bg-slate-50 rounded text-xs">
              <span className="text-slate-600">Topics</span>
              <span className="font-medium text-slate-900">{overview.kafka.topics.length}</span>
            </div>
          </div>
        </div>

        {/* Dapr Sidecars */}
        <div className="p-4">
          <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2 mb-3">
            <span>🔗</span>
            Dapr Sidecars
          </h3>

          <div className="flex items-center justify-between p-2 bg-slate-50 rounded text-xs mb-2">
            <span className="text-slate-600">Healthy</span>
            <span className="font-medium text-slate-900">
              {overview.dapr.healthy} / {overview.dapr.sidecars.length}
            </span>
          </div>

          <div className="space-y-1">
            {overview.dapr.sidecars.map((sidecar) => (
              <div
                key={sidecar.name}
                className="flex items-center justify-between p-1.5 bg-white rounded border border-slate-100"
              >
                <div className="flex items-center gap-1.5">
                  <div className={`w-1 h-1 rounded-full ${sidecar.healthy ? 'bg-green-500' : 'bg-red-500'}`} />
                  <span className="text-xs text-slate-700 truncate">{sidecar.name}</span>
                </div>
                <span className={`text-xs ${sidecar.healthy ? 'text-green-600' : 'text-red-600'}`}>
                  {sidecar.healthy ? '✓' : '✗'}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Kubernetes & Secrets */}
        <div className="p-4">
          <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2 mb-3">
            <span>☸️</span>
            Kubernetes
          </h3>

          <div className="space-y-2">
            <div className="flex items-center justify-between p-2 bg-slate-50 rounded text-xs">
              <span className="text-slate-600">Cluster</span>
              <div className="flex items-center gap-2">
                <div className={`w-1.5 h-1.5 rounded-full ${overview.kubernetes.cluster === 'connected' ? 'bg-green-500' : 'bg-slate-400'}`} />
                <span className="font-medium text-slate-900 capitalize">{overview.kubernetes.cluster}</span>
              </div>
            </div>

            <div className="flex items-center justify-between p-2 bg-slate-50 rounded text-xs">
              <span className="text-slate-600">Mode</span>
              <span className="font-medium text-slate-900 capitalize">{overview.kubernetes.mode}</span>
            </div>

            {/* Secrets Section */}
            <div className="mt-3 pt-3 border-t border-slate-200">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-slate-700">🔐 Secrets</span>
                <span className={`text-xs px-1.5 py-0.5 rounded ${
                  overview.kubernetes.secrets.status === 'healthy' ? 'bg-green-100 text-green-700' :
                  overview.kubernetes.secrets.status === 'incomplete' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-slate-100 text-slate-600'
                }`}>
                  {overview.kubernetes.secrets.status}
                </span>
              </div>

              {overview.kubernetes.mode === 'docker-compose' ? (
                <div className="space-y-1">
                  <p className="text-xs text-slate-600 mb-2">{overview.kubernetes.secrets.message}</p>
                  {overview.kubernetes.secrets.expected && overview.kubernetes.secrets.expected.map((secret) => (
                    <div key={secret} className="flex items-center gap-1.5 p-1.5 bg-green-50 rounded">
                      <div className="w-1 h-1 rounded-full bg-green-500" />
                      <span className="text-xs text-slate-700 font-mono">{secret}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="space-y-1">
                  {overview.kubernetes.secrets.configured.length > 0 && (
                    <div>
                      <p className="text-xs text-green-600 mb-1">✓ Configured ({overview.kubernetes.secrets.configured.length})</p>
                      {overview.kubernetes.secrets.configured.map((secret) => (
                        <div key={secret} className="flex items-center gap-1.5 p-1 bg-green-50 rounded">
                          <span className="text-xs text-slate-700 font-mono truncate">{secret}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  {overview.kubernetes.secrets.missing.length > 0 && (
                    <div className="mt-2">
                      <p className="text-xs text-red-600 mb-1">✗ Missing ({overview.kubernetes.secrets.missing.length})</p>
                      {overview.kubernetes.secrets.missing.map((secret) => (
                        <div key={secret} className="flex items-center gap-1.5 p-1 bg-red-50 rounded">
                          <span className="text-xs text-slate-700 font-mono truncate">{secret}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* CI/CD Pipelines */}
        <div className="p-4">
          <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2 mb-3">
            <span>🔄</span>
            CI/CD
          </h3>

          <div className="flex items-center justify-between p-2 bg-slate-50 rounded text-xs mb-2">
            <span className="text-slate-600">Status</span>
            <div className="flex items-center gap-2">
              <div className={`w-1.5 h-1.5 rounded-full ${overview.cicd.status === 'configured' ? 'bg-green-500' : 'bg-slate-400'}`} />
              <span className="font-medium text-slate-900 capitalize">{overview.cicd.status}</span>
            </div>
          </div>

          {overview.cicd.pipelines.length > 0 ? (
            <div className="space-y-1">
              {overview.cicd.pipelines.map((pipeline) => (
                <div
                  key={pipeline.name}
                  className="flex items-center justify-between p-1.5 bg-white rounded border border-slate-100"
                >
                  <span className="text-xs text-slate-700 truncate">{pipeline.name}</span>
                  <span className="text-xs text-slate-500">{pipeline.type === 'github-actions' ? 'GHA' : pipeline.type}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-500">{overview.cicd.message}</p>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 bg-slate-50 border-t border-slate-200">
        <div className="flex items-center gap-4 text-xs text-slate-600">
          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 bg-green-500 rounded-full" />
            <span>Healthy</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 bg-yellow-500 rounded-full" />
            <span>Degraded</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 bg-red-500 rounded-full" />
            <span>Unhealthy</span>
          </div>
        </div>
        <p className="text-xs text-slate-500 mt-2">Auto-refresh: 5s</p>
      </div>
    </div>
  );
}
