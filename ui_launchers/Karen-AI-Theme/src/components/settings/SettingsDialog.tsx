"use client";

import { useMemo, useState } from "react";
import {
  Bell,
  BookText,
  Bot,
  Cog,
  Cpu,
  GraduationCap,
  KeyRound,
  MessageSquareMore,
  Shield,
  Speaker,
  UserCog,
  Zap,
} from "lucide-react";

import { Separator } from "@/components/ui/separator";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import ApiKeyManager from "./ApiKeyManager";
import BehaviorSettings from "./BehaviorSettings";
import ModelSettings from "./ModelSettings";
import NotificationSettings from "./NotificationSettings";
import OptimizationSettings from "./OptimizationSettings";
import PersonaSettings from "./PersonaSettings";
import PersonalFactsSettings from "./PersonalFactsSettings";
import PrivacySettings from "./PrivacySettings";
import VoiceSettings from "./VoiceSettings";
import TrainingSettingsPanel from "@/components/admin/TrainingSettingsPanel";
import CommsCenterPage from "@/components/comms/CommsCenterPage";

interface SettingsDialogProps {
  inSheet?: boolean;
  adminMode?: boolean;
}

type SettingsSection = {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  render: () => JSX.Element;
};

type SettingsCategory = {
  id: string;
  label: string;
  sections: SettingsSection[];
};

export default function SettingsDialog({ inSheet = false, adminMode = false }: SettingsDialogProps) {
  const categories = useMemo<SettingsCategory[]>(() => {
    const baseCategories: SettingsCategory[] = [
      {
        id: "assistant",
        label: "Assistant",
        sections: [
          { id: "behavior", label: "Behavior", icon: Cog, render: () => <BehaviorSettings /> },
          { id: "persona", label: "Persona", icon: UserCog, render: () => <PersonaSettings inSheet={inSheet} /> },
          { id: "voice", label: "Voice", icon: Speaker, render: () => <VoiceSettings /> },
        ],
      },
      {
        id: "personal",
        label: "Personal",
        sections: [
          { id: "personal-facts", label: "Facts", icon: BookText, render: () => <PersonalFactsSettings /> },
          { id: "notifications", label: "Alerts", icon: Bell, render: () => <NotificationSettings /> },
          { id: "privacy", label: "Privacy", icon: Shield, render: () => <PrivacySettings /> },
        ],
      },
      {
        id: "runtime",
        label: "Models & Runtime",
        sections: [
          { id: "model", label: "Model", icon: Bot, render: () => <ModelSettings /> },
          { id: "api-keys", label: "API Keys", icon: KeyRound, render: () => <ApiKeyManager /> },
        ],
      },
    ];

    if (adminMode) {
      baseCategories[2].sections.push({
        id: "optimization",
        label: "Acceleration",
        icon: Zap, // Changed to Zap for "Acceleration" feel
        render: () => <OptimizationSettings />,
      });

      baseCategories.push({
        id: "admin",
        label: "Admin",
        sections: [
          { id: "training", label: "Training", icon: GraduationCap, render: () => <TrainingSettingsPanel /> },
          { id: "communications", label: "Communications", icon: MessageSquareMore, render: () => <CommsCenterPage /> },
        ],
      });
    }

    return baseCategories;
  }, [adminMode, inSheet]);

  const allSections = categories.flatMap((category) => category.sections);
  const [activeCategoryId, setActiveCategoryId] = useState<string>(categories[0]?.id || "assistant");
  const activeCategory = categories.find((category) => category.id === activeCategoryId) || categories[0];
  const [activeSectionId, setActiveSectionId] = useState<string>(allSections[0]?.id || "behavior");
  const activeSection = allSections.find((section) => section.id === activeSectionId) || allSections[0];

  const handleCategoryChange = (categoryId: string) => {
    setActiveCategoryId(categoryId);
    const nextCategory = categories.find((category) => category.id === categoryId);
    if (!nextCategory) return;
    
    // Check if the current section ID exists in the new category
    const currentSectionInNextCategory = nextCategory.sections.find((s) => s.id === activeSectionId);
    if (!currentSectionInNextCategory) {
      setActiveSectionId(nextCategory.sections[0]?.id || activeSectionId);
    }
  };

  return (
    <div className={inSheet ? "p-4" : "space-y-8"}>
      {!inSheet && (
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <Cog className="h-6 w-6 text-primary" />
            <h2 className="text-3xl font-bold tracking-tight text-foreground">Application Settings</h2>
          </div>
          <p className="text-sm text-muted-foreground max-w-2xl">
            Fine-tune Karen's intelligence, manage your personal data, and configure system runtime parameters.
          </p>
        </div>
      )}

      {!inSheet && <Separator className="bg-border/40" />}

      <div className="space-y-6">
        {/* Primary Tabs */}
        <Tabs value={activeCategoryId} onValueChange={handleCategoryChange} className="w-full">
          <TabsList className="grid h-auto w-full grid-cols-1 gap-2 rounded-2xl border border-border/40 bg-muted/30 p-1 text-foreground sm:grid-cols-3 lg:w-[600px]">
            {categories.filter(c => c.id !== 'admin').map((category) => (
              <TabsTrigger
                key={category.id}
                value={category.id}
                className="rounded-xl border border-transparent px-4 py-2 text-sm font-semibold transition-all data-[state=active]:border-border/60 data-[state=active]:bg-background data-[state=active]:text-primary data-[state=active]:shadow-sm"
              >
                {category.label}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>

        {activeCategory && (
          <div className="flex flex-col gap-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
            {/* Sub-menu (Section Selectors) */}
            <div className="flex flex-col gap-3 rounded-2xl border border-border/40 bg-card/40 p-4 shadow-sm backdrop-blur-sm">
              <div className="flex items-center gap-2 px-1">
                <div className="h-1 w-1 rounded-full bg-primary" />
                <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/80">
                  {activeCategory.label} Configuration
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {activeCategory.sections.map((section) => {
                  const Icon = section.icon;
                  const isActive = section.id === activeSectionId;
                  return (
                    <button
                      key={section.id}
                      type="button"
                      onClick={() => setActiveSectionId(section.id)}
                      className={[
                        "inline-flex items-center gap-2 rounded-full border px-4 py-1.5 text-sm font-medium transition-all",
                        isActive
                          ? "border-primary/40 bg-primary/10 text-primary shadow-sm"
                          : "border-border/40 bg-muted/20 text-muted-foreground hover:border-border/80 hover:bg-muted/40 hover:text-foreground",
                      ].join(" ")}
                    >
                      <Icon className="h-4 w-4" />
                      <span>{section.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Content Area */}
            <section className="min-w-0 space-y-6">
              {activeSection && (
                <div className="animate-in fade-in duration-500">
                  <div className="mb-4 flex items-center justify-between">
                    <div>
                      <h3 className="text-xl font-bold tracking-tight text-foreground">{activeSection.label}</h3>
                      <p className="text-xs font-medium text-muted-foreground/70 uppercase tracking-wide">
                        {activeCategory.label} &rsaquo; {activeSection.label}
                      </p>
                    </div>
                  </div>
                  <Separator className="mb-6 bg-border/40" />
                  <div className="rounded-xl">
                    {activeSection.render()}
                  </div>
                </div>
              )}
            </section>
          </div>
        )}
      </div>
    </div>
  );
}

