
"use client";

import * as React from 'react';
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import ResponsiveCardGrid from "@/components/ui/responsive-card-grid";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Mail, Send, Inbox, Settings, AlertTriangle, Info, Zap, KeyRound } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { alertClassName } from "./utils/alertVariants";
import { Switch } from "@/components/ui/switch";

/**
 * @file GmailPluginPage.tsx
 * @description Page for configuring the Gmail plugin. Users can store
 * credentials locally and interact with Karen to read or compose emails.
 */
export default function GmailPluginPage() {
  const [username, setUsername] = useState<string>(() =>
    typeof window !== "undefined" ? localStorage.getItem("gmail_username") || "" : ""
  );
  const [appPassword, setAppPassword] = useState<string>(() =>
    typeof window !== "undefined" ? localStorage.getItem("gmail_app_password") || "" : ""
  );

  const saveCreds = () => {
    localStorage.setItem("gmail_username", username);
    localStorage.setItem("gmail_app_password", appPassword);
  };


  return (
    <div className="space-y-8">
      <div className="flex items-center space-x-3">
        <Mail className="h-8 w-8 text-red-600 " />
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Gmail Integration</h2>
          <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
            Karen can check unread messages or compose new ones on your behalf.. If the
            backend is configured with a valid <code>GMAIL_API_TOKEN</code>,
            real Gmail actions will be performed;
          </p>
        </div>
      </div>

      <Alert className={alertClassName("destructive")}>
        Karen can check unread messages or compose new ones on your behalf.
        <AlertTriangle className="h-4 w-4 " />
        <AlertTitle>About Gmail Integration</AlertTitle>
        <AlertDescription>
          <p>
            When the backend has a valid <code>GMAIL_API_TOKEN</code> configured,
            drafts. Without it, these actions are simulated for demo purposes.
          </p>
          <p className="mt-2">You can try the features via chat:</p>
          <ul className="list-disc list-inside pl-4 mt-1 text-xs sm:text-sm md:text-base">
            <li>"Check my unread emails."</li>
            <li>"Compose an email to example@example.com with subject 'Hello' and body 'Just saying hi!'"</li>
          </ul>
        </AlertDescription>
      </Alert>

      {/* Connection Settings Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Gmail Credentials</CardTitle>
          <CardDescription>
            Store your credentials locally for the Gmail plugin. In production an OAuth flow should be used instead.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="gmail-user">Gmail Username</Label>
            <input id="gmail-user" value={username} onChange={(e) => setUsername(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="gmail-pass" className="flex items-center"><KeyRound className="mr-2 h-4 w-4 text-primary/80 "/>App Password</Label>
            <input id="gmail-pass" type="password" value={appPassword} onChange={(e) => setAppPassword(e.target.value)} />
            <p className="text-xs text-muted-foreground sm:text-sm md:text-base">Use a Gmail app password for SMTP/IMAP access.</p>
          </div>
        </CardContent>
        <CardFooter className="flex justify-end">
          <Button onClick={saveCreds} >Save Credentials</Button>
        </CardFooter>
      </Card>

      <Separator />

      {/* Available Actions Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Available Actions (via Chat)</CardTitle>
          <CardDescription>
            Ask Karen in the chat to check your unread emails or compose a message.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveCardGrid>
          <div className="p-3 border rounded-md bg-muted/30 sm:p-4 md:p-6">
            <div className="flex items-center mb-1">
              <Inbox className="mr-2 h-4 w-4 text-primary/80 "/>
              <h4 className="font-medium text-sm md:text-base lg:text-lg">Check Unread Emails</h4>
            </div>
            <p className="text-xs text-muted-foreground sm:text-sm md:text-base">Ask Karen: "Check my unread emails."</p>
          </div>
          <div className="p-3 border rounded-md bg-muted/30 sm:p-4 md:p-6">
             <div className="flex items-center mb-1">
              <Send className="mr-2 h-4 w-4 text-primary/80 "/>
              <h4 className="font-medium text-sm md:text-base lg:text-lg">Compose New Email</h4>
            </div>
            <p className="text-xs text-muted-foreground sm:text-sm md:text-base">Ask Karen: "Compose an email to..."</p>
          </div>
          </ResponsiveCardGrid>
        </CardContent>
      </Card>

      <Separator />

      {/* Premium Automations Section (Conceptual) */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center">
            <Zap className="mr-2 h-5 w-5 text-primary/80 " />
            Premium Automations (Conceptual)
          </CardTitle>
          <CardDescription>
            Set up advanced automated tasks for Karen to perform with your Gmail account. (Requires backend implementation).
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between p-4 border rounded-lg bg-muted/30 sm:p-4 md:p-6">
            <div>
              <Label htmlFor="auto-check-unread" className="font-medium">Periodically Check for Important Unread Emails</Label>
              <p className="text-xs text-muted-foreground sm:text-sm md:text-base">Karen will periodically check for new unread emails matching certain criteria and notify you in the Comms Center.</p>
            </div>
            <Switch id="auto-check-unread" disabled />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email-check-criteria">Criteria for "Important" (conceptual)</Label>
            <input id="email-check-criteria" type="text" placeholder="e.g., From:boss@example.com, Subject contains:Urgent" disabled />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email-check-frequency">Check frequency (conceptual)</Label>
            <input id="email-check-frequency" type="text" placeholder="e.g., Every 30 minutes, Hourly" disabled />
          </div>
            <Alert className={alertClassName("default", "bg-background")}>
            <Info className="h-4 w-4 " />
            <AlertTitle className="text-sm font-semibold md:text-base lg:text-lg">Future Feature</AlertTitle>
            <AlertDescription className="text-xs sm:text-sm md:text-base">
              This automation section is a placeholder. Implementing background tasks for Gmail requires dedicated backend services for scheduling, secure authentication (OAuth refresh tokens), and email processing logic.
            </AlertDescription>
          </Alert>
        </CardContent>
        <CardFooter className="flex justify-end">
          <Button disabled >Save Gmail Automations</Button>
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
            <textarea id="gmail-signature" placeholder="e.g., Best regards, [Your Name]" rows={3} disabled />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="gmail-notifications">Notification Preferences for Gmail</Label>
            <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
              (Placeholder for settings like 'Notify on new important emails', etc.)
            </p>
          </div>
        </CardContent>
        <CardFooter className="flex justify-end">
          <Button disabled >Save Gmail Settings</Button>
        </CardFooter>
      </Card>
    </div>
  );
}

