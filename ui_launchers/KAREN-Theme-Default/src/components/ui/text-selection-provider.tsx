"use client";

import * as React from "react";

import { ensureTextSelectable } from "@/hooks/useTextSelection";

export interface TextSelectionProviderProps {
  children: React.ReactNode;
  enableGlobalSelection?: boolean;
  enableKeyboardShortcuts?: boolean;
  enableContextMenu?: boolean;
  debug?: boolean;
}

export function TextSelectionProvider({
  children,
  enableGlobalSelection = true,
  enableKeyboardShortcuts = true,
  enableContextMenu = true,
  debug = false,
}: TextSelectionProviderProps) {
  React.useEffect(() => {
    if (!enableGlobalSelection) {
      return;
    }

    const ensureGlobalSelection = () => {
      if (document.body) {
        ensureTextSelectable(document.body);
      }

      document.querySelectorAll("*").forEach((element) => {
        if (!(element instanceof HTMLElement)) {
          return;
        }

        const skipTags = ["script", "style", "noscript"];
        if (!skipTags.includes(element.tagName.toLowerCase())) {
          ensureTextSelectable(element);
        }
      });
    };

    ensureGlobalSelection();

    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (node instanceof HTMLElement) {
            ensureTextSelectable(node);
          }
        });
      });
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });

    return () => observer.disconnect();
  }, [enableGlobalSelection]);

  React.useEffect(() => {
    if (!enableKeyboardShortcuts) {
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key === "a") {
        if (debug) {
          console.log("Select all triggered");
        }
      }

      if ((event.ctrlKey || event.metaKey) && event.key === "c") {
        const selection = window.getSelection();
        if (selection?.toString() && debug) {
          console.log("Copy triggered:", selection.toString());
        }
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [enableKeyboardShortcuts, debug]);

  React.useEffect(() => {
    if (!enableContextMenu) {
      return;
    }

    const handleContextMenu = (event: MouseEvent) => {
      const selection = window.getSelection();
      if (!selection?.toString()) {
        return;
      }

      if (debug) {
        console.log("Context menu on selection:", selection.toString());
      }

      void event;
    };

    document.addEventListener("contextmenu", handleContextMenu);
    return () => document.removeEventListener("contextmenu", handleContextMenu);
  }, [enableContextMenu, debug]);

  React.useEffect(() => {
    if (!debug) {
      return;
    }

    const handleSelectionChange = () => {
      const selection = window.getSelection();
      if (selection?.toString()) {
        console.log("Selection changed:", selection.toString());
      }
    };

    document.addEventListener("selectionchange", handleSelectionChange);
    return () =>
      document.removeEventListener("selectionchange", handleSelectionChange);
  }, [debug]);

  return <>{children}</>;
}

export function withTextSelection<P extends object>(
  Component: React.ComponentType<P>,
  options: Omit<TextSelectionProviderProps, "children"> = {},
) {
  return function WrappedComponent(props: P) {
    return (
      <TextSelectionProvider {...options}>
        <Component {...props} />
      </TextSelectionProvider>
    );
  };
}

export default TextSelectionProvider;
