'use client';

import * as React from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Shield, UserCog, Mail, CheckCircle } from "lucide-react";
import type { SetupStepProps } from '../SetupWizard';

type WelcomeStepProps = SetupStepProps;

export function WelcomeStep({ onNext }: WelcomeStepProps) {
  const features = [
    {
      icon: UserCog,
      title: "Create Admin Account",
      description: "Set up your super administrator account with secure credentials"
    },
    {
      icon: Mail,
      title: "Verify Email",
      description: "Confirm your email address to ensure account security"
    },
    {
      icon: Shield,
      title: "Security Configuration",
      description: "Configure essential security settings for your AI-Karen instance"
    },
    {
      icon: CheckCircle,
      title: "Complete Setup",
      description: "Finalize configuration and start using AI-Karen"
    }
  ];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-3xl font-bold">Welcome to AI-Karen</CardTitle>
          <CardDescription className="text-lg">
            Let&rsquo;s get your AI-Karen instance set up and ready to use
            Let&rsquo;s get your AI-Karen instance set up and ready to use
            Let&rsquo;s get your AI-Karen instance set up and ready to use
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
            You&rsquo;ll create your super administrator account, verify your email, and configure
          <p className="text-muted-foreground">
            You&rsquo;ll create your super administrator account, verify your email, and configure
            This setup wizard will guide you through the initial configuration process.
            You&rsquo;ll create your super administrator account, verify your email, and configure
            essential security settings.
          </p>

          <div className="grid gap-4 md:grid-cols-2">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <div key={index} className="flex gap-3 p-4 rounded-lg border bg-card">
                  <div className="flex-shrink-0">
                    <Icon className="h-6 w-6 text-primary" />
                  </div>
                  <div className="space-y-1">
                    <h3 className="font-semibold">{feature.title}</h3>
                    <p className="text-sm text-muted-foreground">{feature.description}</p>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="bg-muted/50 rounded-lg p-4 space-y-2">
            <h4 className="font-semibold flex items-center gap-2">
              <Shield className="h-4 w-4" />
              Important Security Note
            </h4>
            <p className="text-sm text-muted-foreground">
              The account you create will have full administrative privileges.
              Please use a strong, unique password and keep your credentials secure.
            </p>
          </div>

          <div className="flex justify-end pt-4">
            <Button onClick={onNext} size="lg" className="px-8">
              Get Started
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
