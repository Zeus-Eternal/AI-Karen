"use client";

import * as React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useState, useEffect } from "react";
import { ErrorBoundary, type ErrorFallbackProps } from "@/components/ui/error-boundary";
import type { LLMProvider, LLMProfile } from "./types";

const ProfileManagerErrorFallback: React.FC<ErrorFallbackProps> = ({ error, resetErrorBoundary }) => (
  <div>
    <div>Something went wrong in ProfileManager: {error?.message}</div>
    <button onClick={resetErrorBoundary}>Try again</button>
  </div>
);

export interface ProfileManagerProps {
  profiles: LLMProfile[];
  setProfiles: (profiles: LLMProfile[]) => void;
  activeProfile: LLMProfile | null;
  setActiveProfile: (profile: LLMProfile | null) => void;
  providers: LLMProvider[];
  onClose?: () => void; // Added optional onClose prop
}

/**
 * Minimal profile manager that lets a user pick the active profile.
 * This replaces an empty placeholder file that previously caused the
 * settings dialog to crash during rendering.
 */
export default function ProfileManager({
  profiles,
  setProfiles,
  activeProfile,
  setActiveProfile,
  providers: _providers,
  onClose,
}: ProfileManagerProps) {
  const [creating, setCreating] = useState(false);

  // Ensure profiles is always an array
  const safeProfiles = Array.isArray(profiles) ? profiles : [];

  const handleCreate = () => {
    const newProfile: LLMProfile = {
      id: `profile-${Date.now()}`,
      name: `Profile ${safeProfiles.length + 1}`,
      description: "User created profile",
      router_policy: "balanced",
      providers: {},
      fallback_provider: "local",
      is_valid: true,
      validation_errors: [],
      created_at: Date.now(),
      updated_at: Date.now(),
    };
    setProfiles([...safeProfiles, newProfile]);
    setActiveProfile(newProfile);
    setCreating(false);
  };

  // Focus management for accessibility
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        // Handle escape key
        onClose?.();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  return (
    <ErrorBoundary fallback={<ProfileManagerErrorFallback error={new Error('ProfileManager error')} resetErrorBoundary={() => {}} />}>
      <Card>
        <CardHeader>
          <CardTitle>Profiles</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {safeProfiles.length === 0 ? (
            <p className="text-sm text-muted-foreground md:text-base lg:text-lg">No profiles defined.</p>
          ) : (
            <ul className="space-y-2">
              {safeProfiles.map(p => (
                <li key={p.id} className="flex items-center justify-between">
                  <span>{p.name}</span>
                  {activeProfile?.id === p.id ? (
                    <span className="text-sm text-muted-foreground md:text-base lg:text-lg">Active</span>
                  ) : (
                    <Button size="sm" variant="secondary" onClick={() => setActiveProfile(p)}>
                      Activate
                    </Button>
                  )}
                </li>
              ))}
            </ul>
          )}
          <Button size="sm" onClick={handleCreate} disabled={creating}>
            {creating ? "Creating..." : "Create New Profile"}
          </Button>
        </CardContent>
      </Card>
    </ErrorBoundary>
  );
}
