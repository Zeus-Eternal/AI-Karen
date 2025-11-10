"use client";

import React from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  CardFooter,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  CalendarDays,
  Clock,
  AlertTriangle,
  Info,
  Settings2,
  KeyRound,
  Globe,
} from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { alertClassName } from "./utils/alertVariants";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";

/**
 * @file DateTimePluginPage.tsx
 * @description Page describing Karen AI's Date & Time services, the services used, and conceptual options for future enhancements.
 * Interaction for current date/time is primarily via chat.
 */
export default function DateTimePluginPage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center space-x-3">
        <CalendarDays className="h-8 w-8 text-primary" />
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Date &amp; Time Service</h2>
          <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
            Karen AI can provide the current date and time, including for specific locations.
          </p>
        </div>
      </div>

      {/* How to use */}
      <Alert>
        <Info className="h-4 w-4" />
        <AlertTitle>How to Use Date &amp; Time Features</AlertTitle>
        <AlertDescription>
          Ask Karen in chat for the current date/time. Examples:
          <ul className="list-disc list-inside pl-4 mt-1 text-xs sm:text-sm md:text-base">
            <li>&quot;What&apos;s the date today?&quot;</li>
            <li>&quot;What time is it?&quot;</li>
            <li>&quot;What&apos;s the time in London?&quot; or &quot;Time in Detroit, MI&quot;</li>
          </ul>
        </AlertDescription>
      </Alert>

      {/* Capabilities */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Current Date &amp; Time Capabilities</CardTitle>
          <CardDescription>
            Karen uses the following methods to provide date and time:
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-start">
            <CalendarDays className="mr-3 h-5 w-5 text-muted-foreground flex-shrink-0 mt-1" />
            <div>
              <h4 className="font-medium">Current Date</h4>
              <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                Provided based on the server&apos;s current system settings.
              </p>
            </div>
          </div>

          <div className="flex items-start">
            <Clock className="mr-3 h-5 w-5 text-muted-foreground flex-shrink-0 mt-1" />
            <div>
              <h4 className="font-medium">Current Time</h4>
              <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                • General queries (&quot;What time is it?&quot;): based on the server&apos;s current system time.
                <br />
                • Specific locations (&quot;Time in Paris?&quot;): fetched via free public services:
              </p>
              <ul className="list-disc list-inside pl-5 mt-1 text-xs text-muted-foreground sm:text-sm md:text-base">
                <li>
                  Primary:{" "}
                  <a
                    href="https://timeapi.io/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="underline"
                  >
                    timeapi.io
                  </a>
                </li>
                <li>
                  Secondary:{" "}
                  <a
                    href="https://worldtimeapi.org/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="underline"
                  >
                    worldtimeapi.org
                  </a>
                </li>
              </ul>
              <p className="text-xs text-muted-foreground mt-1 sm:text-sm md:text-base">
                These services try to resolve common location names. If they fail, Karen will ask you to rephrase the
                location.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Separator />

      {/* Future enhancements */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center">
            <Settings2 className="mr-2 h-5 w-5 text-primary/80" />
            Future Enhancements &amp; Custom Setup (Conceptual)
          </CardTitle>
          <CardDescription>
            For more precise location-based time (especially for ambiguous places), integrate a premium or API-key
            service in the future.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Custom service select (disabled demo) */}
          <div className="space-y-2">
            <Label htmlFor="custom-time-service" className="flex items-center">
              <Globe className="mr-2 h-4 w-4 text-muted-foreground" />
              Custom Time Service
            </Label>
            <Select disabled>
              <SelectTrigger id="custom-time-service" aria-label="Select custom time service">
                <SelectValue placeholder="Select a service (e.g., Google Time Zone API)" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="google_tz">Google Time Zone API (Requires API Key)</SelectItem>
                <SelectItem value="timezonedb">TimezoneDB (Requires API Key)</SelectItem>
                <SelectItem value="other">Other Custom Service</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* API Key */}
          <div className="space-y-2">
            <Label htmlFor="custom-time-api-key" className="flex items-center">
              <KeyRound className="mr-2 h-4 w-4 text-muted-foreground" />
              API Key (for selected custom service)
            </Label>
            <Input
              id="custom-time-api-key"
              placeholder="Enter API key for the selected service"
              disabled
              type="password"
            />
          </div>

          {/* Endpoint */}
          <div className="space-y-2">
            <Label htmlFor="custom-time-endpoint">Custom Endpoint URL (if applicable)</Label>
            <Input id="custom-time-endpoint" placeholder="Enter custom API endpoint if needed" disabled />
          </div>

          {/* Dev note */}
          <Alert>
            <Info className="h-4 w-4" />
            <AlertTitle>Developer Note</AlertTitle>
            <AlertDescription>
              This section is conceptual. Integrating a new time service would require updating Karen&apos;s core tools
              (<code className="px-1">src/ai/tools/core-tools.ts</code>) to call the API, normalize its response, and
              manage credentials securely.
            </AlertDescription>
          </Alert>
        </CardContent>
        <CardFooter className="flex justify-end">
          <Button disabled>Save Custom Time Service Settings</Button>
        </CardFooter>
      </Card>

      {/* Accuracy note */}
      <Alert className={alertClassName("destructive")}>
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>Note on Location Accuracy</AlertTitle>
        <AlertDescription>
          Free services like <code>timeapi.io</code> and <code>worldtimeapi.org</code> are convenient but may not
          perfectly resolve all location names. Production systems typically rely on geolocation + time zone APIs with
          API keys for consistency and coverage.
        </AlertDescription>
      </Alert>
    </div>
  );
}
