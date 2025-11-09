"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { Brain, Code, Sparkles, GraduationCap, Briefcase, ChevronDown } from "lucide-react";

interface Profile {
  id: string;
  name: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
}

const profiles: Profile[] = [
  {
    id: "general",
    name: "General Assistant",
    description: "Helpful and conversational",
    icon: Brain,
    color: "text-blue-500",
  },
  {
    id: "coder",
    name: "Code Expert",
    description: "Focused on programming and development",
    icon: Code,
    color: "text-green-500",
  },
  {
    id: "creative",
    name: "Creative Writer",
    description: "Imaginative and expressive",
    icon: Sparkles,
    color: "text-purple-500",
  },
  {
    id: "teacher",
    name: "Patient Teacher",
    description: "Explains concepts clearly",
    icon: GraduationCap,
    color: "text-yellow-500",
  },
  {
    id: "professional",
    name: "Business Professional",
    description: "Formal and concise",
    icon: Briefcase,
    color: "text-gray-500",
  },
];

export default function ProfileSelector() {
  const [selectedProfile, setSelectedProfile] = useState<Profile>(profiles[0]);

  const handleProfileSelect = (profile: Profile) => {
    setSelectedProfile(profile);
  };

  const Icon = selectedProfile.icon;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" className="flex items-center gap-2">
          <Icon className={`h-4 w-4 ${selectedProfile.color}`} />
          <span className="hidden sm:inline">{selectedProfile.name}</span>
          <ChevronDown className="h-3 w-3 opacity-50" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-64">
        <DropdownMenuLabel>AI Profile</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {profiles.map((profile) => {
          const ProfileIcon = profile.icon;
          const isSelected = profile.id === selectedProfile.id;
          return (
            <DropdownMenuItem
              key={profile.id}
              onSelect={() => handleProfileSelect(profile)}
              className="flex items-start gap-3 py-2"
            >
              <ProfileIcon className={`h-4 w-4 mt-0.5 ${profile.color}`} />
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{profile.name}</span>
                  {isSelected && (
                    <Badge variant="secondary" className="text-[10px]">
                      Active
                    </Badge>
                  )}
                </div>
                <p className="text-xs text-muted-foreground">{profile.description}</p>
              </div>
            </DropdownMenuItem>
          );
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export { ProfileSelector };
