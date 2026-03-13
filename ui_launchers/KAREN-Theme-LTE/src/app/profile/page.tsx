"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, User, LogOut, Settings } from 'lucide-react';

export default function ProfilePage() {
  const router = useRouter();
  const { user, isAuthenticated, logout, authState, checkAuth } = useAuth();
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  useEffect(() => {
    // Check authentication status when component mounts
    if (!isAuthenticated) {
      checkAuth();
    }
  }, [isAuthenticated, checkAuth]);

  const handleLogout = async () => {
    setIsLoggingOut(true);
    try {
      logout();
      router.push('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      setIsLoggingOut(false);
    }
  };

  const handleGoToLogin = () => {
    router.push('/login');
  };

  if (authState.isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-lg font-medium">Loading profile...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>Authentication Required</CardTitle>
            <CardDescription>
              Please log in to view your profile
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Alert>
              <AlertDescription>
                You need to be authenticated to access this page.
              </AlertDescription>
            </Alert>
            <Button 
              onClick={handleGoToLogin}
              className="w-full"
              id="go-to-login-button"
            >
              Go to Login
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Profile</h1>
          <p className="mt-2 text-gray-600">Manage your account settings and view your information</p>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {/* User Information Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                User Information
              </CardTitle>
              <CardDescription>
                Your account details and profile information
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-700">User ID</label>
                <p className="mt-1 text-sm text-gray-900 font-mono" id="user-id-display">
                  {user.userId}
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">Email Address</label>
                <p className="mt-1 text-sm text-gray-900" id="user-email-display">
                  {user.email}
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">Name</label>
                <p className="mt-1 text-sm text-gray-900" id="user-name-display">
                  {user.profile?.firstName} {user.profile?.lastName}
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">Roles</label>
                <div className="mt-1 flex flex-wrap gap-2" id="user-roles-display">
                  {user.roles.map((role) => (
                    <span
                      key={role}
                      className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                    >
                      {role}
                    </span>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Actions Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Account Actions
              </CardTitle>
              <CardDescription>
                Manage your account and session
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button
                variant="outline"
                className="w-full justify-start"
                id="edit-profile-button"
              >
                Edit Profile
              </Button>
              <Button
                variant="outline"
                className="w-full justify-start"
                id="change-password-button"
              >
                Change Password
              </Button>
              <Button
                variant="destructive"
                className="w-full justify-start"
                onClick={handleLogout}
                disabled={isLoggingOut}
                id="logout-button"
              >
                {isLoggingOut ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Logging out...
                  </>
                ) : (
                  <>
                    <LogOut className="mr-2 h-4 w-4" />
                    Log Out
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Test Credentials Info */}
        <div className="mt-8 p-4 bg-green-50 border border-green-200 rounded-md">
          <h3 className="text-sm font-medium text-green-900 mb-2">Test Session Active</h3>
          <div className="text-xs text-green-700 space-y-1">
            <p>You are currently logged in with test credentials.</p>
            <p>User ID: <strong>{user.userId}</strong></p>
            <p>Email: <strong>{user.email}</strong></p>
          </div>
        </div>
      </div>
    </div>
  );
}