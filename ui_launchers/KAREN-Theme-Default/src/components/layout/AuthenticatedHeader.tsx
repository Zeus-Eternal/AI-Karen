"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { UserProfile } from "@/components/auth/UserProfile";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { User, LogOut } from "lucide-react";
import { ThemeToggle } from "@/components/ui/theme-toggle";

import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export const AuthenticatedHeader: React.FC = () => {
  const { user, logout } = useAuth();
  const [showProfile, setShowProfile] = useState(false);

  const initialsFrom = (s?: string) =>
    (s?.trim()?.charAt(0) ?? "?").toUpperCase();

  const handleLogout = () => {
    logout();
  };

  // Optional: close the profile dialog with Escape (Dialog already handles this,
  // but this ensures we gracefully close if focus is elsewhere)
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && showProfile) setShowProfile(false);
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [showProfile]);

  if (!user) return null;

  const userInitials =
    initialsFrom(user?.email) || initialsFrom(user?.userId) || "?";

  return (
    <>
      <div className="flex items-center gap-3">
        <ThemeToggle />

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              className="relative h-10 w-10 rounded-full"
              aria-label="Open user menu"
            >
              <Avatar className="h-10 w-10">
                <AvatarFallback className="bg-primary text-primary-foreground">
                  {userInitials}
                </AvatarFallback>
              </Avatar>
            </Button>
          </DropdownMenuTrigger>

          <DropdownMenuContent className="w-64" align="end" forceMount>
            <DropdownMenuLabel className="font-normal">
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium leading-none md:text-base">
                  {user?.email ?? user?.userId ?? ""}
                </p>
                <p className="text-xs leading-none text-muted-foreground">
                  {Array.isArray(user?.roles)
                    ? user.roles.join(", ")
                    : (user?.roles as unknown) ?? ""}
                </p>
              </div>
            </DropdownMenuLabel>

            <DropdownMenuSeparator />

            <DropdownMenuItem
              onClick={() => setShowProfile(true)}
              className="cursor-pointer"
            >
              <User className="mr-2 h-4 w-4" />
              <span>Profile & Settings</span>
            </DropdownMenuItem>

            {/* Example: route to a settings page if you have one
            <DropdownMenuItem onClick={() => router.push('/settings')} className="cursor-pointer">
              <Settings className="mr-2 h-4 w-4" />
              <span>Settings</span>
            </DropdownMenuItem>
            */}

            <DropdownMenuSeparator />

            <DropdownMenuItem
              onClick={handleLogout}
              className="text-red-600 focus:text-red-700 cursor-pointer"
            >
              <LogOut className="mr-2 h-4 w-4" />
              <span>Sign out</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Profile Dialog */}
      <Dialog open={showProfile} onOpenChange={setShowProfile}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>User Profile</DialogTitle>
          </DialogHeader>
          <UserProfile onClose={() => setShowProfile(false)} />
        </DialogContent>
      </Dialog>
    </>
  );
};
