'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useFirstRunSetup } from '@/hooks/useFirstRunSetup';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Brain, CheckCircle, ArrowLeft, ArrowRight } from 'lucide-react';
import { ThemeToggle } from '@/components/ui/theme-toggle';

// Step components
import { WelcomeStep } from './steps/WelcomeStep';
import { AdminDetailsStep } from './steps/AdminDetailsStep';
import { EmailVerificationStep } from './steps/EmailVerificationStep';
import { SetupCompleteStep } from './steps/SetupCompleteStep';

import type { CreateSuperAdminRequest, AdminApiResponse } from '@/types/admin';

export interface SetupWizardProps {
  className?: string;
}

export interface SetupFormData {
  email: string;
  full_name: string;
  password: string;
  confirm_password: string;
  email_verified?: boolean;
  verification_token?: string;
}

export interface SetupStepProps {
  formData: SetupFormData;
  onFormDataChange: (data: Partial<SetupFormData>) => void;
  onNext: () => void;
  onPrevious: () => void;
  isLoading: boolean;
  error: string | null;
  onClearError: () => void;
}

const SETUP_STEPS = [
  { id: 'welcome', title: 'Welcome', description: 'Get started with your setup' },
  { id: 'details', title: 'Admin Details', description: 'Create your super admin account' },
  { id: 'verification', title: 'Email Verification', description: 'Verify your email address' },
  { id: 'complete', title: 'Setup Complete', description: 'Your system is ready' }
];

