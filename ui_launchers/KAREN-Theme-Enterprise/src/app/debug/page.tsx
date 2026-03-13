"use client";

import { ConnectionDiagnostic } from '@/components/debug/ConnectionDiagnostic';
import { SimpleConnectionTest } from '@/components/debug/SimpleConnectionTest';
import { getConfigManager } from '@/lib/endpoint-config';

export default function DebugPage() {
  const configManager = getConfigManager();
  const config = configManager.getConfiguration();
  const envInfo = configManager.getEnvironmentInfo();

  return (
    <div className="container mx-auto p-8 space-y-8">
      <h1 className="text-2xl font-bold">Debug Information</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">Environment Configuration</h2>
          <div className="bg-gray-100 p-4 rounded-lg">
            <pre className="text-sm overflow-auto">
              {JSON.stringify(envInfo, null, 2)}
            </pre>
          </div>
        </div>

        <div className="space-y-4">
          <h2 className="text-xl font-semibold">Endpoint Configuration</h2>
          <div className="bg-gray-100 p-4 rounded-lg">
            <pre className="text-sm overflow-auto">
              {JSON.stringify({
                backendUrl: config.backendUrl,
                fallbackUrls: config.fallbackUrls,
                healthCheckEnabled: config.healthCheckEnabled,
                corsOrigins: config.corsOrigins,
              }, null, 2)}
            </pre>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <h2 className="text-xl font-semibold">Environment Variables</h2>
        <div className="bg-gray-100 p-4 rounded-lg">
          <pre className="text-sm overflow-auto">
            {JSON.stringify({
              NODE_ENV: process.env.NODE_ENV,
              NEXT_PUBLIC_USE_PROXY: process.env.NEXT_PUBLIC_USE_PROXY,
              NEXT_PUBLIC_KAREN_BACKEND_URL: process.env.NEXT_PUBLIC_KAREN_BACKEND_URL,
              NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL,
            }, null, 2)}
          </pre>
        </div>
      </div>

      <SimpleConnectionTest />
      
      <ConnectionDiagnostic />
    </div>
  );
}