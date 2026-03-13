"use client";

import React, { useState, useEffect } from 'react';
import { useChatAuth } from '@/contexts/ChatAuthContext';
import { useSecurity } from '@/hooks/useSecurity';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  User,
  Shield,
  ShieldCheck,
  ShieldAlert,
  Eye,
  EyeOff,
  Lock,
  Unlock,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Settings,
  Key,
  Clock,
  Activity,
  Mail,
  Phone,
  MapPin,
  Calendar,
  LogOut,
  UserCheck,
  UserX,
  RefreshCw,
  Smartphone
} from 'lucide-react';

// Types for UserProfile
export interface UserProfileProps {
  className?: string;
  onProfileUpdate?: (profile: UserProfileData) => void;
}

export interface UserProfileData {
  id: string;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  avatar?: string;
  role: string;
  permissions: string[];
  securityLevel: 'low' | 'medium' | 'high' | 'strict';
  lastLogin: Date;
  sessionDuration: number;
  isActive: boolean;
  preferences: {
    theme: 'light' | 'dark' | 'system';
    language: string;
    notifications: {
      email: boolean;
      push: boolean;
      chat: boolean;
      security: boolean;
    };
    privacy: {
      showOnlineStatus: boolean;
      showLastSeen: boolean;
      showActivity: boolean;
    };
  };
  statistics: {
    totalMessages: number;
    totalConversations: number;
    averageResponseTime: number;
    securityEvents: number;
    successfulLogins: number;
    failedLogins: number;
  };
  security: {
    twoFactorEnabled: boolean;
    trustedDevices: string[];
    lastPasswordChange: Date;
    activeSessions: number;
    securityScore: number;
  };
}

// Mock user data for demonstration
const mockUserData: UserProfileData = {
  id: 'user_123',
  username: 'john.doe',
  email: 'john.doe@example.com',
  firstName: 'John',
  lastName: 'Doe',
  avatar: '/api/placeholder/150x150.png',
  role: 'user',
  permissions: [
    'chat:read',
    'chat:write',
    'chat:conversations:read',
    'chat:conversations:write',
    'chat:messages:read',
    'chat:messages:write'
  ],
  securityLevel: 'medium',
  lastLogin: new Date(Date.now() - 2 * 60 * 60 * 1000),
  sessionDuration: 120,
  isActive: true,
  preferences: {
    theme: 'system',
    language: 'en',
    notifications: {
      email: true,
      push: false,
      chat: true,
      security: true
    },
    privacy: {
      showOnlineStatus: true,
      showLastSeen: true,
      showActivity: false
    }
  },
  statistics: {
    totalMessages: 1247,
    totalConversations: 89,
    averageResponseTime: 1.2,
    securityEvents: 3,
    successfulLogins: 142,
    failedLogins: 8
  },
  security: {
    twoFactorEnabled: false,
    trustedDevices: ['Chrome on Windows', 'Safari on iPhone'],
    lastPasswordChange: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000),
    activeSessions: 1,
    securityScore: 75
  }
};

