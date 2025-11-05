/**
 * Admin API Tester Component
 *
 * Production utility for testing and validating all admin API integrations:
 * - User Management APIs
 * - Security APIs
 * - System Configuration
 * - Performance Monitoring
 * - Cognitive Health
 * - Reasoning Engine
 * - Audit Logs
 *
 * Useful for validating backend connections and debugging API issues
 */

"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

interface APIEndpoint {
  name: string;
  method: "GET" | "POST" | "PUT" | "DELETE";
  path: string;
  description: string;
  requiresAuth: boolean;
}

interface TestResult {
  endpoint: string;
  status: "success" | "error" | "testing";
  statusCode?: number;
  responseTime?: number;
  error?: string;
  data?: any;
}

export function AdminAPITester() {
  const [results, setResults] = useState<Record<string, TestResult>>({});
  const [testing, setTesting] = useState(false);

  const endpoints: APIEndpoint[] = [
    // User Management
    { name: "User Stats", method: "GET", path: "/api/admin/users/stats", description: "Get user statistics", requiresAuth: true },
    { name: "User List", method: "GET", path: "/api/admin/users", description: "List all users", requiresAuth: true },

    // System Health
    { name: "System Health", method: "GET", path: "/api/admin/system/health", description: "Overall system health", requiresAuth: true },
    { name: "Activity Summary", method: "GET", path: "/api/admin/system/activity-summary?period=week", description: "Weekly activity summary", requiresAuth: true },

    // Cognitive & Reasoning
    { name: "Cognitive Health", method: "GET", path: "/api/cognitive/health", description: "5-layer cognitive engine health", requiresAuth: false },
    { name: "Reasoning Health", method: "GET", path: "/api/reasoning/health", description: "Reasoning engine health", requiresAuth: false },

    // Security
    { name: "Security Dashboard", method: "GET", path: "/api/admin/security/dashboard", description: "Security overview", requiresAuth: true },
    { name: "Security Alerts", method: "GET", path: "/api/admin/security/alerts", description: "Security alerts list", requiresAuth: true },

    // Performance
    { name: "Dashboard Stats", method: "GET", path: "/api/admin/dashboard/stats", description: "Dashboard statistics", requiresAuth: true },

    // Audit
    { name: "Audit Logs", method: "GET", path: "/api/admin/system/audit-logs?limit=10", description: "Recent audit logs", requiresAuth: true },
  ];

  const testEndpoint = async (endpoint: APIEndpoint): Promise<TestResult> => {
    const startTime = Date.now();

    try {
      const response = await fetch(endpoint.path, {
        method: endpoint.method,
        headers: {
          "Content-Type": "application/json",
          "Cache-Control": "no-store",
        },
      });

      const responseTime = Date.now() - startTime;
      let data;

      try {
        data = await response.json();
      } catch {
        data = { raw: await response.text() };
      }

      if (response.ok) {
        return {
          endpoint: endpoint.path,
          status: "success",
          statusCode: response.status,
          responseTime,
          data,
        };
      } else {
        return {
          endpoint: endpoint.path,
          status: "error",
          statusCode: response.status,
          responseTime,
          error: data?.error?.message || `HTTP ${response.status} ${response.statusText}`,
          data,
        };
      }
    } catch (error) {
      const responseTime = Date.now() - startTime;
      return {
        endpoint: endpoint.path,
        status: "error",
        responseTime,
        error: error instanceof Error ? error.message : "Network error",
      };
    }
  };

  const testSingle = async (endpoint: APIEndpoint) => {
    setResults(prev => ({
      ...prev,
      [endpoint.path]: { endpoint: endpoint.path, status: "testing" },
    }));

    const result = await testEndpoint(endpoint);

    setResults(prev => ({
      ...prev,
      [endpoint.path]: result,
    }));
  };

  const testAll = async () => {
    setTesting(true);
    setResults({});

    // Test endpoints sequentially to avoid overwhelming the server
    for (const endpoint of endpoints) {
      await testSingle(endpoint);
      // Small delay between tests
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    setTesting(false);
  };

  const getStatusColor = (status: TestResult["status"]) => {
    switch (status) {
      case "success":
        return "text-green-600 bg-green-50 border-green-200";
      case "error":
        return "text-red-600 bg-red-50 border-red-200";
      case "testing":
        return "text-blue-600 bg-blue-50 border-blue-200";
      default:
        return "text-gray-600 bg-gray-50 border-gray-200";
    }
  };

  const getStatusIcon = (status: TestResult["status"]) => {
    switch (status) {
      case "success":
        return "✓";
      case "error":
        return "✗";
      case "testing":
        return "⟳";
      default:
        return "○";
    }
  };

  const clearResults = () => {
    setResults({});
  };

  return (
    <Card className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Admin API Tester</h2>
        <p className="text-gray-600">
          Test and validate all admin API endpoints for production readiness
        </p>
      </div>

      {/* Actions */}
      <div className="flex gap-3 mb-6">
        <Button
          onClick={testAll}
          disabled={testing}
          className="flex items-center gap-2"
        >
          {testing ? (
            <>
              <span className="animate-spin">⟳</span>
              Testing All Endpoints...
            </>
          ) : (
            <>
              <span>▶</span>
              Test All Endpoints
            </>
          )}
        </Button>
        <Button onClick={clearResults} variant="outline">
          Clear Results
        </Button>
      </div>

      {/* Summary */}
      {Object.keys(results).length > 0 && (
        <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <p className="text-sm text-green-600 font-medium">Passed</p>
            <p className="text-2xl font-bold text-green-700">
              {Object.values(results).filter(r => r.status === "success").length}
            </p>
          </div>
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-sm text-red-600 font-medium">Failed</p>
            <p className="text-2xl font-bold text-red-700">
              {Object.values(results).filter(r => r.status === "error").length}
            </p>
          </div>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-600 font-medium">Avg Response Time</p>
            <p className="text-2xl font-bold text-blue-700">
              {Object.values(results).filter(r => r.responseTime).length > 0
                ? Math.round(
                    Object.values(results)
                      .filter(r => r.responseTime)
                      .reduce((sum, r) => sum + (r.responseTime || 0), 0) /
                      Object.values(results).filter(r => r.responseTime).length
                  )
                : 0}
              ms
            </p>
          </div>
        </div>
      )}

      {/* Endpoints List */}
      <div className="space-y-3">
        {endpoints.map((endpoint, index) => {
          const result = results[endpoint.path];

          return (
            <div
              key={index}
              className={`border rounded-lg p-4 ${
                result ? getStatusColor(result.status) : "border-gray-200"
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-1">
                    <span className="text-2xl">
                      {result ? getStatusIcon(result.status) : "○"}
                    </span>
                    <div>
                      <h3 className="font-semibold text-gray-900">{endpoint.name}</h3>
                      <p className="text-sm text-gray-600">{endpoint.description}</p>
                    </div>
                  </div>

                  <div className="ml-11 space-y-1">
                    <p className="text-sm font-mono text-gray-700">
                      <span className="font-bold">{endpoint.method}</span> {endpoint.path}
                    </p>

                    {result && (
                      <div className="mt-2 space-y-1">
                        {result.statusCode && (
                          <p className="text-sm">
                            <span className="font-medium">Status:</span> {result.statusCode}
                          </p>
                        )}
                        {result.responseTime !== undefined && (
                          <p className="text-sm">
                            <span className="font-medium">Response Time:</span> {result.responseTime}ms
                          </p>
                        )}
                        {result.error && (
                          <p className="text-sm text-red-600">
                            <span className="font-medium">Error:</span> {result.error}
                          </p>
                        )}
                        {result.data && result.status === "success" && (
                          <details className="text-sm">
                            <summary className="cursor-pointer font-medium hover:text-blue-600">
                              View Response Data
                            </summary>
                            <pre className="mt-2 p-2 bg-gray-900 text-gray-100 rounded text-xs overflow-x-auto">
                              {JSON.stringify(result.data, null, 2)}
                            </pre>
                          </details>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                <Button
                  onClick={() => testSingle(endpoint)}
                  size="sm"
                  variant="outline"
                  disabled={testing || result?.status === "testing"}
                  className="ml-4"
                >
                  {result?.status === "testing" ? "Testing..." : "Test"}
                </Button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Production Notes */}
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h4 className="font-medium text-blue-900 mb-2">Production Validation Notes</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Endpoints marked "requiresAuth: true" need valid authentication</li>
          <li>• Cognitive and Reasoning endpoints should be publicly accessible</li>
          <li>• Response times under 100ms are excellent, under 500ms are acceptable</li>
          <li>• Failed endpoints may indicate missing backend services or environment configuration</li>
          <li>• Use this tool to validate API integration before production deployment</li>
        </ul>
      </div>
    </Card>
  );
}
