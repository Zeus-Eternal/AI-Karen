import { Metadata } from "next";
import DeveloperNav from "@/src/components/layout/DeveloperNav";

export const metadata: Metadata = {
  title: {
    template: "%s | Kari Developer",
    default: "Kari Developer",
  },
  description: "AI-powered development environment for Kari",
};

interface DeveloperLayoutProps {
  children: React.ReactNode;
}

export default function DeveloperLayout({ children }: DeveloperLayoutProps) {
  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <div className="w-80 border-r bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="h-full overflow-auto">
          <DeveloperNav />
        </div>
      </div>
      
      {/* Main content */}
      <div className="flex-1 overflow-auto">
        {children}
      </div>
    </div>
  );
}