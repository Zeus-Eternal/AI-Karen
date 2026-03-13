"use client";

import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Search, 
  Filter, 
  Plus, 
  Download, 
  Trash2,
  Edit,
  Eye,
  MoreHorizontal,
  RefreshCw,
  Users,
  Activity,
  Clock,
  Calendar,
  TrendingUp,
  TrendingDown,
  MessageSquare,
  MousePointer,
  BarChart3,
  Target,
  Zap,
  UserCheck,
  UserX
} from 'lucide-react';
import { cn } from '@/lib/utils';

// User engagement data types
interface UserEngagementEntry {
  id: string;
  userId: string;
  userName: string;
  userEmail: string;
  sessionId: string;
  sessionDuration: number; // in seconds
  messagesCount: number;
  interactionsCount: number;
  pagesViewed: number;
  featuresUsed: string[];
  lastActivity: string;
  sessionStart: string;
  sessionEnd: string;
  engagementScore: number; // 0-100
  satisfactionScore: number; // 0-100
  conversionEvents: string[];
  deviceType: 'desktop' | 'mobile' | 'tablet';
  browser: string;
  location: string;
  referrer: string;
  isNewUser: boolean;
  userTier: 'free' | 'premium' | 'enterprise';
  metadata: {
    userAgent?: string;
    screenResolution?: string;
    timezone?: string;
    language?: string;
  };
}

interface EngagementMetrics {
  totalSessions: number;
  totalUsers: number;
  averageSessionDuration: number;
  averageEngagementScore: number;
  averageSatisfactionScore: number;
  totalMessages: number;
  totalInteractions: number;
  conversionRate: number;
  retentionRate: number;
  adoptionRate: number;
  topFeatures: Array<{ feature: string; usage: number }>;
  userGrowth: number;
  activityTrend: 'up' | 'down' | 'stable';
}

interface UserEngagementGridProps {
  className?: string;
}

// Utility function for date formatting
function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'UTC'
  });
}

// Utility function for duration formatting
function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  
  if (hours > 0) {
    return `${hours}h ${minutes}m ${secs}s`;
  } else if (minutes > 0) {
    return `${minutes}m ${secs}s`;
  } else {
    return `${secs}s`;
  }
}

// Utility function for engagement score color
function getEngagementColor(score: number): string {
  if (score >= 80) return 'bg-green-100 text-green-800';
  if (score >= 60) return 'bg-yellow-100 text-yellow-800';
  if (score >= 40) return 'bg-orange-100 text-orange-800';
  return 'bg-red-100 text-red-800';
}

// Utility function for user tier color
function getUserTierColor(tier: string): string {
  switch (tier) {
    case 'enterprise': return 'bg-purple-100 text-purple-800';
    case 'premium': return 'bg-blue-100 text-blue-800';
    case 'free': return 'bg-gray-100 text-gray-800';
    default: return 'bg-gray-100 text-gray-800';
  }
}

