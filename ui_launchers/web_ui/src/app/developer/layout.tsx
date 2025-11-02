import React from 'react';
import { Metadata } from "next";

export const metadata: Metadata = {
  title: {
    template: "%s | Kari",
    default: "Kari",
  },
  description: "Developer console is disabled in production.",
};

interface DeveloperLayoutProps {
  children: React.ReactNode;
}

export default function DeveloperLayout({ children }: DeveloperLayoutProps) {
  return <>{children}</>;
}