// Main UserProfile component
export function UserProfile({ className, onProfileUpdate }: UserProfileProps) {
  const { 
    isAuthenticated, 
    hasChatAccess, 
    chatAuthState,
    checkChatPermission,
    logout
  } = useChatAuth();
  
  const { 
    securityLevel: currentSecurityLevel,
    logSecurityEvent
  } = useSecurity();

  const [isEditing, setIsEditing] = useState(false);
  const [activeTab, setActiveTab] = useState('profile');
  const [profileData, setProfileData] = useState<UserProfileData>(mockUserData);

  // Check if user can edit profile
  const canEditProfile = checkChatPermission('chat:profile:write');

  // Handle profile update
  const handleProfileUpdate = (field: string, value: any) => {
    const updatedProfile = {
      ...profileData,
      [field]: value
    };
    
    setProfileData(updatedProfile);
    
    if (onProfileUpdate) {
      onProfileUpdate(updatedProfile);
    }
    
    logSecurityEvent({
      type: 'security_violation',
      severity: 'low',
      message: `Profile field "${field}" updated`,
      details: { field, value }
    });
  };

  // Handle security level change
  const handleSecurityLevelChange = (level: 'low' | 'medium' | 'high' | 'strict') => {
    handleProfileUpdate('securityLevel', level);
  };

  // Handle notification toggle
  const handleNotificationToggle = (type: string, enabled: boolean) => {
    const updatedNotifications = {
      ...profileData.preferences.notifications,
      [type]: enabled
    };
    
    handleProfileUpdate('preferences', {
      ...profileData.preferences,
      notifications: updatedNotifications
    });
  };

  // Handle privacy toggle
  const handlePrivacyToggle = (type: string, enabled: boolean) => {
    const updatedPrivacy = {
      ...profileData.preferences.privacy,
      [type]: enabled
    };
    
    handleProfileUpdate('preferences', {
      ...profileData.preferences,
      privacy: updatedPrivacy
    });
  };

  // Format date
  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };

  // Get security level color
  const getSecurityLevelColor = (level: string) => {
    const colors: Record<string, string> = {
      low: 'bg-green-100 text-green-800',
      medium: 'bg-yellow-100 text-yellow-800',
      high: 'bg-orange-100 text-orange-800',
      strict: 'bg-red-100 text-red-800'
    };
    return colors[level] || 'bg-gray-100 text-gray-800';
  };

  // Get security score color
  const getSecurityScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-yellow-600';
    if (score >= 50) return 'text-orange-600';
    return 'text-red-600';
  };

  // Get security score label
  const getSecurityScoreLabel = (score: number) => {
    if (score >= 90) return 'Excellent';
    if (score >= 70) return 'Good';
    if (score >= 50) return 'Fair';
    return 'Poor';
  };

  if (!isAuthenticated) {
    return (
      <Card className={`w-full max-w-4xl mx-auto ${className}`}>
        <CardHeader className="text-center">
          <CardTitle className="flex items-center gap-2">
            <UserX className="h-5 w-5" />
            Authentication Required
          </CardTitle>
          <CardDescription>
            Please sign in to view your profile
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={() => {}} className="w-full">
            Sign In
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={`w-full max-w-6xl mx-auto space-y-6 ${className}`}>
      {/* Profile Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Avatar className="h-16 w-16">
                <AvatarImage src={profileData.avatar} alt={profileData.username} />
                <AvatarFallback>
                  {profileData.firstName.charAt(0)}{profileData.lastName.charAt(0)}
                </AvatarFallback>
              </Avatar>
              <div>
                <h2 className="text-2xl font-bold">
                  {profileData.firstName} {profileData.lastName}
                </h2>
                <p className="text-muted-foreground">@{profileData.username}</p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <Badge variant={profileData.isActive ? 'default' : 'secondary'}>
                {profileData.isActive ? 'Active' : 'Inactive'}
              </Badge>
              
              {canEditProfile && (
                <Button
                  variant={isEditing ? 'outline' : 'default'}
                  onClick={() => setIsEditing(!isEditing)}
                >
                  {isEditing ? 'Cancel' : 'Edit Profile'}
                </Button>
              )}
            </div>
          </CardTitle>
        </CardHeader>
        
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Basic Info */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold mb-4">Basic Information</h3>
              
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <span className="font-medium w-24">Username:</span>
                  <span>{profileData.username}</span>
                </div>
                
                <div className="flex items-center gap-2">
                  <span className="font-medium w-24">Email:</span>
                  <span>{profileData.email}</span>
                </div>
                
                <div className="flex items-center gap-2">
                  <span className="font-medium w-24">Role:</span>
                  <Badge variant="outline">{profileData.role}</Badge>
                </div>
                
                <div className="flex items-center gap-2">
                  <span className="font-medium w-24">Security:</span>
                  <Badge className={getSecurityLevelColor(profileData.securityLevel)}>
                    {profileData.securityLevel.toUpperCase()}
                  </Badge>
                </div>
              </div>
            </div>

            {/* Session Info */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold mb-4">Session Information</h3>
              
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  <span className="font-medium">Last Login:</span>
                  <span>{formatDate(profileData.lastLogin)}</span>
                </div>
                
                <div className="flex items-center gap-2">
                  <Activity className="h-4 w-4 text-muted-foreground" />
                  <span className="font-medium">Session Duration:</span>
                  <span>{profileData.sessionDuration} minutes</span>
                </div>
                
                <div className="flex items-center gap-2">
                  <MapPin className="h-4 w-4 text-muted-foreground" />
                  <span className="font-medium">Active Sessions:</span>
                  <span>{profileData.security.activeSessions}</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Detailed Profile Tabs */}
      <Card>
        <CardHeader>
          <CardTitle>Profile Details</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="profile">Profile</TabsTrigger>
              <TabsTrigger value="preferences">Preferences</TabsTrigger>
              <TabsTrigger value="security">Security</TabsTrigger>
              <TabsTrigger value="statistics">Statistics</TabsTrigger>
            </TabsList>

            {/* Profile Tab */}
            <TabsContent value="profile" className="space-y-6">
              <div className="space-y-4">
                <h3 className="text-lg font-semibold mb-4">Profile Information</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">First Name</label>
                    <input
                      type="text"
                      value={profileData.firstName}
                      onChange={(e) => handleProfileUpdate('firstName', e.target.value)}
                      disabled={!isEditing}
                      className="w-full px-3 py-2 border rounded-md"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium mb-2">Last Name</label>
                    <input
                      type="text"
                      value={profileData.lastName}
                      onChange={(e) => handleProfileUpdate('lastName', e.target.value)}
                      disabled={!isEditing}
                      className="w-full px-3 py-2 border rounded-md"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">Email</label>
                  <input
                    type="email"
                    value={profileData.email}
                    onChange={(e) => handleProfileUpdate('email', e.target.value)}
                    disabled={!isEditing}
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">Username</label>
                  <input
                    type="text"
                    value={profileData.username}
                    onChange={(e) => handleProfileUpdate('username', e.target.value)}
                    disabled={!isEditing}
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>
              </div>
            </TabsContent>

            {/* Preferences Tab */}
            <TabsContent value="preferences" className="space-y-6">
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold mb-4">Appearance</h3>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">Theme</label>
                      <select
                        value={profileData.preferences.theme}
                        onChange={(e) => handleProfileUpdate('theme', e.target.value)}
                        disabled={!isEditing}
                        className="w-full px-3 py-2 border rounded-md"
                      >
                        <option value="light">Light</option>
                        <option value="dark">Dark</option>
                        <option value="system">System</option>
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium mb-2">Language</label>
                      <select
                        value={profileData.preferences.language}
                        onChange={(e) => handleProfileUpdate('language', e.target.value)}
                        disabled={!isEditing}
                        className="w-full px-3 py-2 border rounded-md"
                      >
                        <option value="en">English</option>
                        <option value="es">Español</option>
                        <option value="fr">Français</option>
                        <option value="de">Deutsch</option>
                      </select>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold mb-4">Notifications</h3>
                  
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Mail className="h-4 w-4" />
                        <span className="font-medium">Email Notifications</span>
                      </div>
                      <Switch
                        checked={profileData.preferences.notifications.email}
                        onCheckedChange={(checked) => handleNotificationToggle('email', checked)}
                        disabled={!isEditing}
                      />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Phone className="h-4 w-4" />
                        <span className="font-medium">Push Notifications</span>
                      </div>
                      <Switch
                        checked={profileData.preferences.notifications.push}
                        onCheckedChange={(checked) => handleNotificationToggle('push', checked)}
                        disabled={!isEditing}
                      />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <UserCheck className="h-4 w-4" />
                        <span className="font-medium">Chat Notifications</span>
                      </div>
                      <Switch
                        checked={profileData.preferences.notifications.chat}
                        onCheckedChange={(checked) => handleNotificationToggle('chat', checked)}
                        disabled={!isEditing}
                      />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Shield className="h-4 w-4" />
                        <span className="font-medium">Security Notifications</span>
                      </div>
                      <Switch
                        checked={profileData.preferences.notifications.security}
                        onCheckedChange={(checked) => handleNotificationToggle('security', checked)}
                        disabled={!isEditing}
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold mb-4">Privacy</h3>
                  
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Eye className="h-4 w-4" />
                        <span className="font-medium">Show Online Status</span>
                      </div>
                      <Switch
                        checked={profileData.preferences.privacy.showOnlineStatus}
                        onCheckedChange={(checked) => handlePrivacyToggle('showOnlineStatus', checked)}
                        disabled={!isEditing}
                      />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Calendar className="h-4 w-4" />
                        <span className="font-medium">Show Last Seen</span>
                      </div>
                      <Switch
                        checked={profileData.preferences.privacy.showLastSeen}
                        onCheckedChange={(checked) => handlePrivacyToggle('showLastSeen', checked)}
                        disabled={!isEditing}
                      />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Activity className="h-4 w-4" />
                        <span className="font-medium">Show Activity</span>
                      </div>
                      <Switch
                        checked={profileData.preferences.privacy.showActivity}
                        onCheckedChange={(checked) => handlePrivacyToggle('showActivity', checked)}
                        disabled={!isEditing}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </TabsContent>

            {/* Security Tab */}
            <TabsContent value="security" className="space-y-6">
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold mb-4">Security Settings</h3>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">Security Level</label>
                      <select
                        value={profileData.securityLevel}
                        onChange={(e) => handleSecurityLevelChange(e.target.value as any)}
                        disabled={!isEditing}
                        className="w-full px-3 py-2 border rounded-md"
                      >
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                        <option value="strict">Strict</option>
                      </select>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <ShieldCheck className="h-4 w-4" />
                        <span className="font-medium">Two-Factor Authentication</span>
                      </div>
                      <Switch
                        checked={profileData.security.twoFactorEnabled}
                        onCheckedChange={(checked) => handleProfileUpdate('twoFactorEnabled', checked)}
                        disabled={!isEditing}
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold mb-4">Security Score</h3>
                  
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">Current Score:</span>
                      <div className="flex items-center gap-2">
                        <span className={`text-2xl font-bold ${getSecurityScoreColor(profileData.security.securityScore)}`}>
                          {profileData.security.securityScore}
                        </span>
                        <Badge className={getSecurityLevelColor(profileData.securityLevel)}>
                          {getSecurityScoreLabel(profileData.security.securityScore)}
                        </Badge>
                      </div>
                    </div>
                    
                    <div className="mt-4">
                      <Progress value={profileData.security.securityScore} max={100} className="w-full" />
                      <div className="flex justify-between text-sm text-muted-foreground mt-2">
                        <span>Poor</span>
                        <span>Excellent</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold mb-4">Trusted Devices</h3>
                  
                  <div className="space-y-2">
                    {profileData.security.trustedDevices.map((device, index) => (
                      <div key={index} className="flex items-center justify-between p-3 border rounded-md">
                        <div className="flex items-center gap-2">
                          <Phone className="h-4 w-4" />
                          <span>{device}</span>
                        </div>
                        <Button variant="outline" size="sm" disabled={!isEditing}>
                          Remove
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </TabsContent>

            {/* Statistics Tab */}
            <TabsContent value="statistics" className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold mb-4">Activity Statistics</h3>
                  
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">Total Messages:</span>
                      <span className="text-2xl font-bold">{profileData.statistics.totalMessages.toLocaleString()}</span>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="font-medium">Total Conversations:</span>
                      <span className="text-2xl font-bold">{profileData.statistics.totalConversations.toLocaleString()}</span>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="font-medium">Average Response Time:</span>
                      <span className="text-2xl font-bold">{profileData.statistics.averageResponseTime}s</span>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <h3 className="text-lg font-semibold mb-4">Security Statistics</h3>
                  
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">Security Events:</span>
                      <span className="text-2xl font-bold text-red-600">{profileData.statistics.securityEvents}</span>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="font-medium">Successful Logins:</span>
                      <span className="text-2xl font-bold text-green-600">{profileData.statistics.successfulLogins}</span>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="font-medium">Failed Logins:</span>
                      <span className="text-2xl font-bold text-red-600">{profileData.statistics.failedLogins}</span>
                    </div>
                  </div>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <Card>
        <CardHeader>
          <CardTitle>Account Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            <Button variant="outline" onClick={() => {}}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh Session
            </Button>
            
            <Button variant="outline" onClick={() => {}}>
              <Key className="mr-2 h-4 w-4" />
              Change Password
            </Button>
            
            <Button 
              variant="destructive" 
              onClick={() => {
                logout();
                logSecurityEvent({
                  type: 'security_violation',
                  severity: 'low',
                  message: 'User logged out',
                  details: { action: 'logout' }
                });
              }}
            >
              <LogOut className="mr-2 h-4 w-4" />
              Sign Out
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default UserProfile;