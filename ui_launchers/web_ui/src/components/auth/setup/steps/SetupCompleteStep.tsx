'use client';

import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { CheckCircle, Shield, Users, Settings, ArrowRight, Sparkles } from 'lucide-react';
import type { SetupStepProps } from '../SetupWizard';

export interface SetupCompleteStepProps extends SetupStepProps {
  onComplete: () => void;
}

export const SetupCompleteStep: React.FC<SetupCompleteStepProps> = ({ 
  formData, 
  onComplete, 
  isLoading 
}) => {
  const completedFeatures = [
    {
      icon: Shield,
      title: 'Super Admin Account Created',
      description: `Your admin account (${formData.email}) is ready with full system privileges`
    },
    {
      icon: Users,
      title: 'User Management Enabled',
      description: 'You can now create and manage user accounts with different permission levels'
    },
    {
      icon: Settings,
      title: 'System Configuration Ready',
      description: 'Access system settings, security policies, and audit logging features'
    }
  ];

  const nextSteps = [
    'Set up two-factor authentication for enhanced security',
    'Configure system settings and security policies',
    'Create additional admin or user accounts as needed',
    'Review audit logging and monitoring features',
    'Customize your AI assistant preferences'
  ];

  return (
    <div className="space-y-6">
      {/* Success Header */}
      <div className="text-center space-y-4">
        <div className="flex justify-center">
          <div className="relative">
            <CheckCircle className="h-20 w-20 text-green-600 drop-shadow-lg" />
            <div className="absolute inset-0 h-20 w-20 bg-green-600/20 rounded-full blur-xl animate-pulse" />
          </div>
        </div>
        <div className="space-y-2">
          <h2 className="text-3xl font-bold text-green-600">
            Setup Complete!
          </h2>
          <p className="text-lg text-muted-foreground">
            Your AI Karen system is now ready for action
          </p>
        </div>
      </div>

      {/* Completed Features */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-center mb-4 flex items-center justify-center">
          <Sparkles className="h-5 w-5 mr-2 text-primary" />
          What's Been Set Up
        </h3>
        <div className="space-y-3">
          {completedFeatures.map((feature, index) => (
            <Card key={index} className="border-2 border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-950/20">
              <CardContent className="p-4">
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    <feature.icon className="h-6 w-6 text-green-600" />
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold text-green-900 dark:text-green-100">
                      {feature.title}
                    </h4>
                    <p className="text-sm text-green-800 dark:text-green-200 mt-1">
                      {feature.description}
                    </p>
                  </div>
                  <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Account Summary */}
      <Card className="bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800">
        <CardContent className="p-4">
          <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-3">
            Your Admin Account Details:
          </h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-blue-700 dark:text-blue-300">Email:</span>
              <span className="font-mono text-blue-900 dark:text-blue-100">{formData.email}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-blue-700 dark:text-blue-300">Name:</span>
              <span className="text-blue-900 dark:text-blue-100">{formData.full_name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-blue-700 dark:text-blue-300">Role:</span>
              <span className="font-semibold text-blue-900 dark:text-blue-100">Super Administrator</span>
            </div>
            <div className="flex justify-between">
              <span className="text-blue-700 dark:text-blue-300">Email Verified:</span>
              <span className={`font-semibold ${formData.email_verified ? 'text-green-600' : 'text-amber-600'}`}>
                {formData.email_verified ? 'Yes' : 'Pending'}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Next Steps */}
      <Card className="bg-purple-50 dark:bg-purple-950/20 border-purple-200 dark:border-purple-800">
        <CardContent className="p-4">
          <h3 className="font-semibold text-purple-900 dark:text-purple-100 mb-3">
            Recommended Next Steps:
          </h3>
          <ul className="space-y-2 text-sm text-purple-800 dark:text-purple-200">
            {nextSteps.map((step, index) => (
              <li key={index} className="flex items-start space-x-2">
                <span className="flex-shrink-0 w-5 h-5 bg-purple-600 text-white rounded-full flex items-center justify-center text-xs font-bold mt-0.5">
                  {index + 1}
                </span>
                <span>{step}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      {/* Complete Setup Button */}
      <div className="text-center pt-6">
        <Button
          onClick={onComplete}
          disabled={isLoading}
          size="lg"
          className="px-12 py-4 text-lg font-semibold bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 shadow-lg hover:shadow-xl transition-all duration-200"
        >
          {isLoading ? (
            <>
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white mr-3" />
              Finalizing Setup...
            </>
          ) : (
            <>
              <span>Enter AI Karen Dashboard</span>
              <ArrowRight className="ml-3 h-6 w-6" />
            </>
          )}
        </Button>
        <p className="text-sm text-muted-foreground mt-3">
          You'll be automatically logged in and redirected to the admin dashboard
        </p>
      </div>
    </div>
  );
};