
"use client";

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/hooks/use-toast';
import { AlertCircle, Info } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';

/**
 * @file PrivacySettings.tsx
 * @description Component for displaying privacy-related information and guidance on data control.
 * Explains what data is stored locally and how users can manage it.
 */
export default function PrivacySettings() {
  const { toast } = useToast();

  const handlePlaceholderClick = (featureName: string) => {
    toast({
      title: `${featureName} (Planned Feature)`,
      description: `This functionality requires backend implementation and is not yet active.`,
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Privacy & Data Control</CardTitle>
        <CardDescription>
          Understand how Karen AI handles your data and manage your preferences.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        
        <Alert variant="default" className="bg-background border-border">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle className="font-semibold text-sm">Local Browser Storage</AlertTitle>
            <AlertDescription className="text-xs text-muted-foreground space-y-1">
                <p>Karen AI stores your settings and some personalization data directly in your browser's local storage. This ensures your preferences are remembered across sessions on this specific browser. This data includes:</p>
                <ul className="list-disc list-inside pl-4">
                    <li><strong>API Key (for convenience):</strong> The Google AI API key you enter in the "API Key" tab is saved here to pre-fill the field. For the AI to function, this key must also be configured server-side (typically in an <code>.env</code> file).</li>
                    <li><strong>Behavior Settings:</strong> Your choices for Karen's memory depth, personality tone, verbosity, and active listening mode (from the "Behavior" tab).</li>
                    <li><strong>Persona Instructions:</strong> Custom directives you provide for Karen's core persona (from the "Persona" tab).</li>
                    <li><strong>Personal Facts:</strong> Facts you manually add or confirm for Karen to remember about you (managed in the "Facts" tab).</li>
                    <li><strong>Voice Preferences:</strong> Your selected Text-To-Speech voice (from the "Voice" tab).</li>
                    <li><strong>Notification Preferences:</strong> Your choices for in-app alerts (from the "Alerts" tab).</li>
                    <li><strong>Plugin-Specific Settings:</strong> Configuration for plugins like the Weather service (default location, temperature unit).</li>
                </ul>
                <p className="mt-2">
                  <strong>Your Control:</strong> You can modify or clear most of this data through the respective settings tabs. To remove all locally stored data for this application, you can clear your browser's site data for this specific website.
                </p>
            </AlertDescription>
        </Alert>
        
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-foreground">Managing Personal Information</h3>
          <p className="text-xs text-muted-foreground">
            You have direct control over the personal facts Karen remembers. Visit the "Facts" tab to add, review, delete, or confirm facts. Confirmed facts are used to personalize your interactions.
          </p>
        </div>

        <Separator />

        <div className="space-y-2">
          <h3 className="text-sm font-medium text-foreground">Clearing Current Chat Display</h3>
          <p className="text-xs text-muted-foreground">
            To visually clear the messages displayed in the current chat window and start a fresh chat session, simply refresh your browser page. Karen's memory of past topics in new sessions will depend on your "Memory Depth" settings and any "Personal Facts" you've saved.
          </p>
        </div>

        <Separator />

        <div className="space-y-2">
          <h3 className="text-sm font-medium text-foreground">Server-Side Data (Conceptual)</h3>
           <Alert variant="default" className="bg-muted/30">
            <Info className="h-4 w-4 !text-accent-foreground" />
            <AlertTitle className="font-semibold text-accent-foreground text-sm">Information: Server Data</AlertTitle>
            <AlertDescription className="text-muted-foreground text-xs">
              This application primarily uses data stored locally in your browser for settings and personalization. Any persistent storage of user accounts or extensive conversation histories on a server would be governed by the application's backend and its own privacy policy. Currently, there are no specific user settings here for managing server-side data retention, as the focus is on local storage and in-session memory.
            </AlertDescription>
          </Alert>
        </div>
        
        <Separator />

        <div className="space-y-2">
          <h3 className="text-sm font-medium text-foreground">Account Data Deletion Request (Conceptual)</h3>
          <p className="text-xs text-muted-foreground mb-2">
            If this application supported server-side user accounts with persistent data storage, a mechanism to request the deletion of that account and associated data would be provided here.
          </p>
          <Button 
            variant="outline" 
            onClick={() => handlePlaceholderClick("Full Data Deletion Request")}
            className="w-full sm:w-auto"
            disabled
          >
            Request Full Data Deletion (Conceptual Feature)
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
