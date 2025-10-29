/**
 * Main Automation Page - Integrates all automation components
 */

import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Zap, Activity, BarChart3, Settings } from 'lucide-react';

import AutomationStudio from '../components/AutomationStudio';
import WorkflowMonitor from '../components/WorkflowMonitor';

const AutomationPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('studio');

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Zap className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Prompt-Driven Automation</h1>
                <p className="text-gray-600">AI-native workflow automation platform</p>
              </div>
              <Badge variant="secondary" className="ml-2">
                Beta
              </Badge>
            </div>
            
            <div className="flex items-center space-x-2">
              <Badge variant="outline" className="text-green-600 border-green-600">
                AI-Powered
              </Badge>
              <Badge variant="outline" className="text-blue-600 border-blue-600">
                Natural Language
              </Badge>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-6 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-4 lg:w-96">
            <TabsTrigger value="studio" className="flex items-center space-x-2">
              <Zap className="h-4 w-4" />
              <span className="hidden sm:inline">Studio</span>
            </TabsTrigger>
            <TabsTrigger value="monitor" className="flex items-center space-x-2">
              <Activity className="h-4 w-4" />
              <span className="hidden sm:inline">Monitor</span>
            </TabsTrigger>
            <TabsTrigger value="analytics" className="flex items-center space-x-2">
              <BarChart3 className="h-4 w-4" />
              <span className="hidden sm:inline">Analytics</span>
            </TabsTrigger>
            <TabsTrigger value="settings" className="flex items-center space-x-2">
              <Settings className="h-4 w-4" />
              <span className="hidden sm:inline">Settings</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="studio">
            <AutomationStudio />
          </TabsContent>

          <TabsContent value="monitor">
            <WorkflowMonitor />
          </TabsContent>

          <TabsContent value="analytics">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <BarChart3 className="h-5 w-5" />
                  <span>Advanced Analytics</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-12">
                  <BarChart3 className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Advanced Analytics Coming Soon</h3>
                  <p className="text-gray-600 max-w-md mx-auto">
                    Detailed workflow analytics, performance insights, and optimization recommendations 
                    will be available in the next release.
                  </p>
                  <div className="mt-6 space-y-2">
                    <div className="flex items-center justify-center space-x-2 text-sm text-gray-500">
                      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      <span>Workflow performance trends</span>
                    </div>
                    <div className="flex items-center justify-center space-x-2 text-sm text-gray-500">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <span>Plugin usage analytics</span>
                    </div>
                    <div className="flex items-center justify-center space-x-2 text-sm text-gray-500">
                      <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                      <span>Cost optimization insights</span>
                    </div>
                    <div className="flex items-center justify-center space-x-2 text-sm text-gray-500">
                      <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                      <span>Predictive failure analysis</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="settings">
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Automation Settings</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold mb-3">Execution Settings</h3>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between p-4 border rounded-lg">
                        <div>
                          <h4 className="font-medium">Auto-retry Failed Workflows</h4>
                          <p className="text-sm text-gray-600">Automatically retry workflows that fail due to temporary issues</p>
                        </div>
                        <Badge variant="outline">Enabled</Badge>
                      </div>
                      
                      <div className="flex items-center justify-between p-4 border rounded-lg">
                        <div>
                          <h4 className="font-medium">Parallel Execution</h4>
                          <p className="text-sm text-gray-600">Allow multiple workflows to run simultaneously</p>
                        </div>
                        <Badge variant="outline">Enabled</Badge>
                      </div>
                      
                      <div className="flex items-center justify-between p-4 border rounded-lg">
                        <div>
                          <h4 className="font-medium">Smart Scheduling</h4>
                          <p className="text-sm text-gray-600">Optimize workflow scheduling based on historical performance</p>
                        </div>
                        <Badge variant="outline">Enabled</Badge>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-lg font-semibold mb-3">AI Settings</h3>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between p-4 border rounded-lg">
                        <div>
                          <h4 className="font-medium">Auto-optimization</h4>
                          <p className="text-sm text-gray-600">Let AI automatically optimize workflows based on execution patterns</p>
                        </div>
                        <Badge variant="outline">Enabled</Badge>
                      </div>
                      
                      <div className="flex items-center justify-between p-4 border rounded-lg">
                        <div>
                          <h4 className="font-medium">Plugin Discovery</h4>
                          <p className="text-sm text-gray-600">Automatically discover new plugins and suggest workflow improvements</p>
                        </div>
                        <Badge variant="outline">Enabled</Badge>
                      </div>
                      
                      <div className="flex items-center justify-between p-4 border rounded-lg">
                        <div>
                          <h4 className="font-medium">Learning Mode</h4>
                          <p className="text-sm text-gray-600">Learn from workflow executions to improve future recommendations</p>
                        </div>
                        <Badge variant="outline">Enabled</Badge>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-lg font-semibold mb-3">Notification Settings</h3>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between p-4 border rounded-lg">
                        <div>
                          <h4 className="font-medium">Workflow Failures</h4>
                          <p className="text-sm text-gray-600">Get notified when workflows fail</p>
                        </div>
                        <Badge variant="outline">Enabled</Badge>
                      </div>
                      
                      <div className="flex items-center justify-between p-4 border rounded-lg">
                        <div>
                          <h4 className="font-medium">Performance Alerts</h4>
                          <p className="text-sm text-gray-600">Get alerts when workflow performance degrades</p>
                        </div>
                        <Badge variant="outline">Enabled</Badge>
                      </div>
                      
                      <div className="flex items-center justify-between p-4 border rounded-lg">
                        <div>
                          <h4 className="font-medium">Weekly Reports</h4>
                          <p className="text-sm text-gray-600">Receive weekly automation performance reports</p>
                        </div>
                        <Badge variant="outline">Disabled</Badge>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>System Information</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-gray-600">Extension Version</p>
                      <p className="font-medium">1.0.0</p>
                    </div>
                    <div>
                      <p className="text-gray-600">API Version</p>
                      <p className="font-medium">1.0</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Last Plugin Discovery</p>
                      <p className="font-medium">2 hours ago</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Background Tasks</p>
                      <p className="font-medium">Running</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default AutomationPage;