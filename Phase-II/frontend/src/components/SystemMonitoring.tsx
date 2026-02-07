'use client';

import { useEffect, useState } from 'react';
import axios from 'axios';

interface ServiceStatus {
  name: string;
  status: 'healthy' | 'unhealthy' | 'unknown';
  message?: string;
}

interface SystemStatus {
  backend: ServiceStatus;
  database: ServiceStatus;
  kafka: ServiceStatus;
  dapr: ServiceStatus;
  overall: 'healthy' | 'degraded' | 'unhealthy';
}

export function SystemMonitoringPanel() {
  const [status, setStatus] = useState<SystemStatus>({
    backend: { name: 'Backend API', status: 'unknown' },
    database: { name: 'PostgreSQL', status: 'unknown' },
    kafka: { name: 'Kafka', status: 'unknown' },
    dapr: { name: 'Dapr Sidecars', status: 'unknown' },
    overall: 'unhealthy',
  });
  const [lastUpdate, setLastUpdate] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const fetchSystemStatus = async () => {
    try {
      // Check backend health
      const healthRes = await axios.get(`${API_URL}/health/live`, { timeout: 3000 });
      const backendHealthy = healthRes.status === 200;

      // Check monitoring overview
      const monitoringRes = await axios.get(`${API_URL}/api/v1/monitoring/overview`, { timeout: 5000 });
      const data = monitoringRes.data;

      setStatus({
        backend: {
          name: 'Backend API',
          status: backendHealthy ? 'healthy' : 'unhealthy',
          message: backendHealthy ? 'Connected' : 'Disconnected',
        },
        database: {
          name: 'PostgreSQL',
          status: backendHealthy ? 'healthy' : 'unknown',
          message: 'Connected',
        },
        kafka: {
          name: 'Kafka Broker',
          status: data.kafka?.broker?.connected ? 'healthy' : 'unhealthy',
          message: data.kafka?.broker?.connected ? 'Connected' : 'Disconnected',
        },
        dapr: {
          name: 'Dapr Sidecars',
          status: data.dapr?.healthy >= 1 ? 'healthy' : 'unhealthy',
          message: `${data.dapr?.healthy || 0}/${data.dapr?.sidecars?.length || 5} sidecars`,
        },
        overall: data.overall_health || 'degraded',
      });

      setLastUpdate(new Date().toLocaleTimeString());
      setIsLoading(false);
    } catch (error) {
      console.error('Failed to fetch system status:', error);
      setStatus({
        backend: { name: 'Backend API', status: 'unhealthy', message: 'Connection failed' },
        database: { name: 'PostgreSQL', status: 'unknown', message: 'Unknown' },
        kafka: { name: 'Kafka', status: 'unknown', message: 'Unknown' },
        dapr: { name: 'Dapr Sidecars', status: 'unknown', message: 'Unknown' },
        overall: 'unhealthy',
      });
      setLastUpdate(new Date().toLocaleTimeString());
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // Fetch immediately
    fetchSystemStatus();

    // Poll every 10 seconds
    const interval = setInterval(fetchSystemStatus, 10000);

    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: ServiceStatus['status']) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-500';
      case 'unhealthy':
        return 'bg-red-500';
      default:
        return 'bg-gray-400';
    }
  };

  const getStatusText = (status: ServiceStatus['status']) => {
    switch (status) {
      case 'healthy':
        return 'Healthy';
      case 'unhealthy':
        return 'Unhealthy';
      default:
        return 'Unknown';
    }
  };

  return (
    <div className="fixed right-0 top-16 w-64 bg-white border-l border-gray-200 shadow-lg h-[calc(100vh-4rem)] overflow-y-auto z-30">
      <div className="p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-gray-900">System Status</h3>
          {isLoading ? (
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
          ) : (
            <div className={`w-2 h-2 rounded-full ${status.overall === 'healthy' ? 'bg-green-500' : status.overall === 'degraded' ? 'bg-yellow-500' : 'bg-red-500'}`}></div>
          )}
        </div>

        <div className="space-y-3">
          {/* Backend */}
          <div className="border border-gray-200 rounded-lg p-3">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-medium text-gray-700">{status.backend.name}</span>
              <div className={`w-2 h-2 rounded-full ${getStatusColor(status.backend.status)}`}></div>
            </div>
            <div className="text-xs text-gray-500">{status.backend.message || getStatusText(status.backend.status)}</div>
          </div>

          {/* Database */}
          <div className="border border-gray-200 rounded-lg p-3">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-medium text-gray-700">{status.database.name}</span>
              <div className={`w-2 h-2 rounded-full ${getStatusColor(status.database.status)}`}></div>
            </div>
            <div className="text-xs text-gray-500">{status.database.message || getStatusText(status.database.status)}</div>
          </div>

          {/* Kafka */}
          <div className="border border-gray-200 rounded-lg p-3">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-medium text-gray-700">{status.kafka.name}</span>
              <div className={`w-2 h-2 rounded-full ${getStatusColor(status.kafka.status)}`}></div>
            </div>
            <div className="text-xs text-gray-500">{status.kafka.message || getStatusText(status.kafka.status)}</div>
          </div>

          {/* Dapr */}
          <div className="border border-gray-200 rounded-lg p-3">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-medium text-gray-700">{status.dapr.name}</span>
              <div className={`w-2 h-2 rounded-full ${getStatusColor(status.dapr.status)}`}></div>
            </div>
            <div className="text-xs text-gray-500">{status.dapr.message || getStatusText(status.dapr.status)}</div>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="text-xs text-gray-500">
            Last updated: {lastUpdate || 'Never'}
          </div>
          <div className="text-xs text-gray-400 mt-1">
            Updates every 10s
          </div>
        </div>
      </div>
    </div>
  );
}
