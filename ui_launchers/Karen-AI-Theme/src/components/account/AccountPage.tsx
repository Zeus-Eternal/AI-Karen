
"use client";

import { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { User, Mail, Camera, Save, Lock, LogOut, Sun, Moon } from 'lucide-react';
import { Separator } from '@/components/ui/separator';
import { useTheme } from '@/firebase';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { ApiError, apiClient } from '@/lib/api';
import { authService } from '@/lib/auth';
import { useAuth } from '@/lib/useAuth';
import { useRouter } from 'next/navigation';
import { useToast } from '@/hooks/use-toast';

interface AccountUser {
  user_id: string;
  email: string;
  full_name: string;
  roles: string[];
  is_active: boolean;
  created_at: string;
  last_login?: string | null;
  tenant_id: string;
  preferences: Record<string, any>;
  avatarUrl?: string;
}

interface PasswordPayloadResponse {
  detail: string;
}

const emptyAccountUser: AccountUser = {
  user_id: '',
  email: '',
  full_name: '',
  roles: [],
  is_active: true,
  created_at: '',
  last_login: null,
  tenant_id: '',
  preferences: {},
  avatarUrl: '',
};

const getInitials = (name: string) => {
    if (!name.trim()) return 'KA';
    const names = name.split(' ');
    if (names.length === 1) return names[0].charAt(0).toUpperCase();
    return (names[0].charAt(0) + names[names.length - 1].charAt(0)).toUpperCase();
}

const formatDisplayDate = (value?: string | null) => {
    if (!value) return 'Never';

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return 'Unknown';
    }

    return date.toLocaleString();
}

const formatRoleLabel = (roles: string[]) => {
    if (!roles.length) return 'User';
    return roles
        .map((role) => role.replace(/_/g, ' '))
        .map((role) => role.charAt(0).toUpperCase() + role.slice(1))
        .join(', ');
}

