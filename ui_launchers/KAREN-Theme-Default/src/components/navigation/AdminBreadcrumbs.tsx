// ui_launchers/KAREN-Theme-Default/src/components/navigation/AdminBreadcrumbs.tsx
"use client";

import React, { useMemo } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";
import { cn } from "@/lib/utils";
import {
  ChevronRight,
  Home,
  Users,
  Shield,
  Settings,
  Activity,
  BarChart3,
  Lock,
  UserCog,
  FolderTree,
} from "lucide-react";

export type IconType = React.ComponentType<{ className?: string }>;

export interface BreadcrumbItem {
  label: string;
  href?: string;
  icon?: IconType;
  isActive?: boolean;
}

export interface AdminBreadcrumbsProps {
  className?: string;
  /** Provide explicit crumbs to override route-based generation */
  customItems?: BreadcrumbItem[];
  /** If true (default), hide for non-admin users */
  requireAdminAccess?: boolean;
  /** Maximum number of segments to render (keeps UI tidy). 0 = unlimited */
  maxDepth?: number;
  /** Replace labels for specific slugs or full paths */
  labelOverrides?: Record<string, string>;
}

const ROUTE_MAP: Record<string, { label: string; icon?: IconType }> = {
  "/": { label: "Home", icon: Home },
  "/chat": { label: "Chat", icon: FolderTree },
  "/admin": { label: "User Management", icon: Users },
  "/admin/activity": { label: "Activity Monitor", icon: Activity },
  "/admin/super-admin": { label: "Super Admin Dashboard", icon: Shield },
  "/admin/super-admin/admins": { label: "Admin Management", icon: UserCog },
  "/admin/super-admin/system": { label: "System Configuration", icon: Settings },
  "/admin/super-admin/security": { label: "Security Settings", icon: Lock },
  "/admin/super-admin/audit": { label: "Audit Logs", icon: BarChart3 },
};

function titleCaseFromSlug(slug: string): string {
  return decodeURIComponent(slug)
    .split("?")[0]
    .split("#")[0]
    .split("-")
    .map((w) => (w ? w[0].toUpperCase() + w.slice(1) : w))
    .join(" ");
}

export const AdminBreadcrumbs: React.FC<AdminBreadcrumbsProps> = ({
  className,
  customItems,
  requireAdminAccess = true,
  maxDepth = 0,
  labelOverrides = {},
}) => {
  const { hasRole } = useAuth();
  const pathname = usePathname() || "/";

  // RBAC: Only show to admins by default
  // With role hierarchy, super_admins automatically pass hasRole("admin")
  const isAdmin = !requireAdminAccess || hasRole("admin");

  const breadcrumbs = useMemo<BreadcrumbItem[]>(() => {
    // Custom items take full control
    if (customItems && customItems.length > 0) {
      // Ensure only last item isActive if not provided
      const lastIdx = customItems.length - 1;
      return customItems.map((c, i) => ({
        ...c,
        isActive: c.isActive ?? (i === lastIdx && !c.href),
      }));
    }

    const segments = pathname.split("/").filter(Boolean);
    const crumbs: BreadcrumbItem[] = [];

    // Always start with Home unless you're literally on "/"
    if (pathname !== "/") {
      crumbs.push({ label: "Home", href: "/", icon: Home });
    } else {
      crumbs.push({ label: "Home", icon: Home, isActive: true });
      return crumbs;
    }

    let currentPath = "";
    for (let i = 0; i < segments.length; i++) {
      const seg = segments[i];
      currentPath += `/${seg}`;
      const isLast = i === segments.length - 1;

      const mapped = ROUTE_MAP[currentPath];
      const rawLabel = labelOverrides[currentPath] ?? labelOverrides[seg] ?? mapped?.label ?? titleCaseFromSlug(seg);

      crumbs.push({
        label: rawLabel,
        href: isLast ? undefined : currentPath,
        icon: mapped?.icon,
        isActive: isLast,
      });
    }

    // Enforce depth if requested (keep first + last N)
    if (maxDepth > 0 && crumbs.length > maxDepth) {
      const first = crumbs[0];
      const tail = crumbs.slice(crumbs.length - (maxDepth - 1));
      return [first, ...tail];
    }

    return crumbs;
  }, [customItems, pathname, maxDepth, labelOverrides]);

  // Hide if only one crumb (e.g., just Home) or user not allowed
  if (!isAdmin || breadcrumbs.length <= 1) return null;

  return (
    <nav
      className={cn("flex items-center text-sm text-muted-foreground", className)}
      aria-label="Breadcrumb"
    >
      <ol className="flex items-center flex-wrap">
        {breadcrumbs.map((item, index) => {
          const Icon = item.icon;
          const isLast = index === breadcrumbs.length - 1;

          return (
            <li key={`${item.label}-${index}`} className="flex items-center">
              {index > 0 && (
                <ChevronRight
                  className="h-4 w-4 mx-1 text-muted-foreground/50"
                  aria-hidden="true"
                />
              )}

              {item.href && !isLast ? (
                <Link
                  href={item.href}
                  className="flex items-center gap-1 hover:text-foreground transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-sm px-0.5"
                >
                  {Icon ? <Icon className="h-4 w-4" /> : null}
                  <span className="truncate max-w-[22ch]" title={item.label}>
                    {item.label}
                  </span>
                </Link>
              ) : (
                <span
                  className={cn(
                    "flex items-center gap-1 px-0.5",
                    item.isActive && "text-foreground font-medium"
                  )}
                  aria-current={item.isActive ? "page" : undefined}
                >
                  {Icon ? <Icon className="h-4 w-4" /> : null}
                  <span className="truncate max-w-[22ch]" title={item.label}>
                    {item.label}
                  </span>
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
};

export default AdminBreadcrumbs;
