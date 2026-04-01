
"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import ApiKeyManager from "./ApiKeyManager";
import BehaviorSettings from "./BehaviorSettings";
import PersonalFactsSettings from "./PersonalFactsSettings";
import NotificationSettings from "./NotificationSettings";
import PrivacySettings from "./PrivacySettings";
import VoiceSettings from "./VoiceSettings";
import PersonaSettings from "./PersonaSettings";
import ModelSettings from "./ModelSettings";
import { Cog, KeyRound, BookText, Bell, Shield, Speaker, UserCog, Bot, GraduationCap } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import TrainingSettingsPanel from "@/components/admin/TrainingSettingsPanel";
import CommsCenterPage from "@/components/comms/CommsCenterPage";

interface SettingsDialogProps {
  inSheet?: boolean;
  adminMode?: boolean;
}

/**
 * @file SettingsDialog.tsx
 * @description Main component for displaying all application settings.
 * It uses a tabbed interface to organize different settings categories.
 * This component is intended to be rendered as a main view or within a sheet.
 */
export default function SettingsDialog({ inSheet = false, adminMode = false }: SettingsDialogProps) {
  return (
    <div className={inSheet ? "p-4" : "space-y-6"}>
      {!inSheet && (
        <>
          <div>
            <h2 className="text-2xl font-semibold tracking-tight">Application Settings</h2>
            <p className="text-sm text-muted-foreground">
              Customize Karen AI&apos;s behavior, personal knowledge, notifications, and model configuration. Settings are applied through Karen&apos;s current persistence and backend integrations.
            </p>
          </div>
          <Separator />
        </>
      )}
      <Tabs defaultValue="behavior" className="w-full">
        <TabsList className="flex flex-wrap w-full justify-start shrink-0 h-auto">
          <TabsTrigger value="behavior">
            <Cog className="mr-1 sm:mr-2 h-4 w-4" /> Behavior
          </TabsTrigger>
          <TabsTrigger value="persona">
            <UserCog className="mr-1 sm:mr-2 h-4 w-4" /> Persona
          </TabsTrigger>
          <TabsTrigger value="personal-facts">
            <BookText className="mr-1 sm:mr-2 h-4 w-4" /> Facts
          </TabsTrigger>
          <TabsTrigger value="voice">
            <Speaker className="mr-1 sm:mr-2 h-4 w-4" /> Voice
          </TabsTrigger>
          <TabsTrigger value="notifications">
            <Bell className="mr-1 sm:mr-2 h-4 w-4" /> Alerts
          </TabsTrigger>
          <TabsTrigger value="privacy">
            <Shield className="mr-1 sm:mr-2 h-4 w-4" /> Privacy
          </TabsTrigger>
           <TabsTrigger value="model-placeholder">
            <Bot className="mr-1 sm:mr-2 h-4 w-4" /> Model
          </TabsTrigger>
           <TabsTrigger value="apikey-placeholder">
            <KeyRound className="mr-1 sm:mr-2 h-4 w-4" /> API Keys
          </TabsTrigger>
          {adminMode && (
            <TabsTrigger value="training">
              <GraduationCap className="mr-1 sm:mr-2 h-4 w-4" /> Training
            </TabsTrigger>
          )}
          {adminMode && (
            <TabsTrigger value="communications">
              <Bell className="mr-1 sm:mr-2 h-4 w-4" /> Communications
            </TabsTrigger>
          )}
        </TabsList>

        {/* This div ensures padding and allows content to grow within the main scrollable area */}
        <div className="mt-4"> 
          <TabsContent value="behavior">
            <BehaviorSettings />
          </TabsContent>
          <TabsContent value="personal-facts">
            <PersonalFactsSettings />
          </TabsContent>
          <TabsContent value="notifications">
            <NotificationSettings />
          </TabsContent>
          <TabsContent value="privacy">
            <PrivacySettings />
          </TabsContent>
          <TabsContent value="voice">
            <VoiceSettings />
          </TabsContent>
          <TabsContent value="persona">
            <PersonaSettings inSheet={inSheet} />
          </TabsContent>
           <TabsContent value="model-placeholder">
            <ModelSettings />
          </TabsContent>
           <TabsContent value="apikey-placeholder">
            <ApiKeyManager />
          </TabsContent>
          {adminMode && (
            <TabsContent value="training">
              <TrainingSettingsPanel />
            </TabsContent>
          )}
          {adminMode && (
            <TabsContent value="communications">
              <CommsCenterPage />
            </TabsContent>
          )}
        </div>
      </Tabs>
    </div>
  );
}
