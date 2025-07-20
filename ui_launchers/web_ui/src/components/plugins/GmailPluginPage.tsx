
"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Mail, Send, Inbox, Settings, AlertTriangle, Info, Zap } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";

/**
 * @file GmailPluginPage.tsx
 * @description Page describing Karen AI's conceptual Gmail Integration plugin.
 * Users interact with mocked Gmail features (check unread, compose) via chat.
 * This page outlines where settings and real integration points would live.
 */
export default function GmailPluginPage() {
  return (
    <div className="space-y-8">
      <div className="flex items-center space-x-3">
        <Mail className="h-8 w-8 text-red-600" />
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Gmail Integration</h2>
          <p className="text-sm text-muted-foreground">
            Check unread emails or compose new ones with Karen's help (currently using mocked functionality).
          </p>
        </div>
      </div>

      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>Mocked Functionality & Future Integration</AlertTitle>
        <AlertDescription>
          <p>The Gmail features (checking unread, composing emails) are currently **mocked**. Karen will simulate these actions but does not connect to your actual Gmail account.</p>
          <p className="mt-1">Full Gmail integration requires secure account connection (OAuth 2.0) and backend services, which are planned for future development.</p>
          <p className="mt-2">You can try the mocked features via chat:</p>
          <ul className="list-disc list-inside pl-4 mt-1 text-xs">
            <li>"Check my unread emails."</li>
            <li>"Compose an email to example@example.com with subject 'Hello' and body 'Just saying hi!'"</li>
          </ul>
        </AlertDescription>
      </Alert>

      {/* Connection Settings Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Gmail Account Connection</CardTitle>
          <CardDescription>
            Connect your Gmail account to enable live features (Requires backend implementation).
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button className="w-full sm:w-auto" disabled>
            <Mail className="mr-2 h-4 w-4" /> Connect with Google (Gmail)
          </Button>
          <p className="text-xs text-muted-foreground">
            Status: Not Connected. Real connection requires OAuth flow and backend setup.
          </p>
        </CardContent>
      </Card>

      <Separator />

      {/* Available Actions Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Available Actions (via Chat)</CardTitle>
          <CardDescription>
            Interact with these mocked Gmail features by talking to Karen in the chat.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="p-3 border rounded-md bg-muted/30">
            <div className="flex items-center mb-1">
              <Inbox className="mr-2 h-4 w-4 text-primary/80"/>
              <h4 className="font-medium text-sm">Check Unread Emails</h4>
            </div>
            <p className="text-xs text-muted-foreground">Ask Karen: "Check my unread emails."</p>
          </div>
          <div className="p-3 border rounded-md bg-muted/30">
             <div className="flex items-center mb-1">
              <Send className="mr-2 h-4 w-4 text-primary/80"/>
              <h4 className="font-medium text-sm">Compose New Email</h4>
            </div>
            <p className="text-xs text-muted-foreground">Ask Karen: "Compose an email to..."</p>
          </div>
        </CardContent>
      </Card>

      <Separator />

      {/* Premium Automations Section (Conceptual) */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center">
            <Zap className="mr-2 h-5 w-5 text-primary/80" />
            Premium Automations (Conceptual)
          </CardTitle>
          <CardDescription>
            Set up advanced automated tasks for Karen to perform with your Gmail account. (Requires backend implementation).
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between p-4 border rounded-lg bg-muted/30">
            <div>
              <Label htmlFor="auto-check-unread" className="font-medium">Periodically Check for Important Unread Emails</Label>
              <p className="text-xs text-muted-foreground">Karen will periodically check for new unread emails matching certain criteria and notify you in the Comms Center.</p>
            </div>
            <Switch id="auto-check-unread" disabled />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email-check-criteria">Criteria for "Important" (conceptual)</Label>
            <Input id="email-check-criteria" type="text" placeholder="e.g., From:boss@example.com, Subject contains:Urgent" disabled />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email-check-frequency">Check frequency (conceptual)</Label>
            <Input id="email-check-frequency" type="text" placeholder="e.g., Every 30 minutes, Hourly" disabled />
          </div>
           <Alert variant="default" className="bg-background">
            <Info className="h-4 w-4" />
            <AlertTitle className="text-sm font-semibold">Future Feature</AlertTitle>
            <AlertDescription className="text-xs">
              This automation section is a placeholder. Implementing background tasks for Gmail requires dedicated backend services for scheduling, secure authentication (OAuth refresh tokens), and email processing logic.
            </AlertDescription>
          </Alert>
        </CardContent>
        <CardFooter className="flex justify-end">
          <Button disabled>Save Gmail Automations</Button>
        </CardFooter>
      </Card>
      
      <Separator />

      {/* Plugin Settings Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Plugin Settings (Conceptual)</CardTitle>
          <CardDescription>
            Configure default behaviors for the Gmail plugin (Conceptual placeholders).
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="gmail-signature">Default Email Signature</Label>
            <Textarea id="gmail-signature" placeholder="e.g., Best regards, [Your Name]" rows={3} disabled />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="gmail-notifications">Notification Preferences for Gmail</Label>
            <p className="text-xs text-muted-foreground">
              (Placeholder for settings like 'Notify on new important emails', etc.)
            </p>
          </div>
        </CardContent>
        <CardFooter className="flex justify-end">
          <Button disabled>Save Gmail Settings</Button>
        </CardFooter>
      </Card>
    </div>
  );
}

