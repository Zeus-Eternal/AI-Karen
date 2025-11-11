// ui_launchers/KAREN-Theme-Default/src/components/auth/setup/steps/AdminDetailsStep.tsx
"use client";

import React, { useMemo, useState, useCallback } from "react";
import type { SetupStepProps } from "../SetupWizard";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Eye, EyeOff, Shield, AlertTriangle } from "lucide-react";

type AdminDetailsStepProps = SetupStepProps & {
  // Optional: allow wizard to pre-fill (e.g., from earlier step)
  defaultEmail?: string;
  defaultName?: string;
};

type FormData = {
  email: string;
  full_name: string;
  password: string;
  confirm_password: string;
  organization?: string;
  agree_tos: boolean;
};

type FormErrors = Partial<Record<keyof FormData | "general", string>>;

const emailRegex =
  /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;

function scorePassword(pw: string): number {
  if (!pw) return 0;
  // All requirements must be met for production backend
  const rules = [
    /.{8,}/, // min length (required)
    /[a-z]/, // lowercase (required)
    /[A-Z]/, // uppercase (required)
    /\d/,    // digit (required)
    /[^A-Za-z0-9]/, // special char (required)
  ];
  let score = rules.reduce((s, r) => s + (r.test(pw) ? 1 : 0), 0);

  // Extra length bonuses
  if (pw.length >= 12) score += 1;
  if (pw.length >= 16) score += 1;

  // Variety bonus for multiple special characters or character types
  const specialCount = (pw.match(/[^A-Za-z0-9]/g) || []).length;
  if (specialCount >= 2) score += 0.5;

  return Math.min(Math.floor(score), 7); // cap to 7
}

function strengthLabel(score: number) {
  // Score < 5 means missing required elements
  if (score < 5) return { label: "Too Weak", intent: "destructive" as const, pct: Math.min((score / 5) * 50, 50) };
  // Score 5 = meets all requirements (8+ chars, upper, lower, digit, special)
  if (score === 5) return { label: "Good", intent: "default" as const, pct: 65 };
  // Score 6 = 12+ chars
  if (score === 6) return { label: "Strong", intent: "default" as const, pct: 85 };
  // Score 7+ = 16+ chars or extra variety
  return { label: "Excellent", intent: "default" as const, pct: 100 };
}

