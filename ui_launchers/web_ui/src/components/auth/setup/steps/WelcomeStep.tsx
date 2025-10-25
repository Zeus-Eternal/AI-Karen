'use client';

import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Shield, Users, Settings, CheckCircle, ArrowRight } from 'lucide-react';
import type { SetupStepProps } from '../SetupWizard';

export const WelcomeStep: React.FC<SetupStepProps> = ({ onNext, isLoading }) => {
  const features = [
    {
      icon: Shield,
      title: 'Secure Administration',
      description: 'Role-based access control with super admin privileges'
    },
    {
      icon: Users,
      title: 'User Management',
      description: 'Create and manage user accounts with different permission levels'
    },
    {
      icon: Settings,
      title: 'System Configuration',
      description: 'Configure system settings, security policies, and audit logging'
    }
  ];

  return (
    <div className="space-y-6">
      {/* Welcome Message */}
      <div className="text-center space-y-4">
        <h2 className="text-2xl font-semibold text-foreground">
          Welcome to AI Karen!
        </h2>
        <p className="text-muted-foreground text-lg leading-relaxed">
          This is your first time setting up AI Karen. We'll help you create a super admin account 
          and configure your system for secure operation.
        </p>
      </div>

      {/* Features Grid */}
      <div className="grid gap-4 md:grid-cols-1 lg:grid-cols-3">
        {features.map((feature, index) => (
          <Card key={index} className="border-2 border-muted hover:border-primary/50 transition-colors">
            <CardContent className="p-4 text-center space-y-3">
              <div className="flex justify-center">
                <feature.icon className="h-8 w-8 text-primary" />
              </div>
              <h3 className="font-semibold text-foreground">{feature.title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {feature.description}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Setup Requirements */}
      <Card className="bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800">
        <CardContent className="p-4">
          <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-3 flex items-center">
            <CheckCircle className="h-5 w-5 mr-2" />
            What you'll need:
          </h3>
          <ul className="space-y-2 text-sm text-blue-800 dark:text-blue-200">
            <li className="flex items-center">
              <CheckCircle className="h-4 w-4 mr-2 text-blue-600" />
              A valid email address for your admin account
            </li>
            <li className="flex items-center">
              <CheckCircle className="h-4 w-4 mr-2 text-blue-600" />
              A strong password (minimum 12 characters)
            </li>
            <li className="flex items-center">
              <CheckCircle className="h-4 w-4 mr-2 text-blue-600" />
              About 5 minutes to complete the setup
            </li>
          </ul>
        </CardContent>
      </Card>

      {/* Security Notice */}
      <Card className="bg-amber-50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-800">
        <CardContent className="p-4">
          <h3 className="font-semibold text-amber-900 dark:text-amber-100 mb-2 flex items-center">
            <Shield className="h-5 w-5 mr-2" />
            Security Notice
          </h3>
          <p className="text-sm text-amber-800 dark:text-amber-200 leading-relaxed">
            The super admin account you're about to create will have full system access. 
            Please use a strong, unique password and keep your credentials secure.
          </p>
        </CardContent>
      </Card>

      {/* Get Started Button */}
      <div className="text-center pt-4">
        <Button
          onClick={onNext}
          disabled={isLoading}
          size="lg"
          className="px-8 py-3 text-base font-semibold bg-gradient-to-r from-primary to-purple-600 hover:from-primary/90 hover:to-purple-600/90 shadow-lg hover:shadow-xl transition-all duration-200"
        >
          <span>Get Started</span>
          <ArrowRight className="ml-2 h-5 w-5" />
        </Button>
      </div>
    </div>
  );
};