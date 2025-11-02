
"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { CalendarDays, Clock, AlertTriangle, Info, Settings2, KeyRound, Globe } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";

/**
 * @file DateTimePluginPage.tsx
 * @description Page describing Karen AI's Date & Time services, the services used, and conceptual options for future enhancements.
 * Interaction for current date/time is primarily via chat.
 */
export default function DateTimePluginPage() {
  return (
    <div className="space-y-8">
      <div className="flex items-center space-x-3">
        <CalendarDays className="h-8 w-8 text-primary" />
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Date & Time Service</h2>
          <p className="text-sm text-muted-foreground">
            Karen AI can provide the current date and time, including for specific locations.
          </p>
        </div>
      </div>

       <Alert>
        <Info className="h-4 w-4" />
        <AlertTitle>How to Use Date & Time Features</AlertTitle>
        <AlertDescription>
          <p>You can ask Karen AI for the current date or time directly in the chat interface. For example:</p>
          <ul className="list-disc list-inside pl-4 mt-1 text-xs">
              <li>"What's the date today?"</li>
              <li>"What time is it?"</li>
              <li>"What's the time in London?" or "Time in Detroit, MI"</li>
          </ul>
        </AlertDescription>
      </Alert>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Current Date & Time Capabilities</CardTitle>
          <CardDescription>
            Karen uses the following methods to provide date and time:
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-start">
            <CalendarDays className="mr-3 h-5 w-5 text-muted-foreground flex-shrink-0 mt-1" />
            <div>
              <h4 className="font-medium">Current Date</h4>
              <p className="text-xs text-muted-foreground">
                Provided based on the server's current system settings.
              </p>
            </div>
          </div>
          <div className="flex items-start">
            <Clock className="mr-3 h-5 w-5 text-muted-foreground flex-shrink-0 mt-1" />
            <div>
              <h4 className="font-medium">Current Time</h4>
              <p className="text-xs text-muted-foreground">
                - For general queries ("What time is it?"): Provided based on the server's current system time.
                <br />
                - For specific locations ("Time in Paris?"): Karen attempts to fetch this using a combination of free, public time services:
              </p>
              <ul className="list-disc list-inside pl-5 mt-1 text-xs text-muted-foreground">
                  <li>Primary: <a href="https://timeapi.io/" target="_blank" rel="noopener noreferrer" className="underline">timeapi.io</a></li>
                  <li>Secondary: <a href="https://worldtimeapi.org/" target="_blank" rel="noopener noreferrer" className="underline">worldtimeapi.org</a></li>
              </ul>
              <p className="text-xs text-muted-foreground mt-1">
               These services try to resolve common location names. If they fail, Karen will ask you to rephrase the location.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Separator />

      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center">
            <Settings2 className="mr-2 h-5 w-5 text-primary/80" />
            Future Enhancements & Custom Setup (Conceptual)
          </CardTitle>
          <CardDescription>
            For a more consistently precise location-based time experience, especially for less common or ambiguously named locations, integrating a premium or API-key driven service could be an option in the future.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
            <div className="space-y-2">
                <Label htmlFor="custom-time-service" className="flex items-center">
                    <Globe className="mr-2 h-4 w-4 text-muted-foreground" />
                    Hypothetical Custom Time Service
                </Label>
                <Select disabled>
                    <SelectTrigger id="custom-time-service">
                    <SelectValue placeholder="Select a service (e.g., Google Time Zone API)" />
                    </SelectTrigger>
                    <SelectContent>
                    <SelectItem value="google_tz">Google Time Zone API (Requires API Key)</SelectItem>
                    <SelectItem value="timezonedb">TimezoneDB (Requires API Key)</SelectItem>
                    <SelectItem value="other">Other Custom Service</SelectItem>
                    </SelectContent>
                </Select>
            </div>
            <div className="space-y-2">
                <Label htmlFor="custom-time-api-key" className="flex items-center">
                    <KeyRound className="mr-2 h-4 w-4 text-muted-foreground" />
                    API Key (for selected custom service)
                </Label>
                <Input id="custom-time-api-key" placeholder="Enter API key for the selected service" disabled />
            </div>
            <div className="space-y-2">
                <Label htmlFor="custom-time-endpoint">Custom Endpoint URL (if applicable)</Label>
                <Input id="custom-time-endpoint" placeholder="Enter custom API endpoint if needed" disabled />
            </div>
            <Alert variant="default" className="bg-muted/30">
                <Info className="h-4 w-4 !text-accent-foreground" />
                <AlertTitle className="font-semibold text-accent-foreground text-sm">Developer Note</AlertTitle>
                <AlertDescription className="text-muted-foreground text-xs">
                This section is conceptual. Integrating a new time service would require updating Karen's core tools (`src/ai/tools/core-tools.ts`) to make calls to the new API, handle its specific response format, and manage the API key securely.
                </AlertDescription>
            </Alert>
        </CardContent>
        <CardFooter className="flex justify-end">
            <Button disabled>Save Custom Time Service Settings</Button>
        </CardFooter>
      </Card>


      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>Note on Location Accuracy</AlertTitle>
        <AlertDescription>
          Free time services like `timeapi.io` and `worldtimeapi.org` are convenient but may not always perfectly resolve all location name variations. For the most robust experience with a wide range of locations, dedicated geolocation and time zone APIs (often requiring API keys) are typically used in production systems.
        </AlertDescription>
      </Alert>

    </div>
  );
}