export function AdminDetailsStep({
  onNext,
  onPrevious,
  onFormDataChange,
  defaultEmail = "",
  defaultName = "",
}: AdminDetailsStepProps) {
  const [form, setForm] = useState<FormData>({
    email: defaultEmail,
    full_name: defaultName,
    password: "",
    confirm_password: "",
    organization: "",
    agree_tos: false,
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [submitting, setSubmitting] = useState(false);
  const [showPw, setShowPw] = useState(false);
  const [showPw2, setShowPw2] = useState(false);

  const pwScore = useMemo(() => scorePassword(form.password), [form.password]);
  const pwMeta = useMemo(() => strengthLabel(pwScore), [pwScore]);

  const update = useCallback(<K extends keyof FormData>(k: K, v: FormData[K]) => {
    setForm((prev) => ({ ...prev, [k]: v }));
    setErrors((prev) => ({ ...prev, [k]: undefined, general: undefined }));
  }, []);

  const validate = useCallback((): boolean => {
    const next: FormErrors = {};
    if (!form.email.trim()) next.email = "Email is required.";
    else if (!emailRegex.test(form.email.trim())) next.email = "Enter a valid email address.";

    if (!form.full_name.trim()) next.full_name = "Full name is required.";
    else if (form.full_name.trim().length < 2) next.full_name = "Full name must be at least 2 characters.";

    // Password rules - match backend validation requirements
    if (!form.password) next.password = "Password is required.";
    else {
      if (form.password.length < 8) {
        next.password = "Password must be at least 8 characters.";
      } else if (!/[a-z]/.test(form.password)) {
        next.password = "Password must include lowercase letters.";
      } else if (!/[A-Z]/.test(form.password)) {
        next.password = "Password must include uppercase letters.";
      } else if (!/\d/.test(form.password)) {
        next.password = "Password must include numbers.";
      } else if (!/[^A-Za-z0-9]/.test(form.password)) {
        next.password = "Password must include special characters (!@#$%^&*).";
      }
    }

    if (!form.confirm_password) next.confirm_password = "Confirm your password.";
    else if (form.password !== form.confirm_password) next.confirm_password = "Passwords do not match.";

    if (!form.agree_tos) next.agree_tos = "You must agree to the Terms to continue.";

    setErrors(next);
    return Object.keys(next).length === 0;
  }, [form]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setSubmitting(true);
    try {
      // Update wizard form data with validated values
      onFormDataChange({
        email: form.email.trim(),
        full_name: form.full_name.trim(),
        password: form.password,
        confirm_password: form.confirm_password,
      });

      // Proceed to next step
      onNext();
    } catch (err: Error) {
      setErrors({ general: err?.message ?? "Failed to proceed. Please try again." });
    } finally {
      setSubmitting(false);
    }
  };

  const pwAssist = (
    <div className="mt-2">
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>Password strength: {pwMeta.label}</span>
        <span>
          {form.password.length}/
          {form.password.length < 8 ? "8" : form.password.length < 12 ? "12" : "16"}+
        </span>
      </div>
      <Progress value={pwMeta.pct} className="h-2 mt-1" />
      <ul className="mt-2 text-xs text-muted-foreground list-disc pl-5 space-y-1">
        <li>At least 8 characters (12–16 recommended)</li>
        <li>At least one uppercase letter (A-Z)</li>
        <li>At least one lowercase letter (a-z)</li>
        <li>At least one number (0-9)</li>
        <li>At least one special character (!@#$%^&*)</li>
      </ul>
    </div>
  );

  return (
    <Card className="max-w-2xl">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shield className="h-5 w-5" /> Create Super Admin
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6" noValidate>
          {errors.general && (
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>{errors.general}</AlertDescription>
            </Alert>
          )}

          <div className="grid gap-4">
            {/* Email */}
            <div className="grid gap-2">
              <Label htmlFor="email">Email *</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                value={form.email}
                onChange={(e) => update("email", e.target.value)}
                aria-invalid={!!errors.email}
                aria-describedby={errors.email ? "email-error" : undefined}
                placeholder="admin@your-domain.com"
              />
              {errors.email && (
                <p id="email-error" className="text-sm text-red-600">
                  {errors.email}
                </p>
              )}
            </div>

            {/* Full name */}
            <div className="grid gap-2">
              <Label htmlFor="full_name">Full Name *</Label>
              <Input
                id="full_name"
                type="text"
                autoComplete="name"
                value={form.full_name}
                onChange={(e) => update("full_name", e.target.value)}
                aria-invalid={!!errors.full_name}
                aria-describedby={errors.full_name ? "full-name-error" : undefined}
                placeholder="Jane Admin"
              />
              {errors.full_name && (
                <p id="full-name-error" className="text-sm text-red-600">
                  {errors.full_name}
                </p>
              )}
            </div>

            {/* Organization (optional) */}
            <div className="grid gap-2">
              <Label htmlFor="organization">Organization (optional)</Label>
              <Input
                id="organization"
                type="text"
                value={form.organization}
                onChange={(e) => update("organization", e.target.value)}
                placeholder="Acme Corp"
              />
            </div>

            {/* Password */}
            <div className="grid gap-2">
              <Label htmlFor="password">Password *</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPw ? "text" : "password"}
                  autoComplete="new-password"
                  value={form.password}
                  onChange={(e) => update("password", e.target.value)}
                  aria-invalid={!!errors.password}
                  aria-describedby={errors.password ? "password-error" : undefined}
                  placeholder="Create a strong password"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-1.5 top-1.5 h-7 w-7"
                  onClick={() => setShowPw((s) => !s)}
                  aria-label={showPw ? "Hide password" : "Show password"}
                >
                  {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
              {errors.password && (
                <p id="password-error" className="text-sm text-red-600">
                  {errors.password}
                </p>
              )}
              {pwAssist}
            </div>

            {/* Confirm password */}
            <div className="grid gap-2">
              <Label htmlFor="confirm_password">Confirm Password *</Label>
              <div className="relative">
                <Input
                  id="confirm_password"
                  type={showPw2 ? "text" : "password"}
                  autoComplete="new-password"
                  value={form.confirm_password}
                  onChange={(e) => update("confirm_password", e.target.value)}
                  aria-invalid={!!errors.confirm_password}
                  aria-describedby={errors.confirm_password ? "confirm-password-error" : undefined}
                  placeholder="Re-enter password"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-1.5 top-1.5 h-7 w-7"
                  onClick={() => setShowPw2((s) => !s)}
                  aria-label={showPw2 ? "Hide password" : "Show password"}
                >
                  {showPw2 ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
              {errors.confirm_password && (
                <p id="confirm-password-error" className="text-sm text-red-600">
                  {errors.confirm_password}
                </p>
              )}
            </div>

            {/* Terms */}
            <div className="flex items-start gap-3">
              <Checkbox
                id="agree_tos"
                checked={form.agree_tos}
                onCheckedChange={(v) => update("agree_tos", Boolean(v))}
                aria-invalid={!!errors.agree_tos}
              />
              <Label htmlFor="agree_tos" className="leading-relaxed">
                I understand this account will have elevated privileges and agree to the{" "}
                <a className="underline" href="/legal/terms" target="_blank" rel="noreferrer">
                  Terms of Service
                </a>{" "}
                and{" "}
                <a className="underline" href="/legal/security" target="_blank" rel="noreferrer">
                  Security Policy
                </a>
                .
              </Label>
            </div>
            {errors.agree_tos && <p className="text-sm text-red-600">{errors.agree_tos}</p>}
          </div>

          {/* Actions */}
          <div className="flex items-center justify-between pt-2">
            <Button type="button" variant="outline" onClick={onPrevious} disabled={submitting}>
              Back
            </Button>
            <Button
              type="submit"
              disabled={
                submitting ||
                !form.email ||
                !form.full_name ||
                !form.password ||
                !form.confirm_password ||
                !form.agree_tos
              }
            >
              {submitting ? "Continuing..." : "Continue"}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