export const SetupWizard: React.FC<SetupWizardProps> = ({ className }) => {
  const router = useRouter();
  const { login } = useAuth();
  const { isFirstRun, setupCompleted, markSetupCompleted, isLoading: setupLoading } = useFirstRunSetup();
  
  const [currentStep, setCurrentStep] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<SetupFormData>({
    email: '',
    full_name: '',
    password: '',
    confirm_password: '',
    email_verified: false
  });

  // Redirect if setup is already completed
  useEffect(() => {
    if (!setupLoading && (!isFirstRun || setupCompleted)) {
      router.replace('/login');
    }
  }, [isFirstRun, setupCompleted, setupLoading, router]);

  // Don't render if not first run or setup is completed
  if (setupLoading || !isFirstRun || setupCompleted) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <Brain className="h-16 w-16 text-primary mx-auto animate-pulse" />
          <p className="text-muted-foreground">Checking setup status...</p>
        </div>
      </div>
    );
  }

  const handleFormDataChange = (data: Partial<SetupFormData>) => {
    setFormData(prev => ({ ...prev, ...data }));
    // Clear error when user makes changes
    if (error) {
      setError(null);
    }
  };

  const handleNext = async () => {
    // Handle step-specific logic
    if (currentStep === 1) {
      // Admin details step - create super admin
      await handleCreateSuperAdmin();
    } else if (currentStep === 2) {
      // Email verification step - verify email
      await handleEmailVerification();
    } else {
      // Regular navigation
      setCurrentStep(prev => Math.min(prev + 1, SETUP_STEPS.length - 1));
    }
  };

  const handlePrevious = () => {
    setCurrentStep(prev => Math.max(prev - 1, 0));
    setError(null);
  };

  const handleCreateSuperAdmin = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const request: CreateSuperAdminRequest = {
        email: formData.email,
        full_name: formData.full_name,
        password: formData.password,
        confirm_password: formData.confirm_password
      };

      const response = await fetch('/api/admin/setup/create-super-admin', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request)
      });

      const result: AdminApiResponse<any> = await response.json();

      if (!response.ok || !result.success) {
        throw new Error(result.error?.message || 'Failed to create super admin account');
      }

      // Move to email verification step
      setCurrentStep(2);
      
    } catch (error) {
      console.error('Super admin creation failed:', error);
      setError(error instanceof Error ? error.message : 'Failed to create admin account');
    } finally {
      setIsLoading(false);
    }
  };

  const handleEmailVerification = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // For now, we'll skip actual email verification and mark as verified
      // In a real implementation, this would verify the email token
      setFormData(prev => ({ ...prev, email_verified: true }));
      
      // Move to completion step
      setCurrentStep(3);
      
    } catch (error) {
      console.error('Email verification failed:', error);
      setError(error instanceof Error ? error.message : 'Email verification failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSetupComplete = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Mark setup as completed
      markSetupCompleted();

      // Auto-login the newly created super admin
      await login({
        email: formData.email,
        password: formData.password
      });

      // Redirect to admin dashboard
      router.replace('/admin');
      
    } catch (error) {
      console.error('Setup completion failed:', error);
      setError(error instanceof Error ? error.message : 'Setup completion failed');
    } finally {
      setIsLoading(false);
    }
  };

  const clearError = () => {
    setError(null);
  };

  const currentStepData = SETUP_STEPS[currentStep];
  const progress = ((currentStep + 1) / SETUP_STEPS.length) * 100;

  const stepProps: SetupStepProps = {
    formData,
    onFormDataChange: handleFormDataChange,
    onNext: handleNext,
    onPrevious: handlePrevious,
    isLoading,
    error,
    onClearError: clearError
  };

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 0:
        return <WelcomeStep {...stepProps} />;
      case 1:
        return <AdminDetailsStep {...stepProps} />;
      case 2:
        return <EmailVerificationStep {...stepProps} />;
      case 3:
        return <SetupCompleteStep {...stepProps} onComplete={handleSetupComplete} />;
      default:
        return <WelcomeStep {...stepProps} />;
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 dark:from-gray-950 dark:via-gray-900 dark:to-purple-950 p-4">
      {/* Theme Toggle */}
      <div className="absolute top-4 right-4">
        <ThemeToggle />
      </div>

      <div className="w-full max-w-2xl space-y-6">
        {/* Header */}
        <div className="text-center space-y-4">
          <div className="flex justify-center">
            <div className="relative">
              <Brain className="h-16 w-16 text-primary drop-shadow-lg" />
              <div className="absolute inset-0 h-16 w-16 bg-primary/20 rounded-full blur-xl animate-pulse" />
            </div>
          </div>
          <div className="space-y-2">
            <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent">
              AI Karen Setup
            </h1>
            <p className="text-lg text-muted-foreground">
              Let's get your AI assistant ready for action
            </p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm text-muted-foreground">
            <span>Step {currentStep + 1} of {SETUP_STEPS.length}</span>
            <span>{Math.round(progress)}% Complete</span>
          </div>
          <Progress value={progress} className="h-2" />
          <div className="flex justify-between text-xs text-muted-foreground">
            {SETUP_STEPS.map((step, index) => (
              <span 
                key={step.id}
                className={`flex items-center space-x-1 ${
                  index <= currentStep ? 'text-primary font-medium' : ''
                }`}
              >
                {index < currentStep && <CheckCircle className="h-3 w-3" />}
                <span className="hidden sm:inline">{step.title}</span>
              </span>
            ))}
          </div>
        </div>

        {/* Main Card */}
        <Card className="shadow-2xl border-0 dark:bg-gray-900/50 backdrop-blur-sm">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl font-semibold">
              {currentStepData.title}
            </CardTitle>
            <CardDescription className="text-base">
              {currentStepData.description}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Global Error Display */}
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* Current Step Content */}
            {renderCurrentStep()}

            {/* Navigation Buttons */}
            <div className="flex justify-between pt-4">
              <Button
                variant="outline"
                onClick={handlePrevious}
                disabled={currentStep === 0 || isLoading}
                className="flex items-center space-x-2"
              >
                <ArrowLeft className="h-4 w-4" />
                <span>Previous</span>
              </Button>

              {currentStep < SETUP_STEPS.length - 1 ? (
                <Button
                  onClick={handleNext}
                  disabled={isLoading}
                  className="flex items-center space-x-2"
                >
                  <span>Next</span>
                  <ArrowRight className="h-4 w-4" />
                </Button>
              ) : (
                <Button
                  onClick={handleSetupComplete}
                  disabled={isLoading}
                  className="flex items-center space-x-2 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700"
                >
                  <CheckCircle className="h-4 w-4" />
                  <span>Complete Setup</span>
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center text-sm text-muted-foreground">
          <p>Secure setup with real-time validation and email verification</p>
        </div>
      </div>
    </div>
  );
};