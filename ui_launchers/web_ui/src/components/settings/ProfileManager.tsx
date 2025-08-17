"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { Textarea } from '@/components/ui/textarea';
import { Slider } from '@/components/ui/slider';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Brain,
  Settings,
  Plus,
  Edit,
  Trash2,
  Copy,
  Save,
  X,
  AlertCircle,
  CheckCircle2,
  Zap,
  Shield,
  Database,
  Users,
  ArrowUp,
  ArrowDown,
  GripVertical,
  Loader2
} from 'lucide-react';
import { getKarenBackend } from '@/lib/karen-backend';
import { ErrorHandler } from '@/lib/error-handler';

interface LLMProfile {
  id: string;
  name: string;
  description: string;
  router_policy: 'balanced' | 'performance' | 'cost' | 'privacy' | 'custom';
  providers: Record<string, {
    provider: string;
    model?: string;
    priority: number;
    max_cost_per_1k_tokens?: number;
    required_capabilities: string[];
    excluded_capabilities: string[];
  }>;
  fallback_provider: string;
  fallback_model?: string;
  is_valid: boolean;
  validation_errors: string[];
  created_at: number;
  updated_at: number;
  settings?: {
    temperature?: number;
    max_tokens?: number;
    top_p?: number;
    frequency_penalty?: number;
    presence_penalty?: number;
  };
}

interface LLMProvider {
  name: string;
  description: string;
  capabilities: string[];
  provider_type: string;
  requires_api_key: boolean;
}

interface ProfileManagerProps {
  profiles: LLMProfile[];
  providers: LLMProvider[];
  activeProfile: LLMProfile | null;
  onProfileChange: (profileId: string) => void;
  onProfileUpdate: () => void;
}

const ROUTER_POLICIES = [
  { value: 'balanced', label: 'Balanced', description: 'Balance cost, performance, and reliability' },
  { value: 'performance', label: 'Performance', description: 'Prioritize speed and quality' },
  { value: 'cost', label: 'Cost Optimized', description: 'Minimize costs while maintaining quality' },
  { value: 'privacy', label: 'Privacy First', description: 'Prefer local and privacy-focused providers' },
  { value: 'custom', label: 'Custom', description: 'Custom routing configuration' }
];

const USE_CASES = [
  { key: 'chat', label: 'General Chat', description: 'Conversational interactions' },
  { key: 'code', label: 'Code Generation', description: 'Programming and code assistance' },
  { key: 'reasoning', label: 'Complex Reasoning', description: 'Analysis and problem solving' },
  { key: 'creative', label: 'Creative Writing', description: 'Content creation and storytelling' },
  { key: 'summarization', label: 'Summarization', description: 'Text summarization and extraction' },
  { key: 'translation', label: 'Translation', description: 'Language translation tasks' }
];

