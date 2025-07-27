'use client';

import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { UserProfile } from '@/components/auth/UserProfile';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuLabel, 
  DropdownMenuSeparator, 
  DropdownMenuTrigger 
} from '@/components/ui/dropdown-menu';
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle 
} from '@/components/ui/dialog';
import { User, LogOut, Settings } from 'lucide-react';

export const AuthenticatedHeader: React.FC = () => {
  const { user, logout } = useAuth();
  const [showProfile, setShowProfile] = useState(false);

  if (!user) {
    return null;
  }

  const userInitials = user.email.charAt(0).toUpperCase();

  return (
    <>
      <div className="flex items-center gap-3">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="relative h-10 w-10 rounded-full">
              <Avatar className="h-10 w-10">
                <AvatarFallback className="bg-primary text-primary-foreground">
                  {userInitials}
                </AvatarFallback>
              </Avatar>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-56" align="end" forceMount>
            <DropdownMenuLabel className="font-normal">
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium leading-none">{user.email}</p>
                <p className="text-xs leading-none text-muted-foreground">
                  {user.roles.join(', ')}
                </p>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => setShowProfile(true)}>
              <User className="mr-2 h-4 w-4" />
              <span>Profile & Settings</span>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={logout} className="text-red-600">
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