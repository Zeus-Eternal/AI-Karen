'use client';

import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { User } from '@/types/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { X, Save, LogOut, Loader2 } from 'lucide-react';

interface UserProfileProps {
  onClose?: () => void;
}

export const UserProfile: React.FC<UserProfileProps> = ({ onClose }) => {
  const { user, logout, updateUserPreferences, isLoading } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [preferences, setPreferences] = useState(user?.preferences || {});
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');

  if (!user) {
    return null;
  }

  const handleSavePreferences = async () => {
    try {
      setIsSaving(true);
      await updateUserPreferences(preferences);
      setIsEditing(false);
      setSaveMessage('Preferences saved successfully!');
      setTimeout(() => setSaveMessage(''), 3000);
    } catch (error) {
      console.error('Failed to save preferences:', error);
      setSaveMessage('Failed to save preferences. Please try again.');
      setTimeout(() => setSaveMessage(''), 3000);
    } finally {
      setIsSaving(false);
    }
  };

  const handleLogout = () => {
    logout();
    onClose?.();
  };

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <div className="flex justify-between items-center">
          <div>
            <CardTitle className="text-2xl">User Profile</CardTitle>
            <CardDescription>Manage your account and AI preferences</CardDescription>
          </div>
          {onClose && (
            <Button variant="ghost" size="icon" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* User Info */}
        <div>
          <h3 className="text-lg font-semibold mb-4">Account Information</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-muted/50 rounded-lg">
            <div>
              <Label className="text-sm font-medium text-muted-foreground">Email</Label>
              <p className="font-medium">{user.email}</p>
            </div>
            <div>
              <Label className="text-sm font-medium text-muted-foreground">User ID</Label>
              <p className="font-mono text-sm">{user.user_id}</p>
            </div>
            <div>
              <Label className="text-sm font-medium text-muted-foreground">Roles</Label>
              <div className="flex flex-wrap gap-1 mt-1">
                {user.roles.map((role) => (
                  <Badge key={role} variant="secondary">
                    {role}
                  </Badge>
                ))}
              </div>
            </div>
            <div>
              <Label className="text-sm font-medium text-muted-foreground">Tenant ID</Label>
              <p className="font-mono text-sm">{user.tenant_id}</p>
            </div>
          </div>
        </div>

        <Separator />

        {/* AI Preferences */}
        <div>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">AI Preferences</h3>
            <Button
              variant={isEditing ? "outline" : "default"}
              size="sm"
              onClick={() => setIsEditing(!isEditing)}
            >
              {isEditing ? 'Cancel' : 'Edit'}
            </Button>
          </div>

          {saveMessage && (
            <Alert className={saveMessage.includes('success') ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}>
              <AlertDescription>{saveMessage}</AlertDescription>
            </Alert>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label>Personality Tone</Label>
              {isEditing ? (
                <Select
                  value={preferences.personalityTone}
                  onValueChange={(value) => setPreferences(prev => ({ ...prev, personalityTone: value }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="friendly">Friendly</SelectItem>
                    <SelectItem value="professional">Professional</SelectItem>
                    <SelectItem value="casual">Casual</SelectItem>
                    <SelectItem value="formal">Formal</SelectItem>
                  </SelectContent>
                </Select>
              ) : (
                <p className="capitalize p-2 bg-muted/50 rounded">{preferences.personalityTone}</p>
              )}
            </div>

            <div>
              <Label>Verbosity</Label>
              {isEditing ? (
                <Select
                  value={preferences.personalityVerbosity}
                  onValueChange={(value) => setPreferences(prev => ({ ...prev, personalityVerbosity: value }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="concise">Concise</SelectItem>
                    <SelectItem value="balanced">Balanced</SelectItem>
                    <SelectItem value="detailed">Detailed</SelectItem>
                  </SelectContent>
                </Select>
              ) : (
                <p className="capitalize p-2 bg-muted/50 rounded">{preferences.personalityVerbosity}</p>
              )}
            </div>

            <div>
              <Label>Memory Depth</Label>
              {isEditing ? (
                <Select
                  value={preferences.memoryDepth}
                  onValueChange={(value) => setPreferences(prev => ({ ...prev, memoryDepth: value }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="shallow">Shallow</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="deep">Deep</SelectItem>
                  </SelectContent>
                </Select>
              ) : (
                <p className="capitalize p-2 bg-muted/50 rounded">{preferences.memoryDepth}</p>
              )}
            </div>

            <div>
              <Label>Preferred LLM Provider</Label>
              {isEditing ? (
                <Select
                  value={preferences.preferredLLMProvider}
                  onValueChange={(value) => setPreferences(prev => ({ ...prev, preferredLLMProvider: value }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ollama">Ollama (Local)</SelectItem>
                    <SelectItem value="openai">OpenAI</SelectItem>
                    <SelectItem value="gemini">Google Gemini</SelectItem>
                    <SelectItem value="deepseek">Deepseek</SelectItem>
                    <SelectItem value="huggingface">HuggingFace</SelectItem>
                  </SelectContent>
                </Select>
              ) : (
                <p className="p-2 bg-muted/50 rounded">{preferences.preferredLLMProvider}</p>
              )}
            </div>

            <div>
              <Label>Temperature</Label>
              {isEditing ? (
                <Input
                  type="number"
                  min="0"
                  max="2"
                  step="0.1"
                  value={preferences.temperature}
                  onChange={(e) => setPreferences(prev => ({ ...prev, temperature: parseFloat(e.target.value) }))}
                />
              ) : (
                <p className="p-2 bg-muted/50 rounded">{preferences.temperature}</p>
              )}
            </div>

            <div>
              <Label>Max Tokens</Label>
              {isEditing ? (
                <Input
                  type="number"
                  min="100"
                  max="4000"
                  step="100"
                  value={preferences.maxTokens}
                  onChange={(e) => setPreferences(prev => ({ ...prev, maxTokens: parseInt(e.target.value) }))}
                />
              ) : (
                <p className="p-2 bg-muted/50 rounded">{preferences.maxTokens}</p>
              )}
            </div>
          </div>

          {isEditing && (
            <div className="mt-4">
              <Label>Custom Persona Instructions</Label>
              <Textarea
                value={preferences.customPersonaInstructions}
                onChange={(e) => setPreferences(prev => ({ ...prev, customPersonaInstructions: e.target.value }))}
                rows={3}
                placeholder="Enter custom instructions for the AI's personality and behavior..."
              />
            </div>
          )}

          {isEditing && (
            <div className="flex gap-3 mt-6">
              <Button
                onClick={handleSavePreferences}
                disabled={isSaving}
                className="flex items-center gap-2"
              >
                {isSaving ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Save className="h-4 w-4" />
                )}
                {isSaving ? 'Saving...' : 'Save Preferences'}
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  setIsEditing(false);
                  setPreferences(user.preferences);
                }}
              >
                Cancel
              </Button>
            </div>
          )}
        </div>

        <Separator />

        {/* Actions */}
        <div className="flex justify-end">
          <Button
            variant="destructive"
            onClick={handleLogout}
            className="flex items-center gap-2"
          >
            <LogOut className="h-4 w-4" />
            Sign Out
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};