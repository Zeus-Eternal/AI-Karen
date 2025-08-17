
"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import ApiKeyManager from "./ApiKeyManager";
import BehaviorSettings from "./BehaviorSettings";
import PersonalFactsSettings from "./PersonalFactsSettings";
import NotificationSettings from "./NotificationSettings";
import PrivacySettings from "./PrivacySettings";
import VoiceSettings from "./VoiceSettings";
import PersonaSettings from "./PersonaSettings";
import LLMSettings from "./LLMSettings";
import CopilotKitSettings from "./CopilotKitSettings";
import { Cog, KeyRound, BookText, Bell, Shield, Speaker, UserCog, Brain, Bot } from "lucide-react";
import { Separator } from "@/components/ui/separator";

/**
 * @file SettingsDialog.tsx
 * @description Main component for displaying all application settings.
 * It uses a tabbed interface to organize different settings categories.
 * This component is intended to be rendered as a main view.
 */
export default function SettingsDialog() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight">Application Settings</h2>
        <p className="text-sm text-muted-foreground">
          Customize Karen AI's behavior, API connections, personal knowledge, notifications, and more. Your preferences are saved locally in your browser.
        </p>
      </div>
      <Separator />
      <Tabs defaultValue="api-key" className="w-full">
        <TabsList className="flex flex-wrap w-full justify-start shrink-0">
          <TabsTrigger value="llm">
            <Brain className="mr-1 sm:mr-2 h-4 w-4" /> LLM
          </TabsTrigger>
          <TabsTrigger value="copilotkit">
            <Bot className="mr-1 sm:mr-2 h-4 w-4" /> CopilotKit
          </TabsTrigger>
          <TabsTrigger value="api-key">
            <KeyRound className="mr-1 sm:mr-2 h-4 w-4" /> API Key
          </TabsTrigger>
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
        </TabsList>

        {/* This div ensures padding and allows content to grow within the main scrollable area */}
        <div className="mt-4"> 
          <TabsContent value="llm">
            <LLMSettings />
          </TabsContent>
          <TabsContent value="copilotkit">
            <CopilotKitSettings />
          </TabsContent>
          <TabsContent value="api-key">
            <ApiKeyManager />
          </TabsContent>
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
            <PersonaSettings />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
}
