'use client';

import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { CheckCircle2, Sparkles, ArrowRight, Shield, UserCog, Mail, Settings } from "lucide-react";
import type { SetupStepProps } from '../SetupWizard';

export type SetupCompleteStepProps = SetupStepProps & {
  onComplete: () => void | Promise<void>;
};

export function SetupCompleteStep({ onComplete, onPrevious }: SetupCompleteStepProps) {
  const [isCompleting, setIsCompleting] = useState(false);

  const handleComplete = async () => {
    setIsCompleting(true);
    try {
      await onComplete();
    } catch (error) {
      console.error('Error completing setup:', error);
      setIsCompleting(false);
    }
  };

  const completedSteps = [
    {
      icon: UserCog,
      title: "Administrator Account Created",
      description: "Your super admin account has been set up with secure credentials"
    },
    {
      icon: Mail,
      title: "Email Verified",
      description: "Your email address has been confirmed and verified"
    },
    {
      icon: Shield,
      title: "Security Configured",
      description: "Essential security settings have been applied"
    },
    {
      icon: Settings,
      title: "System Initialized",
      description: "AI-Karen is configured and ready to use"
    }
  ];

  const nextSteps = [
    "Explore the dashboard and familiarize yourself with the interface",
    "Configure additional system settings in the admin panel",
    "Set up user roles and permissions",
    "Connect integrations and extensions",
    "Review security and privacy settings"
  ];

  return (
    <div className="space-y-6">
      <Card className="border-primary/20">
        <CardHeader className="text-center space-y-4">
          <div className="flex justify-center">
            <div className="relative">
              <div className="absolute inset-0 bg-primary/20 rounded-full blur-xl"></div>
              <div className="relative bg-primary/10 rounded-full p-6">
                <Sparkles className="h-16 w-16 text-primary" />
              </div>
            </div>
          </div>
          <div>
            <CardTitle className="text-3xl font-bold">Setup Complete!</CardTitle>
            <CardDescription className="text-lg mt-2">
              Your AI-Karen instance is now ready to use
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-4">
            <h3 className="font-semibold text-lg flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-primary" />
              What We&rsquo;ve Accomplished
              What We&rsquo;ve Accomplished
              What We&rsquo;ve Accomplished
            </h3>
            <div className="grid gap-3">
              {completedSteps.map((step, index) => {
                const Icon = step.icon;
                return (
                  <div
                    key={index}
                    className="flex gap-3 p-3 rounded-lg bg-primary/5 border border-primary/10"
                  >
                    <div className="flex-shrink-0 mt-0.5">
                      <Icon className="h-5 w-5 text-primary" />
                    </div>
                    <div className="space-y-1">
                      <h4 className="font-medium text-sm">{step.title}</h4>
                      <p className="text-sm text-muted-foreground">{step.description}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="space-y-4 pt-4 border-t">
            <h3 className="font-semibold text-lg flex items-center gap-2">
              <ArrowRight className="h-5 w-5 text-primary" />
              Suggested Next Steps
            </h3>
            <ul className="space-y-2">
              {nextSteps.map((step, index) => (
                <li key={index} className="flex gap-2 text-sm text-muted-foreground">
                  <span className="text-primary mt-1">•</span>
                  <span>{step}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-muted/50 rounded-lg p-4 space-y-2">
            <h4 className="font-semibold flex items-center gap-2">
              <Shield className="h-4 w-4" />
              Security Reminder
            </h4>
            <p className="text-sm text-muted-foreground">
              Your administrator account has full system access. Keep your credentials secure
              and enable two-factor authentication in your account settings for added security.
            </p>
          </div>

          <div className="flex justify-between pt-4 border-t">
            <Button
              variant="outline"
              onClick={onPrevious}
              disabled={isCompleting}
            >
              Back
            </Button>
            <Button
              onClick={handleComplete}
              disabled={isCompleting}
              size="lg"
              className="px-8"
            >
              {isCompleting ? (
                'Finalizing...'
              ) : (
                <>
                  Enter AI-Karen
                  <ArrowRight className="ml-2 h-4 w-4" />
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
