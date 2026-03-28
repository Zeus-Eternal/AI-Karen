"use client";

import { ReactNode } from "react";

interface PublicWrapperProps {
  children: ReactNode;
  fallback?: ReactNode;
}

export function PublicWrapper({ children, fallback }: PublicWrapperProps) {
  return <>{fallback ?? children}</>;
}
