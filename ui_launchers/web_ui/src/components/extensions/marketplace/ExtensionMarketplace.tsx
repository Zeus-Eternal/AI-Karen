/**
 * Extension Marketplace Browser Component
 * 
 * Provides a comprehensive marketplace interface for discovering, browsing,
 * and installing extensions from the Kari extension ecosystem.
 */
"use client";

import React, { useState, useMemo, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../ui/tabs';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';

import { 
  Search, 
  Filter, 
  Shield, 
  User, 
  Star, 
  Download, 
  Tag, 
  CheckCircle, 
  Plus, 
  Loader2, 
  Info, 
  ExternalLink 
} from 'lucide-react';
interface MarketplaceExtension {
  id: string;
  name: string;
  display_name: string;
  description: string;
  version: string;
  author: string;
  category: string;
  tags: string[];
  rating: number;
  downloads: number;
  verified: boolean;
  price: number | 'free';
  license: string;
  screenshots: string[];
  documentation_url?: string;
  support_url?: string;
  created_at: string;
  updated_at: string;
  compatibility: {
    kari_min_version: string;
    api_version: string;
  };
  capabilities: {
    provides_ui: boolean;
    provides_api: boolean;
    provides_background_tasks: boolean;
    provides_webhooks: boolean;
  };
  installed?: boolean;
  installing?: boolean;
}
interface ExtensionMarketplaceProps {
  className?: string;
  onInstall?: (extensionId: string) => Promise<void>;
  onUninstall?: (extensionId: string) => Promise<void>;
}
export function ExtensionMarketplace({ 
  className, 
  onInstall, 
  onUninstall 
}: ExtensionMarketplaceProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'popular' | 'recent' | 'rating' | 'name'>('popular');
  const [showFilters, setShowFilters] = useState(false);
  const [installingExtensions, setInstallingExtensions] = useState<Set<string>>(new Set());
  //  - in real implementation, this would come from API
  const marketplaceExtensions: MarketplaceExtension[] = [
    {
      id: 'advanced-analytics',
      name: 'advanced-analytics',
      display_name: 'Advanced Analytics Dashboard',
      description: 'Comprehensive analytics and reporting dashboard with real-time metrics, custom charts, and data visualization tools.',
      version: '2.1.0',
      author: 'Analytics Corp',
      category: 'analytics',
      tags: ['dashboard', 'reporting', 'charts', 'metrics'],
      rating: 4.8,
      downloads: 15420,
      verified: true,
      price: 'free',
      license: 'MIT',
      screenshots: [],
      documentation_url: 'https://docs.example.com/analytics',
      support_url: 'https://support.example.com/analytics',
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-10-20T14:30:00Z',
      compatibility: {
        kari_min_version: '0.4.0',
        api_version: '1.0'
      },
      capabilities: {
        provides_ui: true,
        provides_api: true,
        provides_background_tasks: true,
        provides_webhooks: false
      },
      installed: true
    },
    {
      id: 'ai-workflow-builder',
      name: 'ai-workflow-builder',
      display_name: 'AI Workflow Builder',
      description: 'Intelligent workflow automation with AI-powered task orchestration and natural language workflow creation.',
      version: '1.5.2',
      author: 'Automation Labs',
      category: 'automation',
      tags: ['workflow', 'ai', 'automation', 'orchestration'],
      rating: 4.9,
      downloads: 8750,
      verified: true,
      price: 29.99,
      license: 'Commercial',
      screenshots: [],
      documentation_url: 'https://docs.example.com/workflow',
      created_at: '2024-03-10T08:00:00Z',
      updated_at: '2024-10-18T16:45:00Z',
      compatibility: {
        kari_min_version: '0.4.0',
        api_version: '1.0'
      },
      capabilities: {
        provides_ui: true,
        provides_api: true,
        provides_background_tasks: true,
        provides_webhooks: true
      }
    },
    {
      id: 'security-monitor-pro',
      name: 'security-monitor-pro',
      display_name: 'Security Monitor Pro',
      description: 'Enterprise-grade security monitoring with threat detection, vulnerability scanning, and compliance reporting.',
      version: '3.2.1',
      author: 'SecureOps Inc',
      category: 'security',
      tags: ['security', 'monitoring', 'threats', 'compliance'],
      rating: 4.7,
      downloads: 12300,
      verified: true,
      price: 99.99,
      license: 'Enterprise',
      screenshots: [],
      documentation_url: 'https://docs.example.com/security',
      support_url: 'https://support.example.com/security',
      created_at: '2024-02-01T12:00:00Z',
      updated_at: '2024-10-15T09:20:00Z',
      compatibility: {
        kari_min_version: '0.4.0',
        api_version: '1.0'
      },
      capabilities: {
        provides_ui: true,
        provides_api: true,
        provides_background_tasks: true,
        provides_webhooks: true
      }
    },
    {
      id: 'communication-hub',
      name: 'communication-hub',
      display_name: 'Communication Hub',
      description: 'Unified communication platform with multi-channel support, team collaboration, and message routing.',
      version: '1.8.0',
      author: 'CommTech Solutions',
      category: 'communication',
      tags: ['communication', 'chat', 'collaboration', 'messaging'],
      rating: 4.6,
      downloads: 6890,
      verified: false,
      price: 'free',
      license: 'Apache 2.0',
      screenshots: [],
      created_at: '2024-04-20T15:30:00Z',
      updated_at: '2024-10-10T11:15:00Z',
      compatibility: {
        kari_min_version: '0.3.5',
        api_version: '1.0'
      },
      capabilities: {
        provides_ui: true,
        provides_api: true,
        provides_background_tasks: false,
        provides_webhooks: true
      }
    },
    {
      id: 'experimental-ai-features',
      name: 'experimental-ai-features',
      display_name: 'Experimental AI Features',
      description: 'Cutting-edge AI capabilities including advanced reasoning, multimodal processing, and experimental models.',
      version: '0.9.0-beta',
      author: 'AI Research Lab',
      category: 'experimental',
      tags: ['ai', 'experimental', 'research', 'beta'],
      rating: 4.2,
      downloads: 2150,
      verified: false,
      price: 'free',
      license: 'Research',
      screenshots: [],
      documentation_url: 'https://research.example.com/ai',
      created_at: '2024-08-01T10:00:00Z',
      updated_at: '2024-10-25T13:45:00Z',
      compatibility: {
        kari_min_version: '0.4.0',
        api_version: '1.0'
      },
      capabilities: {
        provides_ui: true,
        provides_api: false,
        provides_background_tasks: true,
        provides_webhooks: false
      }
    }
  ];
  const categories = [
    { id: 'all', name: 'All Categories', count: marketplaceExtensions.length },
    { id: 'analytics', name: 'Analytics', count: marketplaceExtensions.filter(e => e.category === 'analytics').length },
    { id: 'automation', name: 'Automation', count: marketplaceExtensions.filter(e => e.category === 'automation').length },
    { id: 'communication', name: 'Communication', count: marketplaceExtensions.filter(e => e.category === 'communication').length },
    { id: 'security', name: 'Security', count: marketplaceExtensions.filter(e => e.category === 'security').length },
    { id: 'experimental', name: 'Experimental', count: marketplaceExtensions.filter(e => e.category === 'experimental').length }
  ];
  const filteredAndSortedExtensions = useMemo(() => {
    let filtered = marketplaceExtensions;
    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(ext => 
        ext.display_name.toLowerCase().includes(query) ||
        ext.description.toLowerCase().includes(query) ||
        ext.tags.some(tag => tag.toLowerCase().includes(query)) ||
        ext.author.toLowerCase().includes(query)
      );
    }
    // Apply category filter
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(ext => ext.category === selectedCategory);
    }
    // Apply sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'popular':
          return b.downloads - a.downloads;
        case 'recent':
          return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
        case 'rating':
          return b.rating - a.rating;
        case 'name':
          return a.display_name.localeCompare(b.display_name);
        default:
          return 0;
      }
    });

    return filtered;
  }, [marketplaceExtensions, searchQuery, selectedCategory, sortBy]);
  const handleInstall = useCallback(async (extension: MarketplaceExtension) => {
    if (installingExtensions.has(extension.id)) return;
    setInstallingExtensions(prev => new Set(prev).add(extension.id));
    try {
      if (onInstall) {
        await onInstall(extension.id);
      }
      // Simulate installation delay
      await new Promise(resolve => setTimeout(resolve, 2000));
    } catch (error) {
    } finally {
      setInstallingExtensions(prev => {
        const newSet = new Set(prev);
        newSet.delete(extension.id);
        return newSet;
      });
    }
  }, [onInstall, installingExtensions]);
  const handleUninstall = useCallback(async (extension: MarketplaceExtension) => {
    if (onUninstall) {
      await onUninstall(extension.id);
    }
  }, [onUninstall]);
  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Extension Marketplace</h1>
          <p className="text-gray-600 mt-1">Discover and install extensions to enhance your Kari experience</p>
        </div>
        <Button
          variant="outline"
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center gap-2"
        >
          <Filter className="h-4 w-4" />
          Filters
        </Button>
      </div>
      {/* Search and Filters */}
      <div className="space-y-4">
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <input
              type="text"
              placeholder="Search extensions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="popular">Most Popular</option>
            <option value="recent">Recently Updated</option>
            <option value="rating">Highest Rated</option>
            <option value="name">Name (A-Z)</option>
          </select>
        </div>
        {showFilters && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Filters</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium mb-2">Categories</h4>
                  <div className="flex flex-wrap gap-2">
                    {categories.map(category => (
                      <button
                        key={category.id}
                        onClick={() => setSelectedCategory(category.id)}
                        className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                          selectedCategory === category.id
                            ? 'bg-blue-100 text-blue-800 border border-blue-200'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        {category.name} ({category.count})
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
      {/* Results */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <p className="text-gray-600">
            {filteredAndSortedExtensions.length} extension{filteredAndSortedExtensions.length !== 1 ? 's' : ''} found
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredAndSortedExtensions.map(extension => (
            <ExtensionCard
              key={extension.id}
              extension={extension}
              installing={installingExtensions.has(extension.id)}
              onInstall={() => handleInstall(extension)}
              onUninstall={() => handleUninstall(extension)}
            />
          ))}
        </div>
        {filteredAndSortedExtensions.length === 0 && (
          <div className="text-center py-12">
            <Search className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No extensions found</h3>
            <p className="text-gray-600">Try adjusting your search terms or filters</p>
          </div>
        )}
      </div>
    </div>
  );
}
interface ExtensionCardProps {
  extension: MarketplaceExtension;
  installing: boolean;
  onInstall: () => void;
  onUninstall: () => void;
}
function ExtensionCard({ extension, installing, onInstall, onUninstall }: ExtensionCardProps) {
  const [showDetails, setShowDetails] = useState(false);
  const formatPrice = (price: number | 'free') => {
    if (price === 'free') return 'Free';
    return `$${price}`;
  };
  const formatDownloads = (downloads: number) => {
    if (downloads >= 1000000) return `${(downloads / 1000000).toFixed(1)}M`;
    if (downloads >= 1000) return `${(downloads / 1000).toFixed(1)}K`;
    return downloads.toString();
  };
  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <CardTitle className="text-lg">{extension.display_name}</CardTitle>
              {extension.verified && (
                <span title="Verified Extension">
                  <Shield className="h-4 w-4 text-blue-600" />
                </span>
              )}
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
              <User className="h-3 w-3" />
              <span>{extension.author}</span>
              <span>•</span>
              <span>v{extension.version}</span>
            </div>
            <div className="flex items-center gap-4 text-sm text-gray-600">
              <div className="flex items-center gap-1">
                <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                <span>{extension.rating}</span>
              </div>
              <div className="flex items-center gap-1">
                <Download className="h-3 w-3" />
                <span>{formatDownloads(extension.downloads)}</span>
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-lg font-semibold text-gray-900">
              {formatPrice(extension.price)}
            </div>
            <Badge variant={extension.category === 'experimental' ? 'destructive' : 'secondary'}>
              {extension.category}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col">
        <CardDescription className="flex-1 mb-4">
          {extension.description}
        </CardDescription>
        <div className="space-y-3">
          {/* Tags */}
          <div className="flex flex-wrap gap-1">
            {extension.tags.slice(0, 3).map(tag => (
              <Badge key={tag} variant="outline" className="text-xs">
                <Tag className="h-2 w-2 mr-1" />
                {tag}
              </Badge>
            ))}
            {extension.tags.length > 3 && (
              <Badge variant="outline" className="text-xs">
                +{extension.tags.length - 3} more
              </Badge>
            )}
          </div>
          {/* Capabilities */}
          <div className="flex flex-wrap gap-1">
            {extension.capabilities.provides_ui && (
              <Badge variant="secondary" className="text-xs">UI</Badge>
            )}
            {extension.capabilities.provides_api && (
              <Badge variant="secondary" className="text-xs">API</Badge>
            )}
            {extension.capabilities.provides_background_tasks && (
              <Badge variant="secondary" className="text-xs">Tasks</Badge>
            )}
            {extension.capabilities.provides_webhooks && (
              <Badge variant="secondary" className="text-xs">Webhooks</Badge>
            )}
          </div>
          {/* Actions */}
          <div className="flex gap-2 pt-2">
            {extension.installed ? (
              <Button
                variant="outline"
                size="sm"
                onClick={onUninstall}
                className="flex-1"
              >
                <CheckCircle className="h-4 w-4 mr-2" />
                Installed
              </Button>
            ) : (
              <Button
                size="sm"
                onClick={onInstall}
                disabled={installing}
                className="flex-1"
              >
                {installing ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Installing...
                  </>
                ) : (
                  <>
                    <Plus className="h-4 w-4 mr-2" />
                    Install
                  </>
                )}
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowDetails(!showDetails)}
            >
              <Info className="h-4 w-4" />
            </Button>
          </div>
          {/* Additional Details */}
          {showDetails && (
            <div className="mt-4 pt-4 border-t border-gray-200 space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">License:</span>
                <span>{extension.license}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Updated:</span>
                <span>{new Date(extension.updated_at).toLocaleDateString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Min Kari Version:</span>
                <span>{extension.compatibility.kari_min_version}</span>
              </div>
              {extension.documentation_url && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Documentation:</span>
                  <a 
                    href={extension.documentation_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800 flex items-center gap-1"
                  >
                    View <ExternalLink className="h-3 w-3" />
                  </a>
                </div>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
