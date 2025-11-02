import React, { useState, useEffect } from 'react';
import { 
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Checkbox } from '@/components/ui/checkbox';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
import { usePluginStore } from '@/store/plugin-store';
/**
 * Plugin Installation Wizard Component
 * 
 * Multi-step wizard for plugin installation with validation and configuration.
 * Based on requirements: 5.2, 5.5, 9.1
 */

"use client";



  ArrowLeft, 
  ArrowRight, 
  Package, 
  Search, 
  Upload, 
  Link, 
  GitBranch,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Download,
  Shield,
  Settings,
  Eye,
  EyeOff,
  Loader2,
  FileText,
  Globe,
  HardDrive,
  Cpu,
  Network,
  Database,
  Users,
  Lock,
  Unlock,
  Info,
  ExternalLink,
} from 'lucide-react';















  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';

  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';



  PluginInstallationRequest, 
  PluginMarketplaceEntry, 
  PluginDependency, 
  Permission,
  PluginManifest,
  PluginConfig,
  PluginConfigField,
} from '@/types/plugins';

// Installation steps
type InstallationStep = 'source' | 'selection' | 'validation' | 'dependencies' | 'permissions' | 'configuration' | 'review' | 'installation' | 'complete';

interface InstallationState {
  step: InstallationStep;
  source: 'marketplace' | 'file' | 'url' | 'git';
  selectedPlugin: PluginMarketplaceEntry | null;
  pluginFile: File | null;
  pluginUrl: string;
  gitRepo: string;
  gitBranch: string;
  manifest: PluginManifest | null;
  dependencies: PluginDependency[];
  resolvedDependencies: PluginDependency[];
  permissions: Permission[];
  grantedPermissions: string[];
  configuration: PluginConfig;
  validationErrors: string[];
  installationId: string | null;
  installationProgress: number;
  installationMessage: string;
  installationError: string | null;
}

interface PluginInstallationWizardProps {
  onClose: () => void;
  onComplete: () => void;
  preselectedPlugin?: PluginMarketplaceEntry;
}

const stepTitles: Record<InstallationStep, string> = {
  source: 'Choose Source',
  selection: 'Select Plugin',
  validation: 'Validate Plugin',
  dependencies: 'Resolve Dependencies',
  permissions: 'Configure Permissions',
  configuration: 'Plugin Configuration',
  review: 'Review Installation',
  installation: 'Installing Plugin',
  complete: 'Installation Complete',
};

const stepDescriptions: Record<InstallationStep, string> = {
  source: 'Choose how you want to install the plugin',
  selection: 'Select the plugin you want to install',
  validation: 'Validating plugin manifest and compatibility',
  dependencies: 'Checking and resolving plugin dependencies',
  permissions: 'Configure security permissions for the plugin',
  configuration: 'Set up plugin configuration options',
  review: 'Review installation details before proceeding',
  installation: 'Installing and configuring the plugin',
  complete: 'Plugin has been successfully installed',
};

