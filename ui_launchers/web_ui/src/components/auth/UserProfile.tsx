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
import { X, Save, LogOut, Loader2, Key, Eye, EyeOff } from 'lucide-react';
import { authService } from '@/services/authService';

// Safe array helper to prevent .map() on undefined
const toArray = <T,>(v: T[] | null | undefined): T[] => (Array.isArray(v) ? v : []);

interface UserProfileProps {
  onClose?: () => void;
}

const ChangePasswordSection: React.FC = () => {
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false
  });
  const [passwordError, setPasswordError] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);

  const validatePassword = (password: string): string[] => {
    const errors: string[] = [];
    if (password.length < 8) errors.push('At least 8 characters');
    if (!/[A-Z]/.test(password)) errors.push('One uppercase letter');
    if (!/[a-z]/.test(password)) errors.push('One lowercase letter');
    if (!/\d/.test(password)) errors.push('One number');
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) errors.push('One special character');
    return errors;
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError('');
    setPasswordSuccess('');

    // Validation
    if (!passwordData.currentPassword) {
      setPasswordError('Current password is required');
      return;
    }

    if (!passwordData.newPassword) {
      setPasswordError('New password is required');
      return;
    }

    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setPasswordError('New passwords do not match');
      return;
    }

    const passwordErrors = validatePassword(passwordData.newPassword);
    if (passwordErrors.length > 0) {
      setPasswordError(`Password must have: ${passwordErrors.join(', ')}`);
      return;
    }

    if (passwordData.currentPassword === passwordData.newPassword) {
      setPasswordError('New password must be different from current password');
      return;
    }

    try {
      setIsUpdating(true);
      await authService.updateCredentials(undefined, passwordData.newPassword);
      setPasswordSuccess('Password updated successfully!');
      setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
      setIsChangingPassword(false);
      setTimeout(() => setPasswordSuccess(''), 3000);
    } catch (error) {
      setPasswordError(error instanceof Error ? error.message : 'Failed to update password');
    } finally {
      setIsUpdating(false);
    }
  };

  const togglePasswordVisibility = (field: 'current' | 'new' | 'confirm') => {
    setShowPasswords(prev => ({ ...prev, [field]: !prev[field] }));
  };

  const resetPasswordForm = () => {
    setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
    setPasswordError('');
    setPasswordSuccess('');
    setIsChangingPassword(false);
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Security</h3>
        <Button
          variant={isChangingPassword ? "outline" : "default"}
          size="sm"
          onClick={() => isChangingPassword ? resetPasswordForm() : setIsChangingPassword(true)}
          className="flex items-center gap-2"
        >
          <Key className="h-4 w-4" />
          {isChangingPassword ? 'Cancel' : 'Change Password'}
        </Button>
      </div>

      {passwordSuccess && (
        <Alert className="mb-4 border-green-200 bg-green-50">
          <AlertDescription>{passwordSuccess}</AlertDescription>
        </Alert>
      )}

      {isChangingPassword ? (
        <form onSubmit={handlePasswordChange} className="space-y-4 p-4 bg-muted/50 rounded-lg">
          {/* Current Password */}
          <div>
            <Label htmlFor="currentPassword">Current Password</Label>
            <div className="relative">
              <Input
                id="currentPassword"
                type={showPasswords.current ? "text" : "password"}
                value={passwordData.currentPassword}
                onChange={(e) => setPasswordData(prev => ({ ...prev, currentPassword: e.target.value }))}
                placeholder="Enter your current password"
                className="pr-10"
                required
              />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                onClick={() => togglePasswordVisibility('current')}
              >
                {showPasswords.current ? (
                  <EyeOff className="h-4 w-4 text-muted-foreground" />
                ) : (
                  <Eye className="h-4 w-4 text-muted-foreground" />
                )}
              </Button>
            </div>
          </div>

          {/* New Password */}
          <div>
            <Label htmlFor="newPassword">New Password</Label>
            <div className="relative">
              <Input
                id="newPassword"
                type={showPasswords.new ? "text" : "password"}
                value={passwordData.newPassword}
                onChange={(e) => setPasswordData(prev => ({ ...prev, newPassword: e.target.value }))}
                placeholder="Enter your new password"
                className="pr-10"
                required
              />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                onClick={() => togglePasswordVisibility('new')}
              >
                {showPasswords.new ? (
                  <EyeOff className="h-4 w-4 text-muted-foreground" />
                ) : (
                  <Eye className="h-4 w-4 text-muted-foreground" />
                )}
              </Button>
            </div>
            {passwordData.newPassword && (
              <div className="mt-2">
                <div className="text-xs text-muted-foreground mb-1">Password requirements:</div>
                <div className="grid grid-cols-2 gap-1 text-xs">
                  {validatePassword(passwordData.newPassword).map((error, index) => (
                    <div key={index} className="text-red-500">• {error}</div>
                  ))}
                  {validatePassword(passwordData.newPassword).length === 0 && (
                    <div className="text-green-600 col-span-2">• Password meets all requirements</div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Confirm Password */}
          <div>
            <Label htmlFor="confirmPassword">Confirm New Password</Label>
            <div className="relative">
              <Input
                id="confirmPassword"
                type={showPasswords.confirm ? "text" : "password"}
                value={passwordData.confirmPassword}
                onChange={(e) => setPasswordData(prev => ({ ...prev, confirmPassword: e.target.value }))}
                placeholder="Confirm your new password"
                className="pr-10"
                required
              />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                onClick={() => togglePasswordVisibility('confirm')}
              >
                {showPasswords.confirm ? (
                  <EyeOff className="h-4 w-4 text-muted-foreground" />
                ) : (
                  <Eye className="h-4 w-4 text-muted-foreground" />
                )}
              </Button>
            </div>
            {passwordData.confirmPassword && passwordData.newPassword !== passwordData.confirmPassword && (
              <div className="text-xs text-red-500 mt-1">Passwords do not match</div>
            )}
          </div>

          {passwordError && (
            <Alert variant="destructive">
              <AlertDescription>{passwordError}</AlertDescription>
            </Alert>
          )}

          <div className="flex gap-3 pt-2">
            <Button
              type="submit"
              disabled={isUpdating || validatePassword(passwordData.newPassword).length > 0 || passwordData.newPassword !== passwordData.confirmPassword}
              className="flex items-center gap-2"
            >
              {isUpdating ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Key className="h-4 w-4" />
              )}
              {isUpdating ? 'Updating...' : 'Update Password'}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={resetPasswordForm}
            >
              Cancel
            </Button>
          </div>
        </form>
      ) : (
        <div className="p-4 bg-muted/50 rounded-lg">
          <p className="text-sm text-muted-foreground">
            Keep your account secure by regularly updating your password.
          </p>
        </div>
      )}
    </div>
  );
};

export const UserProfile: React.FC<UserProfileProps> = ({ onClose }) => {
  const { user, logout } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [preferences, setPreferences] = useState({
    personalityTone: '',
    personalityVerbosity: '',
    memoryDepth: '',
    customPersonaInstructions: '',
    preferredLLMProvider: '',
    preferredModel: '',
    temperature: 0.7,
    maxTokens: 2000,
    notifications: {
      email: true,
      push: false
    },
    ui: {
      theme: 'system',
      language: 'en',
      avatarUrl: ''
    }
  });
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');

  const handleAvatarChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    setSaveMessage('Avatar upload is currently not available in simplified authentication mode.');
    setTimeout(() => setSaveMessage(''), 3000);
  };



  if (!user) {
    return null;
  }

  const handleSavePreferences = async () => {
    setSaveMessage('User preferences updates are currently not available in simplified authentication mode.');
    setTimeout(() => setSaveMessage(''), 3000);
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
              <p className="font-medium">{user.email ?? 'N/A'}</p>
            </div>
            <div>
              <Label className="text-sm font-medium text-muted-foreground">User ID</Label>
              <p className="font-mono text-sm">{user.user_id}</p>
            </div>
            <div>
              <Label className="text-sm font-medium text-muted-foreground">Roles</Label>
              <div className="flex flex-wrap gap-1 mt-1">
                {toArray(user.roles).map((role) => (
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

        {/* Change Password */}
        <ChangePasswordSection />

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
                    <SelectItem value="llama-cpp">LlamaCpp (Local)</SelectItem>
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

            <div>
              <Label>UI Theme</Label>
              {isEditing ? (
                <Select
                  value={preferences.ui.theme}
                  onValueChange={(value) => setPreferences(prev => ({
                    ...prev,
                    ui: { ...(prev as any).ui, theme: value },
                  }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="light">Light</SelectItem>
                    <SelectItem value="dark">Dark</SelectItem>
                  </SelectContent>
                </Select>
              ) : (
                <p className="capitalize p-2 bg-muted/50 rounded">{preferences.ui.theme}</p>
              )}
            </div>

            <div>
              <Label>Avatar</Label>
              {isEditing ? (
                <Input type="file" accept="image/*" onChange={handleAvatarChange} />
              ) : (
                preferences.ui.avatarUrl && (
                  <img src={preferences.ui.avatarUrl} className="h-12 w-12 rounded-full" alt="avatar" />
                )
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
                  // Reset preferences - not available in simplified mode
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
