'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Eye, EyeOff, CheckCircle, XCircle, AlertTriangle, User, Mail, Lock } from 'lucide-react';
import { validateSuperAdminCreation, calculatePasswordStrength } from '@/lib/auth/setup-validation';
import type { SetupStepProps } from '../SetupWizard';
import type { SetupValidationErrors } from '@/types/admin';

export const AdminDetailsStep: React.FC<SetupStepProps> = ({ 
  formData, 
  onFormDataChange, 
  onNext, 
  isLoading, 
  error, 
  onClearError 
}) => {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [validationErrors, setValidationErrors] = useState<SetupValidationErrors>({});
  const [passwordStrength, setPasswordStrength] = useState<{
    score: number;
    level: 'very_weak' | 'weak' | 'medium' | 'strong' | 'very_strong';
    feedback: string[];
  } | null>(null);

  // Real-time validation
  useEffect(() => {
    const validateForm = async () => {
      if (formData.email || formData.full_name || formData.password || formData.confirm_password) {
        const validation = await validateSuperAdminCreation({
          email: formData.email,
          full_name: formData.full_name,
          password: formData.password,
          confirm_password: formData.confirm_password
        });
        
        setValidationErrors(validation.errors);
      }
    };

    validateForm();
  }, [formData]);

  // Password strength calculation
  useEffect(() => {
    if (formData.password) {
      const strength = calculatePasswordStrength(formData.password);
      setPasswordStrength(strength);
    } else {
      setPasswordStrength(null);
    }
  }, [formData.password]);

  const handleInputChange = (field: keyof typeof formData) => (e: React.ChangeEvent<HTMLInputElement>) => {
    onFormDataChange({ [field]: e.target.value });
    onClearError();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Final validation before submission
    const validation = await validateSuperAdminCreation({
      email: formData.email,
      full_name: formData.full_name,
      password: formData.password,
      confirm_password: formData.confirm_password
    });

    if (!validation.isValid) {
      setValidationErrors(validation.errors);
      return;
    }

    onNext();
  };

  const isFormValid = Object.keys(validationErrors).length === 0 && 
                     formData.email && 
                     formData.full_name && 
                     formData.password && 
                     formData.confirm_password;

  const getPasswordStrengthColor = (level: string) => {
    switch (level) {
      case 'very_weak': return 'bg-red-500';
      case 'weak': return 'bg-orange-500';
      case 'medium': return 'bg-yellow-500';
      case 'strong': return 'bg-blue-500';
      case 'very_strong': return 'bg-green-500';
      default: return 'bg-gray-300';
    }
  };

  const getPasswordStrengthText = (level: string) => {
    switch (level) {
      case 'very_weak': return 'Very Weak';
      case 'weak': return 'Weak';
      case 'medium': return 'Medium';
      case 'strong': return 'Strong';
      case 'very_strong': return 'Very Strong';
      default: return '';
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Full Name Field */}
      <div className="space-y-2">
        <Label htmlFor="full_name" className="flex items-center space-x-2">
          <User className="h-4 w-4" />
          <span>Full Name</span>
        </Label>
        <Input
          id="full_name"
          type="text"
          placeholder="Enter your full name"
          value={formData.full_name}
          onChange={handleInputChange('full_name')}
          disabled={isLoading}
          required
          autoComplete="name"
          className={validationErrors.full_name ? 'border-red-500 focus:border-red-500' : ''}
        />
        {validationErrors.full_name && (
          <p className="text-sm text-red-600 flex items-center space-x-1">
            <XCircle className="h-4 w-4" />
            <span>{validationErrors.full_name}</span>
          </p>
        )}
      </div>

      {/* Email Field */}
      <div className="space-y-2">
        <Label htmlFor="email" className="flex items-center space-x-2">
          <Mail className="h-4 w-4" />
          <span>Email Address</span>
        </Label>
        <Input
          id="email"
          type="email"
          placeholder="admin@yourcompany.com"
          value={formData.email}
          onChange={handleInputChange('email')}
          disabled={isLoading}
          required
          autoComplete="email"
          className={validationErrors.email ? 'border-red-500 focus:border-red-500' : ''}
        />
        {validationErrors.email && (
          <p className="text-sm text-red-600 flex items-center space-x-1">
            <XCircle className="h-4 w-4" />
            <span>{validationErrors.email}</span>
          </p>
        )}
        <p className="text-sm text-muted-foreground">
          This will be your super admin login email
        </p>
      </div>

      {/* Password Field */}
      <div className="space-y-2">
        <Label htmlFor="password" className="flex items-center space-x-2">
          <Lock className="h-4 w-4" />
          <span>Password</span>
        </Label>
        <div className="relative">
          <Input
            id="password"
            type={showPassword ? 'text' : 'password'}
            placeholder="Create a strong password"
            value={formData.password}
            onChange={handleInputChange('password')}
            disabled={isLoading}
            required
            autoComplete="new-password"
            className={`pr-10 ${validationErrors.password ? 'border-red-500 focus:border-red-500' : ''}`}
          />
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
            onClick={() => setShowPassword(!showPassword)}
            disabled={isLoading}
          >
            {showPassword ? (
              <EyeOff className="h-4 w-4 text-muted-foreground" />
            ) : (
              <Eye className="h-4 w-4 text-muted-foreground" />
            )}
          </Button>
        </div>
        
        {/* Password Strength Indicator */}
        {passwordStrength && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Password Strength:</span>
              <span className={`font-medium ${
                passwordStrength.level === 'very_strong' ? 'text-green-600' :
                passwordStrength.level === 'strong' ? 'text-blue-600' :
                passwordStrength.level === 'medium' ? 'text-yellow-600' :
                passwordStrength.level === 'weak' ? 'text-orange-600' :
                'text-red-600'
              }`}>
                {getPasswordStrengthText(passwordStrength.level)}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-300 ${getPasswordStrengthColor(passwordStrength.level)}`}
                style={{ width: `${Math.max((passwordStrength.score / 8) * 100, 10)}%` }}
              />
            </div>
            {passwordStrength.feedback.length > 0 && (
              <div className="text-sm text-muted-foreground">
                <p className="font-medium mb-1">Suggestions:</p>
                <ul className="list-disc list-inside space-y-1">
                  {passwordStrength.feedback.slice(0, 3).map((feedback, index) => (
                    <li key={index}>{feedback}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
        
        {validationErrors.password && (
          <p className="text-sm text-red-600 flex items-center space-x-1">
            <XCircle className="h-4 w-4" />
            <span>{validationErrors.password}</span>
          </p>
        )}
      </div>

      {/* Confirm Password Field */}
      <div className="space-y-2">
        <Label htmlFor="confirm_password" className="flex items-center space-x-2">
          <Lock className="h-4 w-4" />
          <span>Confirm Password</span>
        </Label>
        <div className="relative">
          <Input
            id="confirm_password"
            type={showConfirmPassword ? 'text' : 'password'}
            placeholder="Confirm your password"
            value={formData.confirm_password}
            onChange={handleInputChange('confirm_password')}
            disabled={isLoading}
            required
            autoComplete="new-password"
            className={`pr-10 ${validationErrors.confirm_password ? 'border-red-500 focus:border-red-500' : ''}`}
          />
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
            disabled={isLoading}
          >
            {showConfirmPassword ? (
              <EyeOff className="h-4 w-4 text-muted-foreground" />
            ) : (
              <Eye className="h-4 w-4 text-muted-foreground" />
            )}
          </Button>
        </div>
        
        {/* Password Match Indicator */}
        {formData.password && formData.confirm_password && (
          <div className="flex items-center space-x-2 text-sm">
            {formData.password === formData.confirm_password ? (
              <>
                <CheckCircle className="h-4 w-4 text-green-600" />
                <span className="text-green-600">Passwords match</span>
              </>
            ) : (
              <>
                <XCircle className="h-4 w-4 text-red-600" />
                <span className="text-red-600">Passwords do not match</span>
              </>
            )}
          </div>
        )}
        
        {validationErrors.confirm_password && (
          <p className="text-sm text-red-600 flex items-center space-x-1">
            <XCircle className="h-4 w-4" />
            <span>{validationErrors.confirm_password}</span>
          </p>
        )}
      </div>

      {/* Password Requirements */}
      <Card className="bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800">
        <CardContent className="p-4">
          <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-3 flex items-center">
            <AlertTriangle className="h-5 w-5 mr-2" />
            Password Requirements:
          </h3>
          <ul className="space-y-1 text-sm text-blue-800 dark:text-blue-200">
            <li className="flex items-center">
              {formData.password.length >= 12 ? (
                <CheckCircle className="h-4 w-4 mr-2 text-green-600" />
              ) : (
                <XCircle className="h-4 w-4 mr-2 text-red-600" />
              )}
              At least 12 characters long
            </li>
            <li className="flex items-center">
              {/[a-z]/.test(formData.password) ? (
                <CheckCircle className="h-4 w-4 mr-2 text-green-600" />
              ) : (
                <XCircle className="h-4 w-4 mr-2 text-red-600" />
              )}
              Contains lowercase letters
            </li>
            <li className="flex items-center">
              {/[A-Z]/.test(formData.password) ? (
                <CheckCircle className="h-4 w-4 mr-2 text-green-600" />
              ) : (
                <XCircle className="h-4 w-4 mr-2 text-red-600" />
              )}
              Contains uppercase letters
            </li>
            <li className="flex items-center">
              {/\d/.test(formData.password) ? (
                <CheckCircle className="h-4 w-4 mr-2 text-green-600" />
              ) : (
                <XCircle className="h-4 w-4 mr-2 text-red-600" />
              )}
              Contains numbers
            </li>
            <li className="flex items-center">
              {/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(formData.password) ? (
                <CheckCircle className="h-4 w-4 mr-2 text-green-600" />
              ) : (
                <XCircle className="h-4 w-4 mr-2 text-red-600" />
              )}
              Contains special characters
            </li>
          </ul>
        </CardContent>
      </Card>

      {/* Form Validation Summary */}
      {Object.keys(validationErrors).length > 0 && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            Please fix the validation errors above before continuing.
          </AlertDescription>
        </Alert>
      )}

      {/* Submit Button */}
      <div className="pt-4">
        <Button
          type="submit"
          disabled={!isFormValid || isLoading}
          className="w-full h-12 text-base font-semibold"
        >
          {isLoading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2" />
              Creating Admin Account...
            </>
          ) : (
            'Create Super Admin Account'
          )}
        </Button>
      </div>
    </form>
  );
};