export default function DynamicUserEngagementGrid({ className }: UserEngagementGridProps) {
  const [engagements, setEngagements] = useState<UserEngagementEntry[]>([]);
  const [metrics, setMetrics] = useState<EngagementMetrics | null>(null);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedEngagements, setSelectedEngagements] = useState<string[]>([]);
  const [filterTier, setFilterTier] = useState<string>('all');
  const [filterDevice, setFilterDevice] = useState<string>('all');
  const [filterTimeRange, setFilterTimeRange] = useState<string>('7d');
  const [sortBy, setSortBy] = useState<'sessionStart' | 'engagementScore' | 'sessionDuration' | 'messagesCount'>('sessionStart');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  // Mock data - replace with actual API call
  useEffect(() => {
    const mockEngagements: UserEngagementEntry[] = [
      {
        id: '1',
        userId: 'user-123',
        userName: 'John Doe',
        userEmail: 'john.doe@example.com',
        sessionId: 'session-abc123',
        sessionDuration: 1847, // 30 minutes 47 seconds
        messagesCount: 25,
        interactionsCount: 45,
        pagesViewed: 8,
        featuresUsed: ['chat', 'file-upload', 'analytics', 'memory'],
        lastActivity: new Date(Date.now() - 1800000).toISOString(),
        sessionStart: new Date(Date.now() - 1847000).toISOString(),
        sessionEnd: new Date(Date.now() - 1000).toISOString(),
        engagementScore: 85,
        satisfactionScore: 90,
        conversionEvents: ['signup', 'first-message', 'file-upload'],
        deviceType: 'desktop',
        browser: 'Chrome',
        location: 'New York, USA',
        referrer: 'direct',
        isNewUser: false,
        userTier: 'premium',
        metadata: {
          userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
          screenResolution: '1920x1080',
          timezone: 'America/New_York',
          language: 'en-US'
        }
      },
      {
        id: '2',
        userId: 'user-456',
        userName: 'Jane Smith',
        userEmail: 'jane.smith@example.com',
        sessionId: 'session-def456',
        sessionDuration: 923, // 15 minutes 23 seconds
        messagesCount: 12,
        interactionsCount: 28,
        pagesViewed: 5,
        featuresUsed: ['chat', 'memory'],
        lastActivity: new Date(Date.now() - 3600000).toISOString(),
        sessionStart: new Date(Date.now() - 3623000).toISOString(),
        sessionEnd: new Date(Date.now() - 2700000).toISOString(),
        engagementScore: 72,
        satisfactionScore: 78,
        conversionEvents: ['signup', 'first-message'],
        deviceType: 'mobile',
        browser: 'Safari',
        location: 'London, UK',
        referrer: 'google',
        isNewUser: true,
        userTier: 'free',
        metadata: {
          userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)',
          screenResolution: '390x844',
          timezone: 'Europe/London',
          language: 'en-GB'
        }
      },
      {
        id: '3',
        userId: 'user-789',
        userName: 'Bob Johnson',
        userEmail: 'bob.johnson@example.com',
        sessionId: 'session-ghi789',
        sessionDuration: 3421, // 57 minutes 1 second
        messagesCount: 48,
        interactionsCount: 89,
        pagesViewed: 12,
        featuresUsed: ['chat', 'file-upload', 'analytics', 'memory', 'automation'],
        lastActivity: new Date(Date.now() - 7200000).toISOString(),
        sessionStart: new Date(Date.now() - 10621000).toISOString(),
        sessionEnd: new Date(Date.now() - 7200000).toISOString(),
        engagementScore: 92,
        satisfactionScore: 88,
        conversionEvents: ['signup', 'first-message', 'file-upload', 'premium-upgrade'],
        deviceType: 'desktop',
        browser: 'Firefox',
        location: 'San Francisco, USA',
        referrer: 'linkedin',
        isNewUser: false,
        userTier: 'enterprise',
        metadata: {
          userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101',
          screenResolution: '2560x1440',
          timezone: 'America/Los_Angeles',
          language: 'en-US'
        }
      }
    ];

    const mockMetrics: EngagementMetrics = {
      totalSessions: 1247,
      totalUsers: 892,
      averageSessionDuration: 1245, // ~20 minutes
      averageEngagementScore: 76.5,
      averageSatisfactionScore: 82.3,
      totalMessages: 15420,
      totalInteractions: 28930,
      conversionRate: 23.4,
      retentionRate: 67.8,
      adoptionRate: 45.2,
      topFeatures: [
        { feature: 'chat', usage: 892 },
        { feature: 'memory', usage: 456 },
        { feature: 'file-upload', usage: 234 },
        { feature: 'analytics', usage: 189 },
        { feature: 'automation', usage: 67 }
      ],
      userGrowth: 12.3,
      activityTrend: 'up'
    };

    setEngagements(mockEngagements);
    setMetrics(mockMetrics);
    setLoading(false);
  }, []);

  // Filter and sort engagements
  const filteredEngagements = useMemo(() => {
    let filtered = engagements;

    // Apply search filter
    if (searchQuery) {
      filtered = filtered.filter(engagement =>
        engagement.userName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        engagement.userEmail.toLowerCase().includes(searchQuery.toLowerCase()) ||
        engagement.featuresUsed.some(feature => feature.toLowerCase().includes(searchQuery.toLowerCase()))
      );
    }

    // Apply tier filter
    if (filterTier !== 'all') {
      filtered = filtered.filter(engagement => engagement.userTier === filterTier);
    }

    // Apply device filter
    if (filterDevice !== 'all') {
      filtered = filtered.filter(engagement => engagement.deviceType === filterDevice);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      const aValue = a[sortBy];
      const bValue = b[sortBy];
      
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortOrder === 'asc' 
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }
      
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortOrder === 'asc' ? aValue - bValue : bValue - aValue;
      }
      
      return 0;
    });

    return filtered;
  }, [engagements, searchQuery, filterTier, filterDevice, sortBy, sortOrder]);

  const handleRefresh = () => {
    setLoading(true);
    // Simulate refresh
    setTimeout(() => {
      // In real implementation, this would fetch fresh data
      setLoading(false);
    }, 1000);
  };

  const handleExport = () => {
    // In real implementation, this would export engagement data
    const data = {
      engagements: filteredEngagements,
      metrics: metrics,
      exportedAt: new Date().toISOString(),
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `engagement-data-${formatDate(new Date())}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const toggleEngagementSelection = (engagementId: string) => {
    setSelectedEngagements(prev =>
      prev.includes(engagementId)
        ? prev.filter(id => id !== engagementId)
        : [...prev, engagementId]
    );
  };

  const toggleAllSelection = () => {
    if (selectedEngagements.length === filteredEngagements.length) {
      setSelectedEngagements([]);
    } else {
      setSelectedEngagements(filteredEngagements.map(e => e.id));
    }
  };

  return (
    <div className={cn("space-y-6", className)}>
      {/* Metrics Overview */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Sessions</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics.totalSessions.toLocaleString()}</div>
              <p className="text-xs text-muted-foreground">
                {metrics.totalUsers.toLocaleString()} unique users
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg. Session Duration</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatDuration(metrics.averageSessionDuration)}</div>
              <p className="text-xs text-muted-foreground">
                Per user session
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Engagement Score</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics.averageEngagementScore.toFixed(1)}</div>
              <p className="text-xs text-muted-foreground">
                {metrics.activityTrend === 'up' ? (
                  <span className="flex items-center text-green-600">
                    <TrendingUp className="h-3 w-3 mr-1" />
                    +5.2% from last week
                  </span>
                ) : metrics.activityTrend === 'down' ? (
                  <span className="flex items-center text-red-600">
                    <TrendingDown className="h-3 w-3 mr-1" />
                    -2.1% from last week
                  </span>
                ) : (
                  <span className="text-muted-foreground">No change from last week</span>
                )}
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Conversion Rate</CardTitle>
              <Target className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics.conversionRate}%</div>
              <p className="text-xs text-muted-foreground">
                {metrics.adoptionRate}% feature adoption
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Dynamic User Engagement Grid
          </CardTitle>
          <CardDescription>
            Comprehensive user engagement analytics with behavior tracking and insights
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Engagement Controls */}
          <div className="flex flex-col gap-4 mb-6">
            <div className="flex gap-2">
              <Input
                placeholder="Search users..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1"
              />
              
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={loading}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={handleExport}
              >
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            </div>
            
            <div className="flex flex-wrap gap-2">
              <select
                value={filterTier}
                onChange={(e) => setFilterTier(e.target.value)}
                className="px-3 py-1 border border-border rounded-md text-sm"
              >
                <option value="all">All Tiers</option>
                <option value="free">Free</option>
                <option value="premium">Premium</option>
                <option value="enterprise">Enterprise</option>
              </select>
              
              <select
                value={filterDevice}
                onChange={(e) => setFilterDevice(e.target.value)}
                className="px-3 py-1 border border-border rounded-md text-sm"
              >
                <option value="all">All Devices</option>
                <option value="desktop">Desktop</option>
                <option value="mobile">Mobile</option>
                <option value="tablet">Tablet</option>
              </select>
              
              <select
                value={filterTimeRange}
                onChange={(e) => setFilterTimeRange(e.target.value)}
                className="px-3 py-1 border border-border rounded-md text-sm"
              >
                <option value="1d">Last 24 hours</option>
                <option value="7d">Last 7 days</option>
                <option value="30d">Last 30 days</option>
                <option value="90d">Last 90 days</option>
              </select>
              
              <select
                value={`${sortBy}-${sortOrder}`}
                onChange={(e) => {
                  const [sort, order] = e.target.value.split('-');
                  setSortBy(sort as any);
                  setSortOrder(order as any);
                }}
                className="px-3 py-1 border border-border rounded-md text-sm"
              >
                <option value="sessionStart-desc">Most Recent</option>
                <option value="sessionStart-asc">Oldest First</option>
                <option value="engagementScore-desc">Highest Engagement</option>
                <option value="engagementScore-asc">Lowest Engagement</option>
                <option value="sessionDuration-desc">Longest Session</option>
                <option value="sessionDuration-asc">Shortest Session</option>
                <option value="messagesCount-desc">Most Messages</option>
                <option value="messagesCount-asc">Fewest Messages</option>
              </select>
              
              <div className="flex gap-1 ml-auto">
                <Button
                  variant={viewMode === 'grid' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setViewMode('grid')}
                >
                  Grid
                </Button>
                <Button
                  variant={viewMode === 'list' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setViewMode('list')}
                >
                  List
                </Button>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={toggleAllSelection}
                disabled={filteredEngagements.length === 0}
              >
                {selectedEngagements.length === filteredEngagements.length ? 'Deselect All' : 'Select All'}
              </Button>
              
              <Badge className="text-xs bg-secondary text-secondary-foreground">
                {filteredEngagements.length} sessions
              </Badge>
            </div>
          </div>

          {/* Engagement Grid/List */}
          {viewMode === 'grid' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredEngagements.map((engagement) => (
                <Card 
                  key={engagement.id} 
                  className={cn(
                    "cursor-pointer transition-all hover:shadow-md",
                    selectedEngagements.includes(engagement.id) && "ring-2 ring-primary"
                  )}
                  onClick={() => toggleEngagementSelection(engagement.id)}
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <Badge className={cn("text-xs", getUserTierColor(engagement.userTier))}>
                          {engagement.userTier}
                        </Badge>
                        <Badge className={cn("text-xs", getEngagementColor(engagement.engagementScore))}>
                          {engagement.engagementScore}% engagement
                        </Badge>
                        {engagement.isNewUser && (
                          <Badge className="text-xs bg-green-100 text-green-800">
                            New User
                          </Badge>
                        )}
                      </div>
                      <input
                        type="checkbox"
                        checked={selectedEngagements.includes(engagement.id)}
                        onChange={() => toggleEngagementSelection(engagement.id)}
                        className="rounded"
                      />
                    </div>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <h4 className="font-medium text-sm mb-1">{engagement.userName}</h4>
                    <p className="text-xs text-muted-foreground mb-3">{engagement.userEmail}</p>
                    
                    <div className="space-y-2 mb-3">
                      <div className="flex justify-between text-xs">
                        <span className="text-muted-foreground">Session Duration</span>
                        <span>{formatDuration(engagement.sessionDuration)}</span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-muted-foreground">Messages</span>
                        <span>{engagement.messagesCount}</span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-muted-foreground">Interactions</span>
                        <span>{engagement.interactionsCount}</span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-muted-foreground">Satisfaction</span>
                        <span>{engagement.satisfactionScore}%</span>
                      </div>
                    </div>
                    
                    <div className="flex flex-wrap gap-1 mb-3">
                      {engagement.featuresUsed.slice(0, 2).map(feature => (
                        <Badge key={feature} className="text-xs border border-current">
                          {feature}
                        </Badge>
                      ))}
                      {engagement.featuresUsed.length > 2 && (
                        <Badge className="text-xs border border-current">
                          +{engagement.featuresUsed.length - 2}
                        </Badge>
                      )}
                    </div>
                    
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {formatDate(engagement.sessionStart)}
                      </div>
                      <div className="flex items-center gap-1">
                        <Activity className="h-3 w-3" />
                        {engagement.deviceType}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="space-y-2">
              {filteredEngagements.map((engagement) => (
                <Card 
                  key={engagement.id} 
                  className={cn(
                    "cursor-pointer transition-all hover:shadow-md",
                    selectedEngagements.includes(engagement.id) && "ring-2 ring-primary"
                  )}
                  onClick={() => toggleEngagementSelection(engagement.id)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <h4 className="font-medium text-sm">{engagement.userName}</h4>
                          <Badge className={cn("text-xs", getUserTierColor(engagement.userTier))}>
                            {engagement.userTier}
                          </Badge>
                          <Badge className={cn("text-xs", getEngagementColor(engagement.engagementScore))}>
                            {engagement.engagementScore}% engagement
                          </Badge>
                          {engagement.isNewUser && (
                            <Badge className="text-xs bg-green-100 text-green-800">
                              New User
                            </Badge>
                          )}
                        </div>
                        
                        <p className="text-xs text-muted-foreground mb-2">{engagement.userEmail}</p>
                        
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-2">
                          <div className="text-xs">
                            <span className="text-muted-foreground">Duration:</span>
                            <div className="font-medium">{formatDuration(engagement.sessionDuration)}</div>
                          </div>
                          <div className="text-xs">
                            <span className="text-muted-foreground">Messages:</span>
                            <div className="font-medium">{engagement.messagesCount}</div>
                          </div>
                          <div className="text-xs">
                            <span className="text-muted-foreground">Interactions:</span>
                            <div className="font-medium">{engagement.interactionsCount}</div>
                          </div>
                          <div className="text-xs">
                            <span className="text-muted-foreground">Satisfaction:</span>
                            <div className="font-medium">{engagement.satisfactionScore}%</div>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                          <div className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            {formatDate(engagement.sessionStart)}
                          </div>
                          <div className="flex items-center gap-1">
                            <Activity className="h-3 w-3" />
                            {engagement.deviceType} • {engagement.browser}
                          </div>
                          <div className="flex items-center gap-1">
                            <MessageSquare className="h-3 w-3" />
                            {engagement.featuresUsed.length} features used
                          </div>
                        </div>
                      </div>
                      
                      <input
                        type="checkbox"
                        checked={selectedEngagements.includes(engagement.id)}
                        onChange={() => toggleEngagementSelection(engagement.id)}
                        className="rounded ml-4"
                      />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Empty State */}
          {filteredEngagements.length === 0 && !loading && (
            <div className="text-center py-8">
              <Users className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium">No engagement data found</h3>
              <p className="text-muted-foreground">
                {searchQuery 
                  ? `No users matching "${searchQuery}"`
                  : 'No engagement data available'
                }
              </p>
              <Button onClick={handleRefresh} className="mt-4">
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh Data
              </Button>
            </div>
          )}

          {/* Loading State */}
          {loading && (
            <div className="text-center py-8">
              <RefreshCw className="h-8 w-8 mx-auto animate-spin text-muted-foreground" />
              <p className="text-muted-foreground mt-2">Loading engagement data...</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}