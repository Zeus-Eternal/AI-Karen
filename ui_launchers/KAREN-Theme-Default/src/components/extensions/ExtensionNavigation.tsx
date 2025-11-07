/**
 * Extension Navigation Component
 *
 * Provides navigation integration for extensions in the main app navigation
 */

"use client";

import React, { useMemo } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useExtensionNavigation } from "@/lib/extensions/hooks";
import { Badge } from "../ui/badge";

import {
  Puzzle,
  Activity,
  Settings,
  Zap,
  BarChart3,
  MessageSquare,
  Code,
  Link as LinkIcon,
  Shield,
  Beaker,
} from "lucide-react";

export interface ExtensionNavigationProps {
  className?: string;
  compact?: boolean;
}

const iconMap: Record<string, React.ComponentType<any>> = {
  puzzle: Puzzle,
  activity: Activity,
  settings: Settings,
  zap: Zap,
  chart: BarChart3,
  "message-circle": MessageSquare,
  code: Code,
  link: LinkIcon,
  shield: Shield,
  flask: Beaker,
};

export function ExtensionNavigation({
  className,
  compact = false,
}: ExtensionNavigationProps) {
  const pathname = usePathname();
  const navItems = useExtensionNavigation();

  const groupedNavItems = useMemo(() => {
    const groups: Record<string, typeof navItems> = {};

    navItems.forEach((item) => {
      // Group by extension ID or category
      const groupKey = item.extensionId;
      if (!groups[groupKey]) {
        groups[groupKey] = [];
      }
      groups[groupKey].push(item);
    });

    return groups;
  }, [navItems]);

  if (navItems.length === 0) {
    return null;
  }

  return (
    <div className={className}>
      {!compact && (
        <div className="px-3 py-2">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider sm:text-sm md:text-base">
            Extensions
          </h3>
        </div>
      )}

      <nav className="space-y-1">
        {Object.entries(groupedNavItems).map(([extensionId, items]) => (
          <ExtensionNavGroup
            key={extensionId}
            extensionId={extensionId}
            items={items}
            currentPath={pathname}
            compact={compact}
          />
        ))}
      </nav>
    </div>
  );
}

export interface ExtensionNavGroupProps {
  extensionId: string;
  items: Array<{
    id: string;
    extensionId: string;
    label: string;
    path: string;
    icon?: string;
    permissions?: string[];
    order?: number;
    parent?: string;
  }>;
  currentPath: string;
  compact: boolean;
}

function ExtensionNavGroup({
  extensionId,
  items,
  currentPath,
  compact,
}: ExtensionNavGroupProps) {
  const sortedItems = useMemo(() => {
    return [...items].sort((a, b) => (a.order || 999) - (b.order || 999));
  }, [items]);

  // Group items by parent
  const { parentItems, childItems } = useMemo(() => {
    const parents = sortedItems.filter((item) => !item.parent);
    const children = sortedItems.filter((item) => item.parent);
    return { parentItems: parents, childItems: children };
  }, [sortedItems]);

  return (
    <div className="space-y-1">
      {parentItems.map((item) => (
        <ExtensionNavItem
          key={item.id}
          item={item}
          currentPath={currentPath}
          compact={compact}
          children={childItems.filter((child) => child.parent === item.id)}
        />
      ))}
    </div>
  );
}

export interface ExtensionNavItemProps {
  item: {
    id: string;
    extensionId: string;
    label: string;
    path: string;
    icon?: string;
    permissions?: string[];
    order?: number;
    parent?: string;
  };
  currentPath: string;
  compact: boolean;
  children?: Array<{
    id: string;
    extensionId: string;
    label: string;
    path: string;
    icon?: string;
    permissions?: string[];
    order?: number;
    parent?: string;
  }>;
}

function ExtensionNavItem({
  item,
  currentPath,
  compact,
  children = [],
}: ExtensionNavItemProps) {
  const isActive =
    currentPath === item.path || currentPath.startsWith(item.path + "/");
  const hasChildren = children.length > 0;

  const IconComponent =
    item.icon && iconMap[item.icon] ? iconMap[item.icon] : Puzzle;

  return (
    <div>
      <Link
        href={item.path}
        className={`
          group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors
          ${
            isActive
              ? "bg-blue-100 text-blue-700 border-r-2 border-blue-500"
              : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
          }
        `}
      >
        <IconComponent
          className={`
            flex-shrink-0 h-4 w-4 mr-3
            ${
              isActive
                ? "text-blue-500"
                : "text-gray-400 group-hover:text-gray-500"
            }
          `}
        />

        {!compact && (
          <>
            <span className="flex-1 truncate">{item.label}</span>

            {hasChildren && (
              <Badge
                variant="secondary"
                className="ml-2 text-xs sm:text-sm md:text-base"
              >
                {children.length}
              </Badge>
            )}

            {/* Extension indicator */}
            <div className="ml-2 w-2 h-2 bg-blue-400 rounded-full opacity-60 " />
          </>
        )}
      </Link>

      {/* Child items */}
      {hasChildren && !compact && (
        <div className="ml-6 mt-1 space-y-1">
          {children.map((child) => (
            <Link
              key={child.id}
              href={child.path}
              className={`
                group flex items-center px-3 py-1 text-sm rounded-md transition-colors
                ${
                  currentPath === child.path
                    ? "bg-blue-50 text-blue-600"
                    : "text-gray-500 hover:bg-gray-50 hover:text-gray-700"
                }
              `}
            >
              {child.icon && iconMap[child.icon] ? (
                React.createElement(iconMap[child.icon], {
                  className: `flex-shrink-0 h-3 w-3 mr-2 ${
                    currentPath === child.path
                      ? "text-blue-500"
                      : "text-gray-400"
                  }`,
                })
              ) : (
                <div className="w-3 h-3 mr-2 " />
              )}
              <span className="truncate">{child.label}</span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Extension navigation breadcrumbs
 */
export function ExtensionNavigationBreadcrumbs({
  className,
}: {
  className?: string;
}) {
  const pathname = usePathname();
  const navItems = useExtensionNavigation();

  const currentItem = useMemo(() => {
    return navItems.find(
      (item) => pathname === item.path || pathname.startsWith(item.path + "/")
    );
  }, [pathname, navItems]);

  if (!currentItem || !pathname.startsWith("/extensions/")) {
    return null;
  }

  const pathSegments = pathname.split("/").filter(Boolean);
  const breadcrumbs = pathSegments.map((segment, index) => {
    const path = "/" + pathSegments.slice(0, index + 1).join("/");
    const item = navItems.find((nav) => nav.path === path);

    return {
      label:
        item?.label ||
        segment.replace(/-/g, " ").replace(/\b\w/g, (l) => l.toUpperCase()),
      path,
      isLast: index === pathSegments.length - 1,
    };
  });

  return (
    <nav
      className={`flex items-center space-x-2 text-sm text-gray-500 ${className}`}
    >
      <Link href="/extensions" className="hover:text-gray-700">
        Extensions
      </Link>

      {breadcrumbs.map((crumb, index) => (
        <React.Fragment key={crumb.path}>
          <span>/</span>
          {crumb.isLast ? (
            <span className="text-gray-900 font-medium">{crumb.label}</span>
          ) : (
            <Link href={crumb.path} className="hover:text-gray-700">
              {crumb.label}
            </Link>
          )}
        </React.Fragment>
      ))}
    </nav>
  );
}

export default ExtensionNavigation;
