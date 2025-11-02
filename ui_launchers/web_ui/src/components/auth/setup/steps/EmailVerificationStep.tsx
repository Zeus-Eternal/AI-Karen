'use client';
import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Mail, CheckCircle, Clock, RefreshCw, AlertTriangle } from 'lucide-react';
import type { SetupStepProps } from '../SetupWizard';
export const EmailVerificationStep: React.FC<SetupStepProps> = ({ 
  formData, 
  onFormDataChange, 
  onNext, 
  isLoading, 
  error, 
  onClearError 
}) => {
  const [verificationCode, setVerificationCode] = useState('');
  const [isResending, setIsResending] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);
  const [verificationSent, setVerificationSent] = useState(false);
  // Simulate sending verification email on mount
  useEffect(() => {
    if (!verificationSent) {
      sendVerificationEmail();
    }
  }, [verificationSent]);
  // Cooldown timer
  useEffect(() => {
    if (resendCooldown > 0) {
      const timer = setTimeout(() => {
        setResendCooldown(resendCooldown - 1);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [resendCooldown]);
  const sendVerificationEmail = async () => {
    try {
      setIsResending(true);
      onClearError();
      // Simulate API call to send verification email
      await new Promise(resolve => setTimeout(resolve, 1000));
      setVerificationSent(true);
      setResendCooldown(60); // 60 second cooldown
    } catch (error) {
    } finally {
      setIsResending(false);
    }
  };
  const handleVerificationCodeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, '').slice(0, 6); // Only digits, max 6
    setVerificationCode(value);
    onClearError();
  };
  const handleVerifyEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    if (verificationCode.length !== 6) {
      return;
    }
    // For demo purposes, accept any 6-digit code
    // In real implementation, this would verify against the server
    onFormDataChange({ 
      email_verified: true, 
      verification_token: verificationCode 
    });
    onNext();
  };
  const handleSkipVerification = () => {
    // Allow skipping for demo purposes
    // In production, this might not be allowed
    onFormDataChange({ email_verified: false });
    onNext();
  };
  return (
    <div className="space-y-6">
      {/* Email Sent Confirmation */}
      <Card className="bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800">
        <CardContent className="p-4 text-center space-y-3 sm:p-4 md:p-6">
          <div className="flex justify-center">
            <Mail className="h-12 w-12 text-blue-600 sm:w-auto md:w-full" />
          </div>
          <h3 className="font-semibold text-blue-900 dark:text-blue-100">
            Verification Email Sent
          </h3>
          <p className="text-blue-800 dark:text-blue-200">
            We've sent a verification code to:
          </p>
          <p className="font-mono text-lg font-semibold text-blue-900 dark:text-blue-100">
            {formData.email}
          </p>
          <p className="text-sm text-blue-700 dark:text-blue-300 md:text-base lg:text-lg">
            Please check your inbox and enter the 6-digit verification code below.
          </p>
        </CardContent>
      </Card>
      {/* Verification Code Input */}
      <form onSubmit={handleVerifyEmail} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="verification_code" className="text-center block">
            Verification Code
          </Label>
          <div className="flex justify-center">
            <input
              id="verification_code"
              type="text"
              placeholder="000000"
              value={verificationCode}
              onChange={handleVerificationCodeChange}
              disabled={isLoading}
              maxLength={6}
              className="text-center text-2xl font-mono tracking-widest w-48 h-14 sm:w-auto md:w-full"
              autoComplete="one-time-code" />
          </div>
          <p className="text-sm text-muted-foreground text-center md:text-base lg:text-lg">
            Enter the 6-digit code from your email
          </p>
        </div>
        {/* Verify Button */}
        <div className="text-center">
          <button
            type="submit"
            disabled={verificationCode.length !== 6 || isLoading}
            className="px-8 py-3 text-base font-semibold"
           aria-label="Submit form">
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2 sm:w-auto md:w-full" />
                Verifying...
              </>
            ) : (
              <>
                <CheckCircle className="mr-2 h-5 w-5 sm:w-auto md:w-full" />
                Verify Email
              </>
            )}
          </Button>
        </div>
      </form>
      {/* Resend Email */}
      <div className="text-center space-y-3">
        <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
          Didn't receive the email?
        </p>
        <button
          variant="outline"
          onClick={sendVerificationEmail}
          disabled={isResending || resendCooldown  aria-label="Button"> 0}
          className="flex items-center space-x-2"
        >
          {isResending ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current sm:w-auto md:w-full" />
              <span>Sending...</span>
            </>
          ) : resendCooldown > 0 ? (
            <>
              <Clock className="h-4 w-4 sm:w-auto md:w-full" />
              <span>Resend in {resendCooldown}s</span>
            </>
          ) : (
            <>
              <RefreshCw className="h-4 w-4 sm:w-auto md:w-full" />
              <span>Resend Email</span>
            </>
          )}
        </Button>
      </div>
      {/* Email Tips */}
      <Card className="bg-amber-50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-800">
        <CardContent className="p-4 sm:p-4 md:p-6">
          <h3 className="font-semibold text-amber-900 dark:text-amber-100 mb-2 flex items-center">
            <AlertTriangle className="h-5 w-5 mr-2 sm:w-auto md:w-full" />
            Can't find the email?
          </h3>
          <ul className="text-sm text-amber-800 dark:text-amber-200 space-y-1 md:text-base lg:text-lg">
            <li>• Check your spam or junk folder</li>
            <li>• Make sure you entered the correct email address</li>
            <li>• Wait a few minutes - emails can sometimes be delayed</li>
            <li>• Check if your email provider is blocking automated emails</li>
          </ul>
        </CardContent>
      </Card>
      {/* Skip Option (for demo) */}
      <div className="text-center pt-4 border-t border-muted">
        <p className="text-sm text-muted-foreground mb-3 md:text-base lg:text-lg">
          For demo purposes, you can skip email verification
        </p>
        <button
          variant="ghost"
          onClick={handleSkipVerification}
          disabled={isLoading}
          className="text-muted-foreground hover:text-foreground"
         aria-label="Button">
          Skip Verification (Demo Only)
        </Button>
      </div>
    </div>
  );
};
