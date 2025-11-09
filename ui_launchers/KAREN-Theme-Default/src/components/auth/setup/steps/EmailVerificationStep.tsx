'use client';

import React, { useState, useEffect } from 'react';
import type { SetupStepProps } from '../SetupWizard';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Mail, CheckCircle2, Clock, AlertCircle } from "lucide-react";

type EmailVerificationStepProps = SetupStepProps & {
  email?: string;
};

export function EmailVerificationStep({ onNext, onPrevious, email = "your email" }: EmailVerificationStepProps) {
  const [verificationCode, setVerificationCode] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);
  const [error, setError] = useState('');
  const [resendTimer, setResendTimer] = useState(0);
  const [isResending, setIsResending] = useState(false);
  const [resendSuccess, setResendSuccess] = useState(false);

  // Countdown timer for resend functionality
  useEffect(() => {
    if (resendTimer > 0) {
      const timer = setTimeout(() => setResendTimer(resendTimer - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [resendTimer]);

  const handleVerify = async () => {
    setError('');

    if (!verificationCode.trim()) {
      setError('Please enter the verification code');
      return;
    }

    if (verificationCode.length < 6) {
      setError('Verification code must be at least 6 characters');
      return;
    }

    setIsVerifying(true);

    try {
      // TODO: Implement actual API call to verify email
      // const response = await fetch('/api/auth/verify-email', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ code: verificationCode })
      // });

      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));

      // For now, accept any 6+ character code
      // TODO: Replace with actual verification logic
      onNext();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to verify email. Please try again.');
    } finally {
      setIsVerifying(false);
    }
  };

  const handleResendCode = async () => {
    setError('');
    setResendSuccess(false);
    setIsResending(true);

    try {
      // TODO: Implement actual API call to resend verification email
      // const response = await fetch('/api/auth/resend-verification', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ email })
      // });

      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      setResendSuccess(true);
      setResendTimer(60); // 60 second cooldown before allowing another resend

      // Clear success message after 5 seconds
      setTimeout(() => setResendSuccess(false), 5000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to resend verification email');
    } finally {
      setIsResending(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !isVerifying) {
      handleVerify();
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl font-bold flex items-center gap-2">
            <Mail className="h-6 w-6" />
            Verify Your Email
          </CardTitle>
          <CardDescription>
            We've sent a verification code to <strong>{email}</strong>
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <Alert>
            <Clock className="h-4 w-4" />
            <AlertDescription>
              Please check your email inbox (and spam folder) for the verification code.
              The code will expire in 30 minutes.
            </AlertDescription>
          </Alert>

          <div className="space-y-2">
            <Label htmlFor="verificationCode">Verification Code</Label>
            <Input
              id="verificationCode"
              type="text"
              placeholder="Enter 6-digit code"
              value={verificationCode}
              onChange={(e) => {
                setVerificationCode(e.target.value);
                setError('');
              }}
              onKeyPress={handleKeyPress}
              disabled={isVerifying}
              className={error ? 'border-destructive' : ''}
              aria-invalid={!!error}
              aria-describedby={error ? 'verification-error' : undefined}
              maxLength={10}
            />
            {error && (
              <p id="verification-error" className="text-sm text-destructive flex items-center gap-1">
                <AlertCircle className="h-4 w-4" />
                {error}
              </p>
            )}
          </div>

          {resendSuccess && (
            <Alert>
              <CheckCircle2 className="h-4 w-4" />
              <AlertDescription>
                Verification email has been resent successfully!
              </AlertDescription>
            </Alert>
          )}

          <div className="flex flex-col gap-2">
            <p className="text-sm text-muted-foreground">
              Didn't receive the code?
            </p>
            <Button
              variant="outline"
              onClick={handleResendCode}
              disabled={isResending || resendTimer > 0}
              className="w-fit"
            >
              {isResending ? (
                'Sending...'
              ) : resendTimer > 0 ? (
                `Resend in ${resendTimer}s`
              ) : (
                'Resend Verification Email'
              )}
            </Button>
          </div>

          <div className="flex justify-between pt-4 border-t">
            <Button
              variant="outline"
              onClick={onPrevious}
              disabled={isVerifying}
            >
              Back
            </Button>
            <Button
              onClick={handleVerify}
              disabled={isVerifying || !verificationCode.trim()}
            >
              {isVerifying ? 'Verifying...' : 'Verify & Continue'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
