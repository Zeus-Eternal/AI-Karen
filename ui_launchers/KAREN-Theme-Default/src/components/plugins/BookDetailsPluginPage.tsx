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
import ResponsiveCardGrid from "@/components/ui/responsive-card-grid";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Database,
  Info,
  AlertTriangle,
  TableIcon,
  Edit3,
  Trash2,
  PlusSquare,
  MessageSquare,
} from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { alertClassName } from "./utils/alertVariants";

/**
 * @file BookDetailsPluginPage.tsx (Filename remains due to constraints, but content is Database Connector)
 * @description Conceptual SQL Database Connector plugin UI.
 * NOTE: This is a non-functional demo; real connections require a secure backend service.
 */
export default function DatabaseConnectorPluginPage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center space-x-3">
        <Database className="h-8 w-8 text-primary" />
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">
            Database Connector Plugin (Conceptual)
          </h2>
          <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
            Connect to external SQL databases, explore schemas, and interact with your data.
          </p>
        </div>
      </div>

      {/* Concept Warning */}
      <Alert className={alertClassName("destructive")}>
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>Conceptual Demonstration & Mocked Functionality</AlertTitle>
        <AlertDescription>
          The UI elements on this page are for demonstration purposes and are{" "}
          <strong>not currently functional</strong>. Implementing live SQL database connections
          and interactions requires a secure backend service.
          <br />
          Karen AI includes a mocked tool example that simulates querying a database via chat.
          Try asking:
          <ul className="list-disc list-inside pl-4 mt-1">
            <li>&ldquo;Tell me about the item &lsquo;Dune&rsquo;&rdquo;</li>
            <li>&ldquo;What do you know about &lsquo;The Great Gatsby&rsquo;?&rdquo;</li>
          </ul>
        </AlertDescription>
      </Alert>

      {/* Connection Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Database Connection Settings</CardTitle>
          <CardDescription>
            Configure the connection to your external SQL database (Non-functional placeholder).
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="db-server">Server Address</Label>
              <Input id="db-server" placeholder="e.g., mydb.server.com" disabled />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="db-port">Port</Label>
              <Input id="db-port" placeholder="e.g., 5432" type="number" disabled />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="db-user">Username</Label>
              <Input id="db-user" placeholder="Enter username" disabled />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="db-password">Password</Label>
              <Input id="db-password" type="password" placeholder="Enter password" disabled />
            </div>
            <div className="space-y-1.5 md:col-span-2">
              <Label htmlFor="db-name">Database Name</Label>
              <Input id="db-name" placeholder="Enter database name" disabled />
            </div>
          </div>
        </CardContent>
        <CardFooter className="flex justify-end">
          <Button disabled>Connect to Database</Button>
        </CardFooter>
      </Card>

      <Separator />

      {/* Database Explorer */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Database Explorer</CardTitle>
          <CardDescription>View discovered tables and their data (Conceptual placeholder).</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveCardGrid className="md:grid-cols-3">
            <div className="md:col-span-1 space-y-3">
              <h4 className="font-medium text-sm flex items-center md:text-base lg:text-lg">
                <TableIcon className="mr-2 h-4 w-4" />
                Discovered Tables
              </h4>
              <div className="h-48 border rounded-md p-3 bg-muted/50 overflow-y-auto sm:p-4 md:p-6">
                <p className="text-xs text-muted-foreground italic sm:text-sm md:text-base">
                  (Table list would appear here)
                </p>
                <ul className="mt-2 space-y-1">
                  <li className="p-1.5 rounded bg-background/50 text-xs sm:text-sm md:text-base">
                    items (example table)
                  </li>
                  <li className="p-1.5 rounded bg-background/50 text-xs sm:text-sm md:text-base">
                    categories (example table)
                  </li>
                </ul>
              </div>
            </div>

            <div className="md:col-span-2 space-y-3">
              <h4 className="font-medium text-sm md:text-base lg:text-lg">
                Selected Table Data:{" "}
                <span className="text-muted-foreground italic">(No table selected)</span>
              </h4>
              <div className="h-48 border rounded-md p-3 bg-muted/50 overflow-y-auto sm:p-4 md:p-6">
                <p className="text-xs text-muted-foreground italic sm:text-sm md:text-base">
                  (Data rows would appear here)
                </p>
              </div>
            </div>
          </ResponsiveCardGrid>
        </CardContent>
      </Card>

      <Separator />

      {/* Data Interaction */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Data Interaction Methods</CardTitle>
          <CardDescription>Choose how to query or modify data (Conceptual placeholder).</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* NLQ via Chat */}
          <div>
            <Label htmlFor="nlq-query" className="flex items-center mb-1">
              <MessageSquare className="mr-2 h-4 w-4" />
              Natural Language Query (via Chat with Karen)
            </Label>
            <Textarea
              id="nlq-query"
              placeholder="Ask Karen in the chat, e.g., 'Show me details for item_id 123 from the main_items table'"
              rows={3}
              disabled
            />
            <Button className="mt-2" disabled>
              Run Query (Use Chat Instead)
            </Button>
          </div>

          {/* CRUD Controls */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 items-end">
            <div className="space-y-1.5">
              <Label htmlFor="table-select">Select Table for CRUD</Label>
              <Select disabled>
                <SelectTrigger id="table-select" aria-label="Select table">
                  <SelectValue placeholder="Select a table" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="items">items (example)</SelectItem>
                  <SelectItem value="categories">categories (example)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center flex-wrap gap-2">
              <Button variant="outline" disabled>
                <TableIcon className="mr-1.5 h-4 w-4" />
                View Data
              </Button>
              <Button variant="outline" disabled>
                <PlusSquare className="mr-1.5 h-4 w-4" />
                Add Row
              </Button>
              <Button variant="outline" disabled>
                <Edit3 className="mr-1.5 h-4 w-4" />
                Edit Selected
              </Button>
              <Button variant="destructive" disabled>
                <Trash2 className="mr-1.5 h-4 w-4" />
                Delete Selected
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Concept How-To */}
      <Alert>
        <Info className="h-4 w-4" />
        <AlertTitle>How to Use This Conceptual Plugin</AlertTitle>
        <AlertDescription>
          Interact with the conceptual &ldquo;Database Query&rdquo; tool by asking Karen AI directly
          in the main chat interface. For example:
          <ul className="list-disc list-inside pl-4 mt-1">
            <li>&ldquo;What do you know about the item &lsquo;Dune&rsquo;?&rdquo;</li>
            <li>&ldquo;Can you give me details for &lsquo;The Great Gatsby&rsquo; from the database?&rdquo;</li>
          </ul>
          This page illustrates future possibilities for direct database interaction.
        </AlertDescription>
      </Alert>
    </div>
  );
}
