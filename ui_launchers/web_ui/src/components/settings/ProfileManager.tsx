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

  const handleCreate = () => {
    const newProfile: LLMProfile = {
      id: `profile-${Date.now()}`,
      name: `Profile ${profiles.length + 1}`,
      description: "User created profile",
    };
    setProfiles([...profiles, newProfile]);
    setActiveProfile(newProfile);
    setCreating(false);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Profiles</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {profiles.length === 0 ? (
          <p className="text-sm text-muted-foreground">No profiles defined.</p>
        ) : (
          <ul className="space-y-2">
            {profiles.map(p => (
              <li key={p.id} className="flex items-center justify-between">
                <span>{p.name}</span>
                {activeProfile?.id === p.id ? (
                  <span className="text-sm text-muted-foreground">Active</span>
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
          Add Profile
        </Button>
      </CardContent>
    </Card>
  );
}