export default function AccountPage() {
    const router = useRouter();
    const { toast } = useToast();
    const { logout } = useAuth();
    const { theme, setTheme } = useTheme();
    const [account, setAccount] = useState<AccountUser>(emptyAccountUser);
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [isLoading, setIsLoading] = useState(true);
    const [isProfileSaving, setIsProfileSaving] = useState(false);
    const [isPasswordSaving, setIsPasswordSaving] = useState(false);
    const [isLoggingOut, setIsLoggingOut] = useState(false);

    useEffect(() => {
        let isMounted = true;

        const loadAccount = async () => {
            try {
                setIsLoading(true);
                const currentUser = await apiClient.get<AccountUser>('/api/auth/me');
                if (!isMounted) {
                    return;
                }

                setAccount(currentUser);
                setName(currentUser.full_name || '');
                setEmail(currentUser.email || '');
                authService.updateCurrentUser(currentUser);

                const preferredTheme = currentUser.preferences?.theme;
                if ((preferredTheme === 'light' || preferredTheme === 'dark') && preferredTheme !== theme) {
                    setTheme(preferredTheme);
                }
            } catch (error) {
                if (!isMounted) {
                    return;
                }

                if (error instanceof ApiError && error.status === 401) {
                    authService.clearAuth();
                    router.replace('/login');
                    return;
                }

                toast({
                    title: 'Failed to load account',
                    description: error instanceof Error ? error.message : 'Unable to load account details.',
                    variant: 'destructive',
                });
            } finally {
                if (isMounted) {
                    setIsLoading(false);
                }
            }
        };

        loadAccount();

        return () => {
            isMounted = false;
        };
    }, [router, setTheme, theme, toast]);

    const syncAccount = (nextAccount: AccountUser) => {
        setAccount(nextAccount);
        setName(nextAccount.full_name || '');
        setEmail(nextAccount.email || '');
        authService.updateCurrentUser({
            ...nextAccount,
            permissions: authService.getCurrentUser()?.permissions,
        });
    };

    const handleProfileSave = async () => {
        try {
            setIsProfileSaving(true);
            const updatedAccount = await apiClient.put<AccountUser>('/api/auth/me', {
                full_name: name,
                email,
            });
            syncAccount(updatedAccount);
            toast({
                title: 'Profile updated',
                description: 'Your account details have been saved.',
            });
        } catch (error) {
            toast({
                title: 'Profile update failed',
                description: error instanceof Error ? error.message : 'Unable to save profile changes.',
                variant: 'destructive',
            });
        } finally {
            setIsProfileSaving(false);
        }
    };

    const handleThemeChange = async (value: 'light' | 'dark') => {
        const previousTheme = theme;
        setTheme(value);

        try {
            const updatedAccount = await apiClient.put<AccountUser>('/api/auth/me', {
                preferences: {
                    theme: value,
                },
            });
            syncAccount(updatedAccount);
        } catch (error) {
            setTheme(previousTheme);
            toast({
                title: 'Theme update failed',
                description: error instanceof Error ? error.message : 'Unable to save theme preference.',
                variant: 'destructive',
            });
        }
    };

    const handlePasswordUpdate = async () => {
        if (!currentPassword || !newPassword || !confirmPassword) {
            toast({
                title: 'Missing password fields',
                description: 'Fill in all password fields before updating.',
                variant: 'destructive',
            });
            return;
        }

        try {
            setIsPasswordSaving(true);
            const response = await apiClient.post<PasswordPayloadResponse>('/api/auth/change-password', {
                current_password: currentPassword,
                new_password: newPassword,
                confirm_password: confirmPassword,
            });
            setCurrentPassword('');
            setNewPassword('');
            setConfirmPassword('');
            toast({
                title: 'Password updated',
                description: response.detail,
            });
        } catch (error) {
            toast({
                title: 'Password update failed',
                description: error instanceof Error ? error.message : 'Unable to update password.',
                variant: 'destructive',
            });
        } finally {
            setIsPasswordSaving(false);
        }
    };

    const handleLogout = async () => {
        try {
            setIsLoggingOut(true);
            await logout();
            router.replace('/login');
        } catch (error) {
            toast({
                title: 'Logout failed',
                description: error instanceof Error ? error.message : 'Unable to log out.',
                variant: 'destructive',
            });
        } finally {
            setIsLoggingOut(false);
        }
    };

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-semibold tracking-tight">My Account</h2>
                <p className="text-sm text-muted-foreground">
                    View and manage your profile, security, and notification settings.
                </p>
            </div>
            <Separator />
            <div className="grid gap-8 md:grid-cols-3">
                {/* Left Column for Profile Info */}
                <div className="md:col-span-1 space-y-8">
                     <Card>
                        <CardHeader className="items-center text-center">
                            <div className="relative">
                                <Avatar className="h-24 w-24 mb-2">
                                    <AvatarImage src={account.avatarUrl || ''} alt={name} />
                                    <AvatarFallback className="text-3xl">{getInitials(name)}</AvatarFallback>
                                </Avatar>
                                <Button variant="outline" size="icon" className="absolute bottom-0 right-0 rounded-full h-8 w-8">
                                    <Camera className="h-4 w-4" />
                                    <span className="sr-only">Change photo</span>
                                </Button>
                            </div>
                            <CardTitle className="text-xl">{name}</CardTitle>
                            <CardDescription>{formatRoleLabel(account.roles)}</CardDescription>
                        </CardHeader>
                        <CardContent className="text-sm text-muted-foreground text-center">
                            <p>Account created: {formatDisplayDate(account.created_at)}</p>
                            <p>Last login: {formatDisplayDate(account.last_login)}</p>
                        </CardContent>
                         <CardFooter>
                            <Button variant="outline" className="w-full" onClick={handleLogout} disabled={isLoggingOut}>
                                <LogOut className="mr-2 h-4 w-4" />
                                {isLoggingOut ? 'Logging out...' : 'Logout'}
                            </Button>
                        </CardFooter>
                    </Card>
                </div>

                {/* Right Column for Settings */}
                <div className="md:col-span-2 space-y-8">
                    <Card>
                        <CardHeader>
                            <CardTitle>Profile Information</CardTitle>
                            <CardDescription>Update your personal details here.</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-2">
                                <Label htmlFor="name">Full Name</Label>
                                <div className="relative">
                                    <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                    <Input id="name" value={name} onChange={(e) => setName(e.target.value)} className="pl-10" disabled={isLoading || isProfileSaving} />
                                </div>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="email">Email Address</Label>
                                <div className="relative">
                                     <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                    <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="pl-10" disabled={isLoading || isProfileSaving} />
                                </div>
                            </div>
                        </CardContent>
                        <CardFooter className="border-t pt-6">
                            <Button onClick={handleProfileSave} disabled={isLoading || isProfileSaving}>
                                <Save className="mr-2 h-4 w-4"/>
                                {isProfileSaving ? 'Saving...' : 'Save Changes'}
                            </Button>
                        </CardFooter>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle>Display Settings</CardTitle>
                            <CardDescription>Choose your preferred theme.</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <RadioGroup
                                value={theme}
                                onValueChange={(value: 'light' | 'dark') => void handleThemeChange(value)}
                                className="grid grid-cols-2 gap-4"
                            >
                                <div>
                                    <RadioGroupItem value="light" id="light" className="peer sr-only" />
                                    <Label
                                        htmlFor="light"
                                        className="flex flex-col items-center justify-between rounded-md border-2 border-muted bg-popover p-4 hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-primary [&:has([data-state=checked])]:border-primary"
                                    >
                                        <Sun className="mb-3 h-6 w-6" />
                                        Light
                                    </Label>
                                </div>
                                <div>
                                    <RadioGroupItem value="dark" id="dark" className="peer sr-only" />
                                    <Label
                                        htmlFor="dark"
                                        className="flex flex-col items-center justify-between rounded-md border-2 border-muted bg-popover p-4 hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-primary [&:has([data-state=checked])]:border-primary"
                                    >
                                        <Moon className="mb-3 h-6 w-6" />
                                        Dark
                                    </Label>
                                </div>
                            </RadioGroup>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle>Security Settings</CardTitle>
                            <CardDescription>Manage your password and security preferences.</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                             <div className="space-y-2">
                                <Label htmlFor="current-password">Current Password</Label>
                                <Input id="current-password" type="password" placeholder="••••••••" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} disabled={isPasswordSaving} />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="new-password">New Password</Label>
                                <Input id="new-password" type="password" placeholder="••••••••" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} disabled={isPasswordSaving} />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="confirm-password">Confirm New Password</Label>
                                <Input id="confirm-password" type="password" placeholder="••••••••" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} disabled={isPasswordSaving} />
                            </div>
                        </CardContent>
                        <CardFooter className="border-t pt-6">
                            <Button onClick={handlePasswordUpdate} disabled={isPasswordSaving}>
                                <Lock className="mr-2 h-4 w-4"/>
                                {isPasswordSaving ? 'Updating...' : 'Update Password'}
                            </Button>
                        </CardFooter>
                    </Card>
                </div>
            </div>
        </div>
    );
}
