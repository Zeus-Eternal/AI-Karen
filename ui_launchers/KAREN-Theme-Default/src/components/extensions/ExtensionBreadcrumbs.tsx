/**
 * Breadcrumb navigation for the Extension Manager sidebar.
 * Displays the current hierarchy path and allows quick navigation
 * back to a parent level.
 */
"use client";

import React, { memo, useCallback } from "react";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { useExtensionContext } from "@/hooks/use-extension-context";
import type { BreadcrumbItem } from "@/extensions";

export type Crumb = BreadcrumbItem;

function ExtensionBreadcrumbsComponent() {
  const { state, dispatch } = useExtensionContext();
  const { breadcrumbs } = state;

  if (!Array.isArray(breadcrumbs) || breadcrumbs.length === 0) return null;

  const handleClick = useCallback(
    (index: number) => {
      // index is zero-based; levels are 1-based in your reducer
      dispatch({ type: "SET_LEVEL", level: index + 1 });
    },
    [dispatch]
  );

  return (
    <nav
      aria-label="Breadcrumb"
      className="min-w-0" // allow inner truncation
    >
      <ol
        role="list"
        className="flex items-center space-x-2 text-sm text-muted-foreground md:text-base lg:text-lg"
      >
        {breadcrumbs.map((crumb: BreadcrumbItem, idx) => {
          const isLast = idx === breadcrumbs.length - 1;
          const key = crumb.id ?? `${crumb.level}-${crumb.name}-${idx}`;
          return (
            <li key={key} className="flex items-center">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className={`h-7 px-2 py-0 font-normal hover:underline max-w-[12rem] sm:max-w-[16rem] truncate text-ellipsis ${
                  isLast ? "text-foreground cursor-default hover:no-underline" : ""
                }`}
                onClick={!isLast ? () => handleClick(idx) : undefined}
                aria-current={isLast ? "page" : undefined}
                disabled={isLast}
                title={crumb.name}
              >
                <span className="truncate">{crumb.name}</span>
              </Button>

              {!isLast && (
                <Separator
                  orientation="vertical"
                  className="mx-2 h-4 shrink-0"
                  aria-hidden="true"
                />
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

const ExtensionBreadcrumbs = memo(ExtensionBreadcrumbsComponent);
export default ExtensionBreadcrumbs;
