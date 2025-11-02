"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useState } from "react";

interface LLMProvider {
  name: string;
  description: string;
}

interface LLMProfile {
  id: string;
  name: string;
  description: string;
}

interface ProfileManagerProps {
  profiles: LLMProfile[];
  setProfiles: (profiles: LLMProfile[]) => void;
  activeProfile: LLMProfile | null;
  setActiveProfile: (profile: LLMProfile | null) => void;
  providers: LLMProvider[];
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
  providers,
}: ProfileManagerProps) {
  const [creating, setCreating] = useState(false);

  // Ensure profiles is always an array
  const safeProfiles = Array.isArray(profiles) ? profiles : [];

  const handleCreate = () => {
    const newProfile: LLMProfile = {
      id: `profile-${Date.now()}`,
      name: `Profile ${safeProfiles.length + 1}`,
      description: "User created profile",
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
    <ErrorBoundary fallback={<div>Something went wrong in ProfileManager</div>}>
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
                  <button size="sm" variant="secondary" onClick={() = aria-label="Button"> setActiveProfile(p)}>
                    Activate
                  </Button>
                )}
              </li>
            ))}
          </ul>
        )}
        <button size="sm" onClick={handleCreate} disabled={creating} aria-label="Button">
          Add Profile
        </Button>
      </CardContent>
    </Card>
    </ErrorBoundary>
  );
}