export default function ProfileManager({
  profiles,
  providers,
  activeProfile,
  onProfileChange,
  onProfileUpdate
}: ProfileManagerProps) {
  const [editingProfile, setEditingProfile] = useState<LLMProfile | null>(null);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [validating, setValidating] = useState(false);
  const [draggedUseCase, setDraggedUseCase] = useState<string | null>(null);

  const { toast } = useToast();
  const backend = getKarenBackend();

  const createNewProfile = (): LLMProfile => ({
    id: `profile_${Date.now()}`,
    name: '',
    description: '',
    router_policy: 'balanced',
    providers: {},
    fallback_provider: providers[0]?.name || 'local',
    is_valid: false,
    validation_errors: [],
    created_at: Date.now(),
    updated_at: Date.now(),
    settings: {
      temperature: 0.7,
      max_tokens: 4000,
      top_p: 0.9,
      frequency_penalty: 0,
      presence_penalty: 0
    }
  });

  const validateProfile = (profile: LLMProfile): { isValid: boolean; errors: string[] } => {
    const errors: string[] = [];

    if (!profile.name.trim()) {
      errors.push('Profile name is required');
    }

    if (!profile.description.trim()) {
      errors.push('Profile description is required');
    }

    if (Object.keys(profile.providers).length === 0) {
      errors.push('At least one provider assignment is required');
    }

    // Validate provider assignments
    Object.entries(profile.providers).forEach(([useCase, config]) => {
      const provider = providers.find(p => p.name === config.provider);
      if (!provider) {
        errors.push(`Provider "${config.provider}" for ${useCase} is not available`);
      } else {
        // Check if required capabilities are supported
        const unsupportedCaps = config.required_capabilities.filter(
          cap => !provider.capabilities.includes(cap)
        );
        if (unsupportedCaps.length > 0) {
          errors.push(`Provider "${config.provider}" doesn't support required capabilities: ${unsupportedCaps.join(', ')}`);
        }
      }

      if (config.priority < 1 || config.priority > 100) {
        errors.push(`Priority for ${useCase} must be between 1 and 100`);
      }
    });

    // Validate fallback provider
    const fallbackProvider = providers.find(p => p.name === profile.fallback_provider);
    if (!fallbackProvider) {
      errors.push('Fallback provider is not available');
    }

    return { isValid: errors.length === 0, errors };
  };

  const saveProfile = async (profile: LLMProfile) => {
    try {
      setSaving(true);
      
      const validation = validateProfile(profile);
      if (!validation.isValid) {
        toast({
          variant: 'destructive',
          title: 'Validation Failed',
          description: validation.errors[0]
        });
        return;
      }

      const updatedProfile = {
        ...profile,
        is_valid: validation.isValid,
        validation_errors: validation.errors,
        updated_at: Date.now()
      };

      const endpoint = profile.id.startsWith('profile_') ? '/api/providers/profiles' : `/api/providers/profiles/${profile.id}`;
      const method = profile.id.startsWith('profile_') ? 'POST' : 'PUT';

      await backend.makeRequestPublic(endpoint, {
        method,
        body: JSON.stringify(updatedProfile)
      });

      toast({
        title: 'Profile Saved',
        description: `Profile "${profile.name}" has been saved successfully.`
      });

      setIsCreateDialogOpen(false);
      setIsEditDialogOpen(false);
      setEditingProfile(null);
      onProfileUpdate();

    } catch (error) {
      console.error('Failed to save profile:', error);
      const info = (error as any)?.errorInfo || ErrorHandler.handleApiError(error as any, 'saveProfile');
      toast({
        variant: 'destructive',
        title: info.title || 'Save Failed',
        description: info.message || 'Could not save the profile.'
      });
    } finally {
      setSaving(false);
    }
  };

  const deleteProfile = async (profileId: string) => {
    try {
      await backend.makeRequestPublic(`/api/providers/profiles/${profileId}`, {
        method: 'DELETE'
      });

      toast({
        title: 'Profile Deleted',
        description: 'Profile has been deleted successfully.'
      });

      onProfileUpdate();
    } catch (error) {
      console.error('Failed to delete profile:', error);
      const info = (error as any)?.errorInfo || ErrorHandler.handleApiError(error as any, 'deleteProfile');
      toast({
        variant: 'destructive',
        title: info.title || 'Delete Failed',
        description: info.message || 'Could not delete the profile.'
      });
    }
  };

  const duplicateProfile = (profile: LLMProfile) => {
    const newProfile = {
      ...profile,
      id: `profile_${Date.now()}`,
      name: `${profile.name} (Copy)`,
      created_at: Date.now(),
      updated_at: Date.now()
    };
    setEditingProfile(newProfile);
    setIsCreateDialogOpen(true);
  };

  const addProviderAssignment = (profile: LLMProfile, useCase: string) => {
    const updatedProfile = {
      ...profile,
      providers: {
        ...profile.providers,
        [useCase]: {
          provider: providers[0]?.name || 'local',
          priority: 50,
          required_capabilities: [],
          excluded_capabilities: []
        }
      }
    };
    setEditingProfile(updatedProfile);
  };

  const removeProviderAssignment = (profile: LLMProfile, useCase: string) => {
    const { [useCase]: removed, ...remainingProviders } = profile.providers;
    const updatedProfile = {
      ...profile,
      providers: remainingProviders
    };
    setEditingProfile(updatedProfile);
  };

  const updateProviderAssignment = (
    profile: LLMProfile, 
    useCase: string, 
    field: string, 
    value: any
  ) => {
    const updatedProfile = {
      ...profile,
      providers: {
        ...profile.providers,
        [useCase]: {
          ...profile.providers[useCase],
          [field]: value
        }
      }
    };
    setEditingProfile(updatedProfile);
  };

  const getRouterPolicyIcon = (policy: string) => {
    switch (policy) {
      case 'performance':
        return <Zap className="h-4 w-4" />;
      case 'cost':
        return <Database className="h-4 w-4" />;
      case 'privacy':
        return <Shield className="h-4 w-4" />;
      case 'balanced':
        return <Settings className="h-4 w-4" />;
      default:
        return <Brain className="h-4 w-4" />;
    }
  };

  const ProfileEditor = ({ profile, onSave, onCancel }: {
    profile: LLMProfile;
    onSave: (profile: LLMProfile) => void;
    onCancel: () => void;
  }) => {
    const [localProfile, setLocalProfile] = useState(profile);
    const validation = validateProfile(localProfile);

    return (
      <div className="space-y-6 max-h-[80vh] overflow-y-auto">
        {/* Basic Information */}
        <div className="space-y-4">
          <div>
            <Label htmlFor="profile-name">Profile Name</Label>
            <Input
              id="profile-name"
              value={localProfile.name}
              onChange={(e) => setLocalProfile(prev => ({ ...prev, name: e.target.value }))}
              placeholder="Enter profile name"
            />
          </div>
          
          <div>
            <Label htmlFor="profile-description">Description</Label>
            <Textarea
              id="profile-description"
              value={localProfile.description}
              onChange={(e) => setLocalProfile(prev => ({ ...prev, description: e.target.value }))}
              placeholder="Describe this profile's purpose and use cases"
              rows={3}
            />
          </div>
          
          <div>
            <Label htmlFor="router-policy">Router Policy</Label>
            <Select
              value={localProfile.router_policy}
              onValueChange={(value) => setLocalProfile(prev => ({ 
                ...prev, 
                router_policy: value as LLMProfile['router_policy'] 
              }))}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {ROUTER_POLICIES.map(policy => (
                  <SelectItem key={policy.value} value={policy.value}>
                    <div className="flex items-center gap-2">
                      {getRouterPolicyIcon(policy.value)}
                      <div>
                        <div className="font-medium">{policy.label}</div>
                        <div className="text-xs text-muted-foreground">{policy.description}</div>
                      </div>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Provider Assignments */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-medium">Provider Assignments</h4>
            <Select
              value=""
              onValueChange={(useCase) => addProviderAssignment(localProfile, useCase)}
            >
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Add use case" />
              </SelectTrigger>
              <SelectContent>
                {USE_CASES.filter(uc => !localProfile.providers[uc.key]).map(useCase => (
                  <SelectItem key={useCase.key} value={useCase.key}>
                    {useCase.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-4">
            {Object.entries(localProfile.providers).map(([useCase, config]) => {
              const useCaseInfo = USE_CASES.find(uc => uc.key === useCase);
              return (
                <Card key={useCase} className="p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <h5 className="font-medium">{useCaseInfo?.label || useCase}</h5>
                      <p className="text-sm text-muted-foreground">{useCaseInfo?.description}</p>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeProviderAssignment(localProfile, useCase)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label>Provider</Label>
                      <Select
                        value={config.provider}
                        onValueChange={(value) => updateProviderAssignment(localProfile, useCase, 'provider', value)}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {providers.map(provider => (
                            <SelectItem key={provider.name} value={provider.name}>
                              {provider.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label>Priority (1-100)</Label>
                      <div className="space-y-2">
                        <Slider
                          value={[config.priority]}
                          onValueChange={([value]) => updateProviderAssignment(localProfile, useCase, 'priority', value)}
                          min={1}
                          max={100}
                          step={1}
                        />
                        <div className="text-sm text-muted-foreground text-center">
                          {config.priority}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Required Capabilities */}
                  <div className="mt-4">
                    <Label className="text-sm">Required Capabilities</Label>
                    <div className="flex flex-wrap gap-1 mt-2">
                      {providers.find(p => p.name === config.provider)?.capabilities.map(cap => (
                        <Badge
                          key={cap}
                          variant={config.required_capabilities.includes(cap) ? "default" : "outline"}
                          className="cursor-pointer text-xs"
                          onClick={() => {
                            const newCaps = config.required_capabilities.includes(cap)
                              ? config.required_capabilities.filter(c => c !== cap)
                              : [...config.required_capabilities, cap];
                            updateProviderAssignment(localProfile, useCase, 'required_capabilities', newCaps);
                          }}
                        >
                          {cap}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        </div>

        {/* Fallback Configuration */}
        <div>
          <h4 className="font-medium mb-4">Fallback Configuration</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label>Fallback Provider</Label>
              <Select
                value={localProfile.fallback_provider}
                onValueChange={(value) => setLocalProfile(prev => ({ ...prev, fallback_provider: value }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {providers.map(provider => (
                    <SelectItem key={provider.name} value={provider.name}>
                      {provider.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        {/* Generation Settings */}
        {localProfile.settings && (
          <div>
            <h4 className="font-medium mb-4">Generation Settings</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <Label>Temperature</Label>
                <div className="space-y-2">
                  <Slider
                    value={[localProfile.settings.temperature || 0.7]}
                    onValueChange={([value]) => setLocalProfile(prev => ({
                      ...prev,
                      settings: { ...prev.settings, temperature: value }
                    }))}
                    min={0}
                    max={2}
                    step={0.1}
                  />
                  <div className="text-sm text-muted-foreground text-center">
                    {localProfile.settings.temperature?.toFixed(1)}
                  </div>
                </div>
              </div>

              <div>
                <Label>Max Tokens</Label>
                <div className="space-y-2">
                  <Slider
                    value={[localProfile.settings.max_tokens || 4000]}
                    onValueChange={([value]) => setLocalProfile(prev => ({
                      ...prev,
                      settings: { ...prev.settings, max_tokens: value }
                    }))}
                    min={100}
                    max={8000}
                    step={100}
                  />
                  <div className="text-sm text-muted-foreground text-center">
                    {localProfile.settings.max_tokens?.toLocaleString()}
                  </div>
                </div>
              </div>

              <div>
                <Label>Top P</Label>
                <div className="space-y-2">
                  <Slider
                    value={[localProfile.settings.top_p || 0.9]}
                    onValueChange={([value]) => setLocalProfile(prev => ({
                      ...prev,
                      settings: { ...prev.settings, top_p: value }
                    }))}
                    min={0}
                    max={1}
                    step={0.05}
                  />
                  <div className="text-sm text-muted-foreground text-center">
                    {localProfile.settings.top_p?.toFixed(2)}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Validation Errors */}
        {!validation.isValid && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Validation Errors</AlertTitle>
            <AlertDescription>
              <ul className="list-disc list-inside space-y-1">
                {validation.errors.map((error, index) => (
                  <li key={index}>{error}</li>
                ))}
              </ul>
            </AlertDescription>
          </Alert>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-2 pt-4 border-t">
          <Button variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button 
            onClick={() => onSave(localProfile)} 
            disabled={!validation.isValid || saving}
          >
            {saving ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                Save Profile
              </>
            )}
          </Button>
        </div>
      </div>
    );
  };  return
 (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Profile Management</h2>
          <p className="text-muted-foreground">
            Create and manage LLM profiles with custom routing policies and provider preferences.
          </p>
        </div>
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={() => setEditingProfile(createNewProfile())}>
              <Plus className="h-4 w-4 mr-2" />
              Create Profile
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-4xl">
            <DialogHeader>
              <DialogTitle>Create New Profile</DialogTitle>
              <DialogDescription>
                Configure a new LLM profile with custom routing and provider settings.
              </DialogDescription>
            </DialogHeader>
            {editingProfile && (
              <ProfileEditor
                profile={editingProfile}
                onSave={saveProfile}
                onCancel={() => {
                  setIsCreateDialogOpen(false);
                  setEditingProfile(null);
                }}
              />
            )}
          </DialogContent>
        </Dialog>
      </div>

      {/* Active Profile Card */}
      {activeProfile && (
        <Card className="border-l-4 border-l-primary">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {getRouterPolicyIcon(activeProfile.router_policy)}
                <div>
                  <CardTitle className="flex items-center gap-2">
                    {activeProfile.name}
                    <Badge variant="default" className="text-xs">Active</Badge>
                  </CardTitle>
                  <CardDescription>{activeProfile.description}</CardDescription>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={activeProfile.is_valid ? "outline" : "destructive"}>
                  {activeProfile.is_valid ? activeProfile.router_policy : "Invalid"}
                </Badge>
                <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
                  <DialogTrigger asChild>
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => setEditingProfile(activeProfile)}
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-4xl">
                    <DialogHeader>
                      <DialogTitle>Edit Profile</DialogTitle>
                      <DialogDescription>
                        Modify the configuration for "{activeProfile.name}".
                      </DialogDescription>
                    </DialogHeader>
                    {editingProfile && (
                      <ProfileEditor
                        profile={editingProfile}
                        onSave={saveProfile}
                        onCancel={() => {
                          setIsEditDialogOpen(false);
                          setEditingProfile(null);
                        }}
                      />
                    )}
                  </DialogContent>
                </Dialog>
              </div>
            </div>
          </CardHeader>
          
          <CardContent>
            {/* Quick Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div className="text-center">
                <div className="text-2xl font-bold">{Object.keys(activeProfile.providers).length}</div>
                <div className="text-xs text-muted-foreground">Use Cases</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">
                  {new Set(Object.values(activeProfile.providers).map(p => p.provider)).size}
                </div>
                <div className="text-xs text-muted-foreground">Providers</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">
                  {Math.round(Object.values(activeProfile.providers).reduce((sum, p) => sum + p.priority, 0) / Object.keys(activeProfile.providers).length) || 0}
                </div>
                <div className="text-xs text-muted-foreground">Avg Priority</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">
                  {activeProfile.is_valid ? '✓' : '✗'}
                </div>
                <div className="text-xs text-muted-foreground">Valid</div>
              </div>
            </div>

            {/* Provider Assignments Preview */}
            <div className="space-y-2">
              <h5 className="font-medium text-sm">Provider Assignments</h5>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                {Object.entries(activeProfile.providers).map(([useCase, config]) => (
                  <div key={useCase} className="p-2 border rounded text-sm">
                    <div className="flex items-center justify-between">
                      <span className="font-medium capitalize">{useCase.replace('_', ' ')}</span>
                      <Badge variant="outline" className="text-xs">
                        {config.priority}
                      </Badge>
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">
                      {config.provider}
                      {config.model && ` • ${config.model}`}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Validation Errors */}
            {activeProfile.validation_errors.length > 0 && (
              <Alert variant="destructive" className="mt-4">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Configuration Issues</AlertTitle>
                <AlertDescription>
                  <ul className="list-disc list-inside space-y-1">
                    {activeProfile.validation_errors.map((error, index) => (
                      <li key={index} className="text-sm">{error}</li>
                    ))}
                  </ul>
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* All Profiles List */}
      <Card>
        <CardHeader>
          <CardTitle>All Profiles</CardTitle>
          <CardDescription>
            Manage all your LLM profiles. Click to activate or use the actions menu.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {profiles.map((profile) => (
              <Card 
                key={profile.id}
                className={`cursor-pointer transition-all hover:shadow-md ${
                  activeProfile?.id === profile.id ? 'ring-2 ring-primary' : ''
                }`}
                onClick={() => onProfileChange(profile.id)}
              >
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {getRouterPolicyIcon(profile.router_policy)}
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="font-medium">{profile.name}</h4>
                          {activeProfile?.id === profile.id && (
                            <Badge variant="default" className="text-xs">Active</Badge>
                          )}
                          <Badge 
                            variant={profile.is_valid ? "outline" : "destructive"} 
                            className="text-xs"
                          >
                            {profile.is_valid ? profile.router_policy : "Invalid"}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">{profile.description}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <div className="text-right text-sm text-muted-foreground">
                        <div>{Object.keys(profile.providers).length} use cases</div>
                        <div>{new Date(profile.updated_at).toLocaleDateString()}</div>
                      </div>
                      
                      <div className="flex gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            setEditingProfile(profile);
                            setIsEditDialogOpen(true);
                          }}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            duplicateProfile(profile);
                          }}
                        >
                          <Copy className="h-4 w-4" />
                        </Button>
                        
                        {activeProfile?.id !== profile.id && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              if (confirm(`Are you sure you want to delete "${profile.name}"?`)) {
                                deleteProfile(profile.id);
                              }
                            }}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  {/* Quick preview of provider assignments */}
                  <div className="mt-3 flex flex-wrap gap-1">
                    {Object.entries(profile.providers).slice(0, 4).map(([useCase, config]) => (
                      <Badge key={useCase} variant="secondary" className="text-xs">
                        {useCase}: {config.provider}
                      </Badge>
                    ))}
                    {Object.keys(profile.providers).length > 4 && (
                      <Badge variant="outline" className="text-xs">
                        +{Object.keys(profile.providers).length - 4} more
                      </Badge>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
            
            {profiles.length === 0 && (
              <div className="text-center py-8">
                <Brain className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium mb-2">No Profiles Found</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Create your first LLM profile to get started with custom routing.
                </p>
                <Button onClick={() => {
                  setEditingProfile(createNewProfile());
                  setIsCreateDialogOpen(true);
                }}>
                  <Plus className="h-4 w-4 mr-2" />
                  Create First Profile
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}