
"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Database, Info, AlertTriangle, MessageSquare } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

/**
 * @file DatabaseConnectorPluginPage.tsx
 * @description Page describing the current Item Details Lookup feature, which uses a mocked tool
 * to simulate querying a database for specific item examples (like 'Dune' or 'Gatsby').
 * Interaction is via the chat interface.
 */
export default function DatabaseConnectorPluginPage() {
  return (
    <div className="space-y-8">
      <div className="flex items-center space-x-3">
        <Database className="h-8 w-8 text-primary" />
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Item Details Lookup (Simulated Database)</h2>
          <p className="text-sm text-muted-foreground">
            Karen AI can look up details for specific items using a simulated database.
          </p>
        </div>
      </div>

      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>Simulated Functionality & How to Use</AlertTitle>
        <AlertDescription>
          <p>The "Item Details Lookup" feature currently uses a **mocked (simulated) tool**. It does not connect to a live external database.</p>
          <p className="mt-2">Karen can provide details for a few pre-defined examples, such as the items 'Dune' or 'The Great Gatsby'.</p>
          <p className="mt-2">
            To use this feature, ask Karen directly in the chat interface. For example:
          </p>
          <ul className="list-disc list-inside pl-4 mt-1 text-xs">
            <li>"Tell me about the item 'Dune'"</li>
            <li>"What do you know about 'The Great Gatsby'?"</li>
          </ul>
           <p className="mt-2">This page serves as a placeholder for where settings for a more advanced, live database connector plugin might appear in the future.</p>
        </AlertDescription>
      </Alert>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Current Capability</CardTitle>
          <CardDescription>
            Karen can use her "Query Simulated Database" tool when you ask about specific items in the chat.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex items-center">
              <MessageSquare className="mr-2 h-5 w-5 text-muted-foreground" />
              <p className="text-sm">
                **Interaction Method:** Natural Language Query via Chat
              </p>
            </div>
            <p className="text-xs text-muted-foreground pl-7">
              Ask Karen directly in the main chat window for details about supported items. She will use her internal (mocked) tool to fetch this information.
            </p>
          </div>
        </CardContent>
      </Card>

      <Alert>
        <Info className="h-4 w-4" />
        <AlertTitle>Future Enhancements</AlertTitle>
        <AlertDescription>
          A future version of this plugin could potentially allow connections to live external SQL databases, offer schema exploration, and provide more advanced data interaction methods. For now, the functionality is limited to the simulated examples accessible via chat.
        </AlertDescription>
      </Alert>

    </div>
  );
}
