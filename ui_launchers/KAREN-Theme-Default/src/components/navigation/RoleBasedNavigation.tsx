// ui_launchers/KAREN-Theme-Default/src/components/navigation/RoleBasedNavigation.tsx
"use client";

import React, { useMemo, useCallback } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ExtensionNavigation } from "@/components/extensions/ExtensionNavigation";
import { useExtensionsAvailable } from "@/lib/extensions/extension-initializer";

// Icons
import {
  MessageSquare,
  UserCog,
  Puzzle,
  Users,
  Activity,
  Shield,
  Settings,
  Lock,
  BarChart3,
  Home,
} from "lucide-react";

export type Role = "super_admin" | "admin" | "user";

export interface NavigationItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description?: string;
  badge?: string;
  requiredRole?: Role;
  requiredPermission?: string;
  // Future-proof: allow fine-grained feature flags
  featureFlag?: string;
}

export interface RoleBasedNavigationProps {
  className?: string;
  variant?: "sidebar" | "header" | "mobile";
}

export const RoleBasedNavigation: React.FC<RoleBasedNavigationProps> = ({
  className,
  variant = "sidebar",
}) => {
  const pathname = usePathname();
  const { user, hasRole, hasPermission } = useAuth();
  const extensionsAvailable = useExtensionsAvailable();

  // Centralized item registry
  const navigationItems: NavigationItem[] = useMemo(() => {
    const base: NavigationItem[] = [
      {
        href: "/chat",
        label: "Chat",
        icon: MessageSquare,
        description: "AI conversation interface",
      },
      {
        href: "/profile",
        label: "Profile",
        icon: UserCog,
        description: "Manage your account settings",
      },
    ];

    const extensions: NavigationItem[] = extensionsAvailable
      ? [
          {
            href: "/extensions",
            label: "Extensions",
            icon: Puzzle,
            description: "Manage and monitor extensions",
          },
        ]
      : [];

    const admin: NavigationItem[] = [
      {
        href: "/admin",
        label: "User Management",
        icon: Users,
        description: "Manage users and accounts",
        requiredRole: "admin",
        badge: "Admin",
      },
      {
        href: "/admin/activity",
        label: "Activity Monitor",
        icon: Activity,
        description: "Monitor user activity and system usage",
        requiredRole: "admin",
      },
    ];

    const superAdmin: NavigationItem[] = [
      {
        href: "/admin/super-admin",
        label: "Super Admin",
        icon: Shield,
        description: "System administration and configuration",
        requiredRole: "super_admin",
        badge: "Super Admin",
      },
      {
        href: "/admin/super-admin/admins",
        label: "Admin Management",
        icon: UserCog,
        description: "Manage administrator accounts",
        requiredRole: "super_admin",
      },
      {
        href: "/admin/super-admin/system",
        label: "System Config",
        icon: Settings,
        description: "System configuration and settings",
        requiredRole: "super_admin",
      },
      {
        href: "/admin/super-admin/security",
        label: "Security Settings",
        icon: Lock,
        description: "Security policies and configurations",
        requiredRole: "super_admin",
      },
      {
        href: "/admin/super-admin/audit",
        label: "Audit Logs",
        icon: BarChart3,
        description: "System audit logs and compliance",
        requiredRole: "super_admin",
      },
    ];

    return [...base, ...extensions, ...admin, ...superAdmin];
  }, [extensionsAvailable]);

  // RBAC filter with null-safe checks
  const visibleItems = useMemo(() => {
    const can = (item: NavigationItem) => {
      if (!user) return false; // all items require auth in this shell
      if (item.requiredRole && !hasRole(item.requiredRole)) return false;
      if (item.requiredPermission && !hasPermission(item.requiredPermission)) return false;
      return true;
    };
    return navigationItems.filter(can);
  }, [navigationItems, user, hasRole, hasPermission]);

  const isActive = useCallback(
    (href: string) => {
      if (!pathname) return false;
      return pathname === href || (href !== "/" && pathname.startsWith(href));
    },
    [pathname]
  );

  const renderNavigationItem = useCallback(
    (item: NavigationItem) => {
      const active = isActive(item.href);
      const Icon = item.icon;

      // Header variant: compact buttons
      if (variant === "header") {
        return (
          <Link key={item.href} href={item.href} aria-label={`Go to ${item.label}`}>
            <Button
              variant={active ? "secondary" : "ghost"}
              size="sm"
              className={cn("justify-start gap-2", active && "bg-secondary")}
            >
              <Icon className="h-4 w-4" />
              <span className="whitespace-nowrap">{item.label}</span>
              {item.badge && (
                <Badge variant="outline" className="text-xs">
                  {item.badge}
                </Badge>
              )}
            </Button>
          </Link>
        );
      }

      // Sidebar/Mobile variant: full-width rows
      return (
        <Link key={item.href} href={item.href} aria-label={`Go to ${item.label}`}>
          <Button
            variant={active ? "secondary" : "ghost"}
            className={cn("w-full justify-start h-auto p-3", active && "bg-secondary")}
          >
            <div className="flex items-center gap-3 w-full">
              <Icon className="h-4 w-4 flex-shrink-0" />
              <div className="flex-1 text-left">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{item.label}</span>
                  {item.badge && (
                    <Badge
                      variant={
                        item.badge === "Super Admin"
                          ? "destructive"
                          : item.badge === "Admin"
                          ? "default"
                          : "outline"
                      }
                      className="text-xs"
                    >
                      {item.badge}
                    </Badge>
                  )}
                </div>
                {item.description && variant === "sidebar" && (
                  <p className="text-xs text-muted-foreground mt-1">{item.description}</p>
                )}
              </div>
            </div>
          </Button>
        </Link>
      );
    },
    [isActive, variant]
  );

  if (visibleItems.length === 0) return null;

  return (
    <nav
      className={cn("space-y-1", className)}
      role="navigation"
      aria-label={variant === "header" ? "Header Navigation" : "Main Navigation"}
    >
      {variant === "sidebar" && (
        <div className="space-y-4">
          {/* Main Navigation */}
          <div className="px-3 py-2">
            <h2 className="mb-2 px-4 text-lg font-semibold tracking-tight flex items-center gap-2">
              <Home className="h-5 w-5 text-primary" />
              <span className="sr-only">Home</span>
            </h2>
            <div className="space-y-1">{visibleItems.map(renderNavigationItem)}</div>
          </div>

          {/* Extension Navigation */}
          {extensionsAvailable && <ExtensionNavigation className="px-3 py-2" />}
        </div>
      )}

      {variant === "header" && (
        <div className="flex items-center gap-2">{visibleItems.map(renderNavigationItem)}</div>
      )}

      {variant === "mobile" && (
        <div className="space-y-1">
          {visibleItems.map(renderNavigationItem)}
          {extensionsAvailable && <ExtensionNavigation compact />}
        </div>
      )}
    </nav>
  );
};