// Mock data for development
const mockMarketplacePlugins: PluginMarketplaceEntry[] = [
  {
    id: 'slack-integration',
    name: 'Slack Integration',
    description: 'Connect with Slack workspaces and manage messages through AI chat',
    version: '1.0.0',
    author: { name: 'Kari AI Team', verified: true },
    category: 'integration',
    tags: ['slack', 'messaging', 'team', 'communication'],
    downloads: 1250,
    rating: 4.5,
    reviewCount: 23,
    featured: true,
    verified: true,
    compatibility: {
      minVersion: '1.0.0',
      platforms: ['node'],
    },
    screenshots: [],
    pricing: { type: 'free' },
    installUrl: 'https://marketplace.kari.ai/plugins/slack-integration',
    manifest: {
      id: 'slack-integration',
      name: 'Slack Integration',
      version: '1.0.0',
      description: 'Connect with Slack workspaces and manage messages through AI chat',
      author: { name: 'Kari AI Team', email: 'plugins@kari.ai' },
      license: 'MIT',
      homepage: 'https://docs.kari.ai/plugins/slack',
      repository: 'https://github.com/kari-ai/slack-plugin',
      keywords: ['slack', 'messaging', 'team'],
      category: 'integration',
      runtime: { platform: ['node'], nodeVersion: '>=16.0.0' },
      dependencies: [
        {
          id: 'slack-sdk',
          name: 'Slack SDK',
          version: '6.8.0',
          versionConstraint: '^6.8.0',
          optional: false,
          installed: false,
          compatible: true,
        },
      ],
      systemRequirements: {
        minMemory: 64,
        minDisk: 10,
        requiredServices: ['network'],
      },
      permissions: [
        {
          id: 'network-access',
          name: 'Network Access',
          description: 'Access to Slack APIs and webhooks',
          category: 'network',
          level: 'read',
          required: true,
        },
        {
          id: 'slack-workspace',
          name: 'Slack Workspace Access',
          description: 'Read and send messages in Slack workspaces',
          category: 'data',
          level: 'write',
          required: true,
        },
        {
          id: 'user-data',
          name: 'User Data Access',
          description: 'Access user profile information for message attribution',
          category: 'data',
          level: 'read',
          required: false,
        },
      ],
      sandboxed: true,
      securityPolicy: {
        allowNetworkAccess: true,
        allowFileSystemAccess: false,
        allowSystemCalls: false,
        trustedDomains: ['slack.com', 'api.slack.com'],
      },
      configSchema: [
        {
          key: 'botToken',
          type: 'password',
          label: 'Bot Token',
          description: 'Slack bot token (starts with xoxb-)',
          required: true,
          validation: {
            pattern: '^xoxb-[0-9]+-[0-9]+-[a-zA-Z0-9]+$',
          },
        },
        {
          key: 'signingSecret',
          type: 'password',
          label: 'Signing Secret',
          description: 'Slack app signing secret for webhook verification',
          required: true,
        },
        {
          key: 'defaultChannel',
          type: 'string',
          label: 'Default Channel',
          description: 'Default channel for notifications (optional)',
          required: false,
          default: '#general',
        },
        {
          key: 'enableNotifications',
          type: 'boolean',
          label: 'Enable Notifications',
          description: 'Send notifications for important events',
          required: false,
          default: true,
        },
        {
          key: 'messageFormat',
          type: 'select',
          label: 'Message Format',
          description: 'Format for AI-generated messages',
          required: false,
          default: 'markdown',
          options: [
            { label: 'Plain Text', value: 'plain' },
            { label: 'Markdown', value: 'markdown' },
            { label: 'Rich Text', value: 'rich' },
          ],
        },
      ],
      apiVersion: '1.0',
      endpoints: [
        { path: '/slack/events', method: 'POST', description: 'Slack event webhook' },
        { path: '/slack/commands', method: 'POST', description: 'Slack slash commands' },
      ],
      hooks: [
        { event: 'message.received', handler: 'handleSlackMessage', priority: 1 },
        { event: 'user.mentioned', handler: 'handleMention', priority: 2 },
      ],
      ui: {
        hasSettings: true,
        hasDashboard: true,
        hasWidget: false,
        customRoutes: [
          { path: '/slack/channels', component: 'ChannelManager', title: 'Manage Channels' },
          { path: '/slack/users', component: 'UserManager', title: 'Manage Users' },
        ],
      },
    },
  },
  {
    id: 'database-connector',
    name: 'Database Connector',
    description: 'Connect to various databases and execute queries through natural language',
    version: '2.1.0',
    author: { name: 'Community Developer', verified: false },
    category: 'integration',
    tags: ['database', 'sql', 'query', 'data'],
    downloads: 890,
    rating: 4.2,
    reviewCount: 15,
    featured: false,
    verified: false,
    compatibility: {
      minVersion: '1.0.0',
      platforms: ['node'],
    },
    screenshots: [],
    pricing: { type: 'free' },
    installUrl: 'https://marketplace.kari.ai/plugins/database-connector',
    manifest: {
      id: 'database-connector',
      name: 'Database Connector',
      version: '2.1.0',
      description: 'Connect to various databases and execute queries through natural language',
      author: { name: 'Community Developer' },
      license: 'Apache-2.0',
      keywords: ['database', 'sql', 'query'],
      category: 'integration',
      runtime: { platform: ['node'], nodeVersion: '>=14.0.0' },
      dependencies: [
        {
          id: 'mysql2',
          name: 'MySQL Driver',
          version: '3.6.0',
          versionConstraint: '^3.0.0',
          optional: true,
          installed: false,
          compatible: true,
        },
        {
          id: 'pg',
          name: 'PostgreSQL Driver',
          version: '8.11.0',
          versionConstraint: '^8.0.0',
          optional: true,
          installed: false,
          compatible: true,
        },
      ],
      systemRequirements: {
        minMemory: 128,
        minDisk: 50,
        requiredServices: ['network'],
      },
      permissions: [
        {
          id: 'database-access',
          name: 'Database Access',
          description: 'Connect to external databases',
          category: 'network',
          level: 'write',
          required: true,
        },
        {
          id: 'query-execution',
          name: 'Query Execution',
          description: 'Execute SQL queries on connected databases',
          category: 'data',
          level: 'admin',
          required: true,
        },
      ],
      sandboxed: false,
      securityPolicy: {
        allowNetworkAccess: true,
        allowFileSystemAccess: true,
        allowSystemCalls: false,
      },
      configSchema: [
        {
          key: 'connections',
          type: 'json',
          label: 'Database Connections',
          description: 'JSON configuration for database connections',
          required: true,
        },
        {
          key: 'queryTimeout',
          type: 'number',
          label: 'Query Timeout (seconds)',
          description: 'Maximum time to wait for query execution',
          required: false,
          default: 30,
          validation: { min: 1, max: 300 },
        },
      ],
      apiVersion: '1.0',
    },
  },
];

