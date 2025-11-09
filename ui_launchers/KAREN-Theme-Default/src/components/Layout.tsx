"use client";

import React from "react";

export interface LayoutProps {
  children: React.ReactNode;
}

/**
 * Lightweight wrapper component that keeps legacy imports working while the
 * full layout system lives in the modern AppShell module.
 */
export default function Layout({ children }: LayoutProps) {
  return <>{children}</>;
}
