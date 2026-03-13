"use client";
import React, { useState } from "react";
import { 
  MessageSquare, 
  Settings, 
  Database, 
  Activity, 
  FileText,
  BarChart3,
  Zap,
  Users
} from "lucide-react";
import { useRouter } from "next/navigation";

export default function SidebarNavigation() {
  const [activeTab, setActiveTab] = useState("chat");
  const router = useRouter();

  const handleNavigation = (tab: string) => {
    setActiveTab(tab);
    if (tab === "zvec") {
      window.open("http://localhost:9002", "_blank");
    } else if (tab === "chat") {
      router.push("/chat");
    }
  };

  const navItems = [
    {
      id: "chat",
      label: "Chat",
      icon: MessageSquare,
      color: "text-purple-400",
      bgColor: "bg-purple-600/20",
      hoverColor: "hover:bg-purple-600/30",
    },
    {
      id: "analytics",
      label: "Analytics",
      icon: BarChart3,
      color: "text-blue-400",
      bgColor: "",
      hoverColor: "hover:bg-slate-700",
    },
    {
      id: "memory",
      label: "Memory",
      icon: Database,
      color: "text-green-400",
      bgColor: "",
      hoverColor: "hover:bg-slate-700",
    },
    {
      id: "performance",
      label: "Performance",
      icon: Zap,
      color: "text-yellow-400",
      bgColor: "",
      hoverColor: "hover:bg-slate-700",
    },
    {
      id: "zvec",
      label: "Zvec Monitor",
      icon: Activity,
      color: "text-green-400",
      bgColor: "bg-green-600/20",
      hoverColor: "hover:bg-green-600/30",
    },
    {
      id: "files",
      label: "Files",
      icon: FileText,
      color: "text-gray-400",
      bgColor: "",
      hoverColor: "hover:bg-slate-700",
    },
    {
      id: "settings",
      label: "Settings",
      icon: Settings,
      color: "text-gray-400",
      bgColor: "",
      hoverColor: "hover:bg-slate-700",
    },
  ];

  return (
    <nav className="space-y-1">
      {navItems.map((item) => {
        const Icon = item.icon;
        const isActive = activeTab === item.id;
        
        return (
          <button
            key={item.id}
            onClick={() => handleNavigation(item.id)}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
              isActive 
                ? `${item.bgColor} text-white` 
                : `text-white ${item.hoverColor}`
            }`}
          >
            <Icon className={`h-5 w-5 ${isActive ? item.color : ""}`} />
            <span>{item.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