export const PluginInstallationWizard: React.FC<PluginInstallationWizardProps> = ({
  onClose,
  onComplete,
  preselectedPlugin,
}) => {
  const { installPlugin } = usePluginStore();
  
  const [state, setState] = useState<InstallationState>({
    step: preselectedPlugin ? 'validation' : 'source',
    source: 'marketplace',
    selectedPlugin: preselectedPlugin || null,
    pluginFile: null,
    pluginUrl: '',
    gitRepo: '',
    gitBranch: 'main',
    manifest: preselectedPlugin?.manifest || null,
    dependencies: [],
    resolvedDependencies: [],
    permissions: [],
    grantedPermissions: [],
    configuration: {},
    validationErrors: [],
    installationId: null,
    installationProgress: 0,
    installationMessage: '',
    installationError: null,
  });

  const [showPermissionDetails, setShowPermissionDetails] = useState<string | null>(null);
  const [showConfigPassword, setShowConfigPassword] = useState<Record<string, boolean>>({});

  // Auto-advance through validation and dependency resolution
  useEffect(() => {
    if (state.step === 'validation' && state.manifest) {
      // Simulate validation
      setTimeout(() => {
        setState(prev => ({
          ...prev,
          step: 'dependencies',
          dependencies: state.manifest?.dependencies || [],
          permissions: state.manifest?.permissions || [],
        }));
      }, 1500);
    }
  }, [state.step, state.manifest]);

  useEffect(() => {
    if (state.step === 'dependencies' && state.dependencies.length > 0) {
      // Simulate dependency resolution
      setTimeout(() => {
        const resolved = state.dependencies.map(dep => ({
          ...dep,
          installed: Math.random() > 0.3, // 70% chance already installed
        }));
        
        setState(prev => ({
          ...prev,
          resolvedDependencies: resolved,
          step: 'permissions',
        }));
      }, 2000);
    } else if (state.step === 'dependencies' && state.dependencies.length === 0) {
      // No dependencies, skip to permissions
      setState(prev => ({ ...prev, step: 'permissions' }));
    }
  }, [state.step, state.dependencies]);

  const handleNext = () => {
    const stepOrder: InstallationStep[] = ['source', 'selection', 'validation', 'dependencies', 'permissions', 'configuration', 'review', 'installation', 'complete'];
    const currentIndex = stepOrder.indexOf(state.step);
    
    if (currentIndex < stepOrder.length - 1) {
      const nextStep = stepOrder[currentIndex + 1];
      
      // Skip steps based on conditions
      if (nextStep === 'selection' && state.source !== 'marketplace') {
        setState(prev => ({ ...prev, step: 'validation' }));
      } else if (nextStep === 'configuration' && (!state.manifest?.configSchema || state.manifest.configSchema.length === 0)) {
        setState(prev => ({ ...prev, step: 'review' }));
      } else {
        setState(prev => ({ ...prev, step: nextStep }));
      }
    }
  };

  const handleBack = () => {
    const stepOrder: InstallationStep[] = ['source', 'selection', 'validation', 'dependencies', 'permissions', 'configuration', 'review', 'installation', 'complete'];
    const currentIndex = stepOrder.indexOf(state.step);
    
    if (currentIndex > 0) {
      const prevStep = stepOrder[currentIndex - 1];
      
      // Skip steps based on conditions
      if (prevStep === 'selection' && state.source !== 'marketplace') {
        setState(prev => ({ ...prev, step: 'source' }));
      } else if (prevStep === 'configuration' && (!state.manifest?.configSchema || state.manifest.configSchema.length === 0)) {
        setState(prev => ({ ...prev, step: 'permissions' }));
      } else {
        setState(prev => ({ ...prev, step: prevStep }));
      }
    }
  };

  const handleInstall = async () => {
    setState(prev => ({ ...prev, step: 'installation', installationProgress: 0 }));
    
    try {
      const request: PluginInstallationRequest = {
        source: state.source,
        identifier: state.source === 'marketplace' ? state.selectedPlugin!.id : 
                   state.source === 'file' ? state.pluginFile!.name :
                   state.source === 'url' ? state.pluginUrl :
                   `${state.gitRepo}#${state.gitBranch}`,
        version: state.manifest?.version,
        config: state.configuration,
        permissions: state.grantedPermissions,
        autoStart: true,
      };

      // Simulate installation progress
      const progressSteps = [
        { progress: 10, message: 'Downloading plugin...' },
        { progress: 25, message: 'Validating plugin manifest...' },
        { progress: 40, message: 'Resolving dependencies...' },
        { progress: 60, message: 'Installing dependencies...' },
        { progress: 75, message: 'Configuring plugin...' },
        { progress: 90, message: 'Starting plugin...' },
        { progress: 100, message: 'Installation complete!' },
      ];

      for (const step of progressSteps) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        setState(prev => ({
          ...prev,
          installationProgress: step.progress,
          installationMessage: step.message,
        }));
      }

      // Complete installation
      await installPlugin(request);
      setState(prev => ({ ...prev, step: 'complete' }));
      
    } catch (error) {
      setState(prev => ({
        ...prev,
        installationError: error instanceof Error ? error.message : 'Installation failed',
      }));
    }
  };

  const renderSourceSelection = () => (
    <Card>
      <CardHeader>
        <CardTitle>Choose Installation Source</CardTitle>
        <CardDescription>
          Select how you want to install the plugin
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <RadioGroup
          value={state.source}
          onValueChange={(value) => setState(prev => ({ 
            ...prev, 
            source: value as any,
            selectedPlugin: null,
            manifest: null,
          }))}
        >
          <div className="flex items-center space-x-2 p-4 border rounded-lg hover:bg-muted/50 sm:p-4 md:p-6">
            <RadioGroupItem value="marketplace" id="marketplace" />
            <div className="flex-1">
              <Label htmlFor="marketplace" className="flex items-center gap-2 font-medium">
                <Search className="w-4 h-4 sm:w-auto md:w-full" />
                Plugin Marketplace
              </Label>
              <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                Browse and install verified plugins from the official marketplace
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2 p-4 border rounded-lg hover:bg-muted/50 sm:p-4 md:p-6">
            <RadioGroupItem value="file" id="file" />
            <div className="flex-1">
              <Label htmlFor="file" className="flex items-center gap-2 font-medium">
                <Upload className="w-4 h-4 sm:w-auto md:w-full" />
                Upload Plugin File
              </Label>
              <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                Install a plugin from a local .kari-plugin file
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2 p-4 border rounded-lg hover:bg-muted/50 sm:p-4 md:p-6">
            <RadioGroupItem value="url" id="url" />
            <div className="flex-1">
              <Label htmlFor="url" className="flex items-center gap-2 font-medium">
                <Link className="w-4 h-4 sm:w-auto md:w-full" />
                Download from URL
              </Label>
              <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                Install a plugin from a direct download URL
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2 p-4 border rounded-lg hover:bg-muted/50 sm:p-4 md:p-6">
            <RadioGroupItem value="git" id="git" />
            <div className="flex-1">
              <Label htmlFor="git" className="flex items-center gap-2 font-medium">
                <GitBranch className="w-4 h-4 sm:w-auto md:w-full" />
                Git Repository
              </Label>
              <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                Install a plugin directly from a Git repository
              </p>
            </div>
          </div>
        </RadioGroup>
        
        {/* Source-specific inputs */}
        {state.source === 'file' && (
          <div className="space-y-2">
            <Label htmlFor="plugin-file">Plugin File</Label>
            <input
              id="plugin-file"
              type="file"
              accept=".kari-plugin,.zip"
              onChange={(e) = aria-label="Input"> {
                const file = e.target.files?.[0];
                if (file) {
                  setState(prev => ({ ...prev, pluginFile: file }));
                  // Mock manifest extraction
                  setTimeout(() => {
                    setState(prev => ({ 
                      ...prev, 
                      manifest: mockMarketplacePlugins[0].manifest,
                    }));
                  }, 500);
                }
              }}
            />
          </div>
        )}
        
        {state.source === 'url' && (
          <div className="space-y-2">
            <Label htmlFor="plugin-url">Plugin URL</Label>
            <input
              id="plugin-url"
              type="url"
              placeholder="https://example.com/plugin.kari-plugin"
              value={state.pluginUrl}
              onChange={(e) = aria-label="Input"> setState(prev => ({ ...prev, pluginUrl: e.target.value }))}
            />
          </div>
        )}
        
        {state.source === 'git' && (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="git-repo">Git Repository</Label>
              <input
                id="git-repo"
                placeholder="https://github.com/user/plugin-repo"
                value={state.gitRepo}
                onChange={(e) = aria-label="Input"> setState(prev => ({ ...prev, gitRepo: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="git-branch">Branch</Label>
              <input
                id="git-branch"
                placeholder="main"
                value={state.gitBranch}
                onChange={(e) = aria-label="Input"> setState(prev => ({ ...prev, gitBranch: e.target.value }))}
              />
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );

  const renderPluginSelection = () => (
    <Card>
      <CardHeader>
        <CardTitle>Select Plugin</CardTitle>
        <CardDescription>
          Choose a plugin from the marketplace
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {mockMarketplacePlugins.map((plugin) => (
            <div
              key={plugin.id}
              className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                state.selectedPlugin?.id === plugin.id 
                  ? 'border-primary bg-primary/5' 
                  : 'hover:bg-muted/50'
              }`}
              onClick={() => setState(prev => ({ 
                ...prev, 
                selectedPlugin: plugin,
                manifest: plugin.manifest,
              }))}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="font-medium">{plugin.name}</h3>
                    <Badge variant="secondary">v{plugin.version}</Badge>
                    {plugin.verified && (
                      <Badge variant="default" className="text-xs sm:text-sm md:text-base">
                        <CheckCircle className="w-3 h-3 mr-1 sm:w-auto md:w-full" />
                        Verified
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground mb-2 md:text-base lg:text-lg">
                    {plugin.description}
                  </p>
                  <div className="flex items-center gap-4 text-xs text-muted-foreground sm:text-sm md:text-base">
                    <span>by {plugin.author.name}</span>
                    <span>{plugin.downloads.toLocaleString()} downloads</span>
                    <span>★ {plugin.rating} ({plugin.reviewCount} reviews)</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );

  const renderValidation = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Loader2 className="w-5 h-5 animate-spin sm:w-auto md:w-full" />
          Validating Plugin
        </CardTitle>
        <CardDescription>
          Checking plugin manifest and compatibility
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm md:text-base lg:text-lg">
            <CheckCircle className="w-4 h-4 text-green-600 sm:w-auto md:w-full" />
            Plugin manifest is valid
          </div>
          <div className="flex items-center gap-2 text-sm md:text-base lg:text-lg">
            <CheckCircle className="w-4 h-4 text-green-600 sm:w-auto md:w-full" />
            Compatible with current system version
          </div>
          <div className="flex items-center gap-2 text-sm md:text-base lg:text-lg">
            <CheckCircle className="w-4 h-4 text-green-600 sm:w-auto md:w-full" />
            Security policy validated
          </div>
          <div className="flex items-center gap-2 text-sm md:text-base lg:text-lg">
            <Loader2 className="w-4 h-4 animate-spin text-blue-600 sm:w-auto md:w-full" />
            Checking system requirements...
          </div>
        </div>
        
        {state.manifest && (
          <div className="mt-6 p-4 bg-muted/50 rounded-lg sm:p-4 md:p-6">
            <h4 className="font-medium mb-2">Plugin Information</h4>
            <div className="grid grid-cols-2 gap-4 text-sm md:text-base lg:text-lg">
              <div>
                <span className="text-muted-foreground">Name:</span>
                <span className="ml-2">{state.manifest.name}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Version:</span>
                <span className="ml-2">{state.manifest.version}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Author:</span>
                <span className="ml-2">{state.manifest.author.name}</span>
              </div>
              <div>
                <span className="text-muted-foreground">License:</span>
                <span className="ml-2">{state.manifest.license}</span>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );

  const renderDependencies = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {state.resolvedDependencies.length > 0 ? (
            <Package className="w-5 h-5 sm:w-auto md:w-full" />
          ) : (
            <Loader2 className="w-5 h-5 animate-spin sm:w-auto md:w-full" />
          )}
          Resolve Dependencies
        </CardTitle>
        <CardDescription>
          {state.resolvedDependencies.length > 0 
            ? 'Review and install required dependencies'
            : 'Checking plugin dependencies...'
          }
        </CardDescription>
      </CardHeader>
      <CardContent>
        {state.resolvedDependencies.length === 0 ? (
          <div className="text-center py-8">
            <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-muted-foreground sm:w-auto md:w-full" />
            <p className="text-muted-foreground">Resolving dependencies...</p>
          </div>
        ) : (
          <div className="space-y-4">
            {state.resolvedDependencies.map((dep) => (
              <div key={dep.id} className="flex items-center justify-between p-3 border rounded-lg sm:p-4 md:p-6">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className="font-medium">{dep.name}</h4>
                    <Badge variant="outline">v{dep.version}</Badge>
                    {dep.optional && (
                      <Badge variant="secondary" className="text-xs sm:text-sm md:text-base">Optional</Badge>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                    Required version: {dep.versionConstraint}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {dep.installed ? (
                    <Badge variant="default" className="text-xs sm:text-sm md:text-base">
                      <CheckCircle className="w-3 h-3 mr-1 sm:w-auto md:w-full" />
                      Installed
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                      <Download className="w-3 h-3 mr-1 sm:w-auto md:w-full" />
                      Will Install
                    </Badge>
                  )}
                </div>
              </div>
            ))}
            
            {state.resolvedDependencies.some(dep => !dep.installed) && (
              <Alert>
                <Info className="w-4 h-4 sm:w-auto md:w-full" />
                <AlertDescription>
                  Missing dependencies will be automatically installed during the plugin installation process.
                </AlertDescription>
              </Alert>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );

  const renderPermissions = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shield className="w-5 h-5 sm:w-auto md:w-full" />
          Configure Permissions
        </CardTitle>
        <CardDescription>
          Review and grant permissions for this plugin
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {state.permissions.map((permission) => (
            <div key={permission.id} className="flex items-start space-x-3 p-3 border rounded-lg sm:p-4 md:p-6">
              <Checkbox
                id={permission.id}
                checked={state.grantedPermissions.includes(permission.id) || permission.required}
                disabled={permission.required}
                onCheckedChange={(checked) => {
                  if (checked) {
                    setState(prev => ({
                      ...prev,
                      grantedPermissions: [...prev.grantedPermissions, permission.id],
                    }));
                  } else {
                    setState(prev => ({
                      ...prev,
                      grantedPermissions: prev.grantedPermissions.filter(id => id !== permission.id),
                    }));
                  }
                }}
              />
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <Label htmlFor={permission.id} className="font-medium">
                    {permission.name}
                  </Label>
                  <Badge 
                    variant={permission.level === 'admin' ? 'destructive' : 
                           permission.level === 'write' ? 'default' : 'secondary'}
                    className="text-xs sm:text-sm md:text-base"
                  >
                    {permission.level}
                  </Badge>
                  {permission.required && (
                    <Badge variant="outline" className="text-xs sm:text-sm md:text-base">Required</Badge>
                  )}
                  <button
                    variant="ghost"
                    size="sm"
                    onClick={() = aria-label="Button"> setShowPermissionDetails(permission.id)}
                  >
                    <Info className="w-3 h-3 sm:w-auto md:w-full" />
                  </Button>
                </div>
                <p className="text-sm text-muted-foreground mt-1 md:text-base lg:text-lg">
                  {permission.description}
                </p>
              </div>
            </div>
          ))}
          
          {state.permissions.length === 0 && (
            <div className="text-center py-8">
              <Shield className="w-8 h-8 mx-auto mb-4 text-muted-foreground sm:w-auto md:w-full" />
              <p className="text-muted-foreground">This plugin doesn't require any special permissions.</p>
            </div>
          )}
          
          <Alert>
            <AlertTriangle className="w-4 h-4 sm:w-auto md:w-full" />
            <AlertDescription>
              Only grant permissions that you trust this plugin to use. Required permissions cannot be disabled.
            </AlertDescription>
          </Alert>
        </div>
      </CardContent>
    </Card>
  );

  const renderConfiguration = () => {
    if (!state.manifest?.configSchema || state.manifest.configSchema.length === 0) {
      return null;
    }

    const renderConfigField = (field: PluginConfigField) => {
      const value = state.configuration[field.key] ?? field.default ?? '';
      
      const updateConfig = (newValue: any) => {
        setState(prev => ({
          ...prev,
          configuration: {
            ...prev.configuration,
            [field.key]: newValue,
          },
        }));
      };

      switch (field.type) {
        case 'string':
          return (
            <input
              value={value}
              onChange={(e) = aria-label="Input"> updateConfig(e.target.value)}
              placeholder={field.default}
            />
          );
          
        case 'password':
          return (
            <div className="relative">
              <input
                type={showConfigPassword[field.key] ? 'text' : 'password'}
                value={value}
                onChange={(e) = aria-label="Input"> updateConfig(e.target.value)}
                placeholder="Enter password"
              />
              <button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute right-0 top-0 h-full px-3"
                onClick={() = aria-label="Button"> setShowConfigPassword(prev => ({
                  ...prev,
                  [field.key]: !prev[field.key],
                }))}
              >
                {showConfigPassword[field.key] ? (
                  <EyeOff className="w-4 h-4 sm:w-auto md:w-full" />
                ) : (
                  <Eye className="w-4 h-4 sm:w-auto md:w-full" />
                )}
              </Button>
            </div>
          );
          
        case 'number':
          return (
            <input
              type="number"
              value={value}
              onChange={(e) = aria-label="Input"> updateConfig(Number(e.target.value))}
              min={field.validation?.min}
              max={field.validation?.max}
            />
          );
          
        case 'boolean':
          return (
            <Checkbox
              checked={value}
              onCheckedChange={updateConfig}
            />
          );
          
        case 'select':
          return (
            <select value={value} onValueChange={updateConfig} aria-label="Select option">
              <selectTrigger aria-label="Select option">
                <selectValue placeholder="Select an option" />
              </SelectTrigger>
              <selectContent aria-label="Select option">
                {field.options?.map((option) => (
                  <selectItem key={option.value} value={option.value} aria-label="Select option">
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          );
          
        case 'json':
          return (
            <textarea
              value={typeof value === 'string' ? value : JSON.stringify(value, null, 2)}
              onChange={(e) = aria-label="Textarea"> {
                try {
                  const parsed = JSON.parse(e.target.value);
                  updateConfig(parsed);
                } catch {
                  updateConfig(e.target.value);
                }
              }}
              rows={6}
              placeholder="Enter JSON configuration"
            />
          );
          
        default:
          return (
            <input
              value={value}
              onChange={(e) = aria-label="Input"> updateConfig(e.target.value)}
            />
          );
      }
    };

    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5 sm:w-auto md:w-full" />
            Plugin Configuration
          </CardTitle>
          <CardDescription>
            Configure the plugin settings
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {state.manifest.configSchema.map((field) => (
              <div key={field.key} className="space-y-2">
                <div className="flex items-center gap-2">
                  <Label htmlFor={field.key}>
                    {field.label}
                    {field.required && <span className="text-destructive">*</span>}
                  </Label>
                </div>
                {field.description && (
                  <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                    {field.description}
                  </p>
                )}
                {renderConfigField(field)}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderReview = () => (
    <Card>
      <CardHeader>
        <CardTitle>Review Installation</CardTitle>
        <CardDescription>
          Review all settings before installing the plugin
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Plugin Information */}
          <div>
            <h4 className="font-medium mb-3">Plugin Information</h4>
            <div className="grid grid-cols-2 gap-4 text-sm md:text-base lg:text-lg">
              <div>
                <span className="text-muted-foreground">Name:</span>
                <span className="ml-2">{state.manifest?.name}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Version:</span>
                <span className="ml-2">{state.manifest?.version}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Author:</span>
                <span className="ml-2">{state.manifest?.author.name}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Source:</span>
                <span className="ml-2 capitalize">{state.source}</span>
              </div>
            </div>
          </div>
          
          <Separator />
          
          {/* Dependencies */}
          {state.resolvedDependencies.length > 0 && (
            <>
              <div>
                <h4 className="font-medium mb-3">Dependencies</h4>
                <div className="space-y-2">
                  {state.resolvedDependencies.map((dep) => (
                    <div key={dep.id} className="flex items-center justify-between text-sm md:text-base lg:text-lg">
                      <span>{dep.name} v{dep.version}</span>
                      <Badge variant={dep.installed ? 'default' : 'outline'} className="text-xs sm:text-sm md:text-base">
                        {dep.installed ? 'Installed' : 'Will Install'}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
              <Separator />
            </>
          )}
          
          {/* Permissions */}
          {state.grantedPermissions.length > 0 && (
            <>
              <div>
                <h4 className="font-medium mb-3">Granted Permissions</h4>
                <div className="space-y-2">
                  {state.permissions
                    .filter(p => state.grantedPermissions.includes(p.id))
                    .map((permission) => (
                      <div key={permission.id} className="flex items-center justify-between text-sm md:text-base lg:text-lg">
                        <span>{permission.name}</span>
                        <Badge 
                          variant={permission.level === 'admin' ? 'destructive' : 
                                 permission.level === 'write' ? 'default' : 'secondary'}
                          className="text-xs sm:text-sm md:text-base"
                        >
                          {permission.level}
                        </Badge>
                      </div>
                    ))}
                </div>
              </div>
              <Separator />
            </>
          )}
          
          {/* Configuration */}
          {Object.keys(state.configuration).length > 0 && (
            <div>
              <h4 className="font-medium mb-3">Configuration</h4>
              <div className="space-y-2 text-sm md:text-base lg:text-lg">
                {Object.entries(state.configuration).map(([key, value]) => {
                  const field = state.manifest?.configSchema.find(f => f.key === key);
                  const displayValue = field?.type === 'password' ? '***hidden***' : 
                                     typeof value === 'object' ? JSON.stringify(value) : 
                                     String(value);
                  
                  return (
                    <div key={key} className="flex items-center justify-between">
                      <span>{field?.label || key}:</span>
                      <span className="text-muted-foreground">{displayValue}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );

  const renderInstallation = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Loader2 className="w-5 h-5 animate-spin sm:w-auto md:w-full" />
          Installing Plugin
        </CardTitle>
        <CardDescription>
          Please wait while the plugin is being installed
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm md:text-base lg:text-lg">
            <span>Progress</span>
            <span>{state.installationProgress}%</span>
          </div>
          <Progress value={state.installationProgress} />
        </div>
        
        <div className="text-center">
          <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
            {state.installationMessage}
          </p>
        </div>
        
        {state.installationError && (
          <Alert variant="destructive">
            <XCircle className="w-4 h-4 sm:w-auto md:w-full" />
            <AlertDescription>{state.installationError}</AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );

  const renderComplete = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CheckCircle className="w-5 h-5 text-green-600 sm:w-auto md:w-full" />
          Installation Complete
        </CardTitle>
        <CardDescription>
          The plugin has been successfully installed and is ready to use
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="text-center py-8">
          <CheckCircle className="w-16 h-16 mx-auto mb-4 text-green-600 sm:w-auto md:w-full" />
          <h3 className="text-lg font-medium mb-2">
            {state.manifest?.name} is now installed!
          </h3>
          <p className="text-muted-foreground mb-6">
            The plugin is active and ready to use. You can configure it further in the plugin settings.
          </p>
          
          <div className="flex justify-center gap-2">
            <button variant="outline" onClick={onClose} aria-label="Button">
              Close
            </Button>
            <button onClick={onComplete} aria-label="Button">
              View Plugin
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const canProceed = () => {
    switch (state.step) {
      case 'source':
        return state.source === 'marketplace' || 
               (state.source === 'file' && state.pluginFile) ||
               (state.source === 'url' && state.pluginUrl) ||
               (state.source === 'git' && state.gitRepo);
      case 'selection':
        return !!state.selectedPlugin;
      case 'permissions':
        return state.permissions.filter(p => p.required).every(p => 
          state.grantedPermissions.includes(p.id)
        );
      case 'configuration':
        return state.manifest?.configSchema?.filter(f => f.required).every(f => 
          state.configuration[f.key] !== undefined && state.configuration[f.key] !== ''
        ) ?? true;
      default:
        return true;
    }
  };

  const renderStepContent = () => {
    switch (state.step) {
      case 'source':
        return renderSourceSelection();
      case 'selection':
        return renderPluginSelection();
      case 'validation':
        return renderValidation();
      case 'dependencies':
        return renderDependencies();
      case 'permissions':
        return renderPermissions();
      case 'configuration':
        return renderConfiguration();
      case 'review':
        return renderReview();
      case 'installation':
        return renderInstallation();
      case 'complete':
        return renderComplete();
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button variant="ghost" size="sm" onClick={onClose} aria-label="Button">
          <ArrowLeft className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
          Back to Plugins
        </Button>
        <div>
          <h1 className="text-2xl font-bold">{stepTitles[state.step]}</h1>
          <p className="text-muted-foreground">{stepDescriptions[state.step]}</p>
        </div>
      </div>

      {/* Progress Steps */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            {(['source', 'selection', 'validation', 'dependencies', 'permissions', 'configuration', 'review', 'installation', 'complete'] as InstallationStep[]).map((step, index) => {
              const stepOrder = ['source', 'selection', 'validation', 'dependencies', 'permissions', 'configuration', 'review', 'installation', 'complete'];
              const currentIndex = stepOrder.indexOf(state.step);
              const stepIndex = stepOrder.indexOf(step);
              
              // Skip selection step if not marketplace
              if (step === 'selection' && state.source !== 'marketplace') {
                return null;
              }
              
              // Skip configuration step if no config schema
              if (step === 'configuration' && (!state.manifest?.configSchema || state.manifest.configSchema.length === 0)) {
                return null;
              }
              
              const isActive = step === state.step;
              const isCompleted = stepIndex < currentIndex;
              const isUpcoming = stepIndex > currentIndex;
              
              return (
                <div key={step} className="flex items-center">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                    isActive ? 'bg-primary text-primary-foreground' :
                    isCompleted ? 'bg-green-600 text-white' :
                    'bg-muted text-muted-foreground'
                  }`}>
                    {isCompleted ? (
                      <CheckCircle className="w-4 h-4 sm:w-auto md:w-full" />
                    ) : (
                      stepIndex + 1
                    )}
                  </div>
                  {index < 8 && (
                    <div className={`w-12 h-0.5 ${
                      isCompleted ? 'bg-green-600' : 'bg-muted'
                    }`} />
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Step Content */}
      {renderStepContent()}

      {/* Navigation */}
      {!['installation', 'complete'].includes(state.step) && (
        <div className="flex justify-between">
          <button
            variant="outline"
            onClick={handleBack}
            disabled={state.step === 'source' || (state.step === 'validation' && !!preselectedPlugin)}
           aria-label="Button">
            <ArrowLeft className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
            Back
          </Button>
          
          <button
            onClick={state.step === 'review' ? handleInstall : handleNext}
            disabled={!canProceed()}
           aria-label="Button">
            {state.step === 'review' ? 'Install Plugin' : 'Next'}
            <ArrowRight className="w-4 h-4 ml-2 sm:w-auto md:w-full" />
          </Button>
        </div>
      )}

      {/* Permission Details Dialog */}
      <Dialog open={!!showPermissionDetails} onOpenChange={() => setShowPermissionDetails(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Permission Details</DialogTitle>
            <DialogDescription>
              Detailed information about this permission
            </DialogDescription>
          </DialogHeader>
          {showPermissionDetails && (
            <div className="space-y-4">
              {(() => {
                const permission = state.permissions.find(p => p.id === showPermissionDetails);
                if (!permission) return null;
                
                return (
                  <>
                    <div>
                      <h4 className="font-medium">{permission.name}</h4>
                      <p className="text-sm text-muted-foreground mt-1 md:text-base lg:text-lg">
                        {permission.description}
                      </p>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4 text-sm md:text-base lg:text-lg">
                      <div>
                        <span className="text-muted-foreground">Category:</span>
                        <span className="ml-2 capitalize">{permission.category}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Level:</span>
                        <Badge 
                          variant={permission.level === 'admin' ? 'destructive' : 
                                 permission.level === 'write' ? 'default' : 'secondary'}
                          className="ml-2 text-xs sm:text-sm md:text-base"
                        >
                          {permission.level}
                        </Badge>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Required:</span>
                        <span className="ml-2">{permission.required ? 'Yes' : 'No'}</span>
                      </div>
                    </div>
                    
                    <Alert>
                      <Info className="w-4 h-4 sm:w-auto md:w-full" />
                      <AlertDescription>
                        {permission.level === 'admin' && 
                          'This permission grants administrative access and should only be granted to trusted plugins.'
                        }
                        {permission.level === 'write' && 
                          'This permission allows the plugin to modify data or system settings.'
                        }
                        {permission.level === 'read' && 
                          'This permission allows the plugin to read data but not modify it.'
                        }
                      </AlertDescription>
                    </Alert>
                  </>
                );
              })()}